/**
 * EU Trip Tracker - Interactive Tutorial System
 * Phase 3 Implementation: Guided tours and interactive learning experiences
 */

class InteractiveTutorials {
    constructor() {
        this.tutorials = new Map();
        this.currentTutorial = null;
        this.currentStep = 0;
        this.overlay = null;
        this.tourElement = null;
        this.isActive = false;
        
        this.init();
    }

    init() {
        this.createTutorialOverlay();
        this.createTourElement();
        this.loadTutorialDefinitions();
        this.bindEvents();
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
            z-index: 9998;
            display: none;
            pointer-events: none;
        `;
        document.body.appendChild(this.overlay);
    }

    createTourElement() {
        this.tourElement = document.createElement('div');
        this.tourElement.className = 'tutorial-tour';
        this.tourElement.style.cssText = `
            position: fixed;
            z-index: 9999;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            max-width: 400px;
            min-width: 300px;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            pointer-events: auto;
        `;
        document.body.appendChild(this.tourElement);
    }

    loadTutorialDefinitions() {
        // Getting Started Tutorial
        this.tutorials.set('getting-started', {
            id: 'getting-started',
            title: 'Welcome to EU Trip Tracker',
            description: 'Learn the basics of managing employee travel compliance',
            steps: [
                {
                    target: '.sidebar',
                    title: 'Navigation Sidebar',
                    content: 'This is your main navigation. Here you can access all the key features of the system.',
                    position: 'right',
                    action: 'highlight'
                },
                {
                    target: '.dashboard-card, .employee-card',
                    title: 'Employee Dashboard',
                    content: 'The dashboard shows all employees and their current EU travel status. Each card represents an employee with their compliance status.',
                    position: 'bottom',
                    action: 'highlight'
                },
                {
                    target: '.status-indicator',
                    title: 'Status Indicators',
                    content: 'Color-coded status indicators: Green = Safe (30+ days), Amber = Caution (10-29 days), Red = At Risk (<10 days).',
                    position: 'right',
                    action: 'highlight'
                },
                {
                    target: '#globalSearchInput',
                    title: 'Global Search',
                    content: 'Type any employee name to quickly find and navigate to their detail page. This is the fastest way to look up information.',
                    position: 'bottom',
                    action: 'highlight'
                },
                {
                    target: '[href*="bulk_add_trip"]',
                    title: 'Adding Trips',
                    content: 'Click here to add trips for employees. You can add individual trips or bulk trips for multiple employees.',
                    position: 'right',
                    action: 'highlight'
                },
                {
                    target: '[href*="help_page"]',
                    title: 'Help & Support',
                    content: 'Access comprehensive help documentation, tutorials, and support resources anytime.',
                    position: 'right',
                    action: 'highlight'
                }
            ]
        });

        // Dashboard Deep Dive
        this.tutorials.set('dashboard-tour', {
            id: 'dashboard-tour',
            title: 'Dashboard Deep Dive',
            description: 'Explore all dashboard features and functionality',
            steps: [
                {
                    target: '.dashboard-stats, .stats-container',
                    title: 'System Statistics',
                    content: 'View key metrics including total employees, at-risk count, and system health indicators.',
                    position: 'bottom',
                    action: 'highlight'
                },
                {
                    target: '.employee-card',
                    title: 'Employee Cards',
                    content: 'Each card shows an employee\'s current status. Click to view detailed trip history and compliance information.',
                    position: 'top',
                    action: 'highlight'
                },
                {
                    target: '.export-button, [href*="export"]',
                    title: 'Export Data',
                    content: 'Generate reports in CSV or PDF format for HR records, compliance documentation, and management presentations.',
                    position: 'left',
                    action: 'highlight'
                },
                {
                    target: '.filter-controls, .search-filters',
                    title: 'Filtering & Search',
                    content: 'Use filters to narrow down the view by status, department, or other criteria. Perfect for large employee lists.',
                    position: 'bottom',
                    action: 'highlight'
                }
            ]
        });

        // Trip Management Workflow
        this.tutorials.set('trip-management', {
            id: 'trip-management',
            title: 'Trip Management Workflow',
            description: 'Master the art of adding and managing employee trips',
            steps: [
                {
                    target: '.add-trip-button, [href*="add_trip"]',
                    title: 'Adding Individual Trips',
                    content: 'Click to add a single trip for one employee. Perfect for one-off travel or individual bookings.',
                    position: 'right',
                    action: 'highlight'
                },
                {
                    target: '[href*="bulk_add_trip"]',
                    title: 'Bulk Trip Addition',
                    content: 'Add the same trip for multiple employees at once. Great for group travel, company events, or team meetings.',
                    position: 'right',
                    action: 'highlight'
                },
                {
                    target: '[href*="import_excel"]',
                    title: 'Excel Import',
                    content: 'Upload work schedules or trip lists using Excel files. Supports multiple formats with automatic validation.',
                    position: 'right',
                    action: 'highlight'
                },
                {
                    target: '.trip-forecast, .forecast-button',
                    title: 'Trip Forecasting',
                    content: 'Plan future trips and see their impact on compliance before booking. Essential for travel planning.',
                    position: 'top',
                    action: 'highlight'
                }
            ]
        });

        // Compliance Planning
        this.tutorials.set('compliance-planning', {
            id: 'compliance-planning',
            title: 'Compliance Planning',
            description: 'Learn how to plan and monitor EU travel compliance',
            steps: [
                {
                    target: '[href*="what_if_scenario"]',
                    title: 'What-If Scenarios',
                    content: 'Test different travel scenarios to see their impact on compliance. Perfect for planning future trips.',
                    position: 'right',
                    action: 'highlight'
                },
                {
                    target: '[href*="future_job_alerts"]',
                    title: 'Future Job Alerts',
                    content: 'View employees who may face compliance issues with planned future travel. Proactive risk management.',
                    position: 'right',
                    action: 'highlight'
                },
                {
                    target: '[href*="calendar"]',
                    title: 'Calendar View',
                    content: 'Visual timeline of all employee trips. Color-coded by risk level with hover details for easy planning.',
                    position: 'right',
                    action: 'highlight'
                },
                {
                    target: '.compliance-indicator, .risk-indicator',
                    title: 'Compliance Indicators',
                    content: 'Real-time compliance status for each employee. Green = Safe, Amber = Caution, Red = At Risk.',
                    position: 'left',
                    action: 'highlight'
                }
            ]
        });

        // Data Management
        this.tutorials.set('data-management', {
            id: 'data-management',
            title: 'Data Management',
            description: 'Export, import, and manage your travel data',
            steps: [
                {
                    target: '.export-button, [href*="export"]',
                    title: 'Data Export',
                    content: 'Export data in various formats (CSV, PDF) for reporting, compliance, and record-keeping.',
                    position: 'left',
                    action: 'highlight'
                },
                {
                    target: '[href*="import"]',
                    title: 'Data Import',
                    content: 'Import trip data from Excel files or other systems. Supports bulk data entry and validation.',
                    position: 'right',
                    action: 'highlight'
                },
                {
                    target: '[href*="privacy"]',
                    title: 'Privacy Tools',
                    content: 'GDPR-compliant data management tools. Export personal data, manage consent, and ensure compliance.',
                    position: 'right',
                    action: 'highlight'
                },
                {
                    target: '.backup-button, [href*="backup"]',
                    title: 'Data Backup',
                    content: 'Create and manage data backups. Essential for data security and disaster recovery.',
                    position: 'left',
                    action: 'highlight'
                }
            ]
        });
    }

    bindEvents() {
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (this.isActive) {
                if (e.key === 'Escape') {
                    this.endTutorial();
                } else if (e.key === 'ArrowRight' || e.key === 'Enter') {
                    e.preventDefault();
                    this.nextStep();
                } else if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    this.previousStep();
                }
            }
        });

        // Click outside to close
        this.overlay.addEventListener('click', () => {
            this.endTutorial();
        });
    }

    startTutorial(tutorialId) {
        const tutorial = this.tutorials.get(tutorialId);
        if (!tutorial) {
            console.warn(`Tutorial not found: ${tutorialId}`);
            return;
        }

        this.currentTutorial = tutorial;
        this.currentStep = 0;
        this.isActive = true;

        this.overlay.style.display = 'block';
        this.showStep();
    }

    showStep() {
        if (!this.currentTutorial || this.currentStep >= this.currentTutorial.steps.length) {
            this.endTutorial();
            return;
        }

        const step = this.currentTutorial.steps[this.currentStep];
        const targetElement = document.querySelector(step.target);

        if (!targetElement) {
            console.warn(`Tutorial step target not found: ${step.target}`);
            this.currentStep++;
            setTimeout(() => this.showStep(), 100);
            return;
        }

        this.highlightElement(targetElement, step);
        this.showTourPopup(targetElement, step);
    }

    highlightElement(element, step) {
        // Remove existing highlights
        document.querySelectorAll('.tutorial-highlight').forEach(el => {
            el.classList.remove('tutorial-highlight');
            el.style.cssText = el.style.cssText.replace(/position:\s*relative[^;]*;?/g, '');
            el.style.cssText = el.style.cssText.replace(/z-index:\s*\d+[^;]*;?/g, '');
            el.style.cssText = el.style.cssText.replace(/box-shadow:[^;]*;?/g, '');
            el.style.cssText = el.style.cssText.replace(/border-radius:[^;]*;?/g, '');
        });

        // Add highlight to target element
        element.classList.add('tutorial-highlight');
        element.style.cssText += `
            position: relative;
            z-index: 10000;
            box-shadow: 0 0 0 4px #4C739F, 0 0 0 8px rgba(76, 115, 159, 0.3);
            border-radius: 8px;
        `;

        // Scroll element into view
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    showTourPopup(targetElement, step) {
        const rect = targetElement.getBoundingClientRect();
        const position = this.calculatePopupPosition(rect, step.position);

        this.tourElement.innerHTML = `
            <div style="padding: 24px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
                    <div>
                        <h3 style="margin: 0 0 4px 0; color: #1f2937; font-size: 18px; font-weight: 600;">
                            ${step.title}
                        </h3>
                        <div style="color: #6b7280; font-size: 14px;">
                            Step ${this.currentStep + 1} of ${this.currentTutorial.steps.length}
                        </div>
                    </div>
                    <button onclick="interactiveTutorials.endTutorial()" style="
                        background: none;
                        border: none;
                        font-size: 20px;
                        cursor: pointer;
                        color: #9ca3af;
                        padding: 4px;
                        line-height: 1;
                    ">×</button>
                </div>
                
                <div style="color: #4b5563; line-height: 1.6; margin-bottom: 20px; font-size: 15px;">
                    ${step.content}
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; gap: 8px;">
                        ${this.currentStep > 0 ? `
                            <button onclick="interactiveTutorials.previousStep()" style="
                                background: #f3f4f6;
                                color: #374151;
                                border: 1px solid #e5e7eb;
                                padding: 8px 16px;
                                border-radius: 6px;
                                cursor: pointer;
                                font-size: 14px;
                                transition: all 0.2s;
                            " onmouseover="this.style.backgroundColor='#e5e7eb'" onmouseout="this.style.backgroundColor='#f3f4f6'">
                                Previous
                            </button>
                        ` : ''}
                        <button onclick="interactiveTutorials.endTutorial()" style="
                            background: #f3f4f6;
                            color: #374151;
                            border: 1px solid #e5e7eb;
                            padding: 8px 16px;
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 14px;
                            transition: all 0.2s;
                        " onmouseover="this.style.backgroundColor='#e5e7eb'" onmouseout="this.style.backgroundColor='#f3f4f6'">
                            Skip Tour
                        </button>
                    </div>
                    
                    <button onclick="interactiveTutorials.nextStep()" style="
                        background: #4C739F;
                        color: white;
                        border: none;
                        padding: 8px 20px;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 14px;
                        font-weight: 500;
                        transition: all 0.2s;
                    " onmouseover="this.style.backgroundColor='#5B6C8F'" onmouseout="this.style.backgroundColor='#4C739F'">
                        ${this.currentStep === this.currentTutorial.steps.length - 1 ? 'Finish' : 'Next'}
                    </button>
                </div>
            </div>
        `;

        this.tourElement.style.left = `${position.x}px`;
        this.tourElement.style.top = `${position.y}px`;
        this.tourElement.style.opacity = '1';
        this.tourElement.style.visibility = 'visible';
    }

    calculatePopupPosition(rect, position) {
        const margin = 20;
        const popupWidth = 400;
        const popupHeight = 200;
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

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
        x = Math.max(margin, Math.min(x, viewportWidth - popupWidth - margin));
        y = Math.max(margin, Math.min(y, viewportHeight - popupHeight - margin));

        return { x, y };
    }

    nextStep() {
        this.currentStep++;
        this.showStep();
    }

    previousStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep();
        }
    }

    endTutorial() {
        this.isActive = false;
        this.currentTutorial = null;
        this.currentStep = 0;

        // Clean up highlights
        document.querySelectorAll('.tutorial-highlight').forEach(el => {
            el.classList.remove('tutorial-highlight');
            el.style.cssText = el.style.cssText.replace(/position:\s*relative[^;]*;?/g, '');
            el.style.cssText = el.style.cssText.replace(/z-index:\s*\d+[^;]*;?/g, '');
            el.style.cssText = el.style.cssText.replace(/box-shadow:[^;]*;?/g, '');
            el.style.cssText = el.style.cssText.replace(/border-radius:[^;]*;?/g, '');
        });

        // Hide overlay and tour
        this.overlay.style.display = 'none';
        this.tourElement.style.opacity = '0';
        this.tourElement.style.visibility = 'hidden';

        // Mark tutorial as completed
        if (this.currentTutorial) {
            localStorage.setItem(`tutorial-${this.currentTutorial.id}-completed`, 'true');
        }
    }

    showTutorialMenu() {
        const menu = document.createElement('div');
        menu.className = 'tutorial-menu';
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
                <h3 style="margin: 0; color: #1f2937;">Interactive Tutorials</h3>
                <button onclick="this.closest('.tutorial-menu').remove()" style="
                    background: none;
                    border: none;
                    font-size: 24px;
                    cursor: pointer;
                    color: #6b7280;
                ">×</button>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px;">
                ${Array.from(this.tutorials.values()).map(tutorial => `
                    <button onclick="interactiveTutorials.startTutorial('${tutorial.id}'); this.closest('.tutorial-menu').remove();" style="
                        background: #f8fafc;
                        border: 2px solid #e2e8f0;
                        border-radius: 8px;
                        padding: 16px;
                        cursor: pointer;
                        text-align: left;
                        transition: all 0.2s;
                    " onmouseover="this.style.borderColor='#4C739F'; this.style.backgroundColor='#f0f9ff'" onmouseout="this.style.borderColor='#e2e8f0'; this.style.backgroundColor='#f8fafc'">
                        <div style="font-weight: 600; margin-bottom: 4px; color: #1f2937;">${tutorial.title}</div>
                        <div style="color: #64748b; font-size: 14px; line-height: 1.4;">${tutorial.description}</div>
                    </button>
                `).join('')}
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

    isTutorialCompleted(tutorialId) {
        return localStorage.getItem(`tutorial-${tutorialId}-completed`) === 'true';
    }

    resetTutorial(tutorialId) {
        localStorage.removeItem(`tutorial-${tutorialId}-completed`);
    }

    resetAllTutorials() {
        this.tutorials.forEach((tutorial, id) => {
            this.resetTutorial(id);
        });
    }
}

// Initialize interactive tutorials when DOM is loaded
let interactiveTutorials;
document.addEventListener('DOMContentLoaded', function() {
    interactiveTutorials = new InteractiveTutorials();
    window.interactiveTutorials = interactiveTutorials;
    
    // Add tutorial menu button to help system
    if (window.helpSystem) {
        // Add tutorial menu to help system
        window.helpSystem.showTutorialMenu = () => interactiveTutorials.showTutorialMenu();
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = InteractiveTutorials;
}
