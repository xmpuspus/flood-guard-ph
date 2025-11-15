/**
 * Mobile Responsive Manager
 *
 * Enhancement #14: Mobile Responsiveness
 * Touch gestures, bottom sheet, swipe interactions
 */

class MobileResponsiveManager {
    constructor() {
        this.isMobile = this._checkMobile();
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        this.isDrawerOpen = false;
        this.isBottomSheetOpen = false;
        this.bottomSheetStartY = 0;
        this.bottomSheetCurrentY = 0;

        if (this.isMobile) {
            this.init();
        }
    }

    /**
     * Check if device is mobile
     * @private
     */
    _checkMobile() {
        return window.innerWidth <= 768 ||
               /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    /**
     * Initialize mobile features
     */
    init() {
        this.setupMobileLayout();
        this.setupTouchGestures();
        this.setupBottomSheet();
        this.setupNavigationDrawer();
        this.setupViewportFixes();
        this.setupOrientationChange();

        console.log('✓ Mobile responsive features initialized');
    }

    /**
     * Setup mobile layout structure
     */
    setupMobileLayout() {
        // Add mobile header if not exists
        if (!document.querySelector('.mobile-header')) {
            const header = document.createElement('div');
            header.className = 'mobile-header';
            header.innerHTML = `
                <button class="mobile-menu-button" id="mobileMenuBtn" aria-label="Menu">
                    <svg width="24" height="24" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"/>
                    </svg>
                </button>
                <h1 class="mobile-header-title">FloodGuard PH</h1>
                <button class="mobile-menu-button" id="mobileSearchBtn" aria-label="Search">
                    <svg width="24" height="24" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
                    </svg>
                </button>
            `;

            document.body.insertBefore(header, document.body.firstChild);
        }

        // Add mobile navigation drawer
        if (!document.querySelector('.mobile-nav-drawer')) {
            const drawer = document.createElement('div');
            drawer.className = 'mobile-nav-drawer';
            drawer.id = 'mobileNavDrawer';
            drawer.innerHTML = `
                <div class="mobile-nav-header" style="padding: 1rem; border-bottom: 1px solid #e0e0e0;">
                    <h2 style="margin: 0;">Menu</h2>
                </div>
                <div class="mobile-nav-content" style="padding: 1rem;">
                    <!-- Navigation items will be added here -->
                </div>
            `;

            document.body.appendChild(drawer);

            // Add overlay
            const overlay = document.createElement('div');
            overlay.className = 'mobile-nav-overlay';
            overlay.id = 'mobileNavOverlay';
            document.body.appendChild(overlay);
        }

        // Add bottom sheet handle to project panel
        const projectPanel = document.getElementById('projectPanel');
        if (projectPanel && !projectPanel.querySelector('.bottom-sheet-handle')) {
            const handle = document.createElement('div');
            handle.className = 'bottom-sheet-handle';
            projectPanel.insertBefore(handle, projectPanel.firstChild);
        }
    }

    /**
     * Setup touch gestures
     */
    setupTouchGestures() {
        // Swipe detection on map
        const mapPanel = document.getElementById('mapPanel');
        if (mapPanel) {
            mapPanel.addEventListener('touchstart', (e) => {
                this.touchStartX = e.changedTouches[0].screenX;
                this.touchStartY = e.changedTouches[0].screenY;
            }, { passive: true });

            mapPanel.addEventListener('touchend', (e) => {
                this.touchEndX = e.changedTouches[0].screenX;
                this.touchEndY = e.changedTouches[0].screenY;
                this._handleSwipe();
            }, { passive: true });
        }

        // Pull to refresh on chat
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            let pullStartY = 0;
            let isPulling = false;

            chatMessages.addEventListener('touchstart', (e) => {
                if (chatMessages.scrollTop === 0) {
                    pullStartY = e.touches[0].clientY;
                    isPulling = true;
                }
            }, { passive: true });

            chatMessages.addEventListener('touchmove', (e) => {
                if (!isPulling) return;

                const pullDistance = e.touches[0].clientY - pullStartY;
                if (pullDistance > 100) {
                    // Trigger refresh
                    this._triggerPullToRefresh();
                    isPulling = false;
                }
            }, { passive: true });

            chatMessages.addEventListener('touchend', () => {
                isPulling = false;
            }, { passive: true });
        }
    }

