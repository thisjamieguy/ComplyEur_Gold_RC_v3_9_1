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

// Sidebar functionality
function initSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const toggleBtn = document.querySelector('.sidebar-toggle');
    
    
    if (!sidebar || !mainContent || !toggleBtn) return;
    
    // Check if sidebar should be collapsed by default on desktop
    const isDesktop = window.innerWidth >= 1024;
    const shouldCollapse = false; // no persistence
    
    if (isDesktop && shouldCollapse) {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('sidebar-collapsed');
    }
    
    toggleBtn.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('sidebar-collapsed');
        
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
        if (arrow) arrow.textContent = '↕️';
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
        error: '⚠️',
        warning: '⚠️',
        info: 'ℹ️',
        success: '✅'
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

// Progress indicator
function showProgress(container, message = 'Processing...') {
    const progressDiv = document.createElement('div');
    progressDiv.className = 'progress-container';
    progressDiv.innerHTML = `
        <div class="progress-bar" style="width: 0%"></div>
    `;
    
    const messageDiv = document.createElement('div');
    messageDiv.style.cssText = 'text-align: center; margin-top: 8px; color: #6b7280; font-size: 14px;';
    messageDiv.textContent = message;
    
    container.appendChild(progressDiv);
    container.appendChild(messageDiv);
    
    // Animate progress
    setTimeout(() => {
        const bar = progressDiv.querySelector('.progress-bar');
        bar.style.width = '100%';
    }, 100);
    
    return {
        update: (percent) => {
            const bar = progressDiv.querySelector('.progress-bar');
            bar.style.width = `${percent}%`;
        },
        complete: () => {
            const bar = progressDiv.querySelector('.progress-bar');
            bar.style.width = '100%';
            setTimeout(() => {
                progressDiv.remove();
                messageDiv.remove();
            }, 500);
        },
        remove: () => {
            progressDiv.remove();
            messageDiv.remove();
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

// Enhanced tooltip system
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
    
    document.body.appendChild(tooltip);
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
    
    setTimeout(() => tooltip.classList.add('show'), 10);
    
    e.target._tooltip = tooltip;
}

function hideTooltip(e) {
    if (e.target._tooltip) {
        e.target._tooltip.remove();
        delete e.target._tooltip;
    }
}

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

