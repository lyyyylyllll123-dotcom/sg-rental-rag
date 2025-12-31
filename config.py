"""
配置文件 - 应用常量和设置
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== API 配置 ====================
# DeepSeek API 配置
# 优先使用环境变量，如果没有则使用默认值
DEEPSEEK_API_KEY = os.getenv("OPENAI_API_KEY", "sk-4050f4f681bd46dbba956ce599b8dc1f")
DEEPSEEK_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("MODEL_NAME", "deepseek-chat")

# ==================== Embedding 配置 ====================
# 默认使用本地 embedding 模型（多语言支持）
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
USE_API_EMBEDDING = os.getenv("USE_API_EMBEDDING", "false").lower() == "true"

# ==================== RAG 配置 ====================
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))  # 减小到 500，适应短文档
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))  # 相应减小 overlap
# 重排序配置
INITIAL_RETRIEVAL_K = int(os.getenv("INITIAL_RETRIEVAL_K", "20"))  # 初始检索 20 条
FINAL_RETRIEVAL_K = int(os.getenv("FINAL_RETRIEVAL_K", "8"))  # 重排序后返回 8 条
RETRIEVAL_K = FINAL_RETRIEVAL_K  # 保持向后兼容

# ==================== 向量库配置 ====================
FAISS_PERSIST_DIR = "./data/faiss"
FAISS_INDEX_NAME = "singapore_rental"

# ==================== 文件配置 ====================
URLS_JSON_PATH = "./data/urls.json"
EVALUATION_QUESTIONS_PATH = "./data/evaluation_questions.json"

# ==================== 允许的域名白名单 ====================
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

