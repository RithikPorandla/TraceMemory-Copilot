from __future__ import annotations

import streamlit as st

from src.chat.runtime import ChatRuntime
from src.memory.facts import FactItem, extract_fact_items
from src.storage.local_store import PinnedFact


def render_memory_cards_page() -> None:
    if not st.session_state.get("chat_initialized"):
        st.info("Initialize a user + session first.")
        return

    runtime: ChatRuntime = st.session_state.runtime
    min_rating = float(st.session_state.get("min_fact_rating") or 0.7)

    st.subheader("📌 Memory Cards")
    st.caption("Review extracted memory facts, pin durable items, and add curated notes.")

    try:
        memory = runtime.zep.get_memory(runtime.session_id, min_rating=min_rating)
    except Exception as e:
        st.error(f"Could not fetch memory: {e}")
        return

    facts = extract_fact_items(memory)
    pinned = runtime.store.get_pinned_facts(runtime.user_id)
    pinned_map = {p.text: p for p in pinned}

    if st.session_state.get("debug_memory"):
        with st.expander("Debug: raw memory context"):
            st.code((getattr(memory, "context", None) or "").strip() or "(empty)")

    if not facts:
        st.info("No extracted facts yet. Chat more, then revisit this tab.")
        return

    st.write(f"Found **{len(facts)}** fact candidates.")

    if st.button("Save pinned facts", type="primary"):
        runtime.store.set_pinned_facts(runtime.user_id, list(pinned_map.values()))
        st.success("Saved.")

    st.divider()

    for idx, fact in enumerate(facts):
        _render_fact_card(idx, fact, pinned_map)

    # Keep agent pinned facts in sync (used for prompt injection).
    runtime.agent.set_pinned_facts([p.text for p in pinned_map.values()])


def _render_fact_card(idx: int, fact: FactItem, pinned_map: dict[str, PinnedFact]) -> None:
    is_pinned = fact.text in pinned_map

    with st.container(border=True):
        cols = st.columns([6, 2, 2])
        with cols[0]:
            st.markdown(f"**{fact.text}**")
        with cols[1]:
            st.caption("rating: n/a" if fact.rating is None else f"rating: {fact.rating:.2f}")
        with cols[2]:
            if st.button("✅ Pinned" if is_pinned else "📌 Pin", key=f"pin_{idx}"):
                if is_pinned:
                    pinned_map.pop(fact.text, None)
                else:
                    pinned_map[fact.text] = PinnedFact(text=fact.text, rating=fact.rating, source=fact.source)
                st.rerun()

        if fact.text in pinned_map:
            p = pinned_map[fact.text]
            new_text = st.text_area("Edit pinned text", value=p.text, key=f"edit_text_{idx}")
            if new_text.strip() and new_text != p.text:
                pinned_map.pop(fact.text, None)
                pinned_map[new_text.strip()] = PinnedFact(text=new_text.strip(), rating=p.rating, source=p.source)
                st.rerun()

            new_source = st.text_input("Source (optional)", value=p.source or "", key=f"src_{idx}")
            p.source = (new_source or "").strip() or None
