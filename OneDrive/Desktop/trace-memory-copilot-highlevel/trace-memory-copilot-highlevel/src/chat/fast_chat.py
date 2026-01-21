"""Fast, streamlined chat handler using OpenAI API.
This bypasses AutoGen and Ollama for maximum performance and reliability."""
from __future__ import annotations

import time
from typing import Optional

from openai import OpenAI

from src.config import settings
from src.memory.zep_service import ZepMemoryService


class FastChatHandler:
    """Lightweight chat handler optimized for speed using OpenAI."""

    def __init__(
        self,
        zep_service: ZepMemoryService,
        session_id: str,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.zep = zep_service
        self.session_id = session_id
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env or enter it in the sidebar.")
        
        self.openai_client = OpenAI(api_key=self.api_key)
        
        # Memory cache to avoid redundant API calls
        self._memory_cache: Optional[str] = None
        self._memory_cache_time: float = 0.0
        self._cache_ttl: float = 30.0  # Cache memory for 30 seconds

    def get_memory_context(self, min_rating: float = 0.7) -> str:
        """Get memory context with caching to reduce API calls."""
        now = time.time()
        
        # Return cached memory if still valid
        if (
            self._memory_cache is not None
            and (now - self._memory_cache_time) < self._cache_ttl
        ):
            return self._memory_cache

        # Fetch fresh memory
        try:
            memory = self.zep.get_memory(self.session_id, min_rating=min_rating)
            context = (getattr(memory, "context", None) or "").strip()
            
            # Update cache
            self._memory_cache = context[:4000] if len(context) > 4000 else context
            self._memory_cache_time = now
            
            return self._memory_cache
        except Exception as e:
            # On error, return empty context but log
            print(f"Warning: Failed to fetch memory: {e}")
            return ""

    def invalidate_cache(self):
        """Invalidate memory cache (call after adding messages)."""
        self._memory_cache = None
        self._memory_cache_time = 0.0

    def build_system_prompt(self, memory_context: str, pinned_facts: list[str] | None = None) -> str:
        """Build optimized system prompt."""
        pinned = "\n".join([f"- {f}" for f in pinned_facts]) if pinned_facts else "(none)"
        context = memory_context or "(no relevant memory)"
        
        return f"""You are TraceMemory Copilot, a helpful assistant with long-term memory.

### PINNED FACTS (user-approved, durable)
{pinned}

### MEMORY CONTEXT (from Zep, filtered by rating)
{context}

Respond helpfully and concisely. Keep responses under 500 words when possible."""

    def chat(
        self,
        user_message: str,
        min_rating: float = 0.7,
        pinned_facts: list[str] | None = None,
    ) -> str:
        """Handle chat message and return response.
        
        Returns:
            Assistant response text
        """
        # Add user message to Zep
        self.zep.add_user_message(self.session_id, "USER", user_message)
        
        # Invalidate cache to get fresh memory (message added means context changed)
        self.invalidate_cache()
        
        # Get fresh memory context (cache invalidated, so will fetch new)
        memory_context = self.get_memory_context(min_rating=min_rating)
        
        # Build prompt
        system_prompt = self.build_system_prompt(memory_context, pinned_facts)
        
        # Get response from OpenAI
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                max_tokens=512,  # Limit tokens for speed
                top_p=0.9,
            )
            
            answer = response.choices[0].message.content.strip() if response.choices else ""
            
            # Add assistant message to Zep
            if answer:
                self.zep.add_assistant_message(self.session_id, "TraceMemory Copilot", answer)
            
            return answer
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise ValueError(f"OpenAI API authentication failed: {error_msg}. Please check your API key.")
            if "rate_limit" in error_msg.lower():
                raise RuntimeError(f"OpenAI rate limit exceeded. Please try again in a moment.")
            raise RuntimeError(f"Failed to generate response: {error_msg}")

    def get_telemetry(self, memory_context: str) -> dict:
        """Get telemetry data for analytics."""
        return {
            "memory_used": bool(memory_context),
            "memory_chars": len(memory_context),
        }

