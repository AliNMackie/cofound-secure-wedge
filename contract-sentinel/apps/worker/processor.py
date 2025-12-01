import json
import logging
import time
from typing import Dict, Any, List, Tuple
import io
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from google.cloud import dlp_v2
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel
from pypdf import PdfReader

from apps.worker.config import settings
from shared.models import JobStatus, ClauseAnalysis
from shared.database import FirestoreClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContractProcessor:
    def __init__(self):
        self.project_id = settings.PROJECT_ID
        self.location = settings.LOCATION
        
        # Initialize clients
        try:
            self.dlp_client = dlp_v2.DlpServiceClient()
            self.storage_client = storage.Client(project=self.project_id)
            self.firestore_client = FirestoreClient(project_id=self.project_id)
            
            vertexai.init(project=self.project_id, location=self.location)
            self.model = GenerativeModel("gemini-1.5-pro-002")
            self.shadow_model = GenerativeModel("gemini-1.5-flash-001")
        except Exception as e:
            logger.warning(f"Failed to initialize some Cloud clients: {e}")
            self.dlp_client = None
            self.storage_client = None
            self.firestore_client = None
            self.model = None
            self.shadow_model = None

    def download_text_from_gcs(self, gcs_uri: str) -> str:
        """Downloads PDF from GCS and extracts text."""
        try:
            # Parse GCS URI: gs://bucket/path/to/file
            parts = gcs_uri.replace("gs://", "").split("/")
            bucket_name = parts[0]
            blob_name = "/".join(parts[1:])
            
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            file_bytes = blob.download_as_bytes()
            
            # Extract text using pypdf
            reader = PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {gcs_uri}: {e}")
            raise

    def sanitize_document(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Redacts PII using Google Cloud DLP and returns redacted text + map.
        
        Returns:
            Tuple[str, Dict[str, str]]: (redacted_text, {token: original_value})
        """
        if not self.dlp_client:
            logger.warning("DLP client not initialized, skipping redaction.")
            return text, {}

        parent = f"projects/{self.project_id}"
        
        # Configure inspection rules
        inspect_config = {
            "info_types": [
                {"name": "PERSON_NAME"},
                {"name": "US_SOCIAL_SECURITY_NUMBER"}, 
                {"name": "EMAIL_ADDRESS"}
            ],
            "include_quote": True # We need the quote to know what to replace if we used offsets
        }
        
        item = {"value": text}
        
        try:
            # Step 1: Inspect to find PII
            response = self.dlp_client.inspect_content(
                request={
                    "parent": parent,
                    "inspect_config": inspect_config,
                    "item": item,
                }
            )
            
            # Step 2: Manually replace in reverse order to preserve offsets
            # Note: Python strings are immutable, so we'll build a new string or use list of chars.
            # However, for simplicity and correctness with byte offsets, 
            # we need to be careful about encoding. 
            # DLP offsets are in bytes (UTF-8).
            
            encoded_text = text.encode("utf-8")
            # Convert to bytearray for mutable modification
            mutable_text = bytearray(encoded_text)
            
            redaction_map = {}
            
            # Sort findings by start_byte_offset in descending order
            findings = sorted(
                response.result.findings, 
                key=lambda f: f.location.byte_range.start, 
                reverse=True
            )
            
            for finding in findings:
                start = finding.location.byte_range.start
                end = finding.location.byte_range.end
                original_value = finding.quote
                info_type = finding.info_type.name
                
                # Generate token
                token = f"[{info_type}_{uuid.uuid4().hex[:8]}]"
                
                # Store in map
                redaction_map[token] = original_value
                
                # Replace in bytearray
                # We replace the range [start:end] with the token bytes
                token_bytes = token.encode("utf-8")
                mutable_text[start:end] = token_bytes
                
            redacted_text = mutable_text.decode("utf-8")
            return redacted_text, redaction_map
            
        except Exception as e:
            logger.error(f"DLP Redaction failed: {e}")
            return text, {}

    def _call_model(self, model: GenerativeModel, prompt: str) -> Tuple[List[Dict[str, Any]], float]:
        """Helper to call a model and return result + latency."""
        start_time = time.time()
        try:
            response = model.generate_content(prompt)
            content = response.text
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            result = json.loads(content.strip())
        except Exception as e:
            logger.error(f"Model call failed: {e}")
            result = [] # Return empty list on failure? Or raise?
            # For primary, we might want to raise. For shadow, we swallow.
            # But this helper is generic. Let's raise and handle in caller.
            raise
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        return result, latency_ms

    def analyze_contract(self, sanitized_text: str, job_id: str) -> List[Dict[str, Any]]:
        """Analyzes contract using Gemini with Shadow Mode."""
        if not self.model:
            logger.warning("Vertex AI model not initialized, skipping analysis.")
            return []

        golden_rules = """
        Golden Rules:
        1. Indemnification must be mutual.
        2. Payment terms max 60 days.
        """
        
        prompt = f"""
        You are a legal expert. Compare the following contract text against these Golden Rules. 
        Return a JSON object matching the `ClauseAnalysis` schema (list of objects).
        
        {golden_rules}
        
        Contract Text:
        {sanitized_text}
        
        Output format:
        [
            {{
                "original_text": "text of clause",
                "risk_score": 0.8,
                "status": "FLAGGED",
                "regulation_violation": "GDPR Art 28",
                "ai_reasoning": "Explanation..."
            }}
        ]
        """
        
        primary_result = []
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both requests
            future_primary = executor.submit(self._call_model, self.model, prompt)
            future_shadow = executor.submit(self._call_model, self.shadow_model, prompt) if self.shadow_model else None
            
            # Wait for Primary (Blocking)
            try:
                primary_result, primary_latency = future_primary.result()
            except Exception as e:
                logger.error(f"Primary model failed: {e}")
                # If primary fails, we return error stub as before
                return [{
                    "original_text": "Error analyzing document",
                    "risk_score": 1.0,
                    "status": "FLAGGED",
                    "ai_reasoning": f"Analysis failed: {str(e)}"
                }]

            # Process Shadow (Non-blocking / Best Effort)
            if future_shadow:
                try:
                    shadow_result, shadow_latency = future_shadow.result(timeout=5) # Wait a bit, but don't hang forever
                    
                    # Log comparison
                    # Simple comparison: Do they both agree on having > 0 flagged items?
                    primary_flagged = any(r.get("status") == "FLAGGED" for r in primary_result)
                    shadow_flagged = any(r.get("status") == "FLAGGED" for r in shadow_result)
                    agreement = (primary_flagged == shadow_flagged)
                    
                    log_entry = {
                        "event": "shadow_mode_comparison",
                        "job_id": job_id,
                        "primary_model": "gemini-1.5-pro-002",
                        "shadow_model": "gemini-1.5-flash-001",
                        "agreement_bool": agreement,
                        "latency_diff_ms": primary_latency - shadow_latency,
                        "primary_count": len(primary_result),
                        "shadow_count": len(shadow_result)
                    }
                    print(json.dumps(log_entry)) # Log to stdout
                    
                except Exception as e:
                    logger.warning(f"Shadow mode failed or timed out: {e}")
                    # Swallow exception to protect primary flow

        return primary_result

    def process_job(self, job_id: str, gcs_path: str):
        logger.info(f"Processing job {job_id} for file {gcs_path}")
        
        try:
            # 1. Update status
            self.firestore_client.update_job_status(job_id, JobStatus.PROCESSING)
            
            # 2. Download and Extract
            text = self.download_text_from_gcs(gcs_path)
            
            # 3. Redact
            sanitized_text, redaction_map = self.sanitize_document(text)
            
            if redaction_map:
                logger.info(f"Redaction map created with {len(redaction_map)} entries for job {job_id}.")
            
            # 4. Analyze (Pass job_id for shadow logging)
            analysis_results = self.analyze_contract(sanitized_text, job_id)
            
            # 5. Save results
            self.firestore_client.update_job_status(
                job_id, 
                JobStatus.NEEDS_REVIEW, 
                result_data={"analysis_summary": f"Analyzed {len(analysis_results)} clauses"}
            )
            
            doc_ref = self.firestore_client.client.collection("contract_jobs").document(job_id)
            doc_ref.update({"analysis": analysis_results})
            
            logger.info(f"Job {job_id} completed successfully.")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            self.firestore_client.update_job_status(
                job_id, 
                JobStatus.FAILED, 
                result_data={"error": str(e)}
            )
