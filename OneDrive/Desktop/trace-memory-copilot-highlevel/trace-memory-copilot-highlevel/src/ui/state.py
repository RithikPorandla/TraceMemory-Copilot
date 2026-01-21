from __future__ import annotations

import uuid
from typing import Any

import streamlit as st


def ensure_state() -> None:
    """Initialize Streamlit session state keys used across pages."""

    defaults: dict[str, Any] = {
        "chat_initialized": False,
        "messages": [],
        "zep_api_key": "",
        "first_name": "",
        "last_name": "",
        "zep_user_id": "",
        "zep_session_id": "",
        "session_history": [],
        "min_fact_rating": 0.7,
        "debug_memory": False,
        "analytics_events": [],
        "chat_run_id": str(uuid.uuid4()),
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
