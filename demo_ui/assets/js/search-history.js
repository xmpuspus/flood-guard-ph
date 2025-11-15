/**
 * Search History Manager
 *
 * Enhancement #11: Search History UI
 * Dropdown with timestamps, recent searches, and filtering
 */

class SearchHistory {
    constructor(maxItems = 50) {
        this.storageKey = 'floodguard-search-history';
        this.maxItems = maxItems;
        this.history = this._loadHistory();
        this.onHistoryClick = null; // Callback for when history item is clicked
    }

    /**
     * Load history from localStorage
     * @private
     */
    _loadHistory() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                const history = JSON.parse(stored);
                // Filter out old entries (> 30 days)
                const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000);
                return history.filter(item => item.timestamp > thirtyDaysAgo);
            }
        } catch (e) {
            console.error('Failed to load search history:', e);
        }
        return [];
    }

    /**
     * Save history to localStorage
     * @private
     */
    _saveHistory() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.history));
        } catch (e) {
            console.error('Failed to save search history:', e);
        }
    }

    /**
     * Add a query to history
     * @param {string} query - Search query
     * @param {Object} filters - Optional filters applied
     * @param {number} resultCount - Number of results returned
     */
    addQuery(query, filters = {}, resultCount = 0) {
        if (!query || query.trim().length === 0) {
            return;
        }

        // Check if query already exists
        const existingIndex = this.history.findIndex(item =>
            item.query.toLowerCase() === query.toLowerCase()
        );

        const historyItem = {
            query: query.trim(),
            filters: filters,
            resultCount: resultCount,
            timestamp: Date.now(),
            id: `search-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        };

        if (existingIndex !== -1) {
            // Update existing entry (move to top)
            this.history.splice(existingIndex, 1);
        }

        // Add to beginning
        this.history.unshift(historyItem);

        // Limit to maxItems
        if (this.history.length > this.maxItems) {
            this.history = this.history.slice(0, this.maxItems);
        }

        this._saveHistory();
    }

    /**
     * Get recent searches
     * @param {number} count - Number of items to return
     * @returns {Array}
     */
    getRecent(count = 10) {
        return this.history.slice(0, count);
    }

    /**
     * Search history by query string
     * @param {string} searchTerm - Term to search for
     * @param {number} limit - Max results
     * @returns {Array}
     */
    search(searchTerm, limit = 10) {
        if (!searchTerm) {
            return this.getRecent(limit);
        }

        const term = searchTerm.toLowerCase();
        return this.history
            .filter(item => item.query.toLowerCase().includes(term))
            .slice(0, limit);
    }

    /**
     * Delete a specific history item
     * @param {string} id - History item ID
     */
    deleteItem(id) {
        this.history = this.history.filter(item => item.id !== id);
        this._saveHistory();
    }

    /**
     * Clear all history
     */
    clearAll() {
        this.history = [];
        this._saveHistory();
    }

    /**
     * Get history grouped by date
     * @returns {Object} History grouped by 'today', 'yesterday', 'this_week', 'older'
     */
    getGrouped() {
        const now = Date.now();
        const oneDayMs = 24 * 60 * 60 * 1000;
        const oneWeekMs = 7 * oneDayMs;

        const groups = {
            today: [],
            yesterday: [],
            this_week: [],
            older: []
        };

        this.history.forEach(item => {
            const age = now - item.timestamp;

            if (age < oneDayMs) {
                groups.today.push(item);
            } else if (age < 2 * oneDayMs) {
                groups.yesterday.push(item);
            } else if (age < oneWeekMs) {
                groups.this_week.push(item);
            } else {
                groups.older.push(item);
            }
        });

        return groups;
    }

    /**
     * Render history dropdown
     * @param {string} containerId - Container element ID
     * @param {string} filterTerm - Optional filter term
     */
    renderDropdown(containerId, filterTerm = '') {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        const items = filterTerm ? this.search(filterTerm, 10) : this.getRecent(10);

        if (items.length === 0) {
            container.innerHTML = `
                <div class="search-history-empty">
                    <svg width="48" height="48" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 000 2h4a1 1 0 100-2H8zm0 6a1 1 0 100-2h4a1 1 0 100 2H8z" clip-rule="evenodd"/>
                    </svg>
                    <p>No search history</p>
                </div>
            `;
            return;
        }

        let html = '<div class="search-history-dropdown">';

        // Header
        html += `
            <div class="search-history-header">
                <span class="search-history-title">Recent Searches</span>
                <button class="search-history-clear" id="clearHistoryBtn">
                    Clear All
                </button>
            </div>
        `;

        // Items
        html += '<div class="search-history-list">';
        items.forEach(item => {
            const timeAgo = this._formatTimeAgo(item.timestamp);
            const resultText = item.resultCount > 0 ? `${item.resultCount} results` : 'No results';

            html += `
                <div class="search-history-item" data-id="${item.id}">
                    <div class="search-history-item-icon">
                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"/>
                        </svg>
                    </div>
                    <div class="search-history-item-content">
                        <div class="search-history-item-query">${this._escapeHTML(item.query)}</div>
                        <div class="search-history-item-meta">
                            <span class="search-history-item-time">${timeAgo}</span>
                            <span class="search-history-item-separator">•</span>
                            <span class="search-history-item-results">${resultText}</span>
                        </div>
                    </div>
                    <button class="search-history-item-delete" data-id="${item.id}" title="Remove">
                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                        </svg>
                    </button>
                </div>
            `;
        });
        html += '</div>';

        html += '</div>';
        container.innerHTML = html;

        // Setup event listeners
        this._setupDropdownListeners(container);
    }

    /**
     * Setup event listeners for dropdown
     * @private
     */
    _setupDropdownListeners(container) {
        // Clear all button
        const clearBtn = container.querySelector('#clearHistoryBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (confirm('Clear all search history?')) {
                    this.clearAll();
                    this.renderDropdown(container.id);
                }
            });
        }

        // History item clicks
        const historyItems = container.querySelectorAll('.search-history-item');
        historyItems.forEach(item => {
            item.addEventListener('click', (e) => {
                // Don't trigger if clicking delete button
                if (e.target.closest('.search-history-item-delete')) {
                    return;
                }

                const id = item.dataset.id;
                const historyItem = this.history.find(h => h.id === id);

                if (historyItem && this.onHistoryClick) {
                    this.onHistoryClick(historyItem);
                }
            });
        });

        // Delete buttons
        const deleteButtons = container.querySelectorAll('.search-history-item-delete');
        deleteButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = btn.dataset.id;
                this.deleteItem(id);
                this.renderDropdown(container.id);
            });
        });
    }

    /**
     * Format timestamp as "time ago"
     * @private
     */
    _formatTimeAgo(timestamp) {
        const now = Date.now();
        const diffMs = now - timestamp;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;

        // Format as date
        const date = new Date(timestamp);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    /**
     * Escape HTML to prevent XSS
     * @private
     */
    _escapeHTML(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Export history as JSON
     * @returns {string}
     */
    exportHistory() {
        return JSON.stringify(this.history, null, 2);
    }

    /**
     * Import history from JSON
     * @param {string} jsonString - JSON string
     */
    importHistory(jsonString) {
        try {
            const imported = JSON.parse(jsonString);
            if (Array.isArray(imported)) {
                this.history = imported;
                this._saveHistory();
                return true;
            }
        } catch (e) {
            console.error('Failed to import history:', e);
        }
        return false;
    }

    /**
     * Get statistics
     * @returns {Object}
     */
    getStats() {
        const totalSearches = this.history.length;
        const avgResults = this.history.reduce((sum, item) => sum + item.resultCount, 0) / totalSearches || 0;

        // Most common search terms
        const terms = {};
        this.history.forEach(item => {
            const words = item.query.toLowerCase().split(/\s+/);
            words.forEach(word => {
                if (word.length > 3) {
                    terms[word] = (terms[word] || 0) + 1;
                }
            });
        });

        const topTerms = Object.entries(terms)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([term, count]) => ({ term, count }));

        return {
            totalSearches,
            avgResults: Math.round(avgResults),
            topTerms,
            oldestSearch: this.history.length > 0 ? this.history[this.history.length - 1].timestamp : null,
            newestSearch: this.history.length > 0 ? this.history[0].timestamp : null
        };
    }
}

// Create global instance
const searchHistory = new SearchHistory();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SearchHistory;
}
