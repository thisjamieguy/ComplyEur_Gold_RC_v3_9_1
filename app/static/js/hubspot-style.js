// HubSpot Style Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize sidebar functionality
    initSidebar();
    
    // Initialize mobile menu
    initMobileMenu();
    
    // Initialize modals
    initModals();
    
    // Initialize tooltips
    initTooltips();
});

// Also try to initialize when window loads (fallback)
window.addEventListener('load', function() {
    // Re-initialize sidebar if it wasn't initialized before
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.sidebar-toggle');
    if (sidebar && toggleBtn && !toggleBtn.hasAttribute('data-initialized')) {
        console.log('Re-initializing sidebar on window load');
        initSidebar();
    }
});

// Fallback: Direct event listener attachment
setTimeout(function() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const toggleBtn = document.querySelector('.sidebar-toggle');
    
    if (sidebar && mainContent && toggleBtn && !toggleBtn.hasAttribute('data-initialized')) {
        console.log('Fallback: Direct sidebar toggle setup');
        toggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Fallback sidebar toggle clicked');
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('sidebar-collapsed');
        });
        toggleBtn.setAttribute('data-initialized', 'true');
    }
}, 1000);

// Sidebar functionality
function initSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const toggleBtn = document.querySelector('.sidebar-toggle');
    
    console.log('Sidebar elements found:', {
        sidebar: !!sidebar,
        mainContent: !!mainContent,
        toggleBtn: !!toggleBtn
    });
    
    if (!sidebar || !mainContent || !toggleBtn) {
        console.error('Missing sidebar elements:', { sidebar, mainContent, toggleBtn });
        // Try alternative selectors
        const altToggleBtn = document.querySelector('button[aria-label="Toggle Sidebar"]');
        if (altToggleBtn) {
            console.log('Found toggle button with alternative selector');
            return initSidebarWithButton(sidebar, mainContent, altToggleBtn);
        }
        return;
    }
    
    initSidebarWithButton(sidebar, mainContent, toggleBtn);
}

function initSidebarWithButton(sidebar, mainContent, toggleBtn) {
    // Mark as initialized to prevent double initialization
    toggleBtn.setAttribute('data-initialized', 'true');
    
    // Check if sidebar should be collapsed by default on desktop
    const isDesktop = window.innerWidth >= 1024;
    const shouldCollapse = false; // no persistence
    
    if (isDesktop && shouldCollapse) {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('sidebar-collapsed');
    }
    
    toggleBtn.addEventListener('click', function(e) {
        e.preventDefault();
        console.log('Sidebar toggle clicked');
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('sidebar-collapsed');
        console.log('Sidebar collapsed:', sidebar.classList.contains('collapsed'));
        
        // No persistence of this preference
    });
    
    // Handle window resize
    window.addEventListener('resize', function() {
        const isMobile = window.innerWidth < 1024;
        
        if (isMobile) {
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('sidebar-collapsed');
        } else {
            const shouldCollapse = false;
            if (shouldCollapse) {
                sidebar.classList.add('collapsed');
                mainContent.classList.add('sidebar-collapsed');
            }
        }
    });
}

// Mobile menu functionality
function initMobileMenu() {
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.mobile-overlay');
    
    if (!mobileMenuBtn || !sidebar || !overlay) return;
    
    mobileMenuBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        sidebar.classList.add('open');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        document.body.style.position = 'fixed';
        document.body.style.width = '100%';
    });
    
    overlay.addEventListener('click', function() {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
        document.body.style.position = '';
        document.body.style.width = '';
    });
    
    // Close sidebar when clicking nav items on mobile
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            if (window.innerWidth < 1024) {
                sidebar.classList.remove('open');
                overlay.classList.remove('active');
                document.body.style.overflow = '';
                document.body.style.position = '';
                document.body.style.width = '';
            }
        });
    });
    
    // Close sidebar with ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
            document.body.style.overflow = '';
            document.body.style.position = '';
            document.body.style.width = '';
        }
    });
}

