/**
 * EU Trip Tracker - Comprehensive Help System
 * Phase 3 Implementation: Interactive tutorials, tooltips, and contextual help
 */

class HelpSystem {
    constructor() {
        this.tooltips = new Map();
        this.tutorials = new Map();
        this.isTutorialActive = false;
        this.currentTutorial = null;
        this.tutorialStep = 0;
        this.overlay = null;
        this.tooltipElement = null;
        
        this.init();
    }

    init() {
        this.createTooltipElement();
        this.createTutorialOverlay();
        this.bindEvents();
        this.loadTutorials();
        this.initializeTooltips();
    }

    createTooltipElement() {
        this.tooltipElement = document.createElement('div');
        this.tooltipElement.className = 'help-tooltip';
        this.tooltipElement.style.cssText = `
            position: absolute;
            background: #1f2937;
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
            line-height: 1.4;
            max-width: 300px;
            z-index: 10000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            pointer-events: none;
        `;
        document.body.appendChild(this.tooltipElement);
    }

    createTutorialOverlay() {
        this.overlay = document.createElement('div');
        this.overlay.className = 'tutorial-overlay';
        this.overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 9999;
            display: none;
            pointer-events: none;
        `;
        document.body.appendChild(this.overlay);
    }

    bindEvents() {
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isTutorialActive) {
                this.endTutorial();
            }
            if (e.key === 'F1') {
                e.preventDefault();
                this.showHelpMenu();
            }
        });

        // Help button click - only for elements with data-help-click attribute
        document.addEventListener('click', (e) => {
            if (e.target.closest('.help-trigger[data-help-click="true"]')) {
                e.preventDefault();
                const helpId = e.target.closest('.help-trigger').dataset.helpId;
                this.showContextualHelp(helpId);
            }
        });
    }

    loadTutorials() {
        // Tutorial definitions
        this.tutorials.set('getting-started', {
            title: 'Getting Started with EU Trip Tracker',
            steps: [
                {
                    target: '.sidebar',
                    title: 'Welcome to EU Trip Tracker! 🇪🇺',
                    content: 'This is your navigation sidebar. Here you can access all the main features of the system.',
                    position: 'right'
                },
                {
                    target: '.dashboard-card, .employee-card',
                    title: 'Dashboard Overview 📊',
                    content: 'The dashboard shows all employees and their EU travel status. Green = Safe, Amber = Caution, Red = At Risk.',
                    position: 'bottom'
                },
                {
                    target: '[href*="bulk_add_trip"]',
                    title: 'Adding Trips ➕',
                    content: 'Click here to add individual trips. You can also use bulk add or Excel import for multiple trips.',
                    position: 'right'
                },
                {
                    target: '[href*="import_excel"]',
                    title: 'Excel Import 📤',
                    content: 'Upload work schedules or trip lists using Excel files. Perfect for bulk data entry.',
                    position: 'right'
                },
                {
                    target: '#globalSearchInput',
                    title: 'Quick Search 🔍',
                    content: 'Type any employee name to instantly jump to their detail page. Super fast navigation!',
                    position: 'bottom'
                },
                {
                    target: '[href*="help_page"]',
                    title: 'Help & Support 🆘',
                    content: 'Click here anytime for detailed help, tutorials, and documentation.',
                    position: 'right'
                }
            ]
        });

        this.tutorials.set('dashboard-tour', {
            title: 'Dashboard Deep Dive',
            steps: [
                {
                    target: '.dashboard-stats',
                    title: 'System Statistics 📈',
                    content: 'View key metrics: total employees, at-risk count, and system health.',
                    position: 'bottom'
                },
                {
                    target: '.employee-card',
                    title: 'Employee Cards 👤',
                    content: 'Each card shows an employee\'s current status. Click to view detailed trip history.',
                    position: 'top'
                },
                {
                    target: '.status-indicator',
                    title: 'Status Indicators 🚦',
                    content: 'Color-coded status: Green (30+ days), Amber (10-29 days), Red (<10 days).',
                    position: 'right'
                },
                {
                    target: '.export-button',
                    title: 'Export Data 📊',
                    content: 'Generate reports in CSV or PDF format for HR records and compliance.',
                    position: 'left'
                }
            ]
        });

        this.tutorials.set('trip-management', {
            title: 'Trip Management Workflow',
            steps: [
                {
                    target: '.add-trip-button',
                    title: 'Adding Individual Trips ➕',
                    content: 'Click to add a single trip for one employee. Perfect for one-off travel.',
                    position: 'right'
                },
                {
                    target: '[href*="bulk_add_trip"]',
                    title: 'Bulk Trip Addition 👥',
                    content: 'Add the same trip for multiple employees at once. Great for group travel.',
                    position: 'right'
                },
                {
                    target: '[href*="import_excel"]',
                    title: 'Excel Import 📋',
                    content: 'Upload work schedules or trip lists. Supports multiple formats and validation.',
                    position: 'right'
                },
                {
                    target: '.trip-forecast',
                    title: 'Trip Forecasting 🔮',
                    content: 'Plan future trips and see their impact on compliance before booking.',
                    position: 'top'
                }
            ]
        });
    }

    initializeTooltips() {
        // Auto-detect elements with data-help attributes
        document.querySelectorAll('[data-help]').forEach(element => {
            this.addTooltip(element, {
                content: element.dataset.help,
                position: element.dataset.helpPosition || 'top'
            });
        });

        // Add contextual help to common UI elements
        this.addContextualHelp();
    }

    addContextualHelp() {
        // Dashboard elements
        this.addTooltipToSelector('.employee-card', {
            content: 'Click to view detailed trip history and compliance status for this employee.',
            position: 'top'
        });

        this.addTooltipToSelector('.status-indicator.green', {
            content: 'Safe to travel - 30+ days remaining in 180-day window.',
            position: 'right'
        });

        this.addTooltipToSelector('.status-indicator.amber', {
            content: 'Caution - 10-29 days remaining. Consider postponing future travel.',
            position: 'right'
        });

        this.addTooltipToSelector('.status-indicator.red', {
            content: 'At Risk - Less than 10 days remaining or over limit. Immediate attention needed.',
            position: 'right'
        });

        // Form elements
        this.addTooltipToSelector('input[type="date"]', {
            content: 'Use DD/MM/YYYY format. Partial days count as full days toward the 90/180 limit.',
            position: 'top'
        });

        this.addTooltipToSelector('select[name="country"]', {
            content: 'Select the destination country. Only Schengen countries count toward the 90-day limit.',
            position: 'top'
        });

        // Navigation elements - tooltips only, no click functionality
        this.addTooltipToSelector('.nav-item', {
            content: 'Click to navigate to this section. Active sections are highlighted.',
            position: 'right',
            clickable: false
        });
    }

    addTooltipToSelector(selector, options) {
        document.querySelectorAll(selector).forEach(element => {
            this.addTooltip(element, options);
        });
    }

    addTooltip(element, options) {
        const tooltipId = `tooltip-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        // Only add help-trigger class if this is meant to be clickable for help
        if (options.clickable !== false) {
            element.classList.add('help-trigger');
            element.dataset.helpId = tooltipId;
        }
        
        this.tooltips.set(tooltipId, {
            element,
            content: options.content,
            position: options.position || 'top',
            title: options.title || ''
        });

        // Add hover events
        element.addEventListener('mouseenter', (e) => this.showTooltip(tooltipId, e));
        element.addEventListener('mouseleave', () => this.hideTooltip());
        element.addEventListener('mousemove', (e) => this.updateTooltipPosition(e));
    }

