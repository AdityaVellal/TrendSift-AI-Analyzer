# 🔬 TrendSift — AI Viral Content Analyzer

TrendSift is a keyword-based web application that searches the web for trending content, scrapes articles, and uses a **local LLM** (via Ollama) to produce deep, structured case-study style insights.

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)

---

## ✨ Features

- **🔍 Web Search** — Finds relevant articles via SerpAPI or DuckDuckGo
- **📄 Smart Scraping** — Extracts article text, strips ads/nav/scripts
- **🧠 Local AI Analysis** — Uses Ollama (Mistral/Llama) for deep analysis
- **📊 Structured Output** — Hook breakdown, writing style, psychological triggers, reusable insights
- **⚡ Progressive Loading** — Results stream in one-by-one via SSE
- **🎨 Premium UI** — Dark mode, expandable cards, smooth animations

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python + FastAPI |
| Search | SerpAPI / DuckDuckGo fallback |
| Scraping | requests + BeautifulSoup |
| AI | Ollama (local LLM) |
| Frontend | HTML + CSS + JavaScript |
| Streaming | Server-Sent Events (SSE) |

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+** installed
2. **Ollama** installed and running

### 1. Install Ollama

Download from [https://ollama.ai](https://ollama.ai) and install it.

Then pull a model:
```bash
ollama pull mistral
```

Make sure Ollama is running:
```bash
ollama serve
```

### 2. Clone and Setup

```bash
cd TrendSift

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure (Optional)

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` to add your SerpAPI key (optional — DuckDuckGo fallback works without it):
```
SERP_API_KEY=your_key_here
```

### 4. Run

```bash
python -m backend.main
```

Visit **http://localhost:8000** in your browser!

---

## 📁 Project Structure

```
TrendSift/
├── backend/
│   ├── search/
│   │   └── web_search.py      # Web search API integration
│   ├── scraper/
│   │   └── content_scraper.py  # Article text extraction
│   ├── analysis/
│   │   └── llm_analyzer.py     # Ollama LLM integration
│   ├── config.py               # Central configuration
│   └── main.py                 # FastAPI server entry point
├── frontend/
│   ├── pages/
│   │   └── index.html          # Main UI page
│   ├── components/
│   │   └── ResultCard.js       # Result card component
│   ├── styles/
│   │   └── main.css            # Design system
│   └── utils/
│       └── api.js              # API communication + progressive loading
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 📊 Analysis Format

Each analyzed article produces:

1. **Title** — The article headline
2. **Core Idea** — 2-3 sentence thesis summary
3. **Hook Breakdown** — Hook type, text, and why it works
4. **Content Structure** — How the content is organized
5. **Writing Style** — Tone, voice, sentence patterns
6. **Why It Works** — Psychological + structural reasons
7. **Reusable Insights** — Actionable takeaways
8. **Suggested Content Idea** — AI-generated content inspiration

---

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SERP_API_KEY` | — | SerpAPI key (optional) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `mistral` | Which LLM model to use |
| `SEARCH_RESULTS_COUNT` | `5` | How many articles to analyze |
| `MAX_CONTENT_LENGTH` | `4000` | Max chars to send to LLM |

---

## 📝 License

MIT — free to use, modify, and share.
