// Keyboard Shortcuts System - EU Trip Tracker

/**
 * Keyboard shortcuts manager
 */
class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.helpVisible = false;
        this.init();
    }

    init() {
        // Add global keyboard event listener
        document.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        // Initialize default shortcuts
        this.registerDefaultShortcuts();
        
        // Create help modal
        this.createHelpModal();
    }

    /**
     * Register a keyboard shortcut
     * @param {string} key - Key combination (e.g., 'ctrl+k', 'alt+n')
     * @param {Function} handler - Handler function
     * @param {string} description - Description for help
     * @param {object} options - Additional options
     */
    register(key, handler, description, options = {}) {
        const shortcut = {
            key: key.toLowerCase(),
            handler,
            description,
            preventDefault: options.preventDefault !== false,
            stopPropagation: options.stopPropagation || false,
            enabled: options.enabled !== false
        };
        
        this.shortcuts.set(key.toLowerCase(), shortcut);
    }

    /**
     * Unregister a keyboard shortcut
     * @param {string} key - Key combination
     */
    unregister(key) {
        this.shortcuts.delete(key.toLowerCase());
    }

    /**
     * Handle keydown events
     * @param {KeyboardEvent} e - Keyboard event
     */
    handleKeydown(e) {
        // Don't trigger shortcuts when typing in inputs
        if (this.isInputElement(e.target)) {
            return;
        }

        const key = this.getKeyString(e);
        const shortcut = this.shortcuts.get(key);

        if (shortcut && shortcut.enabled) {
            if (shortcut.preventDefault) {
                e.preventDefault();
            }
            if (shortcut.stopPropagation) {
                e.stopPropagation();
            }
            shortcut.handler(e);
        }
    }

    /**
     * Check if element is an input element
     * @param {HTMLElement} element - Element to check
     * @returns {boolean} True if input element
     */
    isInputElement(element) {
        const inputTypes = ['input', 'textarea', 'select'];
        return inputTypes.includes(element.tagName.toLowerCase()) ||
               element.contentEditable === 'true' ||
               element.isContentEditable;
    }

    /**
     * Get key string from keyboard event
     * @param {KeyboardEvent} e - Keyboard event
     * @returns {string} Key combination string
     */
    getKeyString(e) {
        const parts = [];
        
        if (e.ctrlKey) parts.push('ctrl');
        if (e.altKey) parts.push('alt');
        if (e.shiftKey) parts.push('shift');
        if (e.metaKey) parts.push('meta');
        
        // Handle special keys
        const keyMap = {
            ' ': 'space',
            'ArrowUp': 'up',
            'ArrowDown': 'down',
            'ArrowLeft': 'left',
            'ArrowRight': 'right',
            'Enter': 'enter',
            'Escape': 'escape',
            'Tab': 'tab',
            'Backspace': 'backspace',
            'Delete': 'delete'
        };
        
        const key = keyMap[e.key] || e.key.toLowerCase();
        parts.push(key);
        
        return parts.join('+');
    }

    /**
     * Register default shortcuts
     */
    registerDefaultShortcuts() {
        // Global search (Ctrl+K)
        this.register('ctrl+k', () => {
            const searchInput = document.getElementById('globalSearchInput');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }, 'Focus global search');

        // Help (F1 or Ctrl+?)
        this.register('f1', () => this.showHelp(), 'Show help');
        this.register('ctrl+?', () => this.showHelp(), 'Show help');

        // Close modals (Escape)
        this.register('escape', () => {
            const openModal = document.querySelector('.modal.active');
            if (openModal) {
                this.closeModal(openModal);
            }
        }, 'Close modal');

        // Navigation shortcuts
        this.register('alt+h', () => {
            window.location.href = '/';
        }, 'Go to Home');

        this.register('alt+b', () => {
            if (window.history.length > 1) {
                window.history.back();
            } else {
                window.location.href = '/';
            }
        }, 'Go Back');

        this.register('alt+d', () => {
            window.location.href = '/dashboard';
        }, 'Go to Dashboard');

        this.register('alt+a', () => {
            window.location.href = '/bulk_add_trip';
        }, 'Add Trips');

        this.register('alt+i', () => {
            window.location.href = '/import_excel';
        }, 'Import Data');

        this.register('alt+f', () => {
            window.location.href = '/future_job_alerts';
        }, 'Future Alerts');

        // Form shortcuts
        this.register('ctrl+s', (e) => {
            const form = document.querySelector('form:not([data-no-save])');
            if (form) {
                e.preventDefault();
                form.dispatchEvent(new Event('submit'));
            }
        }, 'Save form');

        // Table navigation
        this.register('ctrl+f', () => {
            const searchInput = document.querySelector('input[type="search"], input[placeholder*="search" i]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }, 'Focus table search');

        // Refresh page
        this.register('f5', () => {
            window.location.reload();
        }, 'Refresh page');

        // Toggle sidebar
        this.register('ctrl+b', () => {
            const sidebar = document.querySelector('.sidebar');
            const toggleBtn = document.querySelector('.sidebar-toggle');
            if (sidebar && toggleBtn) {
                toggleBtn.click();
            }
        }, 'Toggle sidebar');
    }

    /**
     * Show help modal
     */
    showHelp() {
        if (this.helpVisible) {
            this.hideHelp();
            return;
        }

        const modal = document.getElementById('keyboardShortcutsHelp');
        if (modal) {
            modal.classList.add('active');
            this.helpVisible = true;
        }
    }

    /**
     * Hide help modal
     */
    hideHelp() {
        const modal = document.getElementById('keyboardShortcutsHelp');
        if (modal) {
            modal.classList.remove('active');
            this.helpVisible = false;
        }
    }

    /**
     * Close modal
     * @param {HTMLElement} modal - Modal element
     */
    closeModal(modal) {
        modal.classList.remove('active');
    }

    /**
     * Create help modal
     */
    createHelpModal() {
        const modal = document.createElement('div');
        modal.id = 'keyboardShortcutsHelp';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 600px;">
                <div class="modal-header">
                    <h3 class="modal-title">Keyboard Shortcuts</h3>
                    <button class="modal-close" onclick="keyboardShortcuts.hideHelp()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="shortcuts-grid">
                        ${this.generateShortcutsHTML()}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="keyboardShortcuts.hideHelp()">Close</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    /**
     * Generate shortcuts HTML
     * @returns {string} HTML for shortcuts
     */
    generateShortcutsHTML() {
        const categories = {
            'Navigation': [],
            'Forms': [],
            'Search': [],
            'General': []
        };

        // Categorize shortcuts
        for (const [key, shortcut] of this.shortcuts) {
            if (key.includes('alt+h') || key.includes('alt+d') || key.includes('alt+a') || key.includes('alt+i') || key.includes('alt+f')) {
                categories['Navigation'].push({ key, ...shortcut });
            } else if (key.includes('ctrl+s') || key.includes('ctrl+f')) {
                categories['Forms'].push({ key, ...shortcut });
            } else if (key.includes('ctrl+k') || key.includes('search')) {
                categories['Search'].push({ key, ...shortcut });
            } else {
                categories['General'].push({ key, ...shortcut });
            }
        }

        // Generate HTML for each category
        let html = '';
        for (const [category, shortcuts] of Object.entries(categories)) {
            if (shortcuts.length === 0) continue;
            
            html += `
                <div class="shortcut-category">
                    <h4>${category}</h4>
                    <div class="shortcut-list">
                        ${shortcuts.map(shortcut => `
                            <div class="shortcut-item">
                                <kbd class="shortcut-key">${this.formatKey(shortcut.key)}</kbd>
                                <span class="shortcut-description">${shortcut.description}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        return html;
    }

    /**
     * Format key for display
     * @param {string} key - Key string
     * @returns {string} Formatted key
     */
    formatKey(key) {
        return key.split('+').map(part => {
            const keyMap = {
                'ctrl': 'Ctrl',
                'alt': 'Alt',
                'shift': 'Shift',
                'meta': 'Cmd',
                'space': 'Space',
                'up': '↑',
                'down': '↓',
                'left': '←',
                'right': '→',
                'enter': 'Enter',
                'escape': 'Esc',
                'tab': 'Tab',
                'backspace': 'Backspace',
                'delete': 'Del'
            };
            return keyMap[part] || part.toUpperCase();
        }).join(' + ');
    }

    /**
     * Enable/disable shortcuts
     * @param {boolean} enabled - Whether to enable shortcuts
     */
    setEnabled(enabled) {
        for (const shortcut of this.shortcuts.values()) {
            shortcut.enabled = enabled;
        }
    }

    /**
     * Get all shortcuts
     * @returns {Array} Array of shortcut objects
     */
    getAllShortcuts() {
        return Array.from(this.shortcuts.values());
    }
}

// Initialize keyboard shortcuts
const keyboardShortcuts = new KeyboardShortcuts();

// Add CSS for shortcuts help modal
const style = document.createElement('style');
style.textContent = `
.shortcuts-grid {
    display: grid;
    gap: 24px;
}

.shortcut-category h4 {
    margin: 0 0 12px 0;
    color: var(--text-primary);
    font-size: 16px;
    font-weight: 600;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 8px;
}

.shortcut-list {
    display: grid;
    gap: 8px;
}

.shortcut-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 0;
}

.shortcut-key {
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    padding: 4px 8px;
    font-family: 'Monaco', 'Consolas', monospace;
    font-size: 12px;
    font-weight: 600;
    color: #374151;
    min-width: 80px;
    text-align: center;
}

.shortcut-description {
    color: var(--text-secondary);
    font-size: 14px;
    margin-left: 16px;
}

@media (max-width: 768px) {
    .shortcut-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
    }
    
    .shortcut-description {
        margin-left: 0;
    }
}
`;
document.head.appendChild(style);

// Export for use in other scripts
window.keyboardShortcuts = keyboardShortcuts;
