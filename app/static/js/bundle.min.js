// Utility Functions - EU Trip Tracker

/**
 * Date formatting utilities
 */
const DateUtils = {
    /**
     * Format date to DD-MM-YYYY format
     * @param {Date|string} date - Date object or date string
     * @returns {string} Formatted date string
     */
    formatDate(date) {
        if (!date) return '';
        
        const d = new Date(date);
        if (isNaN(d.getTime())) return '';
        
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const year = d.getFullYear();
        
        return `${day}-${month}-${year}`;
    },

    /**
     * Format date to YYYY-MM-DD format for input fields
     * @param {Date|string} date - Date object or date string
     * @returns {string} Formatted date string
     */
    formatDateForInput(date) {
        if (!date) return '';
        
        const d = new Date(date);
        if (isNaN(d.getTime())) return '';
        
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        
        return `${year}-${month}-${day}`;
    },

    /**
     * Parse DD-MM-YYYY format to Date object
     * @param {string} dateStr - Date string in DD-MM-YYYY format
     * @returns {Date|null} Date object or null if invalid
     */
    parseDate(dateStr) {
        if (!dateStr) return null;
        
        const parts = dateStr.split('-');
        if (parts.length !== 3) return null;
        
        const day = parseInt(parts[0], 10);
        const month = parseInt(parts[1], 10) - 1; // Months are 0-indexed
        const year = parseInt(parts[2], 10);
        
        const date = new Date(year, month, day);
        if (isNaN(date.getTime())) return null;
        
        return date;
    },

    /**
     * Get today's date in YYYY-MM-DD format
     * @returns {string} Today's date
     */
    today() {
        return this.formatDateForInput(new Date());
    },

    /**
     * Get date N days from today
     * @param {number} days - Number of days to add
     * @returns {string} Future date in YYYY-MM-DD format
     */
    daysFromToday(days) {
        const date = new Date();
        date.setDate(date.getDate() + days);
        return this.formatDateForInput(date);
    },

    /**
     * Check if date is in the future
     * @param {Date|string} date - Date to check
     * @returns {boolean} True if date is in the future
     */
    isFuture(date) {
        const d = new Date(date);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return d > today;
    },

    /**
     * Check if date is in the past
     * @param {Date|string} date - Date to check
     * @returns {boolean} True if date is in the past
     */
    isPast(date) {
        const d = new Date(date);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return d < today;
    },

    /**
     * Calculate days between two dates
     * @param {Date|string} startDate - Start date
     * @param {Date|string} endDate - End date
     * @returns {number} Number of days between dates
     */
    daysBetween(startDate, endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        const diffTime = Math.abs(end - start);
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1; // +1 to include both dates
    }
};

/**
 * Form validation utilities
 */
const ValidationUtils = {
    /**
     * Validate email format
     * @param {string} email - Email to validate
     * @returns {boolean} True if valid email
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    /**
     * Validate password strength
     * @param {string} password - Password to validate
     * @returns {object} Validation result with strength and message
     */
    validatePassword(password) {
        if (!password) {
            return { isValid: false, strength: 'none', message: 'Password is required' };
        }

        if (password.length < 6) {
            return { isValid: false, strength: 'weak', message: 'Password must be at least 6 characters' };
        }

        if (password.length < 8) {
            return { isValid: true, strength: 'weak', message: 'Weak password' };
        }

        if (password.length < 12) {
            return { isValid: true, strength: 'good', message: 'Good password' };
        }

        return { isValid: true, strength: 'strong', message: 'Strong password' };
    },

    /**
     * Validate date range (entry before exit)
     * @param {string} entryDate - Entry date
     * @param {string} exitDate - Exit date
     * @returns {object} Validation result
     */
    validateDateRange(entryDate, exitDate) {
        if (!entryDate || !exitDate) {
            return { isValid: false, message: 'Both dates are required' };
        }

        const entry = new Date(entryDate);
        const exit = new Date(exitDate);

        if (isNaN(entry.getTime()) || isNaN(exit.getTime())) {
            return { isValid: false, message: 'Invalid date format' };
        }

        if (entry >= exit) {
            return { isValid: false, message: 'Entry date must be before exit date' };
        }

        return { isValid: true, message: 'Valid date range' };
    },

    /**
     * Validate required field
     * @param {string} value - Field value
     * @param {string} fieldName - Name of the field
     * @returns {object} Validation result
     */
    validateRequired(value, fieldName) {
        if (!value || value.trim() === '') {
            return { isValid: false, message: `${fieldName} is required` };
        }
        return { isValid: true, message: 'Valid' };
    }
};

