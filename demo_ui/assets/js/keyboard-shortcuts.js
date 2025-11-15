/**
 * Keyboard Shortcuts Manager
 *
 * Enhancement #25: Keyboard Shortcuts
 * 15+ keyboard shortcuts with help dialog
 */

class KeyboardShortcutsManager {
    constructor() {
        this.shortcuts = this._defineShortcuts();
        this.isHelpVisible = false;
        this.enabled = true;
        this.activeModifiers = {
            ctrl: false,
            alt: false,
            shift: false,
            meta: false
        };

        this.init();
    }

    /**
     * Define keyboard shortcuts
     * @private
     */
    _defineShortcuts() {
        return [
            {
                id: 'help',
                keys: ['?', '/'],
                modifiers: [],
                description: 'Show keyboard shortcuts help',
                category: 'General',
                handler: () => this.toggleHelp()
            },
            {
                id: 'search',
                keys: ['s'],
                modifiers: ['ctrl'],
                description: 'Focus search input',
                category: 'Navigation',
                handler: () => this.focusSearch()
            },
            {
                id: 'newChat',
                keys: ['n'],
                modifiers: ['ctrl'],
                description: 'Start new chat',
                category: 'Chat',
                handler: () => this.newChat()
            },
            {
                id: 'clearChat',
                keys: ['k'],
                modifiers: ['ctrl'],
                description: 'Clear chat history',
                category: 'Chat',
                handler: () => this.clearChat()
            },
            {
                id: 'toggleDarkMode',
                keys: ['d'],
                modifiers: ['ctrl'],
                description: 'Toggle dark mode',
                category: 'Appearance',
                handler: () => this.toggleDarkMode()
            },
            {
                id: 'exportData',
                keys: ['e'],
                modifiers: ['ctrl'],
                description: 'Export current data',
                category: 'Actions',
                handler: () => this.exportData()
            },
            {
                id: 'settings',
                keys: [','],
                modifiers: ['ctrl'],
                description: 'Open settings',
                category: 'General',
                handler: () => this.openSettings()
            },
            {
                id: 'closeModal',
                keys: ['Escape'],
                modifiers: [],
                description: 'Close modal/dialog',
                category: 'Navigation',
                handler: () => this.closeModal()
            },
            {
                id: 'focusChat',
                keys: ['c'],
                modifiers: ['alt'],
                description: 'Focus chat panel',
                category: 'Navigation',
                handler: () => this.focusPanel('chat')
            },
            {
                id: 'focusMap',
                keys: ['m'],
                modifiers: ['alt'],
                description: 'Focus map panel',
                category: 'Navigation',
                handler: () => this.focusPanel('map')
            },
            {
                id: 'focusProjects',
                keys: ['p'],
                modifiers: ['alt'],
                description: 'Focus projects panel',
                category: 'Navigation',
                handler: () => this.focusPanel('projects')
            },
            {
                id: 'zoomIn',
                keys: ['+', '='],
                modifiers: ['ctrl'],
                description: 'Zoom in map',
                category: 'Map',
                handler: () => this.zoomMap(1)
            },
            {
                id: 'zoomOut',
                keys: ['-'],
                modifiers: ['ctrl'],
                description: 'Zoom out map',
                category: 'Map',
                handler: () => this.zoomMap(-1)
            },
            {
                id: 'undo',
                keys: ['z'],
                modifiers: ['ctrl'],
                description: 'Undo last action',
                category: 'Actions',
                handler: () => this.undo()
            },
            {
                id: 'redo',
                keys: ['y'],
                modifiers: ['ctrl'],
                description: 'Redo last action',
                category: 'Actions',
                handler: () => this.redo()
            },
            {
                id: 'searchHistory',
                keys: ['h'],
                modifiers: ['ctrl'],
                description: 'Show search history',
                category: 'Search',
                handler: () => this.showSearchHistory()
            },
            {
                id: 'nextProject',
                keys: ['ArrowRight'],
                modifiers: ['ctrl'],
                description: 'Next project',
                category: 'Navigation',
                handler: () => this.navigateProject('next')
            },
            {
                id: 'prevProject',
                keys: ['ArrowLeft'],
                modifiers: ['ctrl'],
                description: 'Previous project',
                category: 'Navigation',
                handler: () => this.navigateProject('prev')
            }
        ];
    }

