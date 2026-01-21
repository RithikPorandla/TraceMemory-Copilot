from __future__ import annotations

from typing import Dict, Union

MEMORY_MAX_CHARS = 4000

from autogen import ConversableAgent, Agent

from src.memory.zep_service import ZepMemoryService


class TraceMemoryAgent(ConversableAgent):
    """ConversableAgent with Zep-backed long-term memory."""

    def __init__(
        self,
        *,
        name: str,
        system_message: str,
        llm_config: dict,
        human_input_mode: str,
        function_map: dict | None,
        zep_service: ZepMemoryService,
        zep_session_id: str,
        min_fact_rating: float = 0.7,
        pinned_facts: list[str] | None = None,
    ):
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            human_input_mode=human_input_mode,
            function_map=function_map,
        )
        self._base_system_message = system_message
        self._zep = zep_service
        self._session_id = zep_session_id
        self._min_fact_rating = min_fact_rating
        self._pinned_facts: list[str] = pinned_facts or []

        # Expose lightweight telemetry for UI analytics.
        # Updated on each user message.
        self.last_memory_context: str = ""
        self.last_memory_chars: int = 0
        self.last_memory_used: bool = False
        
        # Cache memory to avoid redundant API calls
        self._memory_cache: str = ""
        self._memory_cache_timestamp: float = 0.0

        # Persist assistant outputs automatically.
        self.register_hook("process_message_before_send", self._persist_assistant_output)

    def set_pinned_facts(self, pinned_facts: list[str] | None):
        """Set durable, user-approved facts to always include in context."""
        self._pinned_facts = pinned_facts or []

    def prepare_for_user_message(self, user_text: str, user_display_name: str = "USER"):
        """Persist the user message and refresh system prompt with relevant memory."""
        # Add user message (non-blocking for UI, but still synchronous)
        self._zep.add_user_message(self._session_id, user_display_name, user_text)

        # Retrieve memory context (this is the main latency source besides LLM)
        memory = self._zep.get_memory(self._session_id, min_rating=self._min_fact_rating)
        context_raw = (getattr(memory, "context", None) or "").strip()

        if len(context_raw) > MEMORY_MAX_CHARS:
            # Keep the most recent part. Zep contexts often append newer facts.
            context_raw = context_raw[-MEMORY_MAX_CHARS:]

        # Telemetry used by the Analytics dashboard.
        self.last_memory_context = context_raw
        self.last_memory_chars = len(context_raw)
        self.last_memory_used = bool(context_raw)

        context = context_raw or "(no relevant memory)"

        pinned = "\n".join([f"- {f}" for f in self._pinned_facts]) if self._pinned_facts else "(none)"

        self.update_system_message(
            f"{self._base_system_message}\n\n"
            f"### PINNED FACTS (user-approved, durable)\n{pinned}\n\n"
            f"### MEMORY CONTEXT (from Zep, filtered by rating)\n{context}\n"
        )

    def _persist_assistant_output(
        self,
        message: Union[Dict, str],
        sender: Agent,
        recipient: Agent,
        silent: bool,
    ):
        if sender != self:
            return message

        content = message.get("content", "") if isinstance(message, dict) else str(message)
        content = (content or "").strip()
        if content:
            self._zep.add_assistant_message(self._session_id, self.name, content)
        return message