/**
 * UI utility functions
 */
const UIUtils = {
    /**
     * Show loading state on button
     * @param {HTMLElement} button - Button element
     * @param {boolean} loading - Whether to show loading state
     * @param {string} loadingText - Text to show while loading
     */
    setButtonLoading(button, loading, loadingText = 'Loading...') {
        if (!button) return;

        if (loading) {
            button.disabled = true;
            button.classList.add('btn-loading');
            button.setAttribute('data-original-text', button.textContent);
            button.textContent = loadingText;
        } else {
            button.disabled = false;
            button.classList.remove('btn-loading');
            const originalText = button.getAttribute('data-original-text');
            if (originalText) {
                button.textContent = originalText;
                button.removeAttribute('data-original-text');
            }
        }
    },

    /**
     * Show field error
     * @param {HTMLElement} field - Form field
     * @param {string} message - Error message
     */
    showFieldError(field, message) {
        if (!field) return;

        const formGroup = field.closest('.form-group');
        if (!formGroup) return;

        // Remove existing error
        this.clearFieldError(field);

        // Add error class
        formGroup.classList.add('error');

        // Add error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error';
        errorDiv.textContent = message;
        formGroup.appendChild(errorDiv);
    },

    /**
     * Clear field error
     * @param {HTMLElement} field - Form field
     */
    clearFieldError(field) {
        if (!field) return;

        const formGroup = field.closest('.form-group');
        if (!formGroup) return;

        formGroup.classList.remove('error');
        const errorDiv = formGroup.querySelector('.form-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    },

    /**
     * Show success state on field
     * @param {HTMLElement} field - Form field
     */
    showFieldSuccess(field) {
        if (!field) return;

        const formGroup = field.closest('.form-group');
        if (!formGroup) return;

        formGroup.classList.remove('error');
        formGroup.classList.add('success');
    },

    /**
     * Debounce function calls
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} Debounced function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function calls
     * @param {Function} func - Function to throttle
     * @param {number} limit - Time limit in milliseconds
     * @returns {Function} Throttled function
     */
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

/**
 * Storage utilities
 */
const StorageUtils = {
    /**
     * Save data to localStorage with error handling
     * @param {string} key - Storage key
     * @param {any} data - Data to store
     * @returns {boolean} Success status
     */
    save(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Failed to save to localStorage:', error);
            return false;
        }
    },

    /**
     * Load data from localStorage with error handling
     * @param {string} key - Storage key
     * @param {any} defaultValue - Default value if key doesn't exist
     * @returns {any} Stored data or default value
     */
    load(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Failed to load from localStorage:', error);
            return defaultValue;
        }
    },

    /**
     * Remove data from localStorage
     * @param {string} key - Storage key
     * @returns {boolean} Success status
     */
    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Failed to remove from localStorage:', error);
            return false;
        }
    }
};

/**
 * String utilities
 */
const StringUtils = {
    /**
     * Capitalize first letter of string
     * @param {string} str - String to capitalize
     * @returns {string} Capitalized string
     */
    capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    },

    /**
     * Truncate string to specified length
     * @param {string} str - String to truncate
     * @param {number} length - Maximum length
     * @param {string} suffix - Suffix to add if truncated
     * @returns {string} Truncated string
     */
    truncate(str, length, suffix = '...') {
        if (!str || str.length <= length) return str;
        return str.substring(0, length) + suffix;
    },

    /**
     * Escape HTML characters
     * @param {string} str - String to escape
     * @returns {string} Escaped string
     */
    escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
};

