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
