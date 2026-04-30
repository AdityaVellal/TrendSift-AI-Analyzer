"""
config.py - Central configuration for TrendSift

WHY THIS FILE EXISTS:
Instead of scattering settings across multiple files, we keep them
all in one place. This makes it easy to change API keys, URLs, or
model names without hunting through the codebase.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()


# ── Search API Configuration ──────────────────────────────────────
# We use SerpAPI to search the web. You'll need a free API key.
# Sign up at: https://serpapi.com (free tier gives 100 searches/month)
SERP_API_KEY = os.getenv("SERP_API_KEY", "")
# Search Settings
# Increasing this will give you more analysis, but will take longer to complete.
SEARCH_RESULTS_COUNT = 10  # How many articles to analyze per keyword


# ── Ollama Configuration ──────────────────────────────────────────
# Ollama runs locally on your machine at this address by default.
# Make sure Ollama is running before starting TrendSift!
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")


# ── Scraper Configuration ────────────────────────────────────────
# Maximum characters to extract from each article.
# Too much text = slow LLM analysis. Too little = shallow insights.
MAX_CONTENT_LENGTH = 4000  # characters
REQUEST_TIMEOUT = 10  # seconds to wait before giving up on a page


# ── Server Configuration ─────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 8000