// Modal functionality
function initModals() {
    // Close modals when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            closeModal(e.target);
        }
    });
    
    // Close modals with escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal.active');
            if (activeModal) {
                closeModal(activeModal);
            }
        }
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modal) {
    if (typeof modal === 'string') {
        modal = document.getElementById(modal);
    }
    if (modal) {
        modal.classList.remove('active');
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// Tooltip functionality
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const text = e.target.getAttribute('data-tooltip');
    if (!text) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: #1f2937;
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        z-index: 1000;
        pointer-events: none;
        white-space: nowrap;
        opacity: 0;
        transition: opacity 0.2s;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
    
    setTimeout(() => tooltip.style.opacity = '1', 10);
    
    e.target._tooltip = tooltip;
}

function hideTooltip(e) {
    if (e.target._tooltip) {
        e.target._tooltip.remove();
        delete e.target._tooltip;
    }
}

// Utility functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        padding: 16px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        z-index: 3000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => notification.style.transform = 'translateX(0)', 10);
    
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Table sorting functionality
function sortTable(columnIndex, tableId = 'employeeTable') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.getElementsByTagName('tbody')[0];
    const rows = Array.from(tbody.rows);
    const header = table.getElementsByTagName('th')[columnIndex];
    
    // Get current sort direction
    const currentDirection = header.getAttribute('data-sort-direction') || 'none';
    const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
    
    // Reset all headers
    const headers = table.getElementsByTagName('th');
    for (let i = 0; i < headers.length; i++) {
        headers[i].setAttribute('data-sort-direction', 'none');
        const arrow = headers[i].querySelector('.sort-arrow');
        if (arrow) arrow.textContent = '↕';
    }
    
    // Set new direction
    header.setAttribute('data-sort-direction', newDirection);
    const arrow = header.querySelector('.sort-arrow');
    if (arrow) arrow.textContent = newDirection === 'asc' ? '↑' : '↓';
    
    // Sort rows
    rows.sort((a, b) => {
        const aVal = a.cells[columnIndex].textContent.trim();
        const bVal = b.cells[columnIndex].textContent.trim();
        
        // Try to parse as numbers first
        const aNum = parseFloat(aVal);
        const bNum = parseFloat(bVal);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return newDirection === 'asc' ? aNum - bNum : bNum - aNum;
        }
        
        // Sort as strings
        return newDirection === 'asc' ? 
            aVal.localeCompare(bVal) : 
            bVal.localeCompare(aVal);
    });
    
    // Rebuild table
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

// View toggle functionality
function showTableView() {
    const tableView = document.getElementById('tableView');
    const cardView = document.getElementById('cardView');
    const tableBtn = document.getElementById('tableBtn');
    const cardsBtn = document.getElementById('cardsBtn');
    
    if (tableView) tableView.style.display = 'block';
    if (cardView) cardView.style.display = 'none';
    if (tableBtn) {
        tableBtn.className = 'btn btn-primary btn-sm';
        cardsBtn.className = 'btn btn-outline btn-sm';
    }
}

function showCardView() {
    const tableView = document.getElementById('tableView');
    const cardView = document.getElementById('cardView');
    const tableBtn = document.getElementById('tableBtn');
    const cardsBtn = document.getElementById('cardsBtn');
    
    if (tableView) tableView.style.display = 'none';
    if (cardView) cardView.style.display = 'grid';
    if (tableBtn) {
        tableBtn.className = 'btn btn-outline btn-sm';
        cardsBtn.className = 'btn btn-primary btn-sm';
    }
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('error');
            isValid = false;
        } else {
            input.classList.remove('error');
        }
    });
    
    return isValid;
}

// ===========================================
// PHASE 1 USABILITY FIXES - ENHANCED JAVASCRIPT
// ===========================================

// Enhanced notification system
function showNotification(message, type = 'info', options = {}) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    
    const iconMap = {
        error: '⚠',
        warning: '⚠',
        info: 'ℹ',
        success: '✓'
    };
    
    notification.innerHTML = `
        <div class="alert-icon">${iconMap[type] || iconMap.info}</div>
        <div class="alert-content">
            ${options.title ? `<div class="alert-title">${options.title}</div>` : ''}
            <div>${message}</div>
        </div>
        <button class="alert-dismiss" onclick="this.parentElement.remove()">×</button>
    `;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 3000;
        max-width: 400px;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.style.transform = 'translateX(0)', 10);
    
    // Auto-dismiss after delay
    const delay = options.delay || 5000;
    if (delay > 0) {
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        }, delay);
    }
}

