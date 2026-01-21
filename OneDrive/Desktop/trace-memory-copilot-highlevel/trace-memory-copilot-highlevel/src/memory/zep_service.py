from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from zep_cloud.client import Zep
from zep_cloud import FactRatingExamples, FactRatingInstruction
from zep_cloud.types import ThreadContextResponse


@dataclass
class ZepIdentity:
    user_id: str
    session_id: str


class ZepMemoryService:
    """Thin wrapper around the Zep client to manage users, sessions, and memory."""

    def __init__(self, api_key: str, api_url: Optional[str] = None):
        # Zep SDK accepts api_key for cloud; api_url may be used for self-hosted.
        # For cloud, don't pass base_url (defaults to https://api.getzep.com/api/v2)
        # For self-hosted, ensure api_url includes the full path with /api/v2
        kwargs = {"api_key": api_key}
        if api_url:
            # Default cloud API URL - don't override, use SDK defaults
            if api_url == "https://api.getzep.com":
                pass  # Use default environment
            else:
                # Self-hosted: ensure it includes /api/v2
                if not api_url.endswith("/api/v2"):
                    if api_url.endswith("/"):
                        api_url = api_url.rstrip("/") + "/api/v2"
                    else:
                        api_url = api_url + "/api/v2"
                kwargs["base_url"] = api_url
        self.client = Zep(**kwargs)

    def ensure_user(self, user_id: str, first_name: str, last_name: str) -> bool:
        """Ensure user exists. Returns True if user already existed."""
        try:
            self.client.user.get(user_id)
            return True
        except Exception as e:
            # Re-raise authentication/authorization errors - don't try to create user with bad auth
            error_msg = str(e).lower()
            if "401" in error_msg or "unauthorized" in error_msg or "403" in error_msg or "forbidden" in error_msg:
                raise  # Re-raise auth errors
            
            # User doesn't exist, create them
            try:
                fact_rating_instruction = (
                    "Rate facts by relevance and utility. Highly relevant facts directly impact "
                    "the user's ongoing goals or durable preferences. Low relevance facts are "
                    "incidental details that rarely influence future conversations."
                )
                fact_rating_examples = FactRatingExamples(
                    high="The user is building an AI assistant that uses Zep for long-term memory.",
                    medium="The user prefers short, checklist-style answers.",
                    low="The user mentioned the weather today.",
                )
                self.client.user.add(
                    user_id=user_id,
                    first_name=first_name,
                    last_name=last_name,
                    fact_rating_instruction=FactRatingInstruction(
                        instruction=fact_rating_instruction,
                        examples=fact_rating_examples,
                    ),
                )
                return False
            except Exception as create_error:
                # If creation fails with auth error, re-raise it
                create_msg = str(create_error).lower()
                if "401" in create_msg or "unauthorized" in create_msg or "403" in create_msg or "forbidden" in create_msg:
                    raise create_error
                # Otherwise, raise the original error
                raise e

    def create_session(self, user_id: str, session_id: Optional[str] = None) -> str:
        sid = session_id or str(uuid.uuid4())
        # In new API, threads are created via thread.create()
        try:
            self.client.thread.create(thread_id=sid, user_id=user_id)
        except Exception:
            # Thread might already exist, which is fine
            pass
        return sid

    def get_memory(self, session_id: str, min_rating: float = 0.7) -> ThreadContextResponse:
        return self.client.thread.get_user_context(thread_id=session_id, min_rating=min_rating)

    def add_user_message(self, session_id: str, user_role: str, content: str):
        from zep_cloud import Message

        self.client.thread.add_messages(
            thread_id=session_id,
            messages=[Message(name=user_role, role="user", content=content)],
        )

    def add_assistant_message(self, session_id: str, assistant_role: str, content: str):
        from zep_cloud import Message

        self.client.thread.add_messages(
            thread_id=session_id,
            messages=[Message(name=assistant_role, role="assistant", content=content)],
        )

    def delete_session(self, session_id: str) -> bool:
        """Best-effort session deletion (depends on SDK support)."""
        try:
            self.client.thread.delete(thread_id=session_id)
            return True
        except Exception:
            return False
