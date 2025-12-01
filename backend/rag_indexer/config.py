import os

# Project Configuration
PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("REGION", "us-central1")
VERTEX_AI_ENDPOINT = os.environ.get("VERTEX_AI_ENDPOINT")
VERTEX_AI_INDEX_NAME = os.environ.get("VERTEX_AI_INDEX_NAME") # Resource Name for the Index

# Chunking Configuration
CHUNK_SIZE = 512  # Target tokens
CHUNK_OVERLAP = 50 # Tokens overlap

# Embedding Configuration
EMBEDDING_MODEL = "textembedding-gecko@003"
EMBEDDING_DIMENSIONS = 768
BATCH_SIZE = 5
MAX_RETRIES = 3

# Index Configuration
DEPLOYED_INDEX_ID = "ir35_cest_deployed"