    showTooltip(tooltipId, event) {
        const tooltip = this.tooltips.get(tooltipId);
        if (!tooltip) return;

        this.tooltipElement.innerHTML = `
            ${tooltip.title ? `<div style="font-weight: 600; margin-bottom: 4px;">${tooltip.title}</div>` : ''}
            <div>${tooltip.content}</div>
        `;
        
        this.tooltipElement.style.opacity = '1';
        this.tooltipElement.style.visibility = 'visible';
        
        this.updateTooltipPosition(event);
    }

    hideTooltip() {
        this.tooltipElement.style.opacity = '0';
        this.tooltipElement.style.visibility = 'hidden';
    }

    updateTooltipPosition(event) {
        if (this.tooltipElement.style.visibility === 'hidden') return;

        const rect = this.tooltipElement.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        let x = event.pageX + 10;
        let y = event.pageY - 10;

        // Adjust position based on viewport boundaries
        if (x + rect.width > viewportWidth) {
            x = event.pageX - rect.width - 10;
        }
        if (y - rect.height < 0) {
            y = event.pageY + 20;
        }

        this.tooltipElement.style.left = `${x}px`;
        this.tooltipElement.style.top = `${y}px`;
    }

    showContextualHelp(helpId) {
        const tooltip = this.tooltips.get(helpId);
        if (!tooltip) return;

        // Create a more prominent help modal for contextual help
        this.showHelpModal(tooltip.title, tooltip.content);
    }

