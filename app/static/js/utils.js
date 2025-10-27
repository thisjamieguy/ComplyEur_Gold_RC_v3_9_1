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
