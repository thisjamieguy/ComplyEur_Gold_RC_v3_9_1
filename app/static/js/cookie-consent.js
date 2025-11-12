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