    /**
     * Initialize keyboard shortcuts
     */
    init() {
        this.setupEventListeners();
        this.createHelpDialog();
        console.log(`✓ Keyboard shortcuts initialized (${this.shortcuts.length} shortcuts)`);
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        document.addEventListener('keydown', (e) => {
            if (!this.enabled) return;

            // Update modifier states
            this.activeModifiers.ctrl = e.ctrlKey || e.metaKey;
            this.activeModifiers.alt = e.altKey;
            this.activeModifiers.shift = e.shiftKey;
            this.activeModifiers.meta = e.metaKey;

            // Don't trigger shortcuts when typing in inputs (except Escape)
            if (this._isTyping(e.target) && e.key !== 'Escape') {
                return;
            }

            // Find matching shortcut
            const shortcut = this._findMatchingShortcut(e);

            if (shortcut) {
                e.preventDefault();
                shortcut.handler();

                // Visual feedback
                this._showShortcutFeedback(shortcut);
            }
        });

        // Reset modifiers on keyup
        document.addEventListener('keyup', (e) => {
            if (e.key === 'Control' || e.key === 'Meta') this.activeModifiers.ctrl = false;
            if (e.key === 'Alt') this.activeModifiers.alt = false;
            if (e.key === 'Shift') this.activeModifiers.shift = false;
        });
    }

    /**
     * Check if user is typing in an input
     * @private
     */
    _isTyping(element) {
        return element.tagName === 'INPUT' ||
               element.tagName === 'TEXTAREA' ||
               element.isContentEditable;
    }

    /**
     * Find matching shortcut
     * @private
     */
    _findMatchingShortcut(event) {
        return this.shortcuts.find(shortcut => {
            // Check if key matches
            const keyMatches = shortcut.keys.some(key =>
                key.toLowerCase() === event.key.toLowerCase()
            );

            if (!keyMatches) return false;

            // Check modifiers
            const modifiersMatch = this._checkModifiers(shortcut.modifiers, event);

            return modifiersMatch;
        });
    }

    /**
     * Check if modifiers match
     * @private
     */
    _checkModifiers(required, event) {
        const hasCtrl = event.ctrlKey || event.metaKey;
        const hasAlt = event.altKey;
        const hasShift = event.shiftKey;

        const needsCtrl = required.includes('ctrl');
        const needsAlt = required.includes('alt');
        const needsShift = required.includes('shift');

        return (hasCtrl === needsCtrl) &&
               (hasAlt === needsAlt) &&
               (hasShift === needsShift);
    }

    /**
     * Show visual feedback for shortcut
     * @private
     */
    _showShortcutFeedback(shortcut) {
        // Create temporary indicator
        const indicator = document.createElement('div');
        indicator.className = 'shortcut-feedback';
        indicator.textContent = shortcut.description;
        indicator.style.cssText = `
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.85rem;
            z-index: 10000;
            opacity: 0;
            transition: opacity 0.2s;
        `;

        document.body.appendChild(indicator);

        // Animate in
        setTimeout(() => indicator.style.opacity = '1', 10);

        // Remove after 1 second
        setTimeout(() => {
            indicator.style.opacity = '0';
            setTimeout(() => indicator.remove(), 200);
        }, 1000);
    }