    /**
     * Handle swipe gesture
     * @private
     */
    _handleSwipe() {
        const deltaX = this.touchEndX - this.touchStartX;
        const deltaY = this.touchEndY - this.touchStartY;

        // Horizontal swipe threshold: 50px
        if (Math.abs(deltaX) > 50 && Math.abs(deltaX) > Math.abs(deltaY)) {
            if (deltaX > 0) {
                // Swipe right - open drawer
                this.openNavigationDrawer();
            } else {
                // Swipe left - close drawer
                this.closeNavigationDrawer();
            }
        }
    }

    /**
     * Setup bottom sheet for project details
     */
    setupBottomSheet() {
        const projectPanel = document.getElementById('projectPanel');
        const handle = projectPanel?.querySelector('.bottom-sheet-handle');

        if (!projectPanel || !handle) return;

        let isDragging = false;
        let startY = 0;
        let currentHeight = 0;

        handle.addEventListener('touchstart', (e) => {
            isDragging = true;
            startY = e.touches[0].clientY;
            currentHeight = projectPanel.offsetHeight;
            projectPanel.style.transition = 'none';
        }, { passive: true });

        document.addEventListener('touchmove', (e) => {
            if (!isDragging) return;

            const deltaY = startY - e.touches[0].clientY;
            const newHeight = Math.min(Math.max(currentHeight + deltaY, 0), window.innerHeight * 0.8);

            projectPanel.style.height = `${newHeight}px`;
        }, { passive: true });

        document.addEventListener('touchend', () => {
            if (!isDragging) return;

            isDragging = false;
            projectPanel.style.transition = '';

            const currentHeight = projectPanel.offsetHeight;
            const threshold = window.innerHeight * 0.3;

            if (currentHeight < threshold) {
                this.closeBottomSheet();
            } else {
                this.openBottomSheet();
            }
        });
    }

    /**
     * Open bottom sheet
     */
    openBottomSheet() {
        const projectPanel = document.getElementById('projectPanel');
        if (projectPanel) {
            projectPanel.classList.add('open');
            projectPanel.style.height = '70vh';
            this.isBottomSheetOpen = true;

            // Dispatch event
            window.dispatchEvent(new CustomEvent('bottomSheetOpened'));
        }
    }

    /**
     * Close bottom sheet
     */
    closeBottomSheet() {
        const projectPanel = document.getElementById('projectPanel');
        if (projectPanel) {
            projectPanel.classList.remove('open');
            projectPanel.style.height = '0';
            this.isBottomSheetOpen = false;

            // Dispatch event
            window.dispatchEvent(new CustomEvent('bottomSheetClosed'));
        }
    }

    /**
     * Toggle bottom sheet
     */
    toggleBottomSheet() {
        if (this.isBottomSheetOpen) {
            this.closeBottomSheet();
        } else {
            this.openBottomSheet();
        }
    }

    /**
     * Setup navigation drawer
     */
    setupNavigationDrawer() {
        const menuBtn = document.getElementById('mobileMenuBtn');
        const overlay = document.getElementById('mobileNavOverlay');

        if (menuBtn) {
            menuBtn.addEventListener('click', () => {
                this.toggleNavigationDrawer();
            });
        }

        if (overlay) {
            overlay.addEventListener('click', () => {
                this.closeNavigationDrawer();
            });
        }
    }

    /**
     * Open navigation drawer
     */
    openNavigationDrawer() {
        const drawer = document.getElementById('mobileNavDrawer');
        const overlay = document.getElementById('mobileNavOverlay');

        if (drawer) {
            drawer.classList.add('open');
            this.isDrawerOpen = true;
        }

        if (overlay) {
            overlay.classList.add('show');
        }

        // Prevent body scroll
        document.body.classList.add('no-scroll');
    }

    /**
     * Close navigation drawer
     */
    closeNavigationDrawer() {
        const drawer = document.getElementById('mobileNavDrawer');
        const overlay = document.getElementById('mobileNavOverlay');

        if (drawer) {
            drawer.classList.remove('open');
            this.isDrawerOpen = false;
        }

        if (overlay) {
            overlay.classList.remove('show');
        }

        // Restore body scroll
        document.body.classList.remove('no-scroll');
    }

    /**
     * Toggle navigation drawer
     */
    toggleNavigationDrawer() {
        if (this.isDrawerOpen) {
            this.closeNavigationDrawer();
        } else {
            this.openNavigationDrawer();
        }
    }

