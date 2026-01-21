from __future__ import annotations

from difflib import unified_diff

import streamlit as st

from src.chat.runtime import ChatRuntime


def render_session_diff_page() -> None:
    if not st.session_state.get("chat_initialized"):
        st.info("Initialize a user + session first.")
        return

    runtime: ChatRuntime = st.session_state.runtime
    min_rating = float(st.session_state.get("min_fact_rating") or 0.7)

    st.subheader("🧾 Session Diff")
    st.caption("Compare two sessions and see how memory context changed.")

    sessions = runtime.store.list_sessions(runtime.user_id)
    if len(sessions) < 2:
        st.info("Create at least two sessions to compare.")
        return

    c1, c2 = st.columns(2)
    with c1:
        a = st.selectbox("Session A", options=sessions, index=max(0, len(sessions) - 2))
    with c2:
        b = st.selectbox("Session B", options=sessions, index=max(0, len(sessions) - 1))

    if a == b:
        st.warning("Select two different sessions.")
        return

    try:
        mem_a = runtime.zep.get_memory(a, min_rating=min_rating)
        mem_b = runtime.zep.get_memory(b, min_rating=min_rating)
    except Exception as e:
        st.error(f"Could not fetch sessions: {e}")
        return

    ctx_a = (getattr(mem_a, "context", None) or "").strip()
    ctx_b = (getattr(mem_b, "context", None) or "").strip()

    if not ctx_a and not ctx_b:
        st.info("No memory context available for either session at this rating threshold.")
        return

    diff = "\n".join(
        unified_diff(
            ctx_a.splitlines(),
            ctx_b.splitlines(),
            fromfile=f"Session A: {a}",
            tofile=f"Session B: {b}",
            lineterm="",
        )
    )

    st.code(diff or "(no textual diff)")

    with st.expander("Show raw contexts"):
        left, right = st.columns(2)
        with left:
            st.markdown("#### Session A")
            st.text_area("", value=ctx_a, height=240, key="session_a_context")
        with right:
            st.markdown("#### Session B")
            st.text_area("", value=ctx_b, height=240, key="session_b_context")