    showHelpModal(title, content) {
        const modal = document.createElement('div');
        modal.className = 'help-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 10001;
            display: flex;
            align-items: center;
            justify-content: center;
        `;

        modal.innerHTML = `
            <div style="
                background: white;
                border-radius: 12px;
                padding: 24px;
                max-width: 500px;
                margin: 20px;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h3 style="margin: 0; color: #1f2937;">${title}</h3>
                    <button onclick="this.closest('.help-modal').remove()" style="
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        color: #6b7280;
                    ">×</button>
                </div>
                <div style="color: #4b5563; line-height: 1.6;">${content}</div>
                <div style="margin-top: 20px; text-align: right;">
                    <button onclick="this.closest('.help-modal').remove()" style="
                        background: #4C739F;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 6px;
                        cursor: pointer;
                    ">Got it!</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    }

    startTutorial(tutorialId) {
        const tutorial = this.tutorials.get(tutorialId);
        if (!tutorial) return;

        this.currentTutorial = tutorial;
        this.tutorialStep = 0;
        this.isTutorialActive = true;
        this.overlay.style.display = 'block';

        this.showTutorialStep();
    }

    showTutorialStep() {
        if (!this.currentTutorial || this.tutorialStep >= this.currentTutorial.steps.length) {
            this.endTutorial();
            return;
        }

        const step = this.currentTutorial.steps[this.tutorialStep];
        const targetElement = document.querySelector(step.target);
        
        if (!targetElement) {
            console.warn(`Tutorial step target not found: ${step.target}`);
            this.tutorialStep++;
            setTimeout(() => this.showTutorialStep(), 100);
            return;
        }

        this.highlightElement(targetElement, step);
    }

    highlightElement(element, step) {
        // Remove existing highlights
        document.querySelectorAll('.tutorial-highlight').forEach(el => {
            el.classList.remove('tutorial-highlight');
        });

        // Add highlight to target element
        element.classList.add('tutorial-highlight');
        element.style.cssText += `
            position: relative;
            z-index: 10001;
            box-shadow: 0 0 0 4px #4C739F, 0 0 0 8px rgba(76, 115, 159, 0.3);
            border-radius: 8px;
        `;

        // Create tutorial popup
        this.createTutorialPopup(element, step);
    }

    createTutorialPopup(element, step) {
        // Remove existing popup
        const existingPopup = document.querySelector('.tutorial-popup');
        if (existingPopup) existingPopup.remove();

        const popup = document.createElement('div');
        popup.className = 'tutorial-popup';
        
        const rect = element.getBoundingClientRect();
        const position = this.calculatePopupPosition(rect, step.position);
        
        popup.style.cssText = `
            position: fixed;
            left: ${position.x}px;
            top: ${position.y}px;
            background: white;
            border-radius: 12px;
            padding: 20px;
            max-width: 350px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            z-index: 10002;
            animation: tutorialPopupIn 0.3s ease-out;
        `;

        popup.innerHTML = `
            <div style="margin-bottom: 12px;">
                <h4 style="margin: 0 0 8px 0; color: #1f2937; font-size: 18px;">${step.title}</h4>
                <div style="color: #4b5563; line-height: 1.5;">${step.content}</div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="color: #6b7280; font-size: 14px;">
                    Step ${this.tutorialStep + 1} of ${this.currentTutorial.steps.length}
                </div>
                <div>
                    ${this.tutorialStep > 0 ? `
                        <button onclick="helpSystem.previousStep()" style="
                            background: #f3f4f6;
                            color: #374151;
                            border: none;
                            padding: 8px 16px;
                            border-radius: 6px;
                            cursor: pointer;
                            margin-right: 8px;
                        ">Previous</button>
                    ` : ''}
                    <button onclick="helpSystem.nextStep()" style="
                        background: #4C739F;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 6px;
                        cursor: pointer;
                    ">${this.tutorialStep === this.currentTutorial.steps.length - 1 ? 'Finish' : 'Next'}</button>
                </div>
            </div>
        `;

        document.body.appendChild(popup);

        // Add CSS animation
        if (!document.querySelector('#tutorial-animations')) {
            const style = document.createElement('style');
            style.id = 'tutorial-animations';
            style.textContent = `
                @keyframes tutorialPopupIn {
                    from { opacity: 0; transform: scale(0.9) translateY(-10px); }
                    to { opacity: 1; transform: scale(1) translateY(0); }
                }
                .tutorial-highlight {
                    transition: all 0.3s ease;
                }
            `;
            document.head.appendChild(style);
        }
    }

    calculatePopupPosition(rect, position) {
        const margin = 20;
        const popupWidth = 350;
        const popupHeight = 150;

        let x, y;

        switch (position) {
            case 'top':
                x = rect.left + (rect.width / 2) - (popupWidth / 2);
                y = rect.top - popupHeight - margin;
                break;
            case 'bottom':
                x = rect.left + (rect.width / 2) - (popupWidth / 2);
                y = rect.bottom + margin;
                break;
            case 'left':
                x = rect.left - popupWidth - margin;
                y = rect.top + (rect.height / 2) - (popupHeight / 2);
                break;
            case 'right':
                x = rect.right + margin;
                y = rect.top + (rect.height / 2) - (popupHeight / 2);
                break;
            default:
                x = rect.left + (rect.width / 2) - (popupWidth / 2);
                y = rect.top - popupHeight - margin;
        }

        // Ensure popup stays within viewport
        x = Math.max(margin, Math.min(x, window.innerWidth - popupWidth - margin));
        y = Math.max(margin, Math.min(y, window.innerHeight - popupHeight - margin));

        return { x, y };
    }

    nextStep() {
        this.tutorialStep++;
        this.showTutorialStep();
    }

    previousStep() {
        if (this.tutorialStep > 0) {
            this.tutorialStep--;
            this.showTutorialStep();
        }
    }

    endTutorial() {
        this.isTutorialActive = false;
        this.currentTutorial = null;
        this.tutorialStep = 0;
        
        // Clean up
        document.querySelectorAll('.tutorial-highlight').forEach(el => {
            el.classList.remove('tutorial-highlight');
            el.style.boxShadow = '';
        });
        
        document.querySelectorAll('.tutorial-popup').forEach(el => el.remove());
        this.overlay.style.display = 'none';
    }

    showHelpMenu() {
        const menu = document.createElement('div');
        menu.className = 'help-menu';
        menu.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border-radius: 12px;
            padding: 24px;
            max-width: 600px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            z-index: 10001;
        `;

        menu.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 style="margin: 0; color: #1f2937;">Help & Tutorials</h3>
                <button onclick="this.closest('.help-menu').remove()" style="
                    background: none;
                    border: none;
                    font-size: 24px;
                    cursor: pointer;
                    color: #6b7280;
                ">×</button>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px;">
                <button onclick="helpSystem.startTutorial('getting-started'); this.closest('.help-menu').remove();" style="
                    background: #f8fafc;
                    border: 2px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 16px;
                    cursor: pointer;
                    text-align: left;
                    transition: all 0.2s;
                " onmouseover="this.style.borderColor='#4C739F'" onmouseout="this.style.borderColor='#e2e8f0'">
                    <div style="font-weight: 600; margin-bottom: 4px;">🚀 Getting Started</div>
                    <div style="color: #64748b; font-size: 14px;">Learn the basics and main features</div>
                </button>
                <button onclick="helpSystem.startTutorial('dashboard-tour'); this.closest('.help-menu').remove();" style="
                    background: #f8fafc;
                    border: 2px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 16px;
                    cursor: pointer;
                    text-align: left;
                    transition: all 0.2s;
                " onmouseover="this.style.borderColor='#4C739F'" onmouseout="this.style.borderColor='#e2e8f0'">
                    <div style="font-weight: 600; margin-bottom: 4px;">📊 Dashboard Tour</div>
                    <div style="color: #64748b; font-size: 14px;">Explore the dashboard features</div>
                </button>
                <button onclick="helpSystem.startTutorial('trip-management'); this.closest('.help-menu').remove();" style="
                    background: #f8fafc;
                    border: 2px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 16px;
                    cursor: pointer;
                    text-align: left;
                    transition: all 0.2s;
                " onmouseover="this.style.borderColor='#4C739F'" onmouseout="this.style.borderColor='#e2e8f0'">
                    <div style="font-weight: 600; margin-bottom: 4px;">✈️ Trip Management</div>
                    <div style="color: #64748b; font-size: 14px;">Master trip adding and planning</div>
                </button>
                <button onclick="window.location.href='/help'; this.closest('.help-menu').remove();" style="
                    background: #f8fafc;
                    border: 2px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 16px;
                    cursor: pointer;
                    text-align: left;
                    transition: all 0.2s;
                " onmouseover="this.style.borderColor='#4C739F'" onmouseout="this.style.borderColor='#e2e8f0'">
                    <div style="font-weight: 600; margin-bottom: 4px;">📚 Full Documentation</div>
                    <div style="color: #64748b; font-size: 14px;">Complete help and FAQ</div>
                </button>
            </div>
        `;

        // Add backdrop
        const backdrop = document.createElement('div');
        backdrop.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 10000;
        `;
        backdrop.onclick = () => {
            menu.remove();
            backdrop.remove();
        };

        document.body.appendChild(backdrop);
        document.body.appendChild(menu);
    }
}

// Initialize help system when DOM is loaded
let helpSystem;
document.addEventListener('DOMContentLoaded', function() {
    helpSystem = new HelpSystem();
    
    // Make help system globally available
    window.helpSystem = helpSystem;
    
    // Add keyboard shortcut info
    console.log('💡 Help System loaded! Press F1 for quick help menu.');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HelpSystem;
}
