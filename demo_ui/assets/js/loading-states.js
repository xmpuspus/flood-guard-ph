/**
 * Loading State Manager
 *
 * Enhancement #12: Loading States across UI
 * Manages spinners, skeleton loaders, progress bars, and toast notifications
 */

class LoadingStateManager {
    constructor() {
        this.activeLoaders = new Set();
        this.toastQueue = [];
        this.isShowingToast = false;
    }

    /**
     * Show loading indicator in a container
     * @param {string} containerId - ID of container element
     * @param {string} type - Type of loader: 'spinner', 'skeleton', 'progress', 'dots'
     * @param {string} message - Optional loading message
     */
    showLoading(containerId, type = 'spinner', message = 'Loading...') {
        this.activeLoaders.add(containerId);
        const container = document.getElementById(containerId);

        if (!container) {
            console.warn(`Container ${containerId} not found`);
            return;
        }

        // Store original content
        if (!container.dataset.originalContent) {
            container.dataset.originalContent = container.innerHTML;
        }

        let loadingHTML = '';

        switch (type) {
            case 'spinner':
                loadingHTML = `
                    <div class="loading-overlay">
                        <div class="loading-overlay-content">
                            <div class="spinner spinner-dark spinner-large"></div>
                            ${message ? `<div class="loading-overlay-text">${message}</div>` : ''}
                        </div>
                    </div>
                `;
                break;

            case 'skeleton':
                loadingHTML = this.getSkeletonHTML();
                break;

            case 'progress':
                loadingHTML = `
                    <div class="loading-overlay">
                        <div class="loading-overlay-content">
                            <div class="progress-bar">
                                <div class="progress-bar-fill indeterminate"></div>
                            </div>
                            ${message ? `<div class="loading-overlay-text">${message}</div>` : ''}
                        </div>
                    </div>
                `;
                break;

            case 'dots':
                loadingHTML = `
                    <div class="loading-overlay">
                        <div class="loading-overlay-content">
                            <div class="loading-dots">
                                <div class="loading-dot"></div>
                                <div class="loading-dot"></div>
                                <div class="loading-dot"></div>
                            </div>
                            ${message ? `<div class="loading-overlay-text">${message}</div>` : ''}
                        </div>
                    </div>
                `;
                break;

            default:
                console.warn(`Unknown loading type: ${type}`);
                return;
        }

        // Add loading HTML
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading-state-wrapper';
        loadingDiv.innerHTML = loadingHTML;
        container.style.position = 'relative';
        container.appendChild(loadingDiv);
    }