// Enhanced confirmation dialog
function confirmAction(options) {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay active';
        modal.innerHTML = `
            <div class="modal-container">
                <div class="modal-header">
                    <h3 class="modal-title">${options.title || 'Confirm Action'}</h3>
                </div>
                <div class="modal-body">
                    <p>${options.message}</p>
                    ${options.details ? `<div class="alert alert-warning" style="margin-top: 16px;">${options.details}</div>` : ''}
                    ${options.requireText ? `
                        <div class="form-group" style="margin-top: 20px;">
                            <label class="form-label">Type "${options.requireText}" to confirm:</label>
                            <input type="text" id="confirmText" class="form-input" placeholder="${options.requireText}">
                        </div>
                    ` : ''}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline" onclick="closeConfirmModal(false)">Cancel</button>
                    <button type="button" class="btn ${options.danger ? 'btn-danger' : 'btn-primary'}" 
                            id="confirmBtn" onclick="closeConfirmModal(true)" 
                            ${options.requireText ? 'disabled' : ''}>
                        ${options.confirmText || 'Confirm'}
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        document.body.style.overflow = 'hidden';
        
        // Handle text confirmation
        if (options.requireText) {
            const textInput = modal.querySelector('#confirmText');
            const confirmBtn = modal.querySelector('#confirmBtn');
            
            textInput.addEventListener('input', function() {
                confirmBtn.disabled = this.value !== options.requireText;
            });
            
            textInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !confirmBtn.disabled) {
                    closeConfirmModal(true);
                }
            });
            
            textInput.focus();
        }
        
        // Store resolve function globally for the close function
        window._confirmResolve = resolve;
    });
}

function closeConfirmModal(confirmed) {
    const modal = document.querySelector('.modal-overlay.active');
    if (modal) {
        modal.remove();
        document.body.style.overflow = '';
        if (window._confirmResolve) {
            window._confirmResolve(confirmed);
            delete window._confirmResolve;
        }
    }
}

// Enhanced form validation
function validateForm(form, options = {}) {
    const errors = [];
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    // Clear previous errors
    form.querySelectorAll('.form-error').forEach(error => error.remove());
    form.querySelectorAll('.form-input.error, .form-select.error').forEach(input => {
        input.classList.remove('error');
    });
    
    inputs.forEach(input => {
        const value = input.value.trim();
        const fieldName = input.getAttribute('name') || input.getAttribute('id') || 'field';
        
        // Required field validation
        if (!value) {
            errors.push(`${fieldName} is required`);
            showFieldError(input, `${fieldName} is required`);
            return;
        }
        
        // Email validation
        if (input.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                errors.push(`${fieldName} must be a valid email address`);
                showFieldError(input, `${fieldName} must be a valid email address`);
                return;
            }
        }
        
        // Date validation
        if (input.type === 'date' && value) {
            const date = new Date(value);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            if (options.minDate && date < new Date(options.minDate)) {
                errors.push(`${fieldName} must be after ${options.minDate}`);
                showFieldError(input, `${fieldName} must be after ${options.minDate}`);
                return;
            }
            
            if (options.maxDate && date > new Date(options.maxDate)) {
                errors.push(`${fieldName} must be before ${options.maxDate}`);
                showFieldError(input, `${fieldName} must be before ${options.maxDate}`);
                return;
            }
        }
        
        // Password validation
        if (input.type === 'password' && value) {
            if (value.length < 6) {
                errors.push(`${fieldName} must be at least 6 characters long`);
                showFieldError(input, `${fieldName} must be at least 6 characters long`);
                return;
            }
        }
        
        // Custom validation
        if (options.customValidation && options.customValidation[fieldName]) {
            const customError = options.customValidation[fieldName](value, input);
            if (customError) {
                errors.push(customError);
                showFieldError(input, customError);
                return;
            }
        }
    });
    
    // Date range validation
    if (options.dateRange) {
        const entryDate = form.querySelector('input[name="entry_date"]');
        const exitDate = form.querySelector('input[name="exit_date"]');
        
        if (entryDate && exitDate && entryDate.value && exitDate.value) {
            const entry = new Date(entryDate.value);
            const exit = new Date(exitDate.value);
            
            if (entry >= exit) {
                errors.push('Entry date must be before exit date');
                showFieldError(entryDate, 'Entry date must be before exit date');
                showFieldError(exitDate, 'Exit date must be after entry date');
            }
        }
    }
    
    return {
        isValid: errors.length === 0,
        errors: errors
    };
}

function showFieldError(input, message) {
    input.classList.add('error');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'form-error';
    errorDiv.textContent = message;
    
    const formGroup = input.closest('.form-group');
    if (formGroup) {
        formGroup.appendChild(errorDiv);
    }
}

// Enhanced Progress Indicator System
function showProgress(container, options = {}) {
    const {
        message = 'Processing...',
        type = 'bar', // 'bar', 'spinner', 'dots'
        showPercentage = true,
        indeterminate = false,
        color = '#3b82f6'
    } = options;
    
    const progressDiv = document.createElement('div');
    progressDiv.className = 'progress-container';
    progressDiv.style.cssText = `
        position: relative;
        background: #f8fafc;
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
        border: 1px solid #e2e8f0;
    `;
    
    const messageDiv = document.createElement('div');
    messageDiv.style.cssText = 'text-align: center; margin-bottom: 12px; color: #374151; font-size: 14px; font-weight: 500;';
    messageDiv.textContent = message;
    
    let progressElement;
    
    if (type === 'bar') {
        progressElement = document.createElement('div');
        progressElement.className = 'progress-bar-container';
        progressElement.style.cssText = `
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        `;
        
        const bar = document.createElement('div');
        bar.className = 'progress-bar';
        bar.style.cssText = `
            height: 100%;
            background: ${color};
            width: ${indeterminate ? '30%' : '0%'};
            border-radius: 4px;
            transition: width 0.3s ease;
            position: relative;
        `;
        
        if (indeterminate) {
            bar.style.animation = 'progressIndeterminate 2s infinite linear';
        }
        
        progressElement.appendChild(bar);
    } else if (type === 'spinner') {
        progressElement = document.createElement('div');
        progressElement.className = 'progress-spinner';
        progressElement.style.cssText = `
            width: 40px;
            height: 40px;
            border: 4px solid #e2e8f0;
            border-top: 4px solid ${color};
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        `;
    } else if (type === 'dots') {
        progressElement = document.createElement('div');
        progressElement.className = 'progress-dots';
        progressElement.style.cssText = `
            display: flex;
            justify-content: center;
            gap: 4px;
        `;
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.style.cssText = `
                width: 8px;
                height: 8px;
                background: ${color};
                border-radius: 50%;
                animation: progressDots 1.4s infinite ease-in-out;
                animation-delay: ${i * 0.16}s;
            `;
            progressElement.appendChild(dot);
        }
    }
    
    const percentageDiv = showPercentage ? document.createElement('div') : null;
    if (percentageDiv) {
        percentageDiv.className = 'progress-percentage';
        percentageDiv.style.cssText = 'text-align: center; margin-top: 8px; color: #6b7280; font-size: 12px; font-weight: 500;';
        percentageDiv.textContent = '0%';
    }
    
    progressDiv.appendChild(messageDiv);
    progressDiv.appendChild(progressElement);
    if (percentageDiv) progressDiv.appendChild(percentageDiv);
    
    container.appendChild(progressDiv);
    
    // Animate progress for bar type
    if (type === 'bar' && !indeterminate) {
        setTimeout(() => {
            const bar = progressElement.querySelector('.progress-bar');
            bar.style.width = '100%';
        }, 100);
    }
    
    return {
        update: (percent) => {
            if (type === 'bar' && !indeterminate) {
                const bar = progressElement.querySelector('.progress-bar');
                bar.style.width = `${Math.min(100, Math.max(0, percent))}%`;
            }
            if (percentageDiv) {
                percentageDiv.textContent = `${Math.min(100, Math.max(0, Math.round(percent)))}%`;
            }
        },
        setMessage: (newMessage) => {
            messageDiv.textContent = newMessage;
        },
        complete: () => {
            if (type === 'bar' && !indeterminate) {
                const bar = progressElement.querySelector('.progress-bar');
                bar.style.width = '100%';
            }
            if (percentageDiv) {
                percentageDiv.textContent = '100%';
            }
            setTimeout(() => {
                progressDiv.remove();
            }, 1000);
        },
        remove: () => {
            progressDiv.remove();
        }
    };
}

// Global progress overlay for page-level operations
function showGlobalProgress(message = 'Loading...', options = {}) {
    const overlay = document.createElement('div');
    overlay.className = 'global-progress-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 4000;
        backdrop-filter: blur(4px);
    `;
    
    const content = document.createElement('div');
    content.style.cssText = `
        text-align: center;
        background: white;
        padding: 32px;
        border-radius: 12px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        max-width: 400px;
        width: 90%;
    `;
    
    const spinner = document.createElement('div');
    spinner.style.cssText = `
        width: 48px;
        height: 48px;
        border: 4px solid #e2e8f0;
        border-top: 4px solid #3b82f6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 0 auto 16px;
    `;
    
    const messageEl = document.createElement('div');
    messageEl.style.cssText = 'color: #374151; font-size: 16px; font-weight: 500;';
    messageEl.textContent = message;
    
    content.appendChild(spinner);
    content.appendChild(messageEl);
    overlay.appendChild(content);
    document.body.appendChild(overlay);
    
    return {
        setMessage: (newMessage) => {
            messageEl.textContent = newMessage;
        },
        remove: () => {
            overlay.remove();
        }
    };
}

