import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
SAMPLE_FILES_DIR = STORAGE_DIR / "sample_files"
FAISS_DIR = STORAGE_DIR / "faiss_index"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_FILES_DIR.mkdir(parents=True, exist_ok=True)
FAISS_DIR.mkdir(parents=True, exist_ok=True)

class Settings:
    PROJECT_NAME: str = "IntelGraphAI - Industrial Knowledge Intelligence Platform"
    API_V1_STR: str = "/api"
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "intelgraph_db")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "local")  # local | gemini | openai
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_TENANT_ID: str = os.getenv("DEFAULT_TENANT_ID", "tenant_default")
    REQUIRE_MANUAL_APPROVAL_BEFORE_AI: bool = os.getenv("REQUIRE_MANUAL_APPROVAL_BEFORE_AI", "false").lower() in ["true", "1"]
    EMBEDDING_DIM: int = 256

settings = Settings()