    /**
     * Hide loading indicator
     * @param {string} containerId - ID of container element
     * @param {boolean} restore - Whether to restore original content
     */
    hideLoading(containerId, restore = false) {
        this.activeLoaders.delete(containerId);
        const container = document.getElementById(containerId);

        if (!container) {
            return;
        }

        const overlay = container.querySelector('.loading-overlay');
        const wrapper = container.querySelector('.loading-state-wrapper');

        if (overlay) {
            overlay.classList.add('hidden');
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.remove();
                }
            }, 300);
        }

        if (wrapper) {
            setTimeout(() => {
                if (wrapper.parentNode) {
                    wrapper.remove();
                }
            }, 300);
        }

        // Restore original content if requested
        if (restore && container.dataset.originalContent) {
            setTimeout(() => {
                container.innerHTML = container.dataset.originalContent;
                delete container.dataset.originalContent;
            }, 300);
        }
    }

    /**
     * Get skeleton loader HTML
     * @param {number} count - Number of skeleton cards
     */
    getSkeletonHTML(count = 3) {
        let html = '<div class="skeleton-list">';

        for (let i = 0; i < count; i++) {
            html += `
                <div class="skeleton-card shimmer">
                    <div class="skeleton skeleton-title"></div>
                    <div class="skeleton skeleton-paragraph"></div>
                    <div class="skeleton skeleton-paragraph"></div>
                    <div class="skeleton skeleton-paragraph" style="width: 60%;"></div>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    /**
     * Show button loading state
     * @param {string|HTMLElement} button - Button element or ID
     */
    showButtonLoading(button) {
        const btn = typeof button === 'string' ? document.getElementById(button) : button;
        if (!btn) return;

        btn.disabled = true;
        btn.classList.add('btn-loading');
        btn.dataset.originalText = btn.textContent;
    }

    /**
     * Hide button loading state
     * @param {string|HTMLElement} button - Button element or ID
     */
    hideButtonLoading(button) {
        const btn = typeof button === 'string' ? document.getElementById(button) : button;
        if (!btn) return;

        btn.disabled = false;
        btn.classList.remove('btn-loading');

        if (btn.dataset.originalText) {
            btn.textContent = btn.dataset.originalText;
            delete btn.dataset.originalText;
        }
    }

    /**
     * Show toast notification
     * @param {string} message - Message to display
     * @param {string} type - Type: 'success', 'error', 'warning', 'info'
     * @param {number} duration - Duration in milliseconds (default 3000)
     */
    showToast(message, type = 'info', duration = 3000) {
        this.toastQueue.push({ message, type, duration });

        if (!this.isShowingToast) {
            this._processToastQueue();
        }
    }

    /**
     * Process toast queue
     * @private
     */
    _processToastQueue() {
        if (this.toastQueue.length === 0) {
            this.isShowingToast = false;
            return;
        }

        this.isShowingToast = true;
        const { message, type, duration } = this.toastQueue.shift();

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;

        document.body.appendChild(toast);

        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);

        // Remove toast after duration
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
                this._processToastQueue();
            }, 300);
        }, duration);
    }

    /**
     * Update progress bar
     * @param {string} containerId - Container ID
     * @param {number} percentage - Progress percentage (0-100)
     */
    updateProgress(containerId, percentage) {
        const container = document.getElementById(containerId);
        if (!container) return;

        let progressBar = container.querySelector('.progress-bar-fill');

        if (!progressBar) {
            // Create progress bar if it doesn't exist
            container.innerHTML = `
                <div class="progress-bar">
                    <div class="progress-bar-fill progress-bar-determinate"></div>
                </div>
                <div class="progress-percentage">0%</div>
            `;
            progressBar = container.querySelector('.progress-bar-fill');
        }

        const progressText = container.querySelector('.progress-percentage');

        // Update progress
        progressBar.style.width = `${percentage}%`;
        progressBar.classList.remove('indeterminate');
        progressBar.classList.add('progress-bar-determinate');

        if (progressText) {
            progressText.textContent = `${Math.round(percentage)}%`;
        }
    }

    /**
     * Show loading dots in chat
     */
    showChatLoading() {
        const chatContainer = document.getElementById('chatMessages');
        if (!chatContainer) return;

        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'chat-message chat-message-loading';
        loadingDiv.id = 'chatLoadingIndicator';
        loadingDiv.innerHTML = `
            <div class="loading-dots">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
        `;

        chatContainer.appendChild(loadingDiv);
        loadingDiv.scrollIntoView({ behavior: 'smooth' });
    }

    /**
     * Hide chat loading indicator
     */
    hideChatLoading() {
        const loadingIndicator = document.getElementById('chatLoadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
    }

    /**
     * Show map loading
     */
    showMapLoading() {
        const mapContainer = document.getElementById('map');
        if (!mapContainer) return;

        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'map-loading';
        loadingDiv.id = 'mapLoadingIndicator';
        loadingDiv.innerHTML = `
            <div class="spinner spinner-dark spinner-large"></div>
            <div style="margin-top: 1rem; color: #6c757d;">Loading map...</div>
        `;

        mapContainer.appendChild(loadingDiv);
    }

    /**
     * Hide map loading
     */
    hideMapLoading() {
        const loadingIndicator = document.getElementById('mapLoadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
    }

    /**
     * Check if a container is loading
     * @param {string} containerId - Container ID
     * @returns {boolean}
     */
    isLoading(containerId) {
        return this.activeLoaders.has(containerId);
    }

    /**
     * Clear all loading states
     */
    clearAll() {
        const loaders = Array.from(this.activeLoaders);
        loaders.forEach(containerId => this.hideLoading(containerId));
        this.activeLoaders.clear();
    }
}

// Create global instance
const loadingManager = new LoadingStateManager();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoadingStateManager;
}
