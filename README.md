# ⚡ Pulse — AI-Powered News Briefing Agent

&gt; Autonomous intelligence briefing system that reads 50+ sources across 5 fields every morning and delivers curated news with AI-generated insights.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.1+-green.svg)](https://langchain.com)
[![Vue.js](https://img.shields.io/badge/Vue.js-3-4FC08D.svg)](https://vuejs.org)

---

## 🎯 What It Does

Pulse is a **multi-agent AI system** that:

1. **Scans** 50+ news sources across Tech, Finance, Sport, Health, and Geopolitics
2. **Scores** articles for relevance using LLM reasoning
3. **Summarizes** top stories with AI-generated insights
4. **Explains** why each story matters — in 3 sentences or less
5. **Delivers** everything in a clean, filterable dashboard

All running **100% on free tiers** — no OpenAI bills, no cloud costs.

---

## 🏗️ Architecture
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Vue 3     │────▶│   FastAPI   │────▶│   SQLite    │
│  Frontend   │◄────│   Backend   │◄────│   Database  │
└─────────────┘     └──────┬──────┘     └─────────────┘
│
┌──────┴──────┐
│  LangGraph   │
│ Orchestrator │
└──────┬──────┘
│
┌────────────┼────────────┐
▼            ▼            ▼
┌────────┐  ┌────────┐  ┌────────┐
│  RSS   │  │  Web   │  │  LLM   │
│  MCP   │  │  MCP   │  │Router  │
│ Server │  │ Server │  │Groq/   │
│        │  │        │  │Cerebras│
└────────┘  └────────┘  └────────┘


---

## 🚀 Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | Vue 3 (CDN) | Lightweight, reactive, no build step |
| **Backend** | FastAPI | High-performance Python API |
| **Agents** | LangGraph | Multi-agent orchestration with state machines |
| **LLM** | Groq + Cerebras + Gemini | Free tiers, fast inference, automatic fallback |
| **Tools** | MCP Protocol | Standardized tool calling (RSS, Web scraping) |
| **Database** | SQLite | Zero-config, portable |
| **Scheduler** | APScheduler | Daily 8 AM briefings |

---

## 📋 Features

- ✅ **5 Field Agents** — Tech, Finance, Sport, Health, Geopolitics
- ✅ **Multi-Provider LLM** — Automatic fallback Groq → Cerebras → Gemini
- ✅ **Smart Scoring** — LLM rates relevance 1-10 for every article
- ✅ **AI Summaries** — Concise 2-3 sentence briefings
- ✅ **"Why It Matters"** — Contextual impact analysis
- ✅ **"In Breve"** — One-click simplified explanations
- ✅ **Trending Detection** — Hot stories highlighted automatically
- ✅ **Category Filters** — Focus on what you care about
- ✅ **User Feedback** — Thumbs up/down for personalization
- ✅ **Auto-Schedule** — Fresh briefings every morning at 8 AM

---

## 🛠️ Quick Start

```bash
# Clone
git clone https://github.com/elyass399/pulse-ai.git
cd pulse-ai

# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your free API keys: Groq, Cerebras, Gemini

# Initialize database
python init_db.py

# Start backend
uvicorn app.main:app --reload

# Open frontend
open frontend/index.html
