/**
 * ComplyEur Landing Page JavaScript
 * 
 * Features:
 * - Smooth scroll animations using Intersection Observer
 * - Mobile menu toggle
 * - Navbar scroll behavior
 * - Accessibility enhancements
 * - Performance optimizations
 * 
 * No tracking, analytics, or cookies (privacy-first)
 */

(function() {
    'use strict';

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initScrollAnimations();
        initMobileMenu();
        initNavbarScroll();
        initSmoothScrolling();
        initAccessibility();
        
        // Performance: Lazy load non-critical resources
        if ('requestIdleCallback' in window) {
            requestIdleCallback(initLazyFeatures);
        } else {
            setTimeout(initLazyFeatures, 2000);
        }
    });

    /**
     * Scroll-triggered animations using Intersection Observer
     * Fallback for older browsers
     */
    function initScrollAnimations() {
        const animatedElements = document.querySelectorAll('.scroll-animate');
        
        if (!animatedElements.length) return;

        // Check for Intersection Observer support
        if ('IntersectionObserver' in window) {
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };

            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('visible');
                        // Optional: unobserve after animation to improve performance
                        observer.unobserve(entry.target);
                    }
                });
            }, observerOptions);

            animatedElements.forEach(el => observer.observe(el));
        } else {
            // Fallback for older browsers
            initScrollFallback();
        }
    }

    /**
     * Fallback scroll animation for browsers without Intersection Observer
     */
    function initScrollFallback() {
        const animatedElements = document.querySelectorAll('.scroll-animate');
        let ticking = false;

        function updateAnimations() {
            const windowHeight = window.innerHeight;
            
            animatedElements.forEach(el => {
                const rect = el.getBoundingClientRect();
                const isVisible = rect.top < windowHeight && rect.bottom > 0;
                
                if (isVisible) {
                    el.classList.add('visible');
                }
            });
            
            ticking = false;
        }
        
        function requestTick() {
            if (!ticking) {
                requestAnimationFrame(updateAnimations);
                ticking = true;
            }
        }
        
        window.addEventListener('scroll', requestTick, { passive: true });
        updateAnimations(); // Run once on load
    }

    /**
     * Mobile menu toggle functionality
     */
    function initMobileMenu() {
        const mobileMenuToggle = document.getElementById('mobileMenuToggle');
        const navLinks = document.getElementById('navLinks');
        
        if (!mobileMenuToggle || !navLinks) return;

        mobileMenuToggle.addEventListener('click', function() {
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            this.setAttribute('aria-expanded', !isExpanded);
            navLinks.classList.toggle('active');
            
            // Prevent body scroll when menu is open
            if (!isExpanded) {
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = '';
            }
        });

        // Close menu when clicking on a link
        const navLinksItems = navLinks.querySelectorAll('a');
        navLinksItems.forEach(link => {
            link.addEventListener('click', () => {
                mobileMenuToggle.setAttribute('aria-expanded', 'false');
                navLinks.classList.remove('active');
                document.body.style.overflow = '';
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!mobileMenuToggle.contains(e.target) && !navLinks.contains(e.target)) {
                mobileMenuToggle.setAttribute('aria-expanded', 'false');
                navLinks.classList.remove('active');
                document.body.style.overflow = '';
            }
        });

        // Close menu on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && navLinks.classList.contains('active')) {
                mobileMenuToggle.setAttribute('aria-expanded', 'false');
                navLinks.classList.remove('active');
                document.body.style.overflow = '';
                mobileMenuToggle.focus(); // Return focus to toggle button
            }
        });
    }

    /**
     * Navbar scroll behavior - fade to white on scroll
     */
    function initNavbarScroll() {
        const navbar = document.getElementById('navbar');
        if (!navbar) return;

        let lastScroll = 0;
        const scrollThreshold = 50;

        function handleScroll() {
            const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
            
            if (currentScroll > scrollThreshold) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
            
            lastScroll = currentScroll;
        }

        // Use passive listener for better performance
        window.addEventListener('scroll', handleScroll, { passive: true });
        handleScroll(); // Check initial state
    }

    /**
     * Smooth scrolling for anchor links
     */
    function initSmoothScrolling() {
        const navLinks = document.querySelectorAll('a[href^="#"]');
        
        navLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                
                // Skip if it's just "#"
                if (href === '#' || !href) return;
                
                const targetElement = document.querySelector(href);
                
                if (targetElement) {
                    e.preventDefault();
                    
                    // Calculate offset (navbar height + padding)
                    const navbarHeight = 80;
                    const offsetTop = targetElement.offsetTop - navbarHeight;
                    
                    window.scrollTo({
                        top: offsetTop,
                        behavior: 'smooth'
                    });
                    
                    // Update URL without scrolling (for browser history)
                    if (history.pushState) {
                        history.pushState(null, null, href);
                    }
                }
            });
        });
    }

    /**
     * Accessibility enhancements
     */
    function initAccessibility() {
        // Skip link functionality
        const skipLink = document.querySelector('.skip-link');
        if (skipLink) {
            skipLink.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.setAttribute('tabindex', '-1');
                    target.focus();
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    
                    // Remove tabindex after focus (for keyboard navigation)
                    setTimeout(() => target.removeAttribute('tabindex'), 1000);
                }
            });
        }

        // Keyboard navigation for interactive elements
        const interactiveElements = document.querySelectorAll('a, button');
        interactiveElements.forEach(el => {
            // Ensure focus is visible
            el.addEventListener('focus', function() {
                this.style.outline = '2px solid #A8B2D1';
                this.style.outlineOffset = '2px';
            });
            
            el.addEventListener('blur', function() {
                this.style.outline = '';
                this.style.outlineOffset = '';
            });
        });

        // Announce dynamic content changes to screen readers
        const announcer = document.createElement('div');
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.className = 'sr-only';
        announcer.style.cssText = 'position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border-width: 0;';
        document.body.appendChild(announcer);

        // Export announce function for potential future use
        window.announceToScreenReader = function(message) {
            announcer.textContent = message;
            setTimeout(() => announcer.textContent = '', 1000);
        };
    }

    /**
     * Initialize lazy-loaded features (non-critical)
     */
    function initLazyFeatures() {
        // Add any non-critical features here
        // For example: parallax effects, advanced animations, etc.
    }

    /**
     * Performance: Prefetch critical resources
     */
    function prefetchCriticalResources() {
        // Prefetch signup page if user is likely to navigate there
        const ctaButtons = document.querySelectorAll('.btn-primary, .btn-cta-band');
        let hoverTimer;
        
        ctaButtons.forEach(button => {
            button.addEventListener('mouseenter', function() {
                clearTimeout(hoverTimer);
                hoverTimer = setTimeout(() => {
                    const link = this.getAttribute('href');
                    if (link && link.startsWith('/')) {
                        const linkElement = document.createElement('link');
                        linkElement.rel = 'prefetch';
                        linkElement.href = link;
                        document.head.appendChild(linkElement);
                    }
                }, 100);
            }, { passive: true });
        });
    }

    // Initialize prefetching
    if ('requestIdleCallback' in window) {
        requestIdleCallback(prefetchCriticalResources);
    }

    /**
     * Error handling for graceful degradation
     */
    window.addEventListener('error', function(e) {
        // Log errors in development (remove in production for privacy)
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.warn('Landing page error:', e.message);
        }
        
        // Graceful fallback: ensure basic functionality works
        if (e.message.includes('IntersectionObserver')) {
            initScrollFallback();
        }
    }, true);

    /**
     * Export utilities for potential external use
     */
    window.ComplyEurLanding = {
        initScrollAnimations,
        initMobileMenu,
        initNavbarScroll,
        initSmoothScrolling
    };

})();
