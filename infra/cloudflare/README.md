# Cloudflare WAF Configuration
## Phase 4: Network & Infrastructure Security

This directory contains Cloudflare WAF configuration files for enterprise security.

---

## Files

- **`waf-rules.json`** - WAF rule definitions (JSON format for Cloudflare API)
- **`deployment-guide.md`** - Step-by-step deployment instructions

---

## Quick Start

1. Review `deployment-guide.md` for detailed steps
2. Import rules from `waf-rules.json` into Cloudflare Dashboard
3. Test rules in "Log" mode before enabling "Block" mode
4. Monitor WAF events in Cloudflare Dashboard

---

## Rule Summary

### Managed Rulesets
- ✅ OWASP Core Rule Set (Cloudflare managed)

### Custom Rules
1. **Block SQL Injection** - Detects SQL injection patterns
2. **Block XSS** - Detects cross-site scripting attempts
3. **Block Path Traversal** - Prevents directory traversal attacks
4. **Rate Limit Login** - 5 requests/minute per IP
5. **Rate Limit API** - 100 requests/minute per IP
6. **Geolocation Blocking** - Optional (disabled by default)

---

## Testing

After deployment, test with:

```bash
# SQL injection test (should be blocked)
curl -X POST "https://your-domain.com/api" -d "query=' OR '1'='1"

# XSS test (should be blocked)  
curl "https://your-domain.com/search?q=<script>alert('xss')</script>"
```

Both should return `403 Forbidden` if WAF is working correctly.

---

**Status:** Ready for deployment

