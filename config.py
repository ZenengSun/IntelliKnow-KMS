# config.py
import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env 文件中的环境变量
load_dotenv()

class Config:
    # 通义千问配置
    QWEN_API_KEY = os.getenv("QWEN_API_KEY")
    QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    QWEN_CHAT_MODEL = os.getenv("QWEN_CHAT_MODEL", "qwen-plus")
    QWEN_EMBEDDING_MODEL = os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v3")

    # Teams Bot配置（可选）
    TEAMS_APP_ID = os.getenv("TEAMS_APP_ID")
    TEAMS_APP_PASSWORD = os.getenv("TEAMS_APP_PASSWORD")
    TEAMS_APP_TENANT_ID = os.getenv("TEAMS_APP_TENANT_ID")
    MICROSOFT_APP_TYPE = "SingleTenant"

    # # 路径配置
    # BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # DOCUMENTS_DIR = os.path.join(BASE_DIR, "data", "documents")
    # FAISS_INDEX_DIR = os.path.join(BASE_DIR, "data", "faiss_index")

    # 路径配置
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", os.path.join(BASE_DIR, "data", "documents"))
    FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", os.path.join(BASE_DIR, "data", "faiss_index"))
    SQLITE_PATH = os.getenv("SQLITE_PATH", os.path.join(BASE_DIR, "data", "sqlite", "kms.db"))

    # 创建必要目录
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
    os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)

     # 意图配置
    DEFAULT_INTENTS = ["HR", "Legal", "Finance", "General"]
    CONFIDENCE_THRESHOLD = 0.7
    

    # 初始化 OpenAI 客户端 (用于通义千问)
    @staticmethod
    def get_qwen_client():
        return OpenAI(
            api_key=Config.QWEN_API_KEY,
            base_url=Config.QWEN_BASE_URL
        )
    
    @staticmethod
    def get_embedding_config():
        """获取Embedding配置（用于LangChain）"""
        return {
            "openai_api_key": Config.QWEN_API_KEY,
            "openai_api_base": Config.QWEN_BASE_URL,
            "model": Config.QWEN_EMBEDDING_MODEL,
            "chunk_size": 16,
            "max_retries": 3,
            "request_timeout": 30
        }