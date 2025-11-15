/**
 * Error Feedback Manager
 *
 * Enhancement #13: Error Feedback UI
 * Manages user-friendly error messages with action buttons
 */

class ErrorFeedbackManager {
    constructor() {
        this.connectionStatus = 'online';
        this.retryCallbacks = new Map();
        this.setupConnectionMonitoring();
    }

    /**
     * Show error message
     * @param {Object} options - Error options
     */
    showError(options) {
        const {
            containerId = 'errorContainer',
            title = 'An error occurred',
            message = 'Something went wrong. Please try again.',
            code = null,
            details = null,
            type = 'error', // error, warning, info
            actions = [],
            dismissible = true
        } = options;

        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        const errorId = `error-${Date.now()}`;
        const errorHTML = this._buildErrorHTML({
            errorId,
            title,
            message,
            code,
            details,
            type,
            actions,
            dismissible
        });

        container.innerHTML = errorHTML;
        container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        // Setup event listeners
        this._setupErrorListeners(errorId, actions);

        // Add shake animation
        const errorContainer = container.querySelector('.error-container');
        if (errorContainer) {
            errorContainer.classList.add('error-shake');
            setTimeout(() => errorContainer.classList.remove('error-shake'), 500);
        }
    }

    /**
     * Build error HTML
     * @private
     */
    _buildErrorHTML(options) {
        const {
            errorId,
            title,
            message,
            code,
            details,
            type,
            actions,
            dismissible
        } = options;

        const iconSVG = this._getErrorIcon(type);
        const typeClass = type === 'error' ? 'error' : type === 'warning' ? 'warning' : 'info';

        let html = `
            <div class="error-container ${typeClass}" id="${errorId}">
                <div class="error-header">
                    <div class="error-icon ${type}">
                        ${iconSVG}
                    </div>
                    <h3 class="error-title">
                        ${this._escapeHTML(title)}
                        ${code ? `<span class="error-code-badge">${this._escapeHTML(code)}</span>` : ''}
                    </h3>
                </div>
                <div class="error-message">${this._escapeHTML(message)}</div>
        `;

        // Add details toggle if details exist
        if (details) {
            html += `
                <div class="error-details-toggle" data-error-id="${errorId}">
                    Show technical details
                </div>
                <div class="error-details" id="${errorId}-details" style="display: none;">
                    ${this._escapeHTML(details)}
                </div>
            `;
        }

        // Add action buttons
        if (actions && actions.length > 0) {
            html += '<div class="error-actions">';
            actions.forEach((action, index) => {
                const btnClass = action.style || 'primary';
                html += `
                    <button class="error-action-btn ${btnClass}" data-action="${index}">
                        ${action.icon || ''}
                        ${this._escapeHTML(action.label)}
                    </button>
                `;
            });
            html += '</div>';
        }

        // Add dismiss button if dismissible
        if (dismissible && actions.length === 0) {
            html += `
                <div class="error-actions">
                    <button class="error-action-btn secondary" data-dismiss="true">
                        Dismiss
                    </button>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    /**
     * Setup error listeners
     * @private
     */
    _setupErrorListeners(errorId, actions) {
        const errorContainer = document.getElementById(errorId);
        if (!errorContainer) return;

        // Details toggle
        const detailsToggle = errorContainer.querySelector('.error-details-toggle');
        if (detailsToggle) {
            detailsToggle.addEventListener('click', () => {
                const details = document.getElementById(`${errorId}-details`);
                if (details) {
                    const isVisible = details.style.display !== 'none';
                    details.style.display = isVisible ? 'none' : 'block';
                    detailsToggle.classList.toggle('expanded', !isVisible);
                    detailsToggle.textContent = isVisible ? 'Show technical details' : 'Hide technical details';
                }
            });
        }

        // Action buttons
        const actionButtons = errorContainer.querySelectorAll('[data-action]');
        actionButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const actionIndex = parseInt(btn.dataset.action);
                if (actions[actionIndex] && actions[actionIndex].callback) {
                    actions[actionIndex].callback();
                }
            });
        });

        // Dismiss button
        const dismissBtn = errorContainer.querySelector('[data-dismiss]');
        if (dismissBtn) {
            dismissBtn.addEventListener('click', () => {
                this.clearError(errorContainer.parentElement.id);
            });
        }
    }

    /**
     * Clear error from container
     */
    clearError(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '';
        }
    }

    /**
     * Show inline error (for forms)
     */
    showInlineError(inputId, message) {
        const input = document.getElementById(inputId);
        if (!input) return;

        // Add error class to input
        input.classList.add('error');

        // Remove existing error message
        const existingError = input.parentElement.querySelector('.inline-error');
        if (existingError) {
            existingError.remove();
        }

        // Add error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'inline-error';
        errorDiv.innerHTML = `
            <svg class="inline-error-icon" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            <span>${this._escapeHTML(message)}</span>
        `;

        input.parentElement.appendChild(errorDiv);

        // Clear error on input
        input.addEventListener('input', () => {
            this.clearInlineError(inputId);
        }, { once: true });
    }

    /**
     * Clear inline error
     */
    clearInlineError(inputId) {
        const input = document.getElementById(inputId);
        if (!input) return;

        input.classList.remove('error');
        const errorDiv = input.parentElement.querySelector('.inline-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    /**
     * Show empty state
     */
    showEmptyState(containerId, options = {}) {
        const {
            title = 'No results found',
            message = 'Try adjusting your search or filters.',
            actionLabel = 'Clear filters',
            actionCallback = null
        } = options;

        const container = document.getElementById(containerId);
        if (!container) return;

        let html = `
            <div class="empty-state">
                <svg class="empty-state-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <div class="empty-state-title">${this._escapeHTML(title)}</div>
                <div class="empty-state-message">${this._escapeHTML(message)}</div>
        `;

        if (actionCallback) {
            html += `
                <div class="empty-state-action">
                    <button class="error-action-btn primary" id="emptyStateAction">
                        ${this._escapeHTML(actionLabel)}
                    </button>
                </div>
            `;
        }

        html += '</div>';
        container.innerHTML = html;

        if (actionCallback) {
            const btn = document.getElementById('emptyStateAction');
            if (btn) {
                btn.addEventListener('click', actionCallback);
            }
        }
    }

    /**
     * Show rate limit error with countdown
     */
    showRateLimitError(containerId, waitSeconds, retryCallback) {
        const errorId = `rate-limit-${Date.now()}`;

        this.showError({
            containerId,
            title: 'Rate Limit Exceeded',
            message: 'You\'ve made too many requests. Please wait before trying again.',
            type: 'error',
            actions: [],
            dismissible: false
        });

        // Add countdown timer
        const container = document.getElementById(containerId);
        const errorContainer = container.querySelector('.error-container');
        if (errorContainer) {
            errorContainer.classList.add('rate-limit-error');

            const timerDiv = document.createElement('div');
            timerDiv.className = 'countdown-timer';
            timerDiv.innerHTML = `
                <svg class="countdown-timer-icon" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"/>
                </svg>
                <span id="countdownText">Please wait ${waitSeconds}s</span>
            `;
            errorContainer.appendChild(timerDiv);

            // Countdown
            let remaining = waitSeconds;
            const countdownInterval = setInterval(() => {
                remaining--;
                const countdownText = document.getElementById('countdownText');
                if (countdownText) {
                    countdownText.textContent = `Please wait ${remaining}s`;
                }

                if (remaining <= 0) {
                    clearInterval(countdownInterval);
                    this.clearError(containerId);
                    if (retryCallback) {
                        retryCallback();
                    }
                }
            }, 1000);
        }
    }

    /**
     * Show connection status
     */
    updateConnectionStatus(isOnline) {
        this.connectionStatus = isOnline ? 'online' : 'offline';

        let statusDiv = document.getElementById('connectionStatus');

        if (!isOnline) {
            if (!statusDiv) {
                statusDiv = document.createElement('div');
                statusDiv.id = 'connectionStatus';
                statusDiv.className = 'connection-status';
                document.body.appendChild(statusDiv);
            }

            statusDiv.innerHTML = `
                <div class="connection-status-indicator disconnected"></div>
                <div class="connection-status-text">Connection lost. Trying to reconnect...</div>
            `;

            setTimeout(() => statusDiv.classList.add('show'), 10);
        } else {
            if (statusDiv) {
                statusDiv.classList.remove('show');
                setTimeout(() => {
                    if (statusDiv.parentNode) {
                        statusDiv.remove();
                    }
                }, 300);
            }
        }
    }

    /**
     * Setup connection monitoring
     * @private
     */
    setupConnectionMonitoring() {
        window.addEventListener('online', () => {
            this.updateConnectionStatus(true);
        });

        window.addEventListener('offline', () => {
            this.updateConnectionStatus(false);
        });
    }

    /**
     * Get error icon SVG
     * @private
     */
    _getErrorIcon(type) {
        const icons = {
            error: `<svg fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>`,
            warning: `<svg fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>`,
            info: `<svg fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>`
        };
        return icons[type] || icons.error;
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
}

// Create global instance
const errorManager = new ErrorFeedbackManager();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorFeedbackManager;
}
