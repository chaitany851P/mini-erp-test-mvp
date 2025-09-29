// Modern Notification System for Mini ERP

class NotificationManager {
    constructor() {
        this.container = this.createContainer();
        this.notifications = new Map();
    }

    createContainer() {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
        return container;
    }

    show(message, type = 'info', duration = 5000, options = {}) {
        const id = Date.now() + Math.random();
        const notification = this.createNotification(id, message, type, options);
        
        this.container.appendChild(notification);
        this.notifications.set(id, notification);

        // Show with animation
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });

        // Auto-hide
        if (duration > 0) {
            setTimeout(() => {
                this.hide(id);
            }, duration);
        }

        return id;
    }

    createNotification(id, message, type, options = {}) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white border-0 fade-in toast-modern bg-gradient-${type}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('data-id', id);

        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️',
            primary: '🔵'
        };

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center">
                    <span class="me-2 fs-5">${icons[type] || 'ℹ️'}</span>
                    <span>${message}</span>
                    ${options.action ? `<button class="btn btn-sm btn-outline-light ms-auto me-2" onclick="${options.action}">${options.actionText || 'Action'}</button>` : ''}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="notifications.hide(${id})"></button>
            </div>
        `;

        return toast;
    }

    hide(id) {
        const notification = this.notifications.get(id);
        if (notification) {
            notification.style.transform = 'translateX(100%)';
            notification.style.opacity = '0';
            
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
                this.notifications.delete(id);
            }, 300);
        }
    }

    success(message, duration = 4000, options = {}) {
        return this.show(message, 'success', duration, options);
    }

    error(message, duration = 6000, options = {}) {
        return this.show(message, 'danger', duration, options);
    }

    warning(message, duration = 5000, options = {}) {
        return this.show(message, 'warning', duration, options);
    }

    info(message, duration = 4000, options = {}) {
        return this.show(message, 'info', duration, options);
    }

    loading(message = 'Loading...', options = {}) {
        const loadingMessage = `
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            ${message}
        `;
        return this.show(loadingMessage, 'primary', 0, options);
    }

    clear() {
        this.notifications.forEach((notification, id) => {
            this.hide(id);
        });
    }
}

// Initialize global notification manager
const notifications = new NotificationManager();

// Enhanced loading utilities
class LoadingManager {
    constructor() {
        this.activeLoaders = new Set();
    }

    show(element, text = 'Loading...') {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (!element) return null;

        const loaderId = Date.now() + Math.random();
        element.classList.add('loading');
        element.setAttribute('data-loader-id', loaderId);
        
        if (text) {
            const textElement = element.querySelector('.loading-text');
            if (textElement) {
                textElement.textContent = text;
            } else {
                const span = document.createElement('span');
                span.className = 'loading-text visually-hidden';
                span.textContent = text;
                element.appendChild(span);
            }
        }

        this.activeLoaders.add(loaderId);
        return loaderId;
    }

    hide(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }

        if (!element) return;

        element.classList.remove('loading');
        const loaderId = element.getAttribute('data-loader-id');
        
        if (loaderId) {
            element.removeAttribute('data-loader-id');
            this.activeLoaders.delete(loaderId);
        }

        const textElement = element.querySelector('.loading-text');
        if (textElement) {
            textElement.remove();
        }
    }

    showSkeleton(element, options = {}) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }

        if (!element) return;

        const { lines = 3, avatar = false } = options;
        const skeletonContainer = document.createElement('div');
        skeletonContainer.className = 'skeleton-container fade-in';

        if (avatar) {
            const skeletonAvatar = document.createElement('div');
            skeletonAvatar.className = 'skeleton skeleton-avatar mb-3';
            skeletonContainer.appendChild(skeletonAvatar);
        }

        for (let i = 0; i < lines; i++) {
            const skeletonLine = document.createElement('div');
            skeletonLine.className = 'skeleton skeleton-text';
            skeletonLine.style.width = `${60 + Math.random() * 40}%`;
            skeletonContainer.appendChild(skeletonLine);
        }

        element.innerHTML = '';
        element.appendChild(skeletonContainer);
    }

    hideSkeleton(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }

        if (!element) return;

        const skeletonContainer = element.querySelector('.skeleton-container');
        if (skeletonContainer) {
            skeletonContainer.style.opacity = '0';
            setTimeout(() => {
                if (skeletonContainer.parentNode) {
                    skeletonContainer.remove();
                }
            }, 300);
        }
    }
}

// Initialize global loading manager
const loading = new LoadingManager();

// Enhanced form utilities
class FormManager {
    static async submitWithLoading(form, options = {}) {
        const {
            beforeSubmit = () => true,
            onSuccess = () => {},
            onError = (error) => notifications.error(error.message || 'An error occurred'),
            loadingText = 'Submitting...',
            successMessage = 'Form submitted successfully!',
            method = 'POST'
        } = options;

        if (!beforeSubmit()) return false;

        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn ? submitBtn.innerHTML : '';
        
        try {
            // Show loading state
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2"></span>
                    ${loadingText}
                `;
            }

            const loaderId = loading.show(form);
            
            // Prepare form data
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            // Submit form
            const response = await fetch(form.action || window.location.href, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': data.csrfmiddlewaretoken || ''
                },
                body: JSON.stringify(data)
            });

            loading.hide(form);

            if (response.ok) {
                const result = await response.json();
                notifications.success(successMessage);
                onSuccess(result);
                form.reset();
                return true;
            } else {
                throw new Error(`Server error: ${response.status}`);
            }

        } catch (error) {
            onError(error);
            return false;
        } finally {
            // Restore submit button
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        }
    }

    static addValidation(form, rules = {}) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            
            let isValid = true;
            const errors = [];

            // Clear previous errors
            form.querySelectorAll('.form-control').forEach(input => {
                input.classList.remove('is-invalid');
            });

            form.querySelectorAll('.invalid-feedback').forEach(error => {
                error.remove();
            });

            // Validate fields
            Object.keys(rules).forEach(fieldName => {
                const field = form.querySelector(`[name="${fieldName}"]`);
                const rule = rules[fieldName];

                if (field && rule) {
                    const value = field.value.trim();

                    if (rule.required && !value) {
                        isValid = false;
                        errors.push(`${rule.label || fieldName} is required`);
                        this.showFieldError(field, `${rule.label || fieldName} is required`);
                    }

                    if (value && rule.minLength && value.length < rule.minLength) {
                        isValid = false;
                        errors.push(`${rule.label || fieldName} must be at least ${rule.minLength} characters`);
                        this.showFieldError(field, `Must be at least ${rule.minLength} characters`);
                    }

                    if (value && rule.pattern && !rule.pattern.test(value)) {
                        isValid = false;
                        errors.push(`${rule.label || fieldName} format is invalid`);
                        this.showFieldError(field, rule.patternMessage || 'Invalid format');
                    }

                    if (value && rule.custom && !rule.custom(value)) {
                        isValid = false;
                        errors.push(`${rule.label || fieldName} validation failed`);
                        this.showFieldError(field, rule.customMessage || 'Validation failed');
                    }
                }
            });

            if (isValid) {
                this.submitWithLoading(form);
            } else {
                notifications.error(`Please fix ${errors.length} validation error(s)`);
            }
        });
    }

    static showFieldError(field, message) {
        field.classList.add('is-invalid');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
    }
}

// Auto-animate elements when they come into view
class AnimationObserver {
    constructor() {
        this.observer = new IntersectionObserver(this.handleIntersection.bind(this), {
            threshold: 0.1,
            rootMargin: '50px'
        });
        
        this.init();
    }

    init() {
        // Auto-observe elements with animation classes
        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('[data-animate]').forEach(el => {
                this.observer.observe(el);
            });
        });
    }

    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const animation = element.dataset.animate;
                
                element.classList.add(animation);
                this.observer.unobserve(element);
            }
        });
    }
}

// Initialize animation observer
const animationObserver = new AnimationObserver();

// Export for global use
window.notifications = notifications;
window.loading = loading;
window.FormManager = FormManager;
window.AnimationObserver = AnimationObserver;