"""
Application configuration using pydantic-settings.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Groq API Configuration
    groq_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    
    # Local Embedding Model (sentence-transformers)
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Application Settings
    debug: bool = False
    log_level: str = "INFO"
    
    # Vector Database
    chroma_persist_directory: str = "data/chroma_db"
    bible_collection_name: str = "bible_verses"
    
    # RAG Settings
    retrieval_top_k: int = 5
    similarity_threshold: float = 0.7
    
    # Safety Settings
    max_conversation_history: int = 20
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