// Loading state management
function setLoadingState(element, loading = true, text = 'Loading...') {
    if (loading) {
        element.disabled = true;
        element.dataset.originalText = element.textContent;
        element.innerHTML = `<span class="loading-spinner"></span> ${text}`;
    } else {
        element.disabled = false;
        element.textContent = element.dataset.originalText || element.textContent;
        delete element.dataset.originalText;
    }
}

// File upload validation
function validateFileUpload(input, options = {}) {
    const file = input.files[0];
    const errors = [];
    
    if (!file) {
        return { isValid: false, errors: ['Please select a file'] };
    }
    
    // File type validation
    if (options.allowedTypes && options.allowedTypes.length > 0) {
        const fileExtension = file.name.split('.').pop().toLowerCase();
        if (!options.allowedTypes.includes(fileExtension)) {
            errors.push(`File must be one of: ${options.allowedTypes.join(', ')}`);
        }
    }
    
    // File size validation
    if (options.maxSize) {
        const maxSizeBytes = options.maxSize * 1024 * 1024; // Convert MB to bytes
        if (file.size > maxSizeBytes) {
            errors.push(`File size must be less than ${options.maxSize}MB`);
        }
    }
    
    return {
        isValid: errors.length === 0,
        errors: errors,
        file: file
    };
}