// Export utilities for use in other scripts
window.DateUtils = DateUtils;
window.ValidationUtils = ValidationUtils;
window.UIUtils = UIUtils;
window.StorageUtils = StorageUtils;
window.StringUtils = StringUtils;
// Comprehensive Form Validation - EU Trip Tracker

/**
 * Form validation system with real-time validation and error handling
 */
class FormValidator {
    constructor(form, options = {}) {
        this.form = form;
        this.options = {
            validateOnInput: true,
            validateOnBlur: true,
            showErrorsImmediately: true,
            ...options
        };
        this.errors = {};
        this.init();
    }

    init() {
        if (!this.form) return;

        // Add validation event listeners
        if (this.options.validateOnInput) {
            this.form.addEventListener('input', (e) => this.validateField(e.target));
        }
        
        if (this.options.validateOnBlur) {
            this.form.addEventListener('blur', (e) => this.validateField(e.target), true);
        }

        // Validate on form submit
        this.form.addEventListener('submit', (e) => {
            if (!this.validateForm()) {
                e.preventDefault();
                this.showFormErrors();
            }
        });
    }

    /**
     * Validate a single field
     * @param {HTMLElement} field - Field to validate
     * @returns {boolean} True if valid
     */
    validateField(field) {
        if (!field || !field.name) return true;

        const fieldName = field.name;
        const value = field.value.trim();
        const fieldType = field.type || 'text';
        const isRequired = field.hasAttribute('required');

        // Clear previous errors
        this.clearFieldError(field);

        // Required field validation
        if (isRequired && !value) {
            this.setFieldError(field, `${this.getFieldLabel(field)} is required`);
            return false;
        }

        // Skip further validation if field is empty and not required
        if (!value && !isRequired) {
            return true;
        }

        // Type-specific validation
        let isValid = true;
        let errorMessage = '';

        switch (fieldType) {
            case 'email':
                if (!ValidationUtils.isValidEmail(value)) {
                    isValid = false;
                    errorMessage = 'Please enter a valid email address';
                }
                break;

            case 'password':
                const passwordValidation = ValidationUtils.validatePassword(value);
                if (!passwordValidation.isValid) {
                    isValid = false;
                    errorMessage = passwordValidation.message;
                }
                break;

            case 'date':
                if (!this.isValidDate(value)) {
                    isValid = false;
                    errorMessage = 'Please enter a valid date';
                }
                break;

            case 'number':
                if (isNaN(value) || value === '') {
                    isValid = false;
                    errorMessage = 'Please enter a valid number';
                }
                break;
        }

        // Custom validation rules
        const customRules = this.getCustomValidationRules(field);
        for (const rule of customRules) {
            const result = rule(value, field);
            if (!result.isValid) {
                isValid = false;
                errorMessage = result.message;
                break;
            }
        }

        // Date range validation for trip forms
        if (fieldName === 'entry_date' || fieldName === 'exit_date') {
            const entryDate = this.form.querySelector('input[name="entry_date"]');
            const exitDate = this.form.querySelector('input[name="exit_date"]');
            
            if (entryDate && exitDate && entryDate.value && exitDate.value) {
                const rangeValidation = ValidationUtils.validateDateRange(entryDate.value, exitDate.value);
                if (!rangeValidation.isValid) {
                    isValid = false;
                    errorMessage = rangeValidation.message;
                }
            }
        }

        // Future date validation for completed trips
        if (fieldName === 'entry_date' && this.isCompletedTripForm()) {
            if (this.isFutureDate(value)) {
                isValid = false;
                errorMessage = 'Entry date cannot be in the future for completed trips';
            }
        }

        if (!isValid) {
            this.setFieldError(field, errorMessage);
        }

        return isValid;
    }

