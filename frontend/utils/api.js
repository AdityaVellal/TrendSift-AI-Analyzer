/**
 * api.js - Handles communication with the backend and UI state management.
 * 
 * THIS IS WHERE THE MAGIC HAPPENS:
 * This file connects the user's input to the backend pipeline and
 * implements PROGRESSIVE LOADING — the key UX feature of TrendSift.
 * 
 * HOW PROGRESSIVE LOADING WORKS:
 * ─────────────────────────────────
 * Traditional approach: 
 *   Click → Wait 2 minutes → ALL results appear at once
 * 
 * Our approach (Server-Sent Events / SSE):
 *   Click → Results appear ONE BY ONE as each finishes analyzing
 * 
 * TECHNICAL EXPLANATION:
 * 1. User clicks "Analyze"
 * 2. We create an EventSource connection to /api/analyze?keyword=...
 * 3. The backend searches, then for EACH article:
 *    - Scrapes it
 *    - Sends it to the LLM
 *    - Sends the result back to us as an "event"
 * 4. We receive each event and immediately render a new card
 * 5. The card slides in with a smooth animation
 * 
 * This creates the feeling of an intelligent system processing
 * information in real-time — much more engaging than a loading spinner!
 */


// ── DOM References ───────────────────────────────────────────────
// We grab references to DOM elements once at startup, rather than
// finding them repeatedly. This is more efficient.
const searchForm = document.getElementById('searchForm');
const keywordInput = document.getElementById('keywordInput');
const searchBtn = document.getElementById('searchBtn');
const statusBar = document.getElementById('statusBar');
const statusText = document.getElementById('statusText');
const statusProgress = document.getElementById('statusProgress');
const resultsContainer = document.getElementById('resultsContainer');
const emptyState = document.getElementById('emptyState');
const ollamaStatusEl = document.getElementById('ollamaStatus');
const ollamaStatusText = document.getElementById('ollamaStatusText');


// ── State ────────────────────────────────────────────────────────
// Track whether an analysis is currently running (to prevent double-clicks)
let isAnalyzing = false;
let currentEventSource = null;  // Reference to the active SSE connection


console.log('🚀 TrendSift Engine Starting...');

// ── Initialize ───────────────────────────────────────────────────
// When the page loads, check Ollama status and set up event listeners.
document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ DOM Ready. Initializing...');
    checkOllamaStatus();
    loadTrendingTopics();
    
    if (searchForm) {
        searchForm.addEventListener('submit', handleSubmit);
    }
});

/**
 * Fetches current trending topics from the backend and displays them.
 */
async function loadTrendingTopics() {
    console.log('📡 Starting trend discovery...');
    const trendingContainer = document.getElementById('trendingTopics');
    if (!trendingContainer) {
        console.error('❌ Could not find trendingTopics container');
        return;
    }

    try {
        const response = await fetch('/api/trending');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        console.log('✅ Received trends:', data);

        if (data.topics && data.topics.length > 0) {
            trendingContainer.innerHTML = '';
            data.topics.forEach(topic => {
                const tag = document.createElement('span');
                tag.className = 'trending-tag';
                tag.textContent = topic;
                tag.onclick = (e) => {
                    e.preventDefault();
                    console.log('🚀 Triggering analysis for:', topic);
                    keywordInput.value = topic;
                    startAnalysis(topic);
                };
                trendingContainer.appendChild(tag);
            });
        } else {
            throw new Error('No topics in response');
        }
    } catch (err) {
        console.warn('⚠️ Trend fetch failed, using fallback list:', err);
        const fallbacks = ["AI Agents", "Creator Economy", "SaaS Trends", "Remote Work", "Viral Marketing"];
        trendingContainer.innerHTML = '';
        fallbacks.forEach(topic => {
            const tag = document.createElement('span');
            tag.className = 'trending-tag';
            tag.textContent = topic;
            tag.onclick = () => {
                keywordInput.value = topic;
                startAnalysis(topic);
            };
            trendingContainer.appendChild(tag);
        });
    }
}


// ── Ollama Status Check ──────────────────────────────────────────
/**
 * Checks if Ollama is running and updates the status indicator.
 * This runs on page load so the user knows immediately if
 * they need to start Ollama before analyzing.
 */
async function checkOllamaStatus() {
    try {
        const response = await fetch('/api/ollama-status');
        const data = await response.json();

        if (data.running && data.model_available) {
            setOllamaStatus('online', `Ollama ready — ${data.configured_model}`);
        } else if (data.running && !data.model_available) {
            setOllamaStatus('offline', `Model "${data.configured_model}" not found. Run: ollama pull ${data.configured_model}`);
        } else {
            setOllamaStatus('offline', 'Ollama not running. Start it first!');
        }
    } catch {
        setOllamaStatus('offline', 'Cannot connect to TrendSift server');
    }
}

function setOllamaStatus(status, text) {
    ollamaStatusEl.className = `ollama-status ${status}`;
    ollamaStatusText.textContent = text;
}


