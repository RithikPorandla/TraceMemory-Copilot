# TraceMemory Copilot

A Streamlit-based chat assistant that uses **Zep** as a long-term memory backend and **Ollama** for local LLM inference.

This project is optimized for portfolio demos: it shows **persistent memory**, **user/session management**, **exportable transcripts**, plus a **Memory Cards** workflow and a **Session Diff** view to inspect how memory evolves.

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
- A **Zep API key**
- Ollama running locally (`http://127.0.0.1:11434`)

---

## Quickstart

### 1) Configure environment

Copy `.env.example` to `.env` and set your values:

```bash
cp .env.example .env
```

### 2) Install dependencies

Using `uv`:

```bash
uv sync
source .venv/bin/activate
```

Or with pip:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install .
```

### 3) Run Ollama

```bash
ollama pull qwen3:4b
ollama serve
```

### 4) Run the app

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
- Optional LLM-powered change summary (runs locally through Ollama)

### Memory Analytics Dashboard
Quantify how memory behaves across turns and sessions:

- Memory hit rate (how often Zep returned non-empty context)
- Context size trends over turns
- Pinned cards vs auto-extracted Zep facts breakdown
- Session timeline table (with created_at timestamps when available)

---

## License

MIT (see `LICENSE`).
