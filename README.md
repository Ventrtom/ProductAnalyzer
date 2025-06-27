# 🧠 ProductAnalyzer – AI Agent for Roadmap Idea Generation

## 🎯 Goal

ProductAnalyzer is an AI-based agent designed to help Product Managers generate new, high-impact Ideas for software roadmap planning. The system analyzes:

- 📘 Internal documentation (system capabilities)
- ✅ Existing roadmap Ideas (e.g. from JIRA)
- 📊 Market landscape (competitors, trends)
- 📌 Product strategic goals

Its purpose is to suggest **novel, feasible, and impactful ideas**, identify **system weaknesses**, and recommend **market-aligned improvements** using modern LLMs (e.g., GPT-4o).

## 🚀 Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file in the project root based on `.env.example` and add your values.
3. Run the orchestrator from the project root:
   ```bash
   python orchestrator.py
   ```

OpenAI API calls require a valid `OPENAI_API_KEY` in your environment.

---

## 📦 Architecture Overview

User Prompt
│
▼
[Prompt Handler] → [Agent Orchestrator] → [Retriever Module] → [Reasoning Module]
│ ↓
└───────────────→ [Deduplication Layer] ←─────────
│
▼
[Idea Composer] → [Exporter]


---

## 🧩 Modules

### 1. Prompt Handler (`ui/`)
Handles user input via Streamlit or CLI, prepares JSON task prompts.

### 2. Agent Orchestrator (`orchestrator.py`)
Main logic that routes between tools. Can use LangChain or custom flow.

### 3. Retriever Module (`retrievers/`)
- `confluence_scraper.py` – Scrapes system documentation
- `jira_retriever.py` – Imports existing Ideas from JIRA API
- `competitor_scraper.py` – Optionally scrapes or searches market data

### 4. RAG Vector Store (`rag/`)
Embeds and indexes documents using OpenAI + ChromaDB or Weaviate.

### 5. Reasoning Module (`llm_modules/`)
Analyzes documentation and market input to identify improvement opportunities.

### 6. Deduplication Layer
Checks if proposed ideas already exist (via vector similarity).

### 7. Idea Composer (`ideas/composer.py`)
Creates structured proposals with tags, description, business value, etc.

### 8. Exporter (`output/export.py`)
Exports ideas as Markdown, JSON, or into JIRA.

---

## 🛠️ Tech Stack

- Python 3.11+
- LangChain or LlamaIndex
- OpenAI GPT-4o (function calling)
- ChromaDB (vector store)
- JIRA REST API
- Streamlit (optional frontend)

### Configuration
Create a `.env` file in the project root based on `.env.example` and set:

- `JIRA_URL` – Base URL of your JIRA instance
- `JIRA_PROJECT_KEY` – Project key to fetch issues from
- `JIRA_AUTH_TOKEN` – Base64 token used for Basic Auth
- `OPENAI_API_KEY` – Your OpenAI API key

---

## 🚧 Milestone Plan (MVP)

1. [ ] Create retrievers for documentation and JIRA
2. [ ] Setup basic LangChain or custom orchestrator
3. [ ] Connect reasoning via GPT-4o
4. [ ] Implement deduplication check
5. [ ] Generate 1–2 ideas and export to Markdown
6. [ ] Add feedback loop for evaluation
