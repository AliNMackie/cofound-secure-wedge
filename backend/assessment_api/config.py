import os

# Project Configuration
PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("REGION", "us-central1")

# Vertex AI Configuration
VERTEX_AI_ENDPOINT = os.environ.get("VERTEX_AI_ENDPOINT") # Endpoint Name
VERTEX_AI_INDEX_NAME = os.environ.get("VERTEX_AI_INDEX_NAME") # Index Resource Name
DEPLOYED_INDEX_ID = "ir35_cest_deployed"

# Gemini Configuration
# Using Gemini 1.5 Pro as requested
GEMINI_MODEL_NAME = "gemini-1.5-pro-preview-0409" 

# Firestore Configuration
FIRESTORE_COLLECTION = "ir35_assessments"

# RAG Configuration
MAX_NEIGHBORS = 5
