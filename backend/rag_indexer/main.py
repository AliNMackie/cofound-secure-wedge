import functions_framework
import os
import json
import time
import logging
import io
import hashlib
from typing import List, Dict, Any, Tuple

from google.cloud import storage
from google.cloud import secretmanager
from google.cloud import aiplatform
from google.cloud import logging as cloud_logging
from google.protobuf import json_format
from google.api_core import exceptions as google_exceptions
import pypdf

import config

# Configure logging
log_client = cloud_logging.Client()
log_client.setup_logging()
logger = logging.getLogger(__name__)

def fetch_secret(secret_name: str) -> str:
    """
    Fetches a secret from Google Secret Manager.
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{config.PROJECT_ID}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to fetch secret {secret_name}: {e}")
        raise

def download_document(gcs_url: str) -> bytes:
    """
    Downloads a document from Google Cloud Storage.
    """
    if not gcs_url.startswith("gs://"):
        raise ValueError("Invalid GCS URL. Must start with gs://")
    
    try:
        storage_client = storage.Client()
        parts = gcs_url[5:].split("/", 1)
        if len(parts) != 2:
            raise ValueError("Invalid GCS URL format.")
        
        bucket_name, blob_name = parts
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        content = blob.download_as_bytes()
        logger.info(f"Downloaded document: {gcs_url}")
        return content
    except Exception as e:
        logger.error(f"Failed to download document {gcs_url}: {e}")
        raise

def chunk_document(pdf_content: bytes) -> List[Dict[str, Any]]:
    """
    Chunks a PDF document into text segments preserving paragraph boundaries.
    """
    chunks = []
    try:
        pdf_file = io.BytesIO(pdf_content)
        reader = pypdf.PdfReader(pdf_file)
        
        text = ""
        # We'll rely on double newlines for paragraphs. 
        # pypdf sometimes extracts text cleanly, sometimes not.
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                page_text = page_text.replace('\x00', '')
                text += page_text + "\n\n"

        # Split by paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        current_chunk_words = []
        current_chunk_word_count = 0
        
        # Target: 512 tokens ~ 400 words
        # We use a simpler word count target for MVP
        target_word_count = int(config.CHUNK_SIZE / 1.3)
        overlap_word_count = int(config.CHUNK_OVERLAP / 1.3)
        
        for paragraph in paragraphs:
            words = paragraph.split()
            
            # If adding this paragraph exceeds chunk size, finalize current chunk
            if current_chunk_word_count + len(words) > target_word_count and current_chunk_words:
                # Finalize chunk
                chunk_text = " ".join(current_chunk_words)
                chunks.append({
                    "content": chunk_text,
                    "metadata": {"chunk_index": len(chunks), "source_type": "pdf"}
                })
                
                # Start new chunk with overlap (last N words of previous chunk)
                # Note: Paragraph boundaries are preserved by always adding full paragraphs
                # unless a single paragraph is huge.
                # For overlap, we take the last 'overlap_word_count' words from the previous chunk
                overlap = current_chunk_words[-overlap_word_count:] if len(current_chunk_words) > overlap_word_count else current_chunk_words
                current_chunk_words = overlap + words
                current_chunk_word_count = len(current_chunk_words)
                
            else:
                # Add paragraph to current chunk
                current_chunk_words.extend(words)
                current_chunk_word_count += len(words)
        
        # Add the last chunk if not empty
        if current_chunk_words:
             chunk_text = " ".join(current_chunk_words)
             chunks.append({
                "content": chunk_text,
                "metadata": {"chunk_index": len(chunks), "source_type": "pdf"}
            })
            
        logger.info(f"Generated {len(chunks)} chunks.")
        return chunks
        
    except Exception as e:
        logger.error(f"Failed to chunk document: {e}")
        raise

def generate_embeddings(text_chunks: List[Dict[str, Any]]) -> List[List[float]]:
    """
    Generates embeddings for text chunks using Vertex AI.
    """
    embeddings = []
    aiplatform.init(project=config.PROJECT_ID, location=config.REGION)
    
    from vertexai.preview.language_models import TextEmbeddingModel
    
    try:
        model = TextEmbeddingModel.from_pretrained(config.EMBEDDING_MODEL)
        
        # Batch processing
        for i in range(0, len(text_chunks), config.BATCH_SIZE):
            batch = text_chunks[i : i + config.BATCH_SIZE]
            batch_texts = [chunk["content"] for chunk in batch]
            
            retry_count = 0
            while retry_count < config.MAX_RETRIES:
                try:
                    batch_embeddings = model.get_embeddings(batch_texts)
                    embeddings.extend([e.values for e in batch_embeddings])
                    break
                except Exception as e:
                    retry_count += 1
                    logger.warning(f"Error generating embeddings (attempt {retry_count}): {e}")
                    if retry_count == config.MAX_RETRIES:
                        raise
                    time.sleep(2 ** retry_count) # Exponential backoff
            
            # Rate limit pause
            time.sleep(0.1) 
            
        return embeddings
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise

def upsert_to_index(embeddings: List[List[float]], chunks: List[Dict[str, Any]], index_resource_name: str, document_url: str):
    """
    Upserts embeddings to the Vertex AI Index.
    
    Args:
        embeddings: List of embeddings.
        chunks: List of chunk metadata.
        index_resource_name: The full resource name of the Index (not Endpoint).
        document_url: The source document URL for ID generation.
    """
    try:
        # Use the Index resource name to instantiate MatchingEngineIndex
        # index_resource_name format: projects/.../locations/.../indexes/...
        index_id = index_resource_name.split('/')[-1]
        
        # Note: We must use MatchingEngineIndex for data management
        my_index = aiplatform.MatchingEngineIndex(index_name=index_id)
        
        datapoints = []
        for i, embedding in enumerate(embeddings):
            chunk = chunks[i]
            
            # Deterministic ID generation for idempotency
            # Hash(document_url + chunk_index)
            unique_string = f"{document_url}_{i}"
            datapoint_id = hashlib.sha256(unique_string.encode('utf-8')).hexdigest()
            
            datapoints.append({
                "id": datapoint_id,
                "embedding": embedding,
                "restricts": [] # Add filtering restrictions if needed
            })
            
        # Upsert data points to the Index
        # Note: STREAM_UPDATE indices allow upserting directly
        my_index.upsert_datapoints(datapoints=datapoints)
        
        logger.info(f"Upserted {len(datapoints)} datapoints to index: {index_id}")
        
    except Exception as e:
        logger.error(f"Failed to upsert to index: {e}")
        raise

@functions_framework.http
def index_documents(request):
    """
    HTTP Cloud Function entry point.
    """
    try:
        request_json = request.get_json(silent=True)
        if not request_json or 'document_url' not in request_json:
            return json.dumps({"error": "Missing document_url"}), 400
        
        document_url = request_json['document_url']
        logger.info(f"Processing document: {document_url}")
        
        # 1. Download
        pdf_content = download_document(document_url)
        
        # 2. Chunk
        chunks = chunk_document(pdf_content)
        
        if not chunks:
             return json.dumps({"status": "success", "chunks_indexed": 0, "message": "No text found"}), 200

        # 3. Embed
        embeddings = generate_embeddings(chunks)
        
        # 4. Upsert
        # We need the Index Resource Name
        index_resource_name = config.VERTEX_AI_INDEX_NAME
        if not index_resource_name:
             # Fallback to environment variable if not in config (it should be in config loading from env)
             index_resource_name = os.environ.get("VERTEX_AI_INDEX_NAME")
        
        if not index_resource_name:
            raise ValueError("VERTEX_AI_INDEX_NAME environment variable not set")

        upsert_to_index(embeddings, chunks, index_resource_name, document_url)
        
        return json.dumps({
            "status": "success",
            "chunks_indexed": len(embeddings),
            "index_resource": index_resource_name
        }), 200
        
    except Exception as e:
        logger.error(f"Error in index_documents: {e}", exc_info=True)
        return json.dumps({"error": str(e)}), 500
