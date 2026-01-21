from __future__ import annotations

import streamlit as st

from src.config import settings
from src.ui.layout import render_sidebar
from src.ui.state import ensure_state
from src.ui.pages.analytics_page import render_analytics_page
from src.ui.pages.chat_page import render_chat_page
from src.ui.pages.memory_cards_page import render_memory_cards_page
from src.ui.pages.session_diff_page import render_session_diff_page


def main() -> None:
    st.set_page_config(page_title="TraceMemory Copilot", layout="wide")

    ensure_state()
    render_sidebar()

    st.title("🧠 TraceMemory Copilot")
    st.caption("Zep-powered long-term memory assistant with traceable memory controls.")

    tabs = st.tabs(["Chat", "Memory Cards", "Session Diff", "Analytics"])
    with tabs[0]:
        render_chat_page()
    with tabs[1]:
        render_memory_cards_page()
    with tabs[2]:
        render_session_diff_page()
    with tabs[3]:
        render_analytics_page()


if __name__ == "__main__":
    # Streamlit runs this file directly.
    # Config is loaded via src.config.settings.
    main()