// Enhanced tooltip system with contextual help
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip], [data-help]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
        element.addEventListener('focus', showTooltip);
        element.addEventListener('blur', hideTooltip);
    });
    
    // Add help icons to form fields
    addHelpIcons();
}

function showTooltip(e) {
    const text = e.target.getAttribute('data-tooltip') || e.target.getAttribute('data-help');
    if (!text) return;
    
    // Don't show tooltip if there's already one visible
    if (e.target._tooltip) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip tooltip-enhanced';
    
    // Check if it's a help tooltip (more detailed)
    const isHelp = e.target.hasAttribute('data-help');
    const title = e.target.getAttribute('data-help-title') || '';
    
    if (isHelp && title) {
        tooltip.innerHTML = `
            <div class="tooltip-header">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
                <strong>${title}</strong>
            </div>
            <div class="tooltip-content">${text}</div>
        `;
    } else {
        tooltip.textContent = text;
    }
    
    document.body.appendChild(tooltip);
    
    // Position tooltip
    const rect = e.target.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
    let top = rect.top - tooltipRect.height - 8;
    
    // Adjust if tooltip goes off screen
    if (left < 8) left = 8;
    if (left + tooltipRect.width > viewportWidth - 8) {
        left = viewportWidth - tooltipRect.width - 8;
    }
    if (top < 8) {
        // Show below element instead
        top = rect.bottom + 8;
    }
    
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
    
    // Add arrow pointing to element
    const arrow = document.createElement('div');
    arrow.className = 'tooltip-arrow';
    if (top > rect.bottom) {
        // Arrow pointing up (tooltip below)
        arrow.style.top = '-4px';
        arrow.style.left = '50%';
        arrow.style.transform = 'translateX(-50%)';
        arrow.style.borderBottom = '4px solid #1f2937';
        arrow.style.borderLeft = '4px solid transparent';
        arrow.style.borderRight = '4px solid transparent';
    } else {
        // Arrow pointing down (tooltip above)
        arrow.style.bottom = '-4px';
        arrow.style.left = '50%';
        arrow.style.transform = 'translateX(-50%)';
        arrow.style.borderTop = '4px solid #1f2937';
        arrow.style.borderLeft = '4px solid transparent';
        arrow.style.borderRight = '4px solid transparent';
    }
    tooltip.appendChild(arrow);
    
    setTimeout(() => tooltip.classList.add('show'), 10);
    
    e.target._tooltip = tooltip;
}

