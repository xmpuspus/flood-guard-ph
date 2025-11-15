/**
 * Dark Mode Manager
 *
 * Enhancement #24: Dark Mode
 * Manages dark/light theme with system preference detection
 */

class DarkModeManager {
    constructor() {
        this.storageKey = 'floodguard-theme';
        this.currentTheme = this._getInitialTheme();
        this.systemPreference = window.matchMedia('(prefers-color-scheme: dark)');

        this.init();
    }

    /**
     * Initialize dark mode
     */
    init() {
        // Apply initial theme
        this.applyTheme(this.currentTheme, false);

        // Create toggle button
        this.createToggleButton();

        // Listen for system preference changes
        this.setupSystemPreferenceListener();

        // Add transition class after initial load
        setTimeout(() => {
            document.documentElement.classList.add('dark-mode-transition');
        }, 100);
    }

    /**
     * Get initial theme preference
     * Priority: localStorage > system preference > light
     * @private
     */
    _getInitialTheme() {
        // Check localStorage first
        const savedTheme = localStorage.getItem(this.storageKey);
        if (savedTheme) {
            return savedTheme;
        }

        // Check system preference
        if (this.systemPreference && this.systemPreference.matches) {
            return 'dark';
        }

        // Default to light
        return 'light';
    }

    /**
     * Apply theme
     * @param {string} theme - 'light' or 'dark'
     * @param {boolean} animate - Whether to animate transition
     */
    applyTheme(theme, animate = true) {
        const root = document.documentElement;

        if (!animate) {
            root.classList.remove('dark-mode-transition');
        }

        if (theme === 'dark') {
            root.classList.add('dark-mode');
        } else {
            root.classList.remove('dark-mode');
        }

        if (!animate) {
            // Re-add transition class after theme is applied
            setTimeout(() => {
                root.classList.add('dark-mode-transition');
            }, 50);
        }

        this.currentTheme = theme;
        localStorage.setItem(this.storageKey, theme);

        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme }
        }));

        // Update meta theme-color for mobile browsers
        this._updateMetaThemeColor(theme);
    }

    /**
     * Toggle between dark and light mode
     */
    toggle() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
    }

    /**
     * Get current theme
     * @returns {string} 'light' or 'dark'
     */
    getTheme() {
        return this.currentTheme;
    }

    /**
     * Check if dark mode is active
     * @returns {boolean}
     */
    isDarkMode() {
        return this.currentTheme === 'dark';
    }

    /**
     * Create toggle button
     */
    createToggleButton() {
        // Check if button already exists
        if (document.getElementById('themeToggle')) {
            return;
        }

        const button = document.createElement('button');
        button.id = 'themeToggle';
        button.className = 'theme-toggle';
        button.setAttribute('aria-label', 'Toggle dark mode');
        button.innerHTML = `
            <svg class="icon-sun" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clip-rule="evenodd"/>
            </svg>
            <svg class="icon-moon" fill="currentColor" viewBox="0 0 20 20">
                <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"/>
            </svg>
        `;

        button.addEventListener('click', () => {
            this.toggle();
            this._animateToggleButton(button);
        });

        document.body.appendChild(button);
    }

    /**
     * Animate toggle button on click
     * @private
     */
    _animateToggleButton(button) {
        button.style.transform = 'rotate(360deg) scale(1.2)';
        setTimeout(() => {
            button.style.transform = '';
        }, 300);
    }

    /**
     * Setup listener for system preference changes
     * @private
     */
    setupSystemPreferenceListener() {
        if (!this.systemPreference) {
            return;
        }

        this.systemPreference.addEventListener('change', (e) => {
            // Only apply if user hasn't manually set preference
            const userPreference = localStorage.getItem(this.storageKey);
            if (!userPreference) {
                const newTheme = e.matches ? 'dark' : 'light';
                this.applyTheme(newTheme);
            }
        });
    }

    /**
     * Update meta theme-color for mobile browsers
     * @private
     */
    _updateMetaThemeColor(theme) {
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');

        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.setAttribute('name', 'theme-color');
            document.head.appendChild(metaThemeColor);
        }

        const color = theme === 'dark' ? '#1a1d23' : '#ffffff';
        metaThemeColor.setAttribute('content', color);
    }

    /**
     * Reset to system preference
     */
    resetToSystemPreference() {
        localStorage.removeItem(this.storageKey);
        const systemTheme = this.systemPreference && this.systemPreference.matches ? 'dark' : 'light';
        this.applyTheme(systemTheme);
    }

    /**
     * Force light mode
     */
    forceLightMode() {
        this.applyTheme('light');
    }

    /**
     * Force dark mode
     */
    forceDarkMode() {
        this.applyTheme('dark');
    }

    /**
     * Get theme-aware color value
     * Useful for charts, maps, etc.
     * @param {string} lightColor - Color for light mode
     * @param {string} darkColor - Color for dark mode
     * @returns {string} Appropriate color for current theme
     */
    getThemeColor(lightColor, darkColor) {
        return this.isDarkMode() ? darkColor : lightColor;
    }

    /**
     * Get CSS variable value for current theme
     * @param {string} varName - CSS variable name (without --)
     * @returns {string} Variable value
     */
    getCSSVariable(varName) {
        return getComputedStyle(document.documentElement)
            .getPropertyValue(`--${varName}`)
            .trim();
    }

    /**
     * Check if system prefers dark mode
     * @returns {boolean}
     */
    systemPrefersDark() {
        return this.systemPreference && this.systemPreference.matches;
    }

    /**
     * Add theme change listener
     * @param {Function} callback - Callback function receiving theme as parameter
     */
    onThemeChange(callback) {
        window.addEventListener('themeChanged', (e) => {
            callback(e.detail.theme);
        });
    }

    /**
     * Remove theme change listener
     * @param {Function} callback - Callback function to remove
     */
    offThemeChange(callback) {
        window.removeEventListener('themeChanged', callback);
    }
}

// Create global instance
const darkModeManager = new DarkModeManager();

// Expose helper functions globally
window.isDarkMode = () => darkModeManager.isDarkMode();
window.getThemeColor = (light, dark) => darkModeManager.getThemeColor(light, dark);

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DarkModeManager;
}
