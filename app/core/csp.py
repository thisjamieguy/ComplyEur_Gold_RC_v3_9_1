"""
Content Security Policy (CSP) Module
Nonce-based CSP for maximum security
"""

import secrets
from flask import request, g


def generate_nonce() -> str:
    """
    Generate a cryptographically secure nonce for CSP.
    
    Returns:
        Base64-encoded nonce string
    """
    nonce_bytes = secrets.token_bytes(16)
    import base64
    return base64.b64encode(nonce_bytes).decode('utf-8')


def get_csp_nonce() -> str:
    """
    Get or generate CSP nonce for current request.
    Nonce is stored in Flask g object for request lifetime.
    
    Returns:
        Nonce string
    """
    if not hasattr(g, 'csp_nonce'):
        g.csp_nonce = generate_nonce()
    return g.csp_nonce


def build_csp_header(nonce: str) -> str:
    """
    Build Content Security Policy header with nonce.
    
    Args:
        nonce: Nonce for script/style tags
    
    Returns:
        CSP header string
    """
    csp_parts = [
        "default-src 'self'",
        f"script-src 'self' 'nonce-{nonce}'",  # Allow scripts from self with nonce
        f"style-src 'self' 'nonce-{nonce}' 'unsafe-inline'",  # Keep unsafe-inline for CSS compatibility
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'self'",
        "frame-ancestors 'none'",
        "base-uri 'none'",
        "object-src 'none'",
        "form-action 'self'",
    ]
    
    return "; ".join(csp_parts)

