from __future__ import annotations

import pandas as pd
import streamlit as st


def render_analytics_page() -> None:
    """Dashboard showing how often memory is used and how it changes over time."""

    st.subheader("📊 Analytics")
    st.caption("Turn-level telemetry (stored locally in this browser session).")

    events = st.session_state.get("analytics_events", [])
    if not events:
        st.info("No analytics yet. Send a few messages in the Chat tab.")
        return

    df = pd.DataFrame(events)
    df["memory_used"] = df["memory_used"].astype(bool)

    hit_rate = float(df["memory_used"].mean()) if len(df) else 0.0
    st.metric("Memory hit rate", f"{hit_rate*100:.0f}%")

    st.divider()

    st.markdown("### Context size over turns")
    st.line_chart(df["memory_chars"])

    st.markdown("### Per-turn message sizes")
    st.line_chart(df[["user_chars", "assistant_chars"]])

    st.markdown("### Memory usage breakdown")
    used = int(df["memory_used"].sum())
    not_used = int((~df["memory_used"]).sum())
    st.bar_chart(pd.DataFrame({"turns": [used, not_used]}, index=["used", "not_used"]))

    with st.expander("Raw events"):
        st.dataframe(df, use_container_width=True)
