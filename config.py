"""
Configuration File - Application Constants and Settings
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==================== API Configuration ====================
# DeepSeek API Configuration
# Priority: environment variables, if not available use default values
DEEPSEEK_API_KEY = os.getenv("OPENAI_API_KEY", "sk-4050f4f681bd46dbba956ce599b8dc1f")
DEEPSEEK_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("MODEL_NAME", "deepseek-chat")

# ==================== Embedding Configuration ====================
# Default to local embedding model (multilingual support)
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
USE_API_EMBEDDING = os.getenv("USE_API_EMBEDDING", "false").lower() == "true"

# ==================== RAG Configuration ====================
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))  # Reduced to 500, adapted for short documents
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))  # Correspondingly reduced overlap
# Reranking configuration
INITIAL_RETRIEVAL_K = int(os.getenv("INITIAL_RETRIEVAL_K", "15"))  # Initial retrieval of 15 documents (reduced for performance)
FINAL_RETRIEVAL_K = int(os.getenv("FINAL_RETRIEVAL_K", "8"))  # Return 8 documents after reranking
RETRIEVAL_K = FINAL_RETRIEVAL_K  # Maintain backward compatibility

# ==================== Vector Store Configuration ====================
FAISS_PERSIST_DIR = "./data/faiss"
FAISS_INDEX_NAME = "singapore_rental"

# ==================== File Configuration ====================
URLS_JSON_PATH = "./data/urls.json"
EVALUATION_QUESTIONS_PATH = "./data/evaluation_questions.json"

# ==================== Allowed Domain Whitelist ====================
ALLOWED_DOMAINS = [
    "gov.sg",
    "hdb.gov.sg",
    "cea.gov.sg",
    "ura.gov.sg",
]

# ==================== UI Configuration ====================
EXAMPLE_QUESTIONS = [
    "Can students with a student pass rent HOBs?",
    "What is the shortest lease term for a HOB in months?",
    "What is the minimum lease term requirement for private residential properties?",
    "What are the steps in the rental process?",
    "Can EP holders rent entire HDB units?",
    "What deposits do I need to pay when renting?",
    "What are the consequences of illegal subletting?",
]