    /**
     * Validate entire form
     * @returns {boolean} True if form is valid
     */
    validateForm() {
        const fields = this.form.querySelectorAll('input, select, textarea');
        let isFormValid = true;

        this.errors = {};

        fields.forEach(field => {
            if (!this.validateField(field)) {
                isFormValid = false;
            }
        });

        return isFormValid;
    }

    /**
     * Set field error
     * @param {HTMLElement} field - Field element
     * @param {string} message - Error message
     */
    setFieldError(field, message) {
        const fieldName = field.name;
        this.errors[fieldName] = message;

        if (this.options.showErrorsImmediately) {
            UIUtils.showFieldError(field, message);
        }
    }

    /**
     * Clear field error
     * @param {HTMLElement} field - Field element
     */
    clearFieldError(field) {
        const fieldName = field.name;
        delete this.errors[fieldName];

        UIUtils.clearFieldError(field);
    }

    /**
     * Show all form errors
     */
    showFormErrors() {
        Object.keys(this.errors).forEach(fieldName => {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                UIUtils.showFieldError(field, this.errors[fieldName]);
            }
        });

        // Focus first error field
        const firstErrorField = this.form.querySelector('.form-group.error input, .form-group.error select, .form-group.error textarea');
        if (firstErrorField) {
            firstErrorField.focus();
        }
    }

    /**
     * Get field label
     * @param {HTMLElement} field - Field element
     * @returns {string} Field label
     */
    getFieldLabel(field) {
        const label = this.form.querySelector(`label[for="${field.id}"]`);
        if (label) {
            return label.textContent.replace('*', '').trim();
        }
        return field.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * Get custom validation rules for field
     * @param {HTMLElement} field - Field element
     * @returns {Array} Array of validation functions
     */
    getCustomValidationRules(field) {
        const rules = [];

        // Min length validation
        if (field.hasAttribute('minlength')) {
            const minLength = parseInt(field.getAttribute('minlength'));
            rules.push((value) => {
                if (value.length < minLength) {
                    return { isValid: false, message: `Must be at least ${minLength} characters` };
                }
                return { isValid: true };
            });
        }

        // Max length validation
        if (field.hasAttribute('maxlength')) {
            const maxLength = parseInt(field.getAttribute('maxlength'));
            rules.push((value) => {
                if (value.length > maxLength) {
                    return { isValid: false, message: `Must be no more than ${maxLength} characters` };
                }
                return { isValid: true };
            });
        }

        // Pattern validation
        if (field.hasAttribute('pattern')) {
            const pattern = new RegExp(field.getAttribute('pattern'));
            rules.push((value) => {
                if (!pattern.test(value)) {
                    return { isValid: false, message: 'Invalid format' };
                }
                return { isValid: true };
            });
        }

        return rules;
    }

    /**
     * Check if date is valid
     * @param {string} dateStr - Date string
     * @returns {boolean} True if valid date
     */
    isValidDate(dateStr) {
        const date = new Date(dateStr);
        return !isNaN(date.getTime());
    }

    /**
     * Check if date is in the future
     * @param {string} dateStr - Date string
     * @returns {boolean} True if future date
     */
    isFutureDate(dateStr) {
        const date = new Date(dateStr);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return date > today;
    }

    /**
     * Check if this is a completed trip form
     * @returns {boolean} True if completed trip form
     */
    isCompletedTripForm() {
        // Check for trip status indicators or form context
        return this.form.querySelector('input[name="trip_status"][value="completed"]') !== null ||
               this.form.classList.contains('completed-trip-form');
    }

    /**
     * Get validation summary
     * @returns {object} Validation summary
     */
    getValidationSummary() {
        return {
            isValid: Object.keys(this.errors).length === 0,
            errors: this.errors,
            errorCount: Object.keys(this.errors).length
        };
    }
}

/**
 * Duplicate detection system
 */
