import os
import json
import asyncio
import logging
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse

from backend.config import HOST, PORT
from backend.search.web_search import search_web
from backend.scraper.content_scraper import scrape_url
from backend.analysis.llm_analyzer import analyze_content

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("trendsift")

app = FastAPI(title="TrendSift")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "TrendSift is running!"}

@app.get("/api/trending")
async def get_trending_topics():
    """Fetches a diverse set of 5 trending topics for analysis."""
    logger.info("📡 Fetching Top 5 Trending Options...")
    
    # 1. Start with high-quality fallback options (Variety)
    fallback_topics = [
        "AI Agents & Automation", 
        "The Future of Remote Work", 
        "Creator Economy Growth", 
        "Sustainable Tech Trends", 
        "SaaS Market Insights"
    ]
    
    try:
        import httpx
        from xml.etree import ElementTree
        
        # Pulling from the global Top Stories feed
        rss_url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(rss_url)
            if response.status_code == 200:
                root = ElementTree.fromstring(response.text)
                items = root.findall(".//item")
                
                topics = []
                seen_titles = set()
                
                # We pick 5 diverse headlines
                for item in items:
                    title = item.find("title").text
                    clean_title = title.split(" - ")[0].split(" | ")[0].strip()
                    
                    # Filter for quality: not too long, not duplicate, not too short
                    if clean_title and clean_title not in seen_titles and 10 < len(clean_title) < 70:
                        topics.append(clean_title)
                        seen_titles.add(clean_title)
                    
                    if len(topics) >= 5: # Stop at 5 perfect options
                        break
                
                if len(topics) >= 3: # If we got at least a few, use them
                    return {"topics": topics}
                    
    except Exception as e:
        logger.warning(f"Trend fetch failed: {e}")
        
    return {"topics": fallback_topics}

@app.get("/api/ollama-status")
async def ollama_status():
    from backend.analysis.llm_analyzer import check_ollama_status
    status = await check_ollama_status()
    return status

def format_sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"

@app.get("/api/analyze")
async def analyze_keyword(keyword: str = Query(..., description="The topic to research")):
    logger.info(f"🔍 New analysis request: '{keyword}'")

    async def event_stream():
        # STEP 1: Search the web
        logger.info(f"📡 Searching the web for: '{keyword}'")
        yield format_sse({"type": "status", "message": f"Searching the web for '{keyword}'..."})

        try:
            search_results = await search_web(keyword)
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            yield format_sse({"type": "error", "message": f"Search failed: {str(e)}"})
            return

        if not search_results:
            logger.warning("⚠️ No search results found.")
            yield format_sse({"type": "error", "message": "No results found. Try a different keyword."})
            return

        logger.info(f"✅ Found {len(search_results)} results")
        yield format_sse({
            "type": "status",
            "message": f"Found {len(search_results)} articles. Starting analysis..."
        })

        # STEP 2 & 3: Scrape and Analyze
        analyzed_count = 0
        for i, result in enumerate(search_results):
            url = result.get("url", "")
            title = result.get("title", "Untitled")
            snippet = result.get("snippet", "")
            
            yield format_sse({
                "type": "status", 
                "message": f"📄 [{i+1}/{len(search_results)}] Reading: {title[:40]}..."
            })

            # Try to Scrape
            content = ""
            try:
                content = await scrape_url(url)
            except Exception as e:
                logger.error(f"Scraper error for {url}: {e}")

            # Fallback to snippet if scraping failed
            source_type = "full_article"
            if not content or len(content.strip()) < 150:
                logger.warning(f"⚠️ Scraper got no content for {url}. Falling back to snippet.")
                content = f"Title: {title}\nSummary: {snippet}"
                source_type = "snippet"

            # Analyze with LLM
            yield format_sse({
                "type": "status", 
                "message": f"🧠 [{i+1}/{len(search_results)}] AI is analyzing..."
            })
            
            try:
                # FIX: Passing correct arguments to analyze_content
                analysis = await analyze_content(title, url, content)
                
                if analysis:
                    # Add metadata to result
                    analysis["id"] = i + 1
                    analysis["url"] = url
                    analysis["source_title"] = title
                    analysis["analysis_type"] = source_type
                    
                    yield format_sse({
                        "type": "result", 
                        "data": analysis,
                        "index": i + 1
                    })
                    analyzed_count += 1
                else:
                    logger.warning(f"⚠️ AI returned no analysis for {title}")
                
            except Exception as e:
                logger.error(f"❌ AI Analysis failed for {url}: {e}")
                continue

        logger.info(f"🏁 Analysis complete. {analyzed_count} articles analyzed.")
        yield format_sse({
            "type": "status", 
            "message": f"✅ Complete! Analyzed {analyzed_count} articles."
        })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )

# Serve Frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    styles_path = os.path.join(frontend_path, "styles")
    components_path = os.path.join(frontend_path, "components")
    utils_path = os.path.join(frontend_path, "utils")
    
    if os.path.exists(styles_path):
        app.mount("/styles", StaticFiles(directory=styles_path), name="styles")
    if os.path.exists(components_path):
        app.mount("/components", StaticFiles(directory=components_path), name="components")
    if os.path.exists(utils_path):
        app.mount("/utils", StaticFiles(directory=utils_path), name="utils")

    @app.get("/", response_class=HTMLResponse)
    async def serve_frontend():
        index_path = os.path.join(frontend_path, "pages", "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>TrendSift</h1><p>Frontend index.html not found.</p>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)