// ── Form Submit Handler ──────────────────────────────────────────
/**
 * Handles the search form submission.
 * Validates input, disables the button, and starts the SSE stream.
 */
function handleSubmit(e) {
    e.preventDefault();
    
    const keyword = keywordInput.value.trim();
    if (!keyword || isAnalyzing) return;
    
    startAnalysis(keyword);
}


// ── Main Analysis Function ───────────────────────────────────────
/**
 * THE CORE FUNCTION — Starts the progressive loading pipeline.
 * 
 * FLOW:
 * 1. Clear previous results
 * 2. Show the status bar
 * 3. Disable the search button
 * 4. Open an SSE connection to the backend
 * 5. Listen for events and handle each type:
 *    - "status" → Update the status bar text
 *    - "progress" → Show which article is being analyzed
 *    - "result" → Create and display a new card!
 *    - "error" → Show error in status bar
 *    - "done" → Analysis complete, re-enable the form
 */
function startAnalysis(keyword) {
    isAnalyzing = true;

    // ── Reset the UI ────────────────────────────────────────
    resultsContainer.innerHTML = '';
    emptyState.style.display = 'none';
    searchBtn.classList.add('loading');
    searchBtn.disabled = true;
    showStatus('Initializing analysis pipeline...', '');

    // Close any existing SSE connection
    if (currentEventSource) {
        currentEventSource.close();
    }

    // ── Open SSE Connection ─────────────────────────────────
    // EventSource is a browser API that connects to a server
    // and receives a stream of events. It automatically
    // reconnects if the connection drops.
    const encodedKeyword = encodeURIComponent(keyword);
    currentEventSource = new EventSource(`/api/analyze?keyword=${encodedKeyword}`);

    // ── Handle Incoming Events ──────────────────────────────
    currentEventSource.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data);
            handleEvent(payload);
        } catch (err) {
            console.error('Failed to parse SSE event:', err);
        }
    };

    // ── Handle Connection Errors ────────────────────────────
    currentEventSource.onerror = (err) => {
        console.error('SSE connection error:', err);
        
        // EventSource fires error when the connection closes normally too,
        // so we only show an error if we didn't receive a "done" event.
        if (isAnalyzing) {
            showStatus('Connection lost. Please try again.', '', true);
            finishAnalysis();
        }
    };
}


/**
 * Handle a single SSE event based on its type.
 * This is called for EVERY event the server sends.
 */
function handleEvent(payload) {
    switch (payload.type) {
        case 'status':
            showStatus(payload.message, '');
            break;

        case 'progress':
            showStatus(
                payload.message,
                `${payload.current}/${payload.total}`
            );
            break;

        case 'result':
            // 🎉 This is the exciting part — a new result has arrived!
            // Ensure we have an index (id) to avoid the "all cards same id" bug
            const resultIndex = payload.index || (payload.data && payload.data.id) || document.querySelectorAll('.result-card').length + 1;
            addResultCard(payload.data, resultIndex);
            break;

        case 'scrape_error':
        case 'analysis_error':
            // Non-fatal errors — the pipeline continues
            console.warn(`Non-fatal error: ${payload.message}`);
            break;

        case 'error':
            showStatus(payload.message, '', true);
            finishAnalysis();
            break;

        case 'done':
            showDone(payload.message, payload.total_analyzed);
            finishAnalysis();
            break;
    }
}


/**
 * Add a new result card to the page with a smooth entrance animation.
 * This is called each time the backend finishes analyzing one article.
 */
function addResultCard(data, index) {
    // createResultCard is defined in ResultCard.js
    const card = createResultCard(data, index);
    resultsContainer.appendChild(card);

    // Scroll the new card into view smoothly
    // We use setTimeout to let the card render first
    setTimeout(() => {
        card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
}


// ── UI Helper Functions ──────────────────────────────────────────

/**
 * Show the status bar with a message.
 */
function showStatus(message, progress, isError = false) {
    statusBar.className = `status-bar visible ${isError ? 'error' : ''}`;
    statusText.textContent = message;
    statusProgress.textContent = progress;
}

/**
 * Show the "done" state in the status bar.
 */
function showDone(message, totalAnalyzed) {
    statusBar.className = 'status-bar visible done';
    statusText.textContent = message;
    statusProgress.textContent = `✓ ${totalAnalyzed}`;

    // If no results were analyzed, show a helpful message
    if (totalAnalyzed === 0) {
        emptyState.style.display = 'block';
        const emptyText = emptyState.querySelector('.empty-state__text');
        const emptyHint = emptyState.querySelector('.empty-state__hint');
        if (emptyText) emptyText.textContent = 'No articles could be analyzed';
        if (emptyHint) emptyHint.textContent = 'Try a different keyword or check your Ollama setup';
    }
}

/**
 * Clean up after analysis completes (success or failure).
 */
function finishAnalysis() {
    isAnalyzing = false;
    searchBtn.classList.remove('loading');
    searchBtn.disabled = false;
    keywordInput.focus();

    // Close the SSE connection
    if (currentEventSource) {
        currentEventSource.close();
        currentEventSource = null;
    }
}