class DuplicateDetector {
    constructor() {
        this.trips = [];
        this.loadExistingTrips();
    }

    /**
     * Load existing trips from the page
     */
    loadExistingTrips() {
        const tripRows = document.querySelectorAll('#tripTableBody tr[data-trip-id]');
        this.trips = Array.from(tripRows).map(row => {
            const cells = row.cells;
            return {
                id: row.getAttribute('data-trip-id'),
                country: cells[0].textContent.trim(),
                entryDate: cells[1].textContent.trim(),
                exitDate: cells[2].textContent.trim(),
                employeeId: this.getEmployeeIdFromPage()
            };
        });
    }

    /**
     * Check for duplicate trip
     * @param {object} tripData - Trip data to check
     * @returns {object} Duplicate check result
     */
    checkDuplicate(tripData) {
        const { country, entryDate, exitDate, employeeId } = tripData;

        const duplicate = this.trips.find(trip => 
            trip.employeeId === employeeId &&
            trip.country === country &&
            trip.entryDate === DateUtils.formatDate(entryDate) &&
            trip.exitDate === DateUtils.formatDate(exitDate)
        );

        if (duplicate) {
            return {
                isDuplicate: true,
                message: `A trip to ${country} from ${entryDate} to ${exitDate} already exists`,
                duplicateTrip: duplicate
            };
        }

        return { isDuplicate: false };
    }

    /**
     * Get employee ID from current page
     * @returns {string} Employee ID
     */
    getEmployeeIdFromPage() {
        // Try to get from URL
        const urlMatch = window.location.pathname.match(/\/employee\/(\d+)/);
        if (urlMatch) {
            return urlMatch[1];
        }

        // Try to get from hidden input
        const employeeIdInput = document.querySelector('input[name="employee_id"]');
        if (employeeIdInput) {
            return employeeIdInput.value;
        }

        return null;
    }
}

/**
 * Real-time validation for specific form types
 */
class TripFormValidator extends FormValidator {
    constructor(form, options = {}) {
        super(form, options);
        this.duplicateDetector = new DuplicateDetector();
    }

    /**
     * Validate trip form with additional rules
     * @param {HTMLElement} field - Field to validate
     * @returns {boolean} True if valid
     */
    validateField(field) {
        const isValid = super.validateField(field);
        
        // Additional trip-specific validation
        if (field.name === 'country_display' || field.name === 'entry_date' || field.name === 'exit_date') {
            this.validateTripUniqueness();
        }

        return isValid;
    }

    /**
     * Validate trip uniqueness
     */
    validateTripUniqueness() {
        const countryInput = this.form.querySelector('input[name="country_display"]');
        const countryCodeInput = this.form.querySelector('input[name="country_code"]');
        const entryDateInput = this.form.querySelector('input[name="entry_date"]');
        const exitDateInput = this.form.querySelector('input[name="exit_date"]');

        if (!countryInput || !countryCodeInput || !entryDateInput || !exitDateInput) return;

        const country = countryInput.value;
        const entryDate = entryDateInput.value;
        const exitDate = exitDateInput.value;
        const employeeId = this.duplicateDetector.getEmployeeIdFromPage();

        if (country && entryDate && exitDate && employeeId) {
            const tripData = {
                country: country,
                entryDate: entryDate,
                exitDate: exitDate,
                employeeId: employeeId
            };

            const duplicateCheck = this.duplicateDetector.checkDuplicate(tripData);
            if (duplicateCheck.isDuplicate) {
                this.setFieldError(countryInput, duplicateCheck.message);
                return false;
            }
        }

        return true;
    }
}

/**
 * Initialize validation for all forms on page
 */
function initializeFormValidation() {
    // Initialize general form validation
    const forms = document.querySelectorAll('form[data-validate="true"]');
    forms.forEach(form => {
        new FormValidator(form);
    });

    // Initialize trip form validation
    const tripForms = document.querySelectorAll('form[data-trip-form="true"]');
    tripForms.forEach(form => {
        new TripFormValidator(form);
    });

    // Initialize employee form validation
    const employeeForms = document.querySelectorAll('form[data-employee-form="true"]');
    employeeForms.forEach(form => {
        new FormValidator(form);
    });
}

