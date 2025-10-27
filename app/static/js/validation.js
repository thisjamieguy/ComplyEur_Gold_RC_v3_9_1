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