    /**
     * Setup viewport fixes for mobile browsers
     */
    setupViewportFixes() {
        // Fix viewport height on mobile (accounts for browser chrome)
        const setViewportHeight = () => {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
        };

        setViewportHeight();
        window.addEventListener('resize', setViewportHeight);
        window.addEventListener('orientationchange', setViewportHeight);

        // Prevent zoom on input focus (iOS)
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('focus', () => {
                if (input.style.fontSize !== '16px') {
                    input.style.fontSize = '16px';
                }
            });
        });
    }

    /**
     * Setup orientation change handling
     */
    setupOrientationChange() {
        window.addEventListener('orientationchange', () => {
            // Delay to ensure new dimensions are available
            setTimeout(() => {
                this.handleOrientationChange();
            }, 200);
        });
    }

    /**
     * Handle orientation change
     */
    handleOrientationChange() {
        const isLandscape = window.innerWidth > window.innerHeight;

        if (isLandscape) {
            console.log('Switched to landscape mode');
            // Close bottom sheet in landscape
            this.closeBottomSheet();
        } else {
            console.log('Switched to portrait mode');
        }

        // Dispatch event
        window.dispatchEvent(new CustomEvent('orientationChanged', {
            detail: { isLandscape }
        }));
    }

    /**
     * Trigger pull to refresh
     * @private
     */
    _triggerPullToRefresh() {
        console.log('Pull to refresh triggered');

        // Show loading indicator
        if (window.loadingManager) {
            window.loadingManager.showToast('Refreshing...', 'info', 1000);
        }

        // Dispatch refresh event
        window.dispatchEvent(new CustomEvent('pullToRefresh'));
    }

    /**
     * Show mobile floating action button
     * @param {Function} callback - Click handler
     */
    showFAB(callback) {
        let fab = document.getElementById('mobileFAB');

        if (!fab) {
            fab = document.createElement('button');
            fab.id = 'mobileFAB';
            fab.className = 'mobile-fab';
            fab.innerHTML = `
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/>
                </svg>
            `;
            document.body.appendChild(fab);
        }

        fab.onclick = callback;
    }

    /**
     * Hide mobile FAB
     */
    hideFAB() {
        const fab = document.getElementById('mobileFAB');
        if (fab) {
            fab.remove();
        }
    }

    /**
     * Enable haptic feedback (if supported)
     */
    hapticFeedback(type = 'light') {
        if ('vibrate' in navigator) {
            const patterns = {
                light: 10,
                medium: 20,
                heavy: 30
            };
            navigator.vibrate(patterns[type] || 10);
        }
    }

    /**
     * Check if in standalone mode (PWA)
     * @returns {boolean}
     */
    isStandalone() {
        return window.matchMedia('(display-mode: standalone)').matches ||
               window.navigator.standalone === true;
    }

    /**
     * Get safe area insets (iOS)
     * @returns {Object}
     */
    getSafeAreaInsets() {
        const computedStyle = getComputedStyle(document.documentElement);

        return {
            top: parseInt(computedStyle.getPropertyValue('env(safe-area-inset-top)') || '0'),
            right: parseInt(computedStyle.getPropertyValue('env(safe-area-inset-right)') || '0'),
            bottom: parseInt(computedStyle.getPropertyValue('env(safe-area-inset-bottom)') || '0'),
            left: parseInt(computedStyle.getPropertyValue('env(safe-area-inset-left)') || '0')
        };
    }

    /**
     * Show install prompt for PWA
     */
    showInstallPrompt() {
        // This requires beforeinstallprompt event to be captured
        if (window.deferredPrompt) {
            window.deferredPrompt.prompt();
            window.deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('User accepted the install prompt');
                } else {
                    console.log('User dismissed the install prompt');
                }
                window.deferredPrompt = null;
            });
        }
    }

    /**
     * Cleanup
     */
    destroy() {
        this.closeNavigationDrawer();
        this.closeBottomSheet();
        this.hideFAB();
    }
}

// Capture install prompt event
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    window.deferredPrompt = e;
});

// Create global instance only on mobile
let mobileManager = null;
if (window.innerWidth <= 768) {
    mobileManager = new MobileResponsiveManager();
}

// Re-initialize on resize if transitioning to/from mobile
window.addEventListener('resize', () => {
    const isMobile = window.innerWidth <= 768;

    if (isMobile && !mobileManager) {
        mobileManager = new MobileResponsiveManager();
    } else if (!isMobile && mobileManager) {
        mobileManager.destroy();
        mobileManager = null;
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileResponsiveManager;
}