/**
 * Validate file upload
 * @param {HTMLElement} fileInput - File input element
 * @param {object} options - Validation options
 * @returns {object} Validation result
 */
function validateFileUpload(fileInput, options = {}) {
    const {
        allowedTypes = ['xlsx', 'xls'],
        maxSize = 10, // MB
        required = true
    } = options;

    const file = fileInput.files[0];

    if (required && !file) {
        return { isValid: false, errors: ['File is required'] };
    }

    if (!file) {
        return { isValid: true };
    }

    const errors = [];

    // Check file type
    const fileExtension = file.name.split('.').pop().toLowerCase();
    if (!allowedTypes.includes(fileExtension)) {
        errors.push(`File type not supported. Allowed types: ${allowedTypes.join(', ')}`);
    }

    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxSize) {
        errors.push(`File too large. Maximum size: ${maxSize}MB`);
    }

    return {
        isValid: errors.length === 0,
        errors: errors
    };
}

// Auto-initialize validation when DOM is ready
document.addEventListener('DOMContentLoaded', initializeFormValidation);

// Export for use in other scripts
window.FormValidator = FormValidator;
window.TripFormValidator = TripFormValidator;
window.DuplicateDetector = DuplicateDetector;
window.validateFileUpload = validateFileUpload;
// Toast Notification System - EU Trip Tracker

/**
 * Notification system for user feedback
 */
class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.container = null;
        this.init();
    }

    init() {
        // Create notification container
        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1100;
            pointer-events: none;
        `;
        document.body.appendChild(this.container);
    }

    /**
     * Show notification
     * @param {string} message - Notification message
     * @param {string} type - Notification type (success, error, warning, info)
     * @param {object} options - Additional options
     */
    show(message, type = 'info', options = {}) {
        const {
            duration = 5000,
            closable = true,
            action = null,
            persistent = false
        } = options;

        const notification = this.createNotification(message, type, {
            duration,
            closable,
            action,
            persistent
        });

        this.container.appendChild(notification);
        this.notifications.push(notification);

        // Trigger show animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        // Auto-remove after duration
        if (!persistent && duration > 0) {
            setTimeout(() => {
                this.remove(notification);
            }, duration);
        }

        return notification;
    }

    /**
     * Create notification element
     * @param {string} message - Notification message
     * @param {string} type - Notification type
     * @param {object} options - Notification options
     * @returns {HTMLElement} Notification element
     */
    createNotification(message, type, options) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const icon = this.getIcon(type);
        const actionButton = options.action ? this.createActionButton(options.action) : '';

        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">${icon}</div>
                <div class="notification-message">${message}</div>
                ${actionButton}
                ${options.closable ? '<button class="notification-close" aria-label="Close">&times;</button>' : ''}
            </div>
        `;

        // Add close functionality
        if (options.closable) {
            const closeBtn = notification.querySelector('.notification-close');
            closeBtn.addEventListener('click', () => this.remove(notification));
        }

        // Add action functionality
        if (options.action) {
            const actionBtn = notification.querySelector('.notification-action');
            actionBtn.addEventListener('click', options.action.handler);
        }

        return notification;
    }

    /**
     * Get icon for notification type
     * @param {string} type - Notification type
     * @returns {string} Icon HTML
     */
    getIcon(type) {
        const icons = {
            success: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>',
            error: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
            warning: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
            info: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
        };
        return icons[type] || icons.info;
    }

    /**
     * Create action button
     * @param {object} action - Action configuration
     * @returns {string} Action button HTML
     */
    createActionButton(action) {
        return `
            <button class="notification-action" type="button">
                ${action.text}
            </button>
        `;
    }

    /**
     * Remove notification
     * @param {HTMLElement} notification - Notification element
     */
    remove(notification) {
        if (!notification || !notification.parentNode) return;

        notification.classList.remove('show');
        notification.classList.add('hide');

        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            const index = this.notifications.indexOf(notification);
            if (index > -1) {
                this.notifications.splice(index, 1);
            }
        }, 300);
    }

    /**
     * Clear all notifications
     */
    clear() {
        this.notifications.forEach(notification => {
            this.remove(notification);
        });
    }

    /**
     * Show success notification
     * @param {string} message - Success message
     * @param {object} options - Additional options
     */
    success(message, options = {}) {
        return this.show(message, 'success', { duration: 4000, ...options });
    }

    /**
     * Show error notification
     * @param {string} message - Error message
     * @param {object} options - Additional options
     */
    error(message, options = {}) {
        return this.show(message, 'error', { duration: 6000, ...options });
    }

    /**
     * Show warning notification
     * @param {string} message - Warning message
     * @param {object} options - Additional options
     */
    warning(message, options = {}) {
        return this.show(message, 'warning', { duration: 5000, ...options });
    }

    /**
     * Show info notification
     * @param {string} message - Info message
     * @param {object} options - Additional options
     */
    info(message, options = {}) {
        return this.show(message, 'info', { duration: 4000, ...options });
    }
}

