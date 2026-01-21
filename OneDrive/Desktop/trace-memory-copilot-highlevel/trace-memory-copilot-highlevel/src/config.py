from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    zep_api_key: str = os.getenv("ZEP_API_KEY", "")
    zep_api_url: str = os.getenv("ZEP_API_URL", "https://api.getzep.com")

    # OpenAI configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Fast and affordable model
    
    # Ollama configuration (fallback)
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:4b")

    # Default memory threshold
    min_fact_rating: float = float(os.getenv("MIN_FACT_RATING", "0.7"))


settings = Settings()
