import functions_framework
import os
import json
import time
import logging
from typing import List, Dict, Any
from datetime import datetime

from google.cloud import firestore
from google.cloud import aiplatform
from google.cloud import secretmanager
from google.cloud import logging as cloud_logging
import vertexai
from vertexai.preview.generative_models import GenerativeModel, GenerationConfig
from vertexai.preview.language_models import TextEmbeddingModel

import config
from models import AssessmentRequest, AssessmentResponse, RagReference

# Configure logging
log_client = cloud_logging.Client()
log_client.setup_logging()
logger = logging.getLogger(__name__)

# Initialize Firestore
db = firestore.Client()

def get_embeddings(text: str) -> List[float]:
    """Generates embeddings for the query text."""
    try:
        model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
        embeddings = model.get_embeddings([text])
        return embeddings[0].values
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise

def query_vector_search(query_text: str) -> List[RagReference]:
    """Queries the Vertex AI Vector Search index."""
    try:
        embedding = get_embeddings(query_text)
        
        # Get Index Endpoint
        # Vertex AI SDK requires the ID, not full name sometimes, but resource name is safer
        # config.VERTEX_AI_ENDPOINT should be the full resource name
        endpoint_id = config.VERTEX_AI_ENDPOINT.split('/')[-1]
        index_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=endpoint_id)
        
        # Query
        response = index_endpoint.find_neighbors(
            deployed_index_id=config.DEPLOYED_INDEX_ID,
            queries=[embedding],
            num_neighbors=config.MAX_NEIGHBORS
        )
        
        references = []
        if response:
            for neighbor in response[0]:
                # In a real system, we would fetch the actual text content from a Datastore/DB using the ID
                # Since we don't have a separate doc store set up in this task scope, 
                # we will use the ID or look up if we had a mapping.
                # For now, we assume the ID helps identifying the source.
                references.append(RagReference(
                    id=neighbor.id,
                    content_snippet=f"Content for {neighbor.id} (Placeholder for actual content retrieval)", 
                    score=neighbor.distance
                ))
        return references
    except Exception as e:
        logger.error(f"Error querying vector search: {e}")
        # Fail gracefully for RAG, return empty list
        return []

def generate_assessment(request_data: AssessmentRequest, references: List[RagReference]) -> Dict[str, Any]:
    """Generates the assessment using Gemini 1.5 Pro."""
    try:
        vertexai.init(project=config.PROJECT_ID, location=config.REGION)
        model = GenerativeModel(config.GEMINI_MODEL_NAME)
        
        context = "\n".join([f"- {r.id}: {r.content_snippet}" for r in references])
        
        prompt = f"""
        You are an expert IR35 Compliance Officer. 
        Assess the following engagement based on the provided details and the relevant case law/guidelines (Context).
        
        Context:
        {context}
        
        Engagement Details:
        Role: {request_data.role_details}
        Contract Type: {request_data.contract_type}
        Answers: {request_data.answers}
        
        Provide a JSON response with the following fields:
        - determination: "Inside IR35" or "Outside IR35"
        - confidence_score: float between 0.0 and 1.0
        - reasoning: Detailed explanation citing the context where applicable.
        """
        
        generation_config = GenerationConfig(
            temperature=0.2,
            top_p=0.8,
            top_k=40,
            response_mime_type="application/json"
        )
        
        response = model.generate_content(prompt, generation_config=generation_config)
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse Gemini response: {response.text}")
            # Fallback
            return {
                "determination": "Undetermined",
                "confidence_score": 0.0,
                "reasoning": "Failed to parse AI response."
            }
            
    except Exception as e:
        logger.error(f"Error generating assessment: {e}")
        raise

@functions_framework.http
def assess_engagement(request):
    """HTTP Cloud Function entry point."""
    
    # CORS headers
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    try:
        request_json = request.get_json(silent=True)
        if not request_json:
             return (json.dumps({"error": "Invalid JSON"}), 400, headers)
             
        # Validation
        try:
            data = AssessmentRequest(**request_json)
        except Exception as e:
            return (json.dumps({"error": f"Validation Error: {str(e)}"}), 400, headers)
            
        # RAG
        references = query_vector_search(data.role_details)
        
        # Gemini
        ai_result = generate_assessment(data, references)
        
        # Construct Response
        response = AssessmentResponse(
            assessment_id=f"{data.engagement_id}-{int(time.time())}",
            status="Completed",
            determination=ai_result.get("determination", "Undetermined"),
            confidence_score=ai_result.get("confidence_score", 0.0),
            reasoning=ai_result.get("reasoning", ""),
            rag_references=references,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Audit Log (Firestore)
        doc_ref = db.collection(config.FIRESTORE_COLLECTION).document(data.engagement_id)
        doc_ref.set({
            "request": data.model_dump(),
            "response": response.model_dump(),
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        
        return (response.model_dump_json(), 200, headers)
        
    except Exception as e:
        logger.error(f"Internal Error: {e}", exc_info=True)
        return (json.dumps({"error": "Internal Server Error"}), 500, headers)