// Global notification instance
const notifications = new NotificationSystem();

/**
 * Convenience functions for common notifications
 */
function showNotification(message, type = 'info', options = {}) {
    return notifications.show(message, type, options);
}

function showSuccess(message, options = {}) {
    return notifications.success(message, options);
}

function showError(message, options = {}) {
    return notifications.error(message, options);
}

function showWarning(message, options = {}) {
    return notifications.warning(message, options);
}

function showInfo(message, options = {}) {
    return notifications.info(message, options);
}

/**
 * Form submission feedback
 */
function showFormSuccess(form, message = 'Form submitted successfully') {
    showSuccess(message, {
        action: {
            text: 'View',
            handler: () => {
                // Navigate to relevant page or refresh
                if (form.dataset.redirect) {
                    window.location.href = form.dataset.redirect;
                } else {
                    window.location.reload();
                }
            }
        }
    });
}

function showFormError(form, message = 'Please correct the errors and try again') {
    showError(message, {
        action: {
            text: 'Fix',
            handler: () => {
                // Focus first error field
                const firstError = form.querySelector('.form-group.error input, .form-group.error select, .form-group.error textarea');
                if (firstError) {
                    firstError.focus();
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        }
    });
}

/**
 * Trip-specific notifications
 */
function showTripAdded(tripData) {
    showSuccess(`Trip to ${tripData.country} added successfully`, {
        action: {
            text: 'View Details',
            handler: () => {
                window.location.href = `/employee/${tripData.employeeId}`;
            }
        }
    });
}

function showTripUpdated(tripData) {
    showSuccess(`Trip to ${tripData.country} updated successfully`);
}

function showTripDeleted(tripData) {
    showInfo(`Trip to ${tripData.country} deleted`, {
        action: {
            text: 'Undo',
            handler: () => {
                // Implement undo functionality
                console.log('Undo trip deletion:', tripData);
            }
        }
    });
}

/**
 * Import-specific notifications
 */
function showImportSuccess(summary) {
    const message = `Import completed: ${summary.trips_added} trips added, ${summary.employees_created} employees created`;
    showSuccess(message, {
        action: {
            text: 'View Summary',
            handler: () => {
                // Scroll to import summary or show modal
                const summaryElement = document.querySelector('.import-summary');
                if (summaryElement) {
                    summaryElement.scrollIntoView({ behavior: 'smooth' });
                }
            }
        }
    });
}

function showImportError(errors) {
    const message = `Import failed: ${errors.length} error(s) found`;
    showError(message, {
        action: {
            text: 'View Errors',
            handler: () => {
                // Show error details
                console.log('Import errors:', errors);
            }
        }
    });
}

/**
 * Loading state notifications
 */
function showLoading(message = 'Processing...', options = {}) {
    return showInfo(message, {
        persistent: true,
        closable: false,
        ...options
    });
}

function hideLoading(notification) {
    if (notification) {
        notifications.remove(notification);
    }
}

/**
 * Confirmation notifications
 */
function showConfirmation(message, onConfirm, onCancel = null) {
    return showWarning(message, {
        persistent: true,
        action: {
            text: 'Confirm',
            handler: () => {
                onConfirm();
                notifications.clear();
            }
        }
    });
}

// Export for use in other scripts
window.notifications = notifications;
window.showNotification = showNotification;
window.showSuccess = showSuccess;
window.showError = showError;
window.showWarning = showWarning;
window.showInfo = showInfo;
window.showFormSuccess = showFormSuccess;
window.showFormError = showFormError;
window.showTripAdded = showTripAdded;
window.showTripUpdated = showTripUpdated;
window.showTripDeleted = showTripDeleted;
window.showImportSuccess = showImportSuccess;
window.showImportError = showImportError;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showConfirmation = showConfirmation;
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
    
    // Initialize form handlers
    initFormHandlers();
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

// Initialize form handlers
function initFormHandlers() {
    // Handle add employee form submission
    const employeeForm = document.querySelector('form[data-employee-form="true"]');
    if (employeeForm) {
        employeeForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            const nameInput = this.querySelector('input[name="name"]');
            
            // Disable button and show loading state
            submitBtn.disabled = true;
            submitBtn.textContent = 'Adding...';
            
            try {
                const formData = new FormData(this);
                const response = await fetch(this.action, {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Show success message
                    showNotification(`Employee "${nameInput.value}" added successfully!`, 'success');
                    
                    // Clear form
                    nameInput.value = '';
                    
                    // Reload page to show new employee
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    // Show error message
                    showNotification(data.error || 'Failed to add employee', 'error');
                }
            } catch (error) {
                console.error('Error adding employee:', error);
                showNotification('An error occurred while adding the employee', 'error');
            } finally {
                // Re-enable button
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
    }
}

// Minimal cookie consent handler for ComplyEur
// GDPR-compliant: Only essential cookies used, no tracking

document.addEventListener('DOMContentLoaded', function () {
    const banner = document.getElementById('cookie-banner');
    const acceptBtn = document.getElementById('accept-cookies');
    
    if (!banner || !acceptBtn) {
        return; // Elements not found, exit silently
    }
    
    // Check if user has already accepted cookies
    if (!getCookie('cookie_consent')) {
        banner.style.display = 'block';
    }
    
    // Handle accept button click
    acceptBtn.addEventListener('click', function () {
        setCookie('cookie_consent', 'true', 90);
        banner.style.display = 'none';
    });
    
    /**
     * Set a cookie with specified name, value, and expiration days
     * @param {string} name - Cookie name
     * @param {string} value - Cookie value
     * @param {number} days - Days until expiration
     */
    function setCookie(name, value, days) {
        const expires = new Date(Date.now() + days * 864e5).toUTCString();
        // Use Secure flag if on HTTPS, SameSite=Strict for security
        const secureFlag = window.location.protocol === 'https:' ? '; Secure' : '';
        document.cookie = `${name}=${value}; expires=${expires}; path=/; SameSite=Strict${secureFlag}`;
    }
    
    /**
     * Get a cookie value by name
     * @param {string} name - Cookie name
     * @returns {string|undefined} Cookie value or undefined if not found
     */
    function getCookie(name) {
        const cookieString = document.cookie;
        if (!cookieString) {
            return undefined;
        }
        
        const cookies = cookieString.split('; ');
        const cookie = cookies.find(row => row.startsWith(name + '='));
        
        if (cookie) {
            return cookie.split('=')[1];
        }
        
        return undefined;
    }
});

