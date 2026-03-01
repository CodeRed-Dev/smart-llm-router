"""
Configuration Module

Centralized configuration management using Pydantic settings.
"""

import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # LLM Configuration
    FAST_MODEL_NAME: str = "llama2:7b"  # Small, fast model
    STRONG_MODEL_NAME: str = "llama2:13b"  # Larger, more capable model
    JUDGE_MODEL_NAME: str = "llama2:7b"  # Model for evaluation
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_TIMEOUT_SECONDS: int = 30
    MAX_RETRIES: int = 3

    # Cache Configuration
    CACHE_TTL_SECONDS: int = 3600  # 1 hour

    # Database Configuration
    DATABASE_PATH: str = "metrics.db"

    # Routing Thresholds
    ROUTING_PROMPT_LENGTH_THRESHOLD: int = 200
    JUDGE_CORRECTNESS_THRESHOLD: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()