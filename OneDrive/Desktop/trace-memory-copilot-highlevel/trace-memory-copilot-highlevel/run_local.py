from __future__ import annotations

import os

from autogen import UserProxyAgent

from src.agent import TraceMemoryAgent
from src.config import settings
from src.llm_config import build_ollama_config_list
from src.memory.user_utils import generate_user_id
from src.memory.zep_service import ZepMemoryService
from src.prompts import TRACE_MEMORY_SYSTEM_MESSAGE


def main():
    api_key = os.getenv("ZEP_API_KEY", "")
    if not api_key:
        raise ValueError("Missing ZEP_API_KEY in environment")

    first_name = os.getenv("FIRST_NAME", "Rithik")
    last_name = os.getenv("LAST_NAME", "Porandla")
    user_id = generate_user_id(first_name, last_name)

    zep = ZepMemoryService(api_key=api_key, api_url=settings.zep_api_url)
    zep.ensure_user(user_id, first_name, last_name)
    session_id = zep.create_session(user_id=user_id)

    agent = TraceMemoryAgent(
        name="TraceMemory Copilot",
        system_message=TRACE_MEMORY_SYSTEM_MESSAGE,
        llm_config={"config_list": build_ollama_config_list()},
        zep_service=zep,
        zep_session_id=session_id,
        min_fact_rating=settings.min_fact_rating,
        function_map=None,
        human_input_mode="NEVER",
    )

    user = UserProxyAgent(
        name="UserProxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0,
        code_execution_config=False,
        llm_config=False,
    )

    print("TraceMemory Copilot CLI (type 'exit' to quit)")
    while True:
        text = input("You: ").strip()
        if text.lower() in {"exit", "quit"}:
            break

        agent.prepare_for_user_message(text, user_display_name=f"{first_name} {last_name}".upper())
        user.initiate_chat(recipient=agent, message=text + " /no_think", max_turns=1, clear_history=False)
        print("Copilot:", user.last_message(agent).get("content", ""))


if __name__ == "__main__":
    main()
