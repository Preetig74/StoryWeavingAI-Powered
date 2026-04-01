# AI-Powered Story Weaver

A Streamlit storytelling app where the AI acts as a collaborative co-writer.  
Built with:

- **Python + Streamlit**
- **OpenAI-compatible LLM client**
- **LangGraph** for flow orchestration
- **ChromaDB** for lightweight continuity memory

## Why this stack

This follows the challenge guidance to use **Python + Streamlit** for fast execution and a clean UI.  
For the LLM backend, the app supports **OpenAI, Groq, and OpenRouter** using the official `openai` Python client with provider-specific configuration.

That gives you:
- fast prototyping
- flexibility to swap providers
- strong prompt control
- simple local setup

## Features

- Story setup screen
  - Title
  - Genre dropdown
  - Initial hook / setting
  - "Start the Story" button
- Main storytelling view
  - Full story so far
  - User contribution box
  - "Continue with AI"
  - "Give Me Choices"
- Story controls
  - Temperature / creativity slider
  - Genre + story rules display
- Continuity helpers
  - Character tracker
  - Continuity notes
  - Chroma-backed memory retrieval
- Bonus
  - Export Markdown
  - Undo last AI turn

## Project structure

```text
story_weaver_app/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
└── src/
    ├── config.py
    ├── prompts.py
    ├── llm.py
    ├── memory.py
    ├── graph_flow.py
    └── utils.py
```

## Setup

### 1. Create environment

```bash
python -m venv .venv
```

#### Mac / Linux
```bash
source .venv/bin/activate
```

#### Windows PowerShell
```powershell
.venv\Scripts\Activate.ps1
```

### 2. Install packages

```bash
pip install -r requirements.txt
```

### 3. Add environment variables

Copy `.env.example` to `.env` and fill in your key.

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

### 4. Run the app

```bash
streamlit run app.py
```

## Provider options

### OpenAI
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=...
MODEL_NAME=gpt-4.1-mini
```

### Groq
```env
LLM_PROVIDER=groq
GROQ_API_KEY=...
MODEL_NAME=llama-3.3-70b-versatile
```

### OpenRouter
```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=...
MODEL_NAME=openai/gpt-4.1-mini
```

## Memory / consistency strategy

The challenge asks that the **entire story history** be sent with each call.  
This app does that.

In addition, it also stores:
- story snapshots
- continuity notes
- character tracker summaries
- user turns

Those are saved in **ChromaDB** and retrieved as extra continuity hints.  
This improves consistency without replacing the full-history requirement.

## Final system prompt

The app uses an improved prompt that enforces:
- genre consistency
- continuity
- character consistency
- concise but vivid narration
- no contradiction of established facts

You can see it in `src/prompts.py`.

## What did not work well at first

A naive prompt caused the model to drift in tone and occasionally repeat facts.  
This was improved by:
- separating system prompt and task prompt
- passing continuity notes and character summaries
- retrieving lightweight memory from ChromaDB

## What I would improve with another day

- streaming token output
- editable story rules
- better structured JSON parsing for tracker extraction
- long-story summarization to control token growth
- “genre remix” button
- unit tests for prompt and parsing helpers
