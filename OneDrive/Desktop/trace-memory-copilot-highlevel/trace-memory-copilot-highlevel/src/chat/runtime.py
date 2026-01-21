"""Simplified runtime without AutoGen dependency for direct chat flow."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.config import settings
from src.memory.user_utils import generate_user_id
from src.memory.zep_service import ZepMemoryService
from src.storage.local_store import LocalUserStore
from src.chat.fast_chat import FastChatHandler


class LightweightAgent:
    """Lightweight agent wrapper for backwards compatibility with memory cards."""
    def __init__(self, chat_handler: FastChatHandler):
        self._pinned_facts: list[str] = []
        self._chat_handler = chat_handler
        # Analytics fields
        self.last_memory_context: str = ""
        self.last_memory_chars: int = 0
        self.last_memory_used: bool = False
    
    def set_pinned_facts(self, pinned_facts: list[str] | None):
        """Set pinned facts for memory context."""
        self._pinned_facts = pinned_facts or []


@dataclass
class ChatRuntime:
    """Lightweight runtime for chat operations."""
    zep: ZepMemoryService
    chat_handler: FastChatHandler
    user_id: str
    session_id: str
    store: LocalUserStore
    openai_api_key: str  # Store API key for new sessions
    openai_model: str  # Store model for new sessions
    # Lightweight agent for backwards compatibility
    agent: Optional[LightweightAgent] = None


def init_runtime(
    *,
    zep_api_key: str,
    openai_api_key: str,
    first_name: str,
    last_name: str,
    min_fact_rating: float,
) -> ChatRuntime:
    """Initialize Zep and chat handler.
    
    Simplified initialization without AutoGen overhead.
    """
    if not zep_api_key:
        raise ValueError("Missing Zep API key")
    if not openai_api_key:
        raise ValueError("Missing OpenAI API key")

    first = (first_name or "User").strip() or "User"
    last = (last_name or "").strip()

    user_id = generate_user_id(first, last)
    zep = ZepMemoryService(api_key=zep_api_key, api_url=settings.zep_api_url)
    
    # Ensure user exists
    zep.ensure_user(user_id, first, last)

    store = LocalUserStore()
    session_id = zep.create_session(user_id=user_id)
    store.add_session(user_id, session_id)

    # Create fast chat handler with OpenAI
    chat_handler = FastChatHandler(
        zep_service=zep,
        session_id=session_id,
        api_key=openai_api_key,
        model=settings.openai_model,
    )

    # Create lightweight agent for backwards compatibility
    agent = LightweightAgent(chat_handler)

    return ChatRuntime(
        zep=zep,
        chat_handler=chat_handler,
        user_id=user_id,
        session_id=session_id,
        store=store,
        openai_api_key=openai_api_key,
        openai_model=settings.openai_model,
        agent=agent,
    )


def new_session(runtime: ChatRuntime, *, min_fact_rating: float) -> ChatRuntime:
    """Start a new Zep session for the same user."""
    session_id = runtime.zep.create_session(user_id=runtime.user_id)
    runtime.store.add_session(runtime.user_id, session_id)

    chat_handler = FastChatHandler(
        zep_service=runtime.zep,
        session_id=session_id,
        api_key=runtime.openai_api_key,
        model=runtime.openai_model,
    )

    # Create lightweight agent for backwards compatibility
    agent = LightweightAgent(chat_handler)

    return ChatRuntime(
        zep=runtime.zep,
        chat_handler=chat_handler,
        user_id=runtime.user_id,
        session_id=session_id,
        store=runtime.store,
        openai_api_key=runtime.openai_api_key,
        openai_model=runtime.openai_model,
        agent=agent,
    )