function hideTooltip(e) {
    if (e.target._tooltip) {
        e.target._tooltip.remove();
        delete e.target._tooltip;
    }
}

// Add help icons to form fields
function addHelpIcons() {
    const formGroups = document.querySelectorAll('.form-group');
    
    formGroups.forEach(group => {
        const label = group.querySelector('.form-label');
        const input = group.querySelector('.form-input, .form-select, textarea');
        
        if (label && input && !group.querySelector('.help-icon')) {
            // Check if this field has help content
            const helpText = getFieldHelpText(input);
            if (helpText) {
                const helpIcon = document.createElement('button');
                helpIcon.type = 'button';
                helpIcon.className = 'help-icon';
                helpIcon.setAttribute('data-help', helpText);
                helpIcon.setAttribute('data-help-title', label.textContent);
                helpIcon.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                `;
                helpIcon.title = 'Click for help';
                
                // Position help icon
                helpIcon.style.cssText = `
                    position: absolute;
                    right: 8px;
                    top: 50%;
                    transform: translateY(-50%);
                    background: none;
                    border: none;
                    color: #6b7280;
                    cursor: pointer;
                    padding: 4px;
                    border-radius: 50%;
                    transition: all 0.2s;
                    z-index: 10;
                `;
                
                // Make input container relative
                const inputContainer = input.parentElement;
                if (inputContainer) {
                    inputContainer.style.position = 'relative';
                    inputContainer.appendChild(helpIcon);
                }
            }
        }
    });
}

// Get help text for specific form fields
function getFieldHelpText(input) {
    const fieldName = input.name || input.id || '';
    const helpTexts = {
        'name': 'Enter the employee\'s full name as it appears on their passport.',
        'country_code': 'Select the EU country where the employee will be traveling. Ireland is non-Schengen and has different rules.',
        'entry_date': 'The date the employee enters the EU country. This counts as day 1 of their stay.',
        'exit_date': 'The date the employee leaves the EU country. This is the last day counted in their stay.',
        'employee_id': 'Select the employee for this trip. You can add new employees from the dashboard.',
        'new_password': 'Choose a strong password with at least 6 characters. This will be used to access the admin panel.',
        'current_password': 'Enter your current password to confirm this change.',
        'confirm_password': 'Re-enter the new password to confirm it\'s correct.'
    };
    
    return helpTexts[fieldName] || '';
}

// User Preferences and Customization System
class UserPreferences {
    constructor() {
        this.prefs = this.loadPreferences();
        this.init();
    }
    
    init() {
        this.applyPreferences();
        // Settings panel now handled by admin dropdown menu
    }
    
    loadPreferences() {
        const defaultPrefs = {
            theme: 'light',
            sidebarCollapsed: false,
            defaultView: 'table', // 'table' or 'card'
            itemsPerPage: 25,
            autoRefresh: false,
            refreshInterval: 30, // seconds
            showTooltips: true,
            compactMode: false,
            colorScheme: 'default', // 'default', 'high-contrast', 'colorblind-friendly'
            animations: true,
            soundEffects: false
        };
        
        try {
            const stored = localStorage.getItem('euTrackerPreferences');
            return stored ? { ...defaultPrefs, ...JSON.parse(stored) } : defaultPrefs;
        } catch (e) {
            console.warn('Failed to load user preferences:', e);
            return defaultPrefs;
        }
    }
    
    savePreferences() {
        try {
            localStorage.setItem('euTrackerPreferences', JSON.stringify(this.prefs));
            this.applyPreferences();
            showNotification('Preferences saved successfully', 'success');
        } catch (e) {
            console.error('Failed to save preferences:', e);
            showNotification('Failed to save preferences', 'error');
        }
    }
    
    applyPreferences() {
        // Apply theme
        document.body.setAttribute('data-theme', this.prefs.theme);
        
        // Apply sidebar state
        if (this.prefs.sidebarCollapsed) {
            document.querySelector('.sidebar')?.classList.add('collapsed');
            document.querySelector('.main-content')?.classList.add('sidebar-collapsed');
        }
        
        // Apply view preference
        if (this.prefs.defaultView === 'card') {
            const cardView = document.getElementById('cardView');
            const tableView = document.getElementById('tableView');
            if (cardView && tableView) {
                cardView.style.display = 'grid';
                tableView.style.display = 'none';
                // Update button states
                const tableBtn = document.getElementById('tableBtn');
                const cardsBtn = document.getElementById('cardsBtn');
                if (tableBtn && cardsBtn) {
                    tableBtn.className = 'btn btn-outline btn-sm';
                    cardsBtn.className = 'btn btn-primary btn-sm';
                }
            }
        }
        
        // Apply compact mode
        if (this.prefs.compactMode) {
            document.body.classList.add('compact-mode');
        } else {
            document.body.classList.remove('compact-mode');
        }
        
        // Apply color scheme
        document.body.setAttribute('data-color-scheme', this.prefs.colorScheme);
        
        // Apply animations
        if (!this.prefs.animations) {
            document.body.classList.add('no-animations');
        } else {
            document.body.classList.remove('no-animations');
        }
    }
    
    createSettingsPanel() {
        // Settings button removed - now handled by admin dropdown menu
        // No longer creating standalone settings button in topbar
    }
    
    openSettingsModal() {
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 600px;">
                <div class="modal-header">
                    <h3 class="modal-title">User Preferences</h3>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="settings-grid">
                        <div class="setting-group">
                            <h4>Appearance</h4>
                            <div class="setting-item">
                                <label class="setting-label">Theme</label>
                                <select id="themeSelect" class="form-select">
                                    <option value="light" ${this.prefs.theme === 'light' ? 'selected' : ''}>Light</option>
                                    <option value="dark" ${this.prefs.theme === 'dark' ? 'selected' : ''}>Dark</option>
                                    <option value="auto" ${this.prefs.theme === 'auto' ? 'selected' : ''}>Auto</option>
                                </select>
                            </div>
                            <div class="setting-item">
                                <label class="setting-label">Color Scheme</label>
                                <select id="colorSchemeSelect" class="form-select">
                                    <option value="default" ${this.prefs.colorScheme === 'default' ? 'selected' : ''}>Default</option>
                                    <option value="high-contrast" ${this.prefs.colorScheme === 'high-contrast' ? 'selected' : ''}>High Contrast</option>
                                    <option value="colorblind-friendly" ${this.prefs.colorScheme === 'colorblind-friendly' ? 'selected' : ''}>Colorblind Friendly</option>
                                </select>
                            </div>
                            <div class="setting-item">
                                <label class="setting-label">
                                    <input type="checkbox" id="compactModeCheck" ${this.prefs.compactMode ? 'checked' : ''}>
                                    Compact Mode
                                </label>
                            </div>
                        </div>
                        
                        <div class="setting-group">
                            <h4>Interface</h4>
                            <div class="setting-item">
                                <label class="setting-label">Default View</label>
                                <select id="defaultViewSelect" class="form-select">
                                    <option value="table" ${this.prefs.defaultView === 'table' ? 'selected' : ''}>Table View</option>
                                    <option value="card" ${this.prefs.defaultView === 'card' ? 'selected' : ''}>Card View</option>
                                </select>
                            </div>
                            <div class="setting-item">
                                <label class="setting-label">Items Per Page</label>
                                <select id="itemsPerPageSelect" class="form-select">
                                    <option value="10" ${this.prefs.itemsPerPage === 10 ? 'selected' : ''}>10</option>
                                    <option value="25" ${this.prefs.itemsPerPage === 25 ? 'selected' : ''}>25</option>
                                    <option value="50" ${this.prefs.itemsPerPage === 50 ? 'selected' : ''}>50</option>
                                    <option value="100" ${this.prefs.itemsPerPage === 100 ? 'selected' : ''}>100</option>
                                </select>
                            </div>
                            <div class="setting-item">
                                <label class="setting-label">
                                    <input type="checkbox" id="showTooltipsCheck" ${this.prefs.showTooltips ? 'checked' : ''}>
                                    Show Tooltips
                                </label>
                            </div>
                        </div>
                        
                        <div class="setting-group">
                            <h4>Behavior</h4>
                            <div class="setting-item">
                                <label class="setting-label">
                                    <input type="checkbox" id="autoRefreshCheck" ${this.prefs.autoRefresh ? 'checked' : ''}>
                                    Auto Refresh
                                </label>
                            </div>
                            <div class="setting-item" id="refreshIntervalItem" style="${this.prefs.autoRefresh ? '' : 'display: none;'}">
                                <label class="setting-label">Refresh Interval (seconds)</label>
                                <input type="number" id="refreshIntervalInput" class="form-input" value="${this.prefs.refreshInterval}" min="10" max="300">
                            </div>
                            <div class="setting-item">
                                <label class="setting-label">
                                    <input type="checkbox" id="animationsCheck" ${this.prefs.animations ? 'checked' : ''}>
                                    Enable Animations
                                </label>
                            </div>
                            <div class="setting-item">
                                <label class="setting-label">
                                    <input type="checkbox" id="soundEffectsCheck" ${this.prefs.soundEffects ? 'checked' : ''}>
                                    Sound Effects
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-outline" onclick="this.closest('.modal').remove()">Cancel</button>
                    <button class="btn btn-primary" onclick="userPrefs.saveSettings()">Save Settings</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Add event listeners
        document.getElementById('autoRefreshCheck').addEventListener('change', function() {
            const intervalItem = document.getElementById('refreshIntervalItem');
            intervalItem.style.display = this.checked ? 'block' : 'none';
        });
    }
    
    saveSettings() {
        // Update preferences from form
        this.prefs.theme = document.getElementById('themeSelect').value;
        this.prefs.colorScheme = document.getElementById('colorSchemeSelect').value;
        this.prefs.compactMode = document.getElementById('compactModeCheck').checked;
        this.prefs.defaultView = document.getElementById('defaultViewSelect').value;
        this.prefs.itemsPerPage = parseInt(document.getElementById('itemsPerPageSelect').value);
        this.prefs.showTooltips = document.getElementById('showTooltipsCheck').checked;
        this.prefs.autoRefresh = document.getElementById('autoRefreshCheck').checked;
        this.prefs.refreshInterval = parseInt(document.getElementById('refreshIntervalInput').value);
        this.prefs.animations = document.getElementById('animationsCheck').checked;
        this.prefs.soundEffects = document.getElementById('soundEffectsCheck').checked;
        
        this.savePreferences();
        
        // Close modal
        document.querySelector('.modal.active').remove();
    }
}

// Initialize user preferences
let userPrefs;
document.addEventListener('DOMContentLoaded', function() {
    userPrefs = new UserPreferences();
});

// Initialize enhanced functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize existing functionality
    initSidebar();
    initMobileMenu();
    initModals();
    initTooltips();
    
    // Add form validation to all forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const validation = validateForm(form, {
                dateRange: form.querySelector('input[name="entry_date"]') && form.querySelector('input[name="exit_date"]')
            });
            
            if (!validation.isValid) {
                e.preventDefault();
                showNotification(validation.errors.join(', '), 'error');
                return false;
            }
        });
    });
    
    // Add real-time validation to inputs
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.hasAttribute('required') && !this.value.trim()) {
                showFieldError(this, 'This field is required');
            }
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('error') && this.value.trim()) {
                this.classList.remove('error');
                const errorDiv = this.parentNode.querySelector('.form-error');
                if (errorDiv) errorDiv.remove();
            }
        });
    });
});

