from __future__ import annotations

from src.config import settings


def build_ollama_config_list(model: str | None = None, host: str | None = None):
    """Build the AG2/AutoGen-compatible config_list for Ollama.
    
    Note: For better performance, consider using direct Ollama client in chat_page.py
    instead of AutoGen wrapper.
    """
    return [
        {
            "model": model or settings.ollama_model,
            "api_type": "ollama",
            "client_host": host or settings.ollama_host,
            "timeout": 60,  # Reduced timeout for faster failure
            "temperature": 0.7,
            "max_tokens": 512,  # Reduced for faster generation
        }
    ]
