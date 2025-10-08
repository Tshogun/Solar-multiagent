import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    GROQ_API_KEY: str = ""
    SERPAPI_KEY: Optional[str] = None
    
    # LLM Settings
    LLM_MODEL: str = "mixtral-8x7b-32768"  # Groq model
    LLM_TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 2048
    
    # Embedding Settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # RAG Settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RETRIEVAL: int = 5
    
    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".pdf"}
    UPLOAD_DIR: Path = Path("data/uploads")
    
    # Vector Store Settings
    FAISS_INDEX_PATH: Path = Path("data/faiss_index")
    
    # Logging Settings
    LOG_FILE: Path = Path("logs/agent_logs.json")
    LOG_LEVEL: str = "INFO"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    
    # Search Settings
    WEB_SEARCH_RESULTS: int = 5
    ARXIV_MAX_RESULTS: int = 5
    
    # Sample PDFs
    SAMPLE_PDFS_DIR: Path = Path("sample_pdfs")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Initialize settings
settings = Settings()

# Create necessary directories
def initialize_directories():
    """Create required directories if they don't exist"""
    dirs = [
        settings.UPLOAD_DIR,
        settings.FAISS_INDEX_PATH,
        settings.LOG_FILE.parent,
        settings.SAMPLE_PDFS_DIR
    ]
    
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Initialized directories")


# Validate required settings
def validate_settings():
    """Validate critical settings"""
    if not settings.GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not found in environment variables. "
            "Please set it in .env file or environment."
        )
    
    print(f"✓ Configuration validated")
    print(f"  - LLM Model: {settings.LLM_MODEL}")
    print(f"  - Embedding Model: {settings.EMBEDDING_MODEL}")
    print(f"  - FAISS Index: {settings.FAISS_INDEX_PATH}")


if __name__ == "__main__":
    initialize_directories()
    validate_settings()