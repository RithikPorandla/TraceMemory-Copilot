from __future__ import annotations

import streamlit as st

from src.config import settings


def render_sidebar() -> None:
    """Global sidebar controls."""

    with st.sidebar:
        st.header("⚙️ Settings")
        
        st.text_input(
            "Zep API Key",
            type="password",
            value=st.session_state.get("zep_api_key") or settings.zep_api_key,
            key="zep_api_key",
            help="Required. Stored in memory for this browser session only.",
        )
        
        st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.get("openai_api_key") or settings.openai_api_key,
            key="openai_api_key",
            help="Required for chat. Get one at https://platform.openai.com/api-keys",
        )

        st.divider()
        st.subheader("Identity")
        st.text_input("First name", key="first_name", placeholder="Rithik")
        st.text_input("Last name", key="last_name", placeholder="Porandla")

        st.divider()
        st.subheader("Memory")
        default_rating = settings.min_fact_rating
        current_rating = st.session_state.get("min_fact_rating", default_rating)
        st.slider(
            "Minimum fact rating",
            min_value=0.0,
            max_value=1.0,
            value=float(current_rating) if current_rating is not None else default_rating,
            step=0.05,
            key="min_fact_rating",
            help="Higher values = stricter memory selection.",
        )

        st.checkbox("Debug memory context", key="debug_memory")
