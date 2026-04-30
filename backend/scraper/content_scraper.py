import logging
import requests
from bs4 import BeautifulSoup
from backend.config import MAX_CONTENT_LENGTH, REQUEST_TIMEOUT

logger = logging.getLogger("trendsift.scraper")

async def scrape_url(url: str) -> str:
    """
    Scrape and extract clean text content from a URL.
    """
    logger.info(f"Scraping: {url}")

    try:
        # Step 0: Follow Redirects
        final_url = url
        if "news.google.com" in url:
            try:
                r = requests.get(url, timeout=10, allow_redirects=True)
                final_url = r.url
                logger.info(f"Followed redirect to: {final_url}")
            except Exception as e:
                logger.warning(f"Could not follow redirect for {url}: {e}")

        # Step 1: Download the page
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        response = requests.get(
            final_url,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        response.raise_for_status()

        # Step 2: Extract text
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove noise elements
        for tag in ["script", "style", "nav", "footer", "header", "aside", "form"]:
            for element in soup.find_all(tag):
                element.decompose()

        # Try to find semantic content
        content_element = soup.find("article") or soup.find("main") or soup.find(id="content") or soup.find(class_="content")
        
        if content_element:
            text = content_element.get_text(separator="\n", strip=True)
        else:
            # Fallback: Just get all paragraphs
            paragraphs = soup.find_all("p")
            text = "\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text()) > 30])

        # Final fallback: the entire body if text is still too short
        if not text or len(text.strip()) < 200:
            body = soup.find("body")
            if body:
                text = body.get_text(separator="\n", strip=True)

        cleaned = _clean_text(text)
        logger.info(f"✅ Successfully scraped {len(cleaned)} characters")
        return cleaned[:MAX_CONTENT_LENGTH]

    except Exception as e:
        logger.error(f"❌ Scraping failed for {url}: {e}")
        return ""

def _clean_text(text: str) -> str:
    """Clean up whitespace and redundant newlines."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    # Filter out very short lines (probably nav items or menus)
    filtered_lines = [line for line in lines if len(line) > 20]
    return "\n".join(filtered_lines)
