/**
 * ResultCard.js - Renders a single analysis result as an expandable card.
 * 
 * WHAT THIS DOES:
 * Takes the structured analysis data from our LLM and turns it into
 * a beautiful, expandable card. Each card shows:
 *   - Title & core idea (always visible)
 *   - Full analysis details (shown when you click to expand)
 * 
 * WHY A SEPARATE COMPONENT?
 * Separation of concerns: this file only knows how to render a card.
 * The api.js file only knows how to fetch data. They don't depend on
 * each other's internals — this makes the code easier to maintain.
 */


/**
 * Creates the HTML for a single result card.
 * 
 * @param {Object} data - The analysis data from the LLM
 * @param {number} index - The card number (1, 2, 3, etc.)
 * @returns {HTMLElement} The card DOM element
 */
function createResultCard(data, index) {
    const card = document.createElement('div');
    card.className = 'result-card';
    card.id = `result-card-${index}`;

    // Ensure data exists and has fallback values
    const title = data.title || data.source_title || 'Untitled Article';
    const coreIdea = data.core_idea || 'No summary provided.';
    const sourceUrl = data.url || data.source_url || '';

    // Build the card HTML
    card.innerHTML = `
        <div class="result-card__header" onclick="toggleCard(${index})" role="button" tabindex="0" aria-expanded="false">
            <div class="result-card__index">${String(index).padStart(2, '0')}</div>
            <div class="result-card__info">
                <h2 class="result-card__title">${escapeHtml(title)}</h2>
                <p class="result-card__core-idea">${escapeHtml(coreIdea)}</p>
                ${data.analysis_type === 'snippet' ? '<span class="badge badge--snippet">Snippet Only</span>' : ''}
            </div>
            <div class="result-card__toggle">▼</div>
        </div>

        <div class="result-card__body" id="card-body-${index}">
            <div class="result-card__content">
                ${renderHookBreakdown(data.hook_breakdown)}
                ${renderSection('📐', 'Content Structure', data.content_structure)}
                ${renderSection('✍️', 'Writing Style', data.writing_style)}
                ${renderWhyItWorks(data.why_it_works)}
                ${renderInsights(data.reusable_insights)}
                ${renderSuggestion(data.suggested_content_idea)}
                ${renderSourceLink(sourceUrl)}
            </div>
        </div>
    `;

    return card;
}



/**
 * Toggle a card's expanded/collapsed state.
 * Called when the user clicks on a card header.
 */
function toggleCard(index) {
    const card = document.getElementById(`result-card-${index}`);
    if (!card) return;

    const isExpanded = card.classList.toggle('expanded');
    
    // Update accessibility attribute
    const header = card.querySelector('.result-card__header');
    if (header) {
        header.setAttribute('aria-expanded', isExpanded.toString());
    }
}


// ── Section Renderers ──────────────────────────────────────────

/**
 * Renders the Hook Breakdown section.
 * Shows what type of hook the content uses and why it's effective.
 */
function renderHookBreakdown(hook) {
    if (!hook) return '';
    return `
        <div class="analysis-section">
            <div class="analysis-section__label">
                <span class="analysis-section__label-icon">🪝</span>
                Hook Breakdown
            </div>
            <div class="hook-card">
                ${hook.hook_type ? `<div class="hook-card__type">🎯 ${escapeHtml(hook.hook_type)}</div>` : ''}
                ${hook.hook_text ? `<div class="hook-card__text">"${escapeHtml(hook.hook_text)}"</div>` : ''}
                ${hook.why_it_works ? `<div class="hook-card__why">${escapeHtml(hook.why_it_works)}</div>` : ''}
            </div>
        </div>
    `;
}


/**
 * Renders a generic text section (Structure, Style, etc.)
 */
function renderSection(icon, label, text) {
    if (!text) return '';
    return `
        <div class="analysis-section">
            <div class="analysis-section__label">
                <span class="analysis-section__label-icon">${icon}</span>
                ${label}
            </div>
            <p class="analysis-section__text">${escapeHtml(text)}</p>
        </div>
    `;
}


/**
 * Renders the "Why It Works" dual-column section.
 * Shows psychological and structural reasons side by side.
 */
function renderWhyItWorks(why) {
    if (!why) return '';

    const psychReasons = why.psychological_reasons || [];
    const structReasons = why.structural_reasons || [];

    if (psychReasons.length === 0 && structReasons.length === 0) return '';

    return `
        <div class="analysis-section">
            <div class="analysis-section__label">
                <span class="analysis-section__label-icon">🧠</span>
                Why It Works
            </div>
            <div class="why-grid">
                <div class="why-column">
                    <div class="why-column__title why-column__title--psych">🧬 Psychological</div>
                    <ul class="why-column__list">
                        ${psychReasons.map(r => `<li class="why-column__item">${escapeHtml(r)}</li>`).join('')}
                    </ul>
                </div>
                <div class="why-column">
                    <div class="why-column__title why-column__title--struct">🏗️ Structural</div>
                    <ul class="why-column__list">
                        ${structReasons.map(r => `<li class="why-column__item">${escapeHtml(r)}</li>`).join('')}
                    </ul>
                </div>
            </div>
        </div>
    `;
}


/**
 * Renders the Reusable Insights list.
 * Each insight is an actionable takeaway you can apply to your own content.
 */
function renderInsights(insights) {
    if (!insights || insights.length === 0) return '';
    return `
        <div class="analysis-section">
            <div class="analysis-section__label">
                <span class="analysis-section__label-icon">💡</span>
                Reusable Insights
            </div>
            <div class="insights-list">
                ${insights.map(insight => `
                    <div class="insight-item">
                        <span class="insight-item__bullet">✦</span>
                        <span>${escapeHtml(insight)}</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}


/**
 * Renders the Suggested Content Idea card.
 * A creative AI-generated content idea inspired by the analyzed piece.
 */
function renderSuggestion(suggestion) {
    if (!suggestion) return '';
    return `
        <div class="analysis-section">
            <div class="analysis-section__label">
                <span class="analysis-section__label-icon">💫</span>
                Suggested Content Idea
            </div>
            <div class="suggestion-card">
                <div class="suggestion-card__icon">💡</div>
                <p class="suggestion-card__text">${escapeHtml(suggestion)}</p>
            </div>
        </div>
    `;
}


/**
 * Renders a link back to the original article.
 */
function renderSourceLink(url) {
    if (!url) return '';
    // Show a truncated version of the URL for display
    let displayUrl = url;
    try {
        const parsed = new URL(url);
        displayUrl = parsed.hostname + (parsed.pathname.length > 30 ? parsed.pathname.substring(0, 30) + '...' : parsed.pathname);
    } catch { /* ignore parse errors */ }
    
    return `
        <a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="source-link">
            🔗 ${escapeHtml(displayUrl)}
        </a>
    `;
}


// ── Utility Functions ──────────────────────────────────────────

/**
 * Escapes HTML special characters to prevent XSS attacks.
 * 
 * WHY THIS IS IMPORTANT:
 * If the article title contains HTML like <script>alert('hacked')</script>,
 * without escaping, it would actually execute as JavaScript. Escaping
 * converts < to &lt; etc., making it safe to display.
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}
