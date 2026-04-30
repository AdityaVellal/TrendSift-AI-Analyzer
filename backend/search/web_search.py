import logging
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from backend.config import SERP_API_KEY, SEARCH_RESULTS_COUNT

logger = logging.getLogger("trendsift.search")


async def search_web(keyword: str) -> list[dict]:
    """
    Search the web for articles related to the given keyword.
    """
    # ── Strategy 1: SerpAPI (If Key Provided) ─────────────────
    if SERP_API_KEY and SERP_API_KEY != "your_api_key_here":
        logger.info("Using SerpAPI for search")
        results = _search_with_serpapi(keyword)
        if results: return results
    
    # ── Strategy 2: Google News RSS (Most Reliable Fallback) ──
    logger.info("Using Google News RSS strategy...")
    results = _search_with_google_news_rss(keyword)
    if results: return results

    # ── Strategy 3: duckduckgo-search library ─────────────────
    logger.info("Trying duckduckgo-search fallback...")
    return _search_with_ddgs(keyword)



def _search_with_serpapi(keyword: str) -> list[dict]:
    """Search using SerpAPI (Google Search API)."""
    try:
        response = requests.get(
            "https://serpapi.com/search",
            params={
                "q": keyword,
                "api_key": SERP_API_KEY,
                "num": SEARCH_RESULTS_COUNT,
                "engine": "google",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("organic_results", [])[:SEARCH_RESULTS_COUNT]:
            results.append({
                "title": item.get("title", "Untitled"),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            })
        return results
    except Exception as e:
        logger.error(f"SerpAPI failed: {e}")
        return []


def _search_with_ddgs(keyword: str) -> list[dict]:
    """Robust fallback search using the duckduckgo-search library."""
    try:
        results = []
        with DDGS() as ddgs:
            ddgs_results = ddgs.text(keyword, max_results=SEARCH_RESULTS_COUNT)
            for r in ddgs_results:
                results.append({
                    "title": r.get("title", "Untitled"),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
        return results
    except Exception as e:
        logger.error(f"DDGS failed: {e}")
        return []


def _search_with_google_news_rss(keyword: str) -> list[dict]:
    """
    Search using Google News RSS feed.
    
    WHY THIS WORKS:
    RSS feeds are XML data meant for machines to read. They don't 
    have the aggressive bot protection that regular search result
    pages have. This is a very reliable way to get news/articles.
    """
    try:
        # Google News RSS URL
        import urllib.parse
        encoded_query = urllib.parse.quote(keyword)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.content)
        results = []
        
        # Google News RSS items are in <channel><item>
        for item in root.findall(".//item")[:SEARCH_RESULTS_COUNT]:
            title = item.find("title").text if item.find("title") is not None else "Untitled"
            link = item.find("link").text if item.find("link") is not None else ""
            
            # Google News links are often encoded/redirected
            # BeautifulSoup can help extract clean links if needed, 
            # but usually the direct link in <link> works.
            
            if title and link:
                results.append({
                    "title": title,
                    "url": link,
                    "snippet": f"Latest news about {keyword}",
                })
                
        logger.info(f"Google News RSS returned {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Google News RSS fallback failed: {e}")
        return []


