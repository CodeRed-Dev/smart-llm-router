"""
Configuration module with simple environment-backed settings.
"""

import os
from typing import Literal


class Settings:
    FAST_MODEL_PATH: str = os.getenv("FAST_MODEL_PATH", "llama2:7b")
    STRONG_MODEL_PATH: str = os.getenv("STRONG_MODEL_PATH", "llama2:13b")
    JUDGE_MODEL_PATH: str = os.getenv("JUDGE_MODEL_PATH", STRONG_MODEL_PATH)
    MODEL_DEVICE: Literal["auto", "cpu", "cuda"] = os.getenv("MODEL_DEVICE", "auto")
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    ROUTING_PROMPT_LENGTH_THRESHOLD: int = int(os.getenv("ROUTING_PROMPT_LENGTH_THRESHOLD", "200"))
    JUDGE_CORRECTNESS_THRESHOLD: int = int(os.getenv("JUDGE_CORRECTNESS_THRESHOLD", "5"))
    LLM_BACKEND: Literal["transformers", "ollama"] = os.getenv("LLM_BACKEND", "ollama").lower()
    OLLAMA_BIN_PATH: str = os.getenv("OLLAMA_BIN_PATH", "ollama")


settings = Settings()
