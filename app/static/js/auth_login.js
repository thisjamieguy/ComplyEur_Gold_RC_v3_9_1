// Authentication login page JavaScript
// Moved from inline script to external file for CSP compliance

document.addEventListener('DOMContentLoaded', function() {
    const pwd = document.getElementById('password');
    const toggle = document.getElementById('toggle');
    const caps = document.getElementById('caps');
    
    if (toggle && pwd) {
        toggle.addEventListener('click', function() {
            pwd.type = pwd.type === 'password' ? 'text' : 'password';
            toggle.textContent = pwd.type === 'password' ? 'Show' : 'Hide';
        });
        
        pwd.addEventListener('keyup', function(e) {
            const s = e.getModifierState && e.getModifierState('CapsLock');
            if (caps) {
                caps.hidden = !s;
            }
        });
    }
});

