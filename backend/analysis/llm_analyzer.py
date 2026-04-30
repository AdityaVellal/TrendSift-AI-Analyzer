"""
llm_analyzer.py - Sends content to Ollama for deep, structured analysis.

WHAT THIS MODULE DOES:
Takes scraped article content and sends it to a LOCAL LLM (via Ollama)
with a carefully crafted prompt. The LLM returns a structured analysis
following our case-study format.

HOW OLLAMA WORKS:
1. Ollama runs as a local server on your machine (default: http://localhost:11434)
2. You pull a model once:  ollama pull mistral
3. Then you send HTTP requests to it, just like any API
4. It processes the text and returns a response

KEY CONCEPT - PROMPT ENGINEERING:
The quality of AI output depends heavily on HOW you ask. Our prompt:
- Tells the LLM exactly what role to play (content strategist)
- Specifies the exact output format (JSON structure)
- Provides clear instructions for each analysis section
- Asks for specific, actionable insights (not generic fluff)

SETUP INSTRUCTIONS:
1. Download Ollama from https://ollama.ai
2. Install it (just run the installer)
3. Open a terminal and run:  ollama pull mistral
4. Keep Ollama running (it starts automatically on install)
"""

import json
import logging
import httpx
from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger("trendsift.analysis")

# ── The Analysis Prompt ──────────────────────────────────────────
# This is the most important part — it tells the AI EXACTLY what to do.
# A good prompt = good results. A vague prompt = garbage output.
ANALYSIS_PROMPT = """You are an elite content strategist and viral content analyst.

Analyze the following article content and provide a DETAILED case-study style analysis.

ARTICLE TITLE: {title}
ARTICLE URL: {url}

ARTICLE CONTENT:
{content}

---

You MUST respond with a valid JSON object (no markdown, no code fences, just raw JSON) with EXACTLY this structure:

{{
    "title": "The article title",
    "core_idea": "A 2-3 sentence summary of the central thesis or main idea of the content. What is the author trying to convey?",
    "hook_breakdown": {{
        "hook_type": "What type of hook is used? (e.g., curiosity gap, bold claim, data-driven, personal story, contrarian take, question, listicle)",
        "hook_text": "The actual opening hook text or a close paraphrase",
        "why_it_works": "Explain WHY this hook captures attention — what psychological trigger does it activate?"
    }},
    "content_structure": "Describe how the content is organized: sections, flow, transitions, use of examples, data, stories. Is it listicle, narrative, how-to, case study, opinion?",
    "writing_style": "Analyze the writing tone, voice, sentence length, use of jargon, personality level. Is it conversational, academic, punchy, storytelling?",
    "why_it_works": {{
        "psychological_reasons": ["List 2-3 psychological principles that make this content engaging (e.g., social proof, curiosity gap, loss aversion, identity signaling)"],
        "structural_reasons": ["List 2-3 structural elements that make it effective (e.g., scannable formatting, progressive disclosure, strong CTA)"]
    }},
    "reusable_insights": [
        "Actionable insight 1 that can be applied to other content",
        "Actionable insight 2",
        "Actionable insight 3",
        "Actionable insight 4",
        "Actionable insight 5"
    ],
    "suggested_content_idea": "Based on this analysis, suggest a NEW content idea that uses similar principles but on a different angle or for a different audience. Be specific and creative."
}}

IMPORTANT: Return ONLY the JSON object. No explanations, no markdown formatting, no code blocks. Just the raw JSON."""


