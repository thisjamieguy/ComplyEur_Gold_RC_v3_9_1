/**
 * EU Trip Tracker - User Customization System
 * Phase 3 Implementation: User preferences, view customization, and personalization
 */

class CustomizationSystem {
    constructor() {
        this.preferences = {
            theme: 'light',
            density: 'comfortable',
            sidebarCollapsed: false,
            tableColumns: {},
            dashboardLayout: 'grid',
            notifications: {
                email: true,
                browser: true,
                sound: false
            },
            dateFormat: 'DD/MM/YYYY',
            timezone: 'Europe/London',
            language: 'en'
        };
        
        this.availableThemes = ['light', 'dark', 'high-contrast'];
        this.availableDensities = ['compact', 'comfortable', 'spacious'];
        this.availableDateFormats = ['DD/MM/YYYY', 'MM/DD/YYYY', 'YYYY-MM-DD'];
        
        this.init();
    }

    init() {
        this.loadPreferences();
        this.createCustomizationUI();
        this.applyPreferences();
        this.bindEvents();
    }

    loadPreferences() {
        const saved = localStorage.getItem('euTrackerPreferences');
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                this.preferences = { ...this.preferences, ...parsed };
            } catch (e) {
                console.warn('Failed to load preferences:', e);
            }
        }
    }

    savePreferences() {
        localStorage.setItem('euTrackerPreferences', JSON.stringify(this.preferences));
    }

    createCustomizationUI() {
        // Add customization button to topbar
        const topbarRight = document.querySelector('.topbar-right');
        if (topbarRight && !document.querySelector('.customization-button')) {
            const customButton = document.createElement('button');
            customButton.className = 'customization-button';
            customButton.innerHTML = `
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M12 1v6m0 6v6m9-9h-6m-6 0H3"></path>
                </svg>
                <span>Customize</span>
            `;
            customButton.style.cssText = `
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 8px 14px;
                font-size: 14px;
                background: transparent;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                cursor: pointer;
                color: #374151;
                transition: all 0.2s;
            `;
            customButton.onmouseover = () => {
                customButton.style.backgroundColor = '#f9fafb';
                customButton.style.borderColor = '#4C739F';
            };
            customButton.onmouseout = () => {
                customButton.style.backgroundColor = 'transparent';
                customButton.style.borderColor = '#e5e7eb';
            };
            customButton.onclick = () => this.showCustomizationPanel();
            
            topbarRight.insertBefore(customButton, topbarRight.firstChild);
        }
    }

    showCustomizationPanel() {
        // Remove existing panel
        const existing = document.querySelector('.customization-panel');
        if (existing) existing.remove();

        const panel = document.createElement('div');
        panel.className = 'customization-panel';
        panel.style.cssText = `
            position: fixed;
            top: 0;
            right: 0;
            width: 400px;
            height: 100vh;
            background: white;
            box-shadow: -4px 0 12px rgba(0, 0, 0, 0.1);
            z-index: 10001;
            overflow-y: auto;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;

        panel.innerHTML = `
            <div style="padding: 24px; border-bottom: 1px solid #e5e7eb;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3 style="margin: 0; color: #1f2937;">Customize Interface</h3>
                    <button onclick="this.closest('.customization-panel').remove()" style="
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        color: #6b7280;
                    ">×</button>
                </div>
                
                <!-- Theme Selection -->
                <div style="margin-bottom: 24px;">
                    <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #374151;">Theme</label>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
                        ${this.availableThemes.map(theme => `
                            <button onclick="customizationSystem.setTheme('${theme}')" 
                                    class="theme-option ${this.preferences.theme === theme ? 'active' : ''}"
                                    data-theme="${theme}"
                                    style="
                                        padding: 12px;
                                        border: 2px solid ${this.preferences.theme === theme ? '#4C739F' : '#e5e7eb'};
                                        border-radius: 8px;
                                        background: ${this.preferences.theme === theme ? '#f0f9ff' : 'white'};
                                        cursor: pointer;
                                        text-align: center;
                                        font-size: 14px;
                                        transition: all 0.2s;
                                    ">${theme.charAt(0).toUpperCase() + theme.slice(1).replace('-', ' ')}</button>
                        `).join('')}
                    </div>
                </div>

                <!-- Density Selection -->
                <div style="margin-bottom: 24px;">
                    <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #374151;">Density</label>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
                        ${this.availableDensities.map(density => `
                            <button onclick="customizationSystem.setDensity('${density}')" 
                                    class="density-option ${this.preferences.density === density ? 'active' : ''}"
                                    data-density="${density}"
                                    style="
                                        padding: 12px;
                                        border: 2px solid ${this.preferences.density === density ? '#4C739F' : '#e5e7eb'};
                                        border-radius: 8px;
                                        background: ${this.preferences.density === density ? '#f0f9ff' : 'white'};
                                        cursor: pointer;
                                        text-align: center;
                                        font-size: 14px;
                                        transition: all 0.2s;
                                    ">${density.charAt(0).toUpperCase() + density.slice(1)}</button>
                        `).join('')}
                    </div>
                </div>

                <!-- Date Format -->
                <div style="margin-bottom: 24px;">
                    <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #374151;">Date Format</label>
                    <select id="dateFormatSelect" style="
                        width: 100%;
                        padding: 8px 12px;
                        border: 1px solid #e5e7eb;
                        border-radius: 6px;
                        font-size: 14px;
                    ">
                        ${this.availableDateFormats.map(format => `
                            <option value="${format}" ${this.preferences.dateFormat === format ? 'selected' : ''}>${format}</option>
                        `).join('')}
                    </select>
                </div>

                <!-- Dashboard Layout -->
                <div style="margin-bottom: 24px;">
                    <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #374151;">Dashboard Layout</label>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;">
                        <button onclick="customizationSystem.setDashboardLayout('grid')" 
                                class="layout-option ${this.preferences.dashboardLayout === 'grid' ? 'active' : ''}"
                                style="
                                    padding: 12px;
                                    border: 2px solid ${this.preferences.dashboardLayout === 'grid' ? '#4C739F' : '#e5e7eb'};
                                    border-radius: 8px;
                                    background: ${this.preferences.dashboardLayout === 'grid' ? '#f0f9ff' : 'white'};
                                    cursor: pointer;
                                    text-align: center;
                                    font-size: 14px;
                                    transition: all 0.2s;
                                ">Grid View</button>
                        <button onclick="customizationSystem.setDashboardLayout('list')" 
                                class="layout-option ${this.preferences.dashboardLayout === 'list' ? 'active' : ''}"
                                style="
                                    padding: 12px;
                                    border: 2px solid ${this.preferences.dashboardLayout === 'list' ? '#4C739F' : '#e5e7eb'};
                                    border-radius: 8px;
                                    background: ${this.preferences.dashboardLayout === 'list' ? '#f0f9ff' : 'white'};
                                    cursor: pointer;
                                    text-align: center;
                                    font-size: 14px;
                                    transition: all 0.2s;
                                ">List View</button>
                    </div>
                </div>

                <!-- Notifications -->
                <div style="margin-bottom: 24px;">
                    <label style="display: block; font-weight: 600; margin-bottom: 12px; color: #374151;">Notifications</label>
                    <div style="space-y: 8px;">
                        <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                            <input type="checkbox" ${this.preferences.notifications.email ? 'checked' : ''} 
                                   onchange="customizationSystem.setNotification('email', this.checked)">
                            <span>Email notifications</span>
                        </label>
                        <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                            <input type="checkbox" ${this.preferences.notifications.browser ? 'checked' : ''} 
                                   onchange="customizationSystem.setNotification('browser', this.checked)">
                            <span>Browser notifications</span>
                        </label>
                        <label style="display: flex; align-items: center; gap: 8px;">
                            <input type="checkbox" ${this.preferences.notifications.sound ? 'checked' : ''} 
                                   onchange="customizationSystem.setNotification('sound', this.checked)">
                            <span>Sound alerts</span>
                        </label>
                    </div>
                </div>

                <!-- Table Customization -->
                <div style="margin-bottom: 24px;">
                    <label style="display: block; font-weight: 600; margin-bottom: 12px; color: #374151;">Table Columns</label>
                    <div id="tableColumnsConfig">
                        <!-- Will be populated dynamically -->
                    </div>
                </div>

                <!-- Reset Button -->
                <div style="border-top: 1px solid #e5e7eb; padding-top: 20px;">
                    <button onclick="customizationSystem.resetToDefaults()" style="
                        width: 100%;
                        padding: 12px;
                        background: #f3f4f6;
                        color: #374151;
                        border: 1px solid #e5e7eb;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 14px;
                        transition: all 0.2s;
                    " onmouseover="this.style.backgroundColor='#e5e7eb'" onmouseout="this.style.backgroundColor='#f3f4f6'">
                        Reset to Defaults
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(panel);
        
        // Animate in
        setTimeout(() => {
            panel.style.transform = 'translateX(0)';
        }, 10);

        // Populate table columns config
        this.populateTableColumnsConfig();
    }

    populateTableColumnsConfig() {
        const container = document.getElementById('tableColumnsConfig');
        if (!container) return;

        // Get all tables on the page
        const tables = document.querySelectorAll('table');
        const tableConfigs = {};

        tables.forEach((table, index) => {
            const tableId = `table-${index}`;
            const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
            
            tableConfigs[tableId] = {
                name: `Table ${index + 1}`,
                headers: headers,
                visible: headers.map(() => true) // All visible by default
            };
        });

        container.innerHTML = Object.entries(tableConfigs).map(([tableId, config]) => `
            <div style="margin-bottom: 16px;">
                <div style="font-weight: 500; margin-bottom: 8px; color: #6b7280;">${config.name}</div>
                <div style="space-y: 4px;">
                    ${config.headers.map((header, index) => `
                        <label style="display: flex; align-items: center; gap: 8px; font-size: 14px;">
                            <input type="checkbox" ${config.visible[index] ? 'checked' : ''} 
                                   onchange="customizationSystem.toggleTableColumn('${tableId}', ${index}, this.checked)">
                            <span>${header}</span>
                        </label>
                    `).join('')}
                </div>
            </div>
        `).join('');
    }

    setTheme(theme) {
        this.preferences.theme = theme;
        this.savePreferences();
        this.applyTheme(theme);
        this.updateActiveButtons('.theme-option', 'data-theme', theme);
    }

    setDensity(density) {
        this.preferences.density = density;
        this.savePreferences();
        this.applyDensity(density);
        this.updateActiveButtons('.density-option', 'data-density', density);
    }

    setDashboardLayout(layout) {
        this.preferences.dashboardLayout = layout;
        this.savePreferences();
        this.applyDashboardLayout(layout);
        this.updateActiveButtons('.layout-option', 'onclick', `customizationSystem.setDashboardLayout('${layout}')`);
    }

    setNotification(type, enabled) {
        this.preferences.notifications[type] = enabled;
        this.savePreferences();
    }

    setDateFormat(format) {
        this.preferences.dateFormat = format;
        this.savePreferences();
        this.applyDateFormat(format);
    }

    toggleTableColumn(tableId, columnIndex, visible) {
        if (!this.preferences.tableColumns[tableId]) {
            this.preferences.tableColumns[tableId] = {};
        }
        this.preferences.tableColumns[tableId][columnIndex] = visible;
        this.savePreferences();
        this.applyTableColumnVisibility(tableId, columnIndex, visible);
    }

    updateActiveButtons(selector, attribute, value) {
        document.querySelectorAll(selector).forEach(button => {
            const isActive = button.getAttribute(attribute) === value;
            button.classList.toggle('active', isActive);
            button.style.borderColor = isActive ? '#4C739F' : '#e5e7eb';
            button.style.backgroundColor = isActive ? '#f0f9ff' : 'white';
        });
    }

    applyPreferences() {
        this.applyTheme(this.preferences.theme);
        this.applyDensity(this.preferences.density);
        this.applyDashboardLayout(this.preferences.dashboardLayout);
        this.applyDateFormat(this.preferences.dateFormat);
        this.applyTableColumnPreferences();
    }

    applyTheme(theme) {
        document.body.className = document.body.className.replace(/theme-\w+/g, '');
        document.body.classList.add(`theme-${theme}`);
        
        // Add theme-specific CSS
        if (!document.querySelector('#theme-styles')) {
            const style = document.createElement('style');
            style.id = 'theme-styles';
            document.head.appendChild(style);
        }
        
        const themeStyles = document.getElementById('theme-styles');
        themeStyles.textContent = this.getThemeCSS(theme);
    }

    getThemeCSS(theme) {
        const themes = {
            light: `
                :root {
                    --bg-primary: #ffffff;
                    --bg-secondary: #f9fafb;
                    --text-primary: #1f2937;
                    --text-secondary: #6b7280;
                    --border-color: #e5e7eb;
                }
            `,
            dark: `
                :root {
                    --bg-primary: #1f2937;
                    --bg-secondary: #374151;
                    --text-primary: #f9fafb;
                    --text-secondary: #d1d5db;
                    --border-color: #4b5563;
                }
                .theme-dark {
                    background-color: var(--bg-primary);
                    color: var(--text-primary);
                }
                .theme-dark .card, .theme-dark .panel {
                    background-color: var(--bg-secondary);
                    border-color: var(--border-color);
                }
            `,
            'high-contrast': `
                :root {
                    --bg-primary: #ffffff;
                    --bg-secondary: #f0f0f0;
                    --text-primary: #000000;
                    --text-secondary: #333333;
                    --border-color: #000000;
                }
                .theme-high-contrast {
                    background-color: var(--bg-primary);
                    color: var(--text-primary);
                }
                .theme-high-contrast .card, .theme-high-contrast .panel {
                    background-color: var(--bg-secondary);
                    border: 2px solid var(--border-color);
                }
            `
        };
        
        return themes[theme] || themes.light;
    }

    applyDensity(density) {
        document.body.className = document.body.className.replace(/density-\w+/g, '');
        document.body.classList.add(`density-${density}`);
        
        const densityStyles = {
            compact: `
                .density-compact .card { padding: 12px; }
                .density-compact .btn { padding: 6px 12px; font-size: 13px; }
                .density-compact .form-input { padding: 6px 10px; }
                .density-compact .table th, .density-compact .table td { padding: 8px; }
            `,
            comfortable: `
                .density-comfortable .card { padding: 16px; }
                .density-comfortable .btn { padding: 8px 16px; font-size: 14px; }
                .density-comfortable .form-input { padding: 8px 12px; }
                .density-comfortable .table th, .density-comfortable .table td { padding: 12px; }
            `,
            spacious: `
                .density-spacious .card { padding: 24px; }
                .density-spacious .btn { padding: 12px 24px; font-size: 16px; }
                .density-spacious .form-input { padding: 12px 16px; }
                .density-spacious .table th, .density-spacious .table td { padding: 16px; }
            `
        };
        
        if (!document.querySelector('#density-styles')) {
            const style = document.createElement('style');
            style.id = 'density-styles';
            document.head.appendChild(style);
        }
        
        document.getElementById('density-styles').textContent = densityStyles[density] || densityStyles.comfortable;
    }

    applyDashboardLayout(layout) {
        const dashboard = document.querySelector('.dashboard, .content-body');
        if (!dashboard) return;
        
        dashboard.className = dashboard.className.replace(/layout-\w+/g, '');
        dashboard.classList.add(`layout-${layout}`);
        
        const layoutStyles = {
            grid: `
                .layout-grid .employee-cards {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 16px;
                }
            `,
            list: `
                .layout-list .employee-cards {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }
                .layout-list .employee-card {
                    display: flex;
                    align-items: center;
                    padding: 12px 16px;
                }
            `
        };
        
        if (!document.querySelector('#layout-styles')) {
            const style = document.createElement('style');
            style.id = 'layout-styles';
            document.head.appendChild(style);
        }
        
        document.getElementById('layout-styles').textContent = layoutStyles[layout] || layoutStyles.grid;
    }

    applyDateFormat(format) {
        // This would typically be handled by a date formatting library
        // For now, we'll just store the preference
        console.log('Date format set to:', format);
    }

    applyTableColumnPreferences() {
        Object.entries(this.preferences.tableColumns).forEach(([tableId, columns]) => {
            const table = document.getElementById(tableId);
            if (!table) return;
            
            Object.entries(columns).forEach(([columnIndex, visible]) => {
                this.applyTableColumnVisibility(tableId, parseInt(columnIndex), visible);
            });
        });
    }

    applyTableColumnVisibility(tableId, columnIndex, visible) {
        const table = document.getElementById(tableId);
        if (!table) return;
        
        const header = table.querySelectorAll('th')[columnIndex];
        const cells = table.querySelectorAll(`td:nth-child(${columnIndex + 1})`);
        
        if (header) header.style.display = visible ? '' : 'none';
        cells.forEach(cell => {
            cell.style.display = visible ? '' : 'none';
        });
    }

    resetToDefaults() {
        this.preferences = {
            theme: 'light',
            density: 'comfortable',
            sidebarCollapsed: false,
            tableColumns: {},
            dashboardLayout: 'grid',
            notifications: {
                email: true,
                browser: true,
                sound: false
            },
            dateFormat: 'DD/MM/YYYY',
            timezone: 'Europe/London',
            language: 'en'
        };
        
        this.savePreferences();
        this.applyPreferences();
        
        // Refresh the customization panel
        this.showCustomizationPanel();
    }

    bindEvents() {
        // Bind date format change
        document.addEventListener('change', (e) => {
            if (e.target.id === 'dateFormatSelect') {
                this.setDateFormat(e.target.value);
            }
        });
    }
}

// Initialize customization system when DOM is loaded
let customizationSystem;
document.addEventListener('DOMContentLoaded', function() {
    customizationSystem = new CustomizationSystem();
    window.customizationSystem = customizationSystem;
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CustomizationSystem;
}
