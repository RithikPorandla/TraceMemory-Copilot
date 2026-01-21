# TraceMemory Copilot

A Streamlit-based chat assistant that uses **Zep** as a long-term memory backend and **OpenAI** for LLM inference.

This project demonstrates **persistent memory**, **user/session management**, **exportable transcripts**, plus a **Memory Cards** workflow and a **Session Diff** view to inspect how memory evolves.

---

## What it does

- Creates (or reuses) a Zep **User** and starts a Zep **Session**
- Stores each user and assistant message into Zep memory
- Retrieves relevant memory context (summarized facts/entities) and injects it into the assistant system prompt
- Provides a Streamlit UI with:
  - User identity + session controls
  - Min fact rating slider
  - Transcript export to JSON
  - Optional memory inspector (debug)
  - **Memory Cards** tab: pin, edit, and save high-value facts locally
  - **Session Diff** tab: compare Zep memory contexts across sessions and optionally summarize changes
  - Memory Cards (review, pin, edit durable facts)
  - Session Diff (compare memory context across sessions)

---

## Requirements

- Python 3.11+
- A **Zep API key** (for long-term memory)
- An **OpenAI API key** (for LLM responses)

---

## Quickstart

### 1) Configure environment

Create a `.env` file in the project root with your API keys:

```bash
ZEP_API_KEY=your_zep_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 2) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

### 3) Run the app

```bash
streamlit run app.py
```

Open the URL printed in your terminal (usually `http://localhost:8501`).

---

## Standout features

### Memory Cards
TraceMemory Copilot lets you turn retrieved Zep facts into **editable memory cards**:

- Refresh facts from Zep for the current session
- Pin high-value facts into a durable list
- Edit the text, rating, and source metadata
- Save pinned cards locally per user (for demos and iteration)

### Session Diff
Compare the memory context between two sessions and see what changed:

- Unified diff view (Added/Removed/Changed lines)
- Optional raw context panel
- Optional LLM-powered change summary (powered by OpenAI)

### Memory Analytics Dashboard
Quantify how memory behaves across turns and sessions:

- Memory hit rate (how often Zep returned non-empty context)
- Context size trends over turns
- Pinned cards vs auto-extracted Zep facts breakdown
- Session timeline table (with created_at timestamps when available)

---

## License

MIT (see `LICENSE`).