async def analyze_content(title: str, url: str, content: str) -> dict | None:
    """
    Send article content to Ollama for structured analysis.
    
    Args:
        title: The article title
        url: The article URL
        content: The scraped and cleaned article text
    
    Returns:
        A dictionary containing the structured analysis, or None if analysis fails.
    
    HOW IT WORKS:
    1. We format the prompt with the article's title, URL, and content
    2. We send it to Ollama's /api/generate endpoint
    3. Ollama processes it with the local LLM model
    4. We parse the JSON response and return the structured analysis
    """
    logger.info(f"Sending to LLM for analysis: {title[:50]}...")

    # Format the prompt with the article data
    prompt = ANALYSIS_PROMPT.format(
        title=title,
        url=url,
        content=content[:3500],  # Trim content to avoid overwhelming the LLM
    )

    try:
        # ── Send to Ollama ───────────────────────────────────
        # Ollama exposes a REST API. We use the /api/generate endpoint.
        # 'stream: false' means we wait for the full response
        # (instead of receiving it token by token).
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    # Temperature controls creativity:
                    # 0.0 = very focused/deterministic
                    # 1.0 = very creative/random
                    # 0.3 = slightly creative, mostly factual (good for analysis)
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 2000,  # Max tokens in response
                    },
                },
            )
            response.raise_for_status()

        result = response.json()
        raw_text = result.get("response", "")

        if not raw_text:
            logger.error("LLM returned empty response")
            return None

        # ── Parse the JSON response ──────────────────────────
        # The LLM should return valid JSON, but sometimes it adds
        # extra text or formatting. We need to extract just the JSON.
        analysis = _parse_llm_response(raw_text)

        if analysis:
            # Add the source URL to the analysis
            analysis["source_url"] = url
            logger.info(f"✅ Analysis complete for: {title[:50]}")
            return analysis
        else:
            logger.error(f"Failed to parse LLM response for: {title[:50]}")
            return None

    except httpx.ConnectError:
        logger.error(
            "❌ Cannot connect to Ollama. Is it running?\n"
            "   Start it with: ollama serve\n"
            "   Then pull a model: ollama pull mistral"
        )
        return None
    except httpx.TimeoutException:
        logger.error(f"⏰ LLM analysis timed out for: {title[:50]}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected LLM error: {e}")
        return None


def _parse_llm_response(raw_text: str) -> dict | None:
    """
    Parse the LLM response text into a Python dictionary.
    
    WHY THIS IS NEEDED:
    LLMs don't always follow instructions perfectly. They might:
    - Add markdown code fences around the JSON (```json ... ```)
    - Include explanatory text before/after the JSON
    - Have minor JSON formatting issues
    
    This function handles all those edge cases.
    """
    # Clean up the response
    text = raw_text.strip()

    # Remove markdown code fences if present
    if "```json" in text:
        text = text.split("```json", 1)[1]
        if "```" in text:
            text = text.split("```", 1)[0]
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            text = parts[1]
        elif len(parts) >= 2:
            text = parts[1]

    text = text.strip()

    # Try to parse as JSON directly
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find a JSON object in the text (between first { and last })
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        json_str = text[start:end]
        return json.loads(json_str)
    except (ValueError, json.JSONDecodeError):
        pass

    # Last resort: try to fix common JSON issues
    try:
        # Sometimes LLMs use single quotes instead of double quotes
        fixed = text.replace("'", '"')
        start = fixed.index("{")
        end = fixed.rindex("}") + 1
        return json.loads(fixed[start:end])
    except (ValueError, json.JSONDecodeError):
        logger.error(f"Could not parse LLM response as JSON. Raw response:\n{raw_text[:500]}")
        return None


async def check_ollama_status() -> dict:
    """
    Check if Ollama is running and which models are available.
    
    Returns a dict with:
    - running: bool (whether Ollama is reachable)
    - models: list of available model names
    - error: error message if not running
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check if Ollama is reachable
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            data = response.json()

            models = [m["name"] for m in data.get("models", [])]
            return {
                "running": True,
                "models": models,
                "configured_model": OLLAMA_MODEL,
                "model_available": any(OLLAMA_MODEL in m for m in models),
            }
    except Exception as e:
        return {
            "running": False,
            "models": [],
            "configured_model": OLLAMA_MODEL,
            "model_available": False,
            "error": str(e),
        }