    /**
     * Create help dialog
     */
    createHelpDialog() {
        const dialog = document.createElement('div');
        dialog.id = 'shortcutsHelp';
        dialog.className = 'shortcuts-modal';
        dialog.style.display = 'none';

        const categorized = this._categorizeShortcuts();

        let html = `
            <div class="shortcuts-modal-overlay"></div>
            <div class="shortcuts-modal-content">
                <div class="shortcuts-modal-header">
                    <h2>Keyboard Shortcuts</h2>
                    <button class="shortcuts-close-btn" onclick="window.keyboardShortcuts.toggleHelp()">
                        <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                        </svg>
                    </button>
                </div>
                <div class="shortcuts-modal-body">
        `;

        Object.entries(categorized).forEach(([category, shortcuts]) => {
            html += `
                <div class="shortcuts-category">
                    <h3 class="shortcuts-category-title">${category}</h3>
                    <div class="shortcuts-list">
            `;

            shortcuts.forEach(shortcut => {
                const keys = this._formatShortcutKeys(shortcut);
                html += `
                    <div class="shortcut-item">
                        <div class="shortcut-keys">${keys}</div>
                        <div class="shortcut-description">${shortcut.description}</div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;

        dialog.innerHTML = html;
        document.body.appendChild(dialog);

        // Close on overlay click
        const overlay = dialog.querySelector('.shortcuts-modal-overlay');
        overlay.addEventListener('click', () => this.toggleHelp());
    }

    /**
     * Categorize shortcuts
     * @private
     */
    _categorizeShortcuts() {
        const categorized = {};

        this.shortcuts.forEach(shortcut => {
            const category = shortcut.category || 'Other';
            if (!categorized[category]) {
                categorized[category] = [];
            }
            categorized[category].push(shortcut);
        });

        return categorized;
    }

    /**
     * Format shortcut keys for display
     * @private
     */
    _formatShortcutKeys(shortcut) {
        const parts = [];

        // Add modifiers
        if (shortcut.modifiers.includes('ctrl')) {
            parts.push('<kbd>Ctrl</kbd>');
        }
        if (shortcut.modifiers.includes('alt')) {
            parts.push('<kbd>Alt</kbd>');
        }
        if (shortcut.modifiers.includes('shift')) {
            parts.push('<kbd>Shift</kbd>');
        }

        // Add key
        const keyName = shortcut.keys[0].length === 1 ?
            shortcut.keys[0].toUpperCase() :
            shortcut.keys[0];
        parts.push(`<kbd>${keyName}</kbd>`);

        return parts.join(' + ');
    }

    /**
     * Toggle help dialog
     */
    toggleHelp() {
        const dialog = document.getElementById('shortcutsHelp');
        if (!dialog) return;

        this.isHelpVisible = !this.isHelpVisible;
        dialog.style.display = this.isHelpVisible ? 'flex' : 'none';

        if (this.isHelpVisible) {
            document.body.classList.add('no-scroll');
        } else {
            document.body.classList.remove('no-scroll');
        }
    }

    // Shortcut handlers

    focusSearch() {
        const searchInput = document.getElementById('chatInput');
        if (searchInput) {
            searchInput.focus();
        }
    }

    newChat() {
        window.dispatchEvent(new CustomEvent('newChat'));
    }

    clearChat() {
        if (confirm('Clear chat history?')) {
            window.dispatchEvent(new CustomEvent('clearChat'));
        }
    }

    toggleDarkMode() {
        if (window.darkModeManager) {
            window.darkModeManager.toggle();
        }
    }

    exportData() {
        window.dispatchEvent(new CustomEvent('exportData'));
    }

    openSettings() {
        const settingsBtn = document.getElementById('settingsBtn');
        if (settingsBtn) {
            settingsBtn.click();
        }
    }

    closeModal() {
        // Close any open modals
        const modals = document.querySelectorAll('.modal[style*="display: block"], .modal.show');
        modals.forEach(modal => {
            modal.style.display = 'none';
            modal.classList.remove('show');
        });

        // Close bottom sheet on mobile
        if (window.mobileManager) {
            window.mobileManager.closeBottomSheet();
        }

        // Close shortcuts help
        if (this.isHelpVisible) {
            this.toggleHelp();
        }
    }

    focusPanel(panelType) {
        const panels = {
            chat: 'chatInput',
            map: 'map',
            projects: 'projectPanel'
        };

        const elementId = panels[panelType];
        const element = document.getElementById(elementId);

        if (element) {
            element.focus();
            element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    zoomMap(direction) {
        window.dispatchEvent(new CustomEvent('mapZoom', {
            detail: { direction }
        }));
    }

    undo() {
        window.dispatchEvent(new CustomEvent('undo'));
    }

    redo() {
        window.dispatchEvent(new CustomEvent('redo'));
    }

    showSearchHistory() {
        window.dispatchEvent(new CustomEvent('showSearchHistory'));
    }

    navigateProject(direction) {
        window.dispatchEvent(new CustomEvent('navigateProject', {
            detail: { direction }
        }));
    }

    /**
     * Enable shortcuts
     */
    enable() {
        this.enabled = true;
    }

    /**
     * Disable shortcuts
     */
    disable() {
        this.enabled = false;
    }

    /**
     * Add custom shortcut
     */
    addShortcut(shortcut) {
        this.shortcuts.push(shortcut);
    }

    /**
     * Remove shortcut by ID
     */
    removeShortcut(id) {
        this.shortcuts = this.shortcuts.filter(s => s.id !== id);
    }
}

// Add CSS for shortcuts help
const style = document.createElement('style');
style.textContent = `
.shortcuts-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 10000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.shortcuts-modal-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.5);
}

.shortcuts-modal-content {
    position: relative;
    background: white;
    border-radius: 12px;
    max-width: 700px;
    max-height: 80vh;
    width: 90%;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}

.dark-mode .shortcuts-modal-content {
    background: var(--bg-secondary);
}

.shortcuts-modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.5rem;
    border-bottom: 1px solid #e0e0e0;
}

.dark-mode .shortcuts-modal-header {
    border-bottom-color: var(--border-color);
}

.shortcuts-modal-header h2 {
    margin: 0;
    font-size: 1.5rem;
}

.shortcuts-close-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 6px;
    transition: background 0.2s;
}

.shortcuts-close-btn:hover {
    background: #f0f0f0;
}

.dark-mode .shortcuts-close-btn:hover {
    background: var(--bg-hover);
}

.shortcuts-modal-body {
    padding: 1.5rem;
    overflow-y: auto;
}

.shortcuts-category {
    margin-bottom: 2rem;
}

.shortcuts-category:last-child {
    margin-bottom: 0;
}

.shortcuts-category-title {
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #6c757d;
    margin-bottom: 1rem;
}

.shortcuts-list {
    display: grid;
    gap: 0.75rem;
}

.shortcut-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 0;
}

.shortcut-keys {
    display: flex;
    gap: 0.5rem;
    flex-shrink: 0;
    min-width: 180px;
}

.shortcut-keys kbd {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    padding: 0.25rem 0.5rem;
    font-family: 'Courier New', monospace;
    font-size: 0.85rem;
    font-weight: 600;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.dark-mode .shortcut-keys kbd {
    background: var(--bg-tertiary);
    border-color: var(--border-color);
    color: var(--text-primary);
}

.shortcut-description {
    color: #495057;
    font-size: 0.95rem;
}

.dark-mode .shortcut-description {
    color: var(--text-secondary);
}

@media (max-width: 768px) {
    .shortcuts-modal-content {
        width: 95%;
        max-height: 90vh;
    }

    .shortcut-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
    }

    .shortcut-keys {
        min-width: auto;
    }
}
`;
document.head.appendChild(style);

// Create global instance
const keyboardShortcuts = new KeyboardShortcutsManager();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KeyboardShortcutsManager;
}
