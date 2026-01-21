"""Streamlined chat page using fast direct Ollama calls."""
from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from src.chat.runtime import ChatRuntime, init_runtime, new_session


def render_chat_page() -> None:
    """Main chat experience - optimized for speed."""
    _render_init_controls()
    
    if not st.session_state.get("chat_initialized"):
        st.info("Initialize a user + session from the sidebar to start chatting.")
        return

    runtime: ChatRuntime = st.session_state.runtime

    # Render message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle user input
    user_text = st.chat_input("Ask something…")
    if user_text:
        _handle_user_message(runtime, user_text)


def _render_init_controls() -> None:
    """Render control buttons and session info."""
    col1, col2, col3 = st.columns([2, 2, 3])

    with col1:
        if st.button("Initialize", use_container_width=True):
            _initialize()

    with col2:
        if st.button("New session", use_container_width=True, disabled=not st.session_state.get("chat_initialized")):
            _new_session()

    with col3:
        if st.session_state.get("chat_initialized"):
            st.caption(
                f"User: **{st.session_state.zep_user_id}** | "
                f"Session: **{st.session_state.zep_session_id}**"
            )

    st.divider()

    colx, coly = st.columns([2, 3])
    with colx:
        if st.button("Clear local chat view", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with coly:
        if st.session_state.get("chat_initialized"):
            _export_transcript_button()


def _initialize() -> None:
    """Initialize chat runtime with user credentials."""
    from src.config import settings
    
    # Get Zep API key from session state or settings, with proper trimming
    zep_key = (st.session_state.get("zep_api_key") or settings.zep_api_key or "").strip()
    zep_key = zep_key.strip('"\'')
    
    # Get OpenAI API key from session state or settings
    openai_key = (st.session_state.get("openai_api_key") or settings.openai_api_key or "").strip()
    openai_key = openai_key.strip('"\'')
    
    # Debug: log key source (without showing full key)
    if st.session_state.get("openai_api_key"):
        key_source = "sidebar (session state)"
    elif settings.openai_api_key:
        key_source = ".env file"
    else:
        key_source = "none found"
    
    first = (st.session_state.get("first_name") or "").strip()
    last = (st.session_state.get("last_name") or "").strip()
    min_rating = float(st.session_state.get("min_fact_rating") or 0.7)

    if not zep_key:
        st.error("Missing Zep API key. Please enter your API key in the sidebar.")
        return
    
    if not openai_key:
        st.error("Missing OpenAI API key. Please enter your OpenAI API key in the sidebar.")
        st.info("Get your API key at: https://platform.openai.com/api-keys")
        return

    # Validate OpenAI API key format (check first)
    if len(openai_key) < 10:
        st.error("OpenAI API key appears too short. Please check that you've pasted the complete key.")
        return
    if not openai_key.startswith("sk-"):
        st.warning("⚠️ OpenAI API key format looks unusual. OpenAI API keys typically start with 'sk-'. Please verify your key.")
    if len(openai_key) < 50:
        st.warning("⚠️ OpenAI API key appears incomplete. Full keys are typically 150+ characters long.")
    
    # Validate Zep API key format and length
    if len(zep_key) < 10:
        st.error("Zep API key appears too short. Please check that you've pasted the complete key.")
        return
    
    # Zep API keys typically start with "z_" and are JWT tokens (have 3 parts separated by dots)
    if not zep_key.startswith("z_"):
        st.warning("⚠️ Zep API key format looks unusual. Zep API keys typically start with 'z_'. Please verify your key.")
    elif zep_key.count(".") < 2:
        st.warning("⚠️ Zep API key format looks unusual. Zep JWT tokens typically have 3 parts separated by dots.")
    
    # Validate OpenAI API key format (typically starts with sk-)
    if len(openai_key) < 10:
        st.error("OpenAI API key appears too short. Please check that you've pasted the complete key.")
        return
    if not openai_key.startswith("sk-"):
        st.warning("⚠️ OpenAI API key format looks unusual. OpenAI API keys typically start with 'sk-'. Please verify your key.")
    
    try:
        runtime = init_runtime(
            zep_api_key=zep_key,
            openai_api_key=openai_key,
            first_name=first,
            last_name=last,
            min_fact_rating=min_rating,
        )
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        
        # Check for authentication errors
        if "401" in error_msg or "unauthorized" in error_msg.lower() or "403" in error_msg:
            st.error("🔐 **Authentication failed**")
            st.error("Please verify:")
            st.markdown("""
            - Your Zep API key is correct (check for typos)
            - The API key hasn't expired
            - The API key is from your Zep Cloud account
            - The key is pasted completely (no truncation)
            """)
            # Show which API key failed
            if "openai" in error_msg.lower() or "OpenAI" in error_msg:
                st.caption(f"OpenAI key preview: ...{openai_key[-10:] if len(openai_key) > 10 else openai_key}")
            else:
                st.caption(f"Zep key preview: ...{zep_key[-10:] if len(zep_key) > 10 else zep_key}")
        else:
            st.error(f"Initialization error ({error_type}): {error_msg}")
            # Show full error in expander for debugging
            with st.expander("🔍 Full error details"):
                import traceback
                st.code(traceback.format_exc())
        return

    # Update session state
    st.session_state.runtime = runtime
    st.session_state.chat_initialized = True
    st.session_state.zep_user_id = runtime.user_id
    st.session_state.zep_session_id = runtime.session_id
    st.session_state.session_history = runtime.store.list_sessions(runtime.user_id)
    st.session_state.messages = []
    st.session_state.analytics_events = []
    st.rerun()


def _new_session() -> None:
    """Create a new chat session."""
    runtime: ChatRuntime = st.session_state.runtime
    min_rating = float(st.session_state.get("min_fact_rating") or 0.7)
    
    runtime2 = new_session(runtime, min_fact_rating=min_rating)
    
    st.session_state.runtime = runtime2
    st.session_state.zep_session_id = runtime2.session_id
    st.session_state.session_history = runtime2.store.list_sessions(runtime2.user_id)
    st.session_state.messages = []
    st.session_state.analytics_events = []
    st.rerun()


def _handle_user_message(runtime: ChatRuntime, user_text: str) -> None:
    """Handle user message and generate response - optimized for speed."""
    # Add user message to UI
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    # Generate response using fast chat handler
    with st.chat_message("assistant"):
        try:
            min_rating = float(st.session_state.get("min_fact_rating") or 0.7)
            
            # Get pinned facts if available
            pinned_facts = None
            if hasattr(runtime, "agent") and runtime.agent:
                pinned_facts = getattr(runtime.agent, "_pinned_facts", None)
            
            # Use fast chat handler for direct, optimized response
            with st.spinner("Thinking…"):
                answer = runtime.chat_handler.chat(
                    user_message=user_text,
                    min_rating=min_rating,
                    pinned_facts=pinned_facts,
                )
            
            if answer:
                st.markdown(answer)
            else:
                st.warning("No response generated. Please try again.")
                
        except ValueError as e:
            # API key or configuration error
            st.error(str(e))
            if "api key" in str(e).lower() or "authentication" in str(e).lower():
                st.info("💡 **Tip**: Make sure your OpenAI API key is correct and active. You can check it at https://platform.openai.com/account/api-keys")
            else:
                st.info("💡 **Tip**: Check your model name in the settings. Default is 'gpt-4o-mini'.")
            answer = ""
        except Exception as e:
            # Other errors
            error_msg = str(e)
            st.error(f"Error: {error_msg}")
            if "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                st.info("💡 **Tip**: Verify your OpenAI API key in the sidebar. Make sure it's complete and starts with 'sk-'.")
            elif "rate_limit" in error_msg.lower():
                st.info("💡 **Tip**: OpenAI rate limit exceeded. Please wait a moment and try again.")
            else:
                st.info("💡 **Tip**: Check your OpenAI API key and network connection.")
            answer = ""

    # Update message history
    if answer:
        st.session_state.messages.append({"role": "assistant", "content": answer})

    # Update analytics and agent telemetry
    try:
        min_rating = float(st.session_state.get("min_fact_rating") or 0.7)
        memory_context = runtime.chat_handler.get_memory_context(min_rating=min_rating)
        telemetry = runtime.chat_handler.get_telemetry(memory_context)
        
        # Update agent telemetry for backwards compatibility
        if runtime.agent:
            runtime.agent.last_memory_context = memory_context
            runtime.agent.last_memory_chars = telemetry["memory_chars"]
            runtime.agent.last_memory_used = telemetry["memory_used"]
        
        # Update analytics events
        st.session_state.analytics_events.append(
            {
                "ts": datetime.utcnow().isoformat() + "Z",
                "session_id": runtime.session_id,
                "memory_used": telemetry["memory_used"],
                "memory_chars": telemetry["memory_chars"],
                "user_chars": len(user_text),
                "assistant_chars": len(answer) if answer else 0,
            }
        )
    except Exception:
        # Analytics failure shouldn't break chat
        pass


def _export_transcript_button() -> None:
    """Export chat transcript as JSON."""
    payload = {
        "user_id": st.session_state.zep_user_id,
        "session_id": st.session_state.zep_session_id,
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "messages": st.session_state.messages,
    }
    st.download_button(
        "Download transcript (JSON)",
        data=json.dumps(payload, indent=2),
        file_name=f"transcript_{st.session_state.zep_user_id}_{st.session_state.zep_session_id}.json",
        mime="application/json",
        use_container_width=True,
    )
