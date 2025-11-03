# Cloudflare WAF Deployment Guide
## Phase 4: Network & Infrastructure Security

**Last Updated:** 2025-01-XX

---

## 📋 Prerequisites

1. Domain registered with Cloudflare
2. DNS records pointing to Render service
3. Cloudflare proxy enabled (orange cloud icon)
4. Cloudflare account with WAF access

---

## 🚀 Deployment Steps

### Step 1: Enable Cloudflare Proxy

1. Log into Cloudflare Dashboard
2. Select your domain
3. Go to **DNS** > **Records**
4. Ensure proxy is enabled (orange cloud icon)
5. Verify DNS points to Render service

### Step 2: Configure SSL/TLS

1. Go to **SSL/TLS** > **Overview**
2. Set encryption mode to **"Full (strict)"**
3. Go to **SSL/TLS** > **Edge Certificates**
4. Enable **"Always Use HTTPS"**
5. Set **"Minimum TLS Version"** to **1.3**
6. Enable **"TLS 1.3"**

### Step 3: Enable WAF

1. Go to **Security** > **WAF**
2. Click **"Managed rules"**
3. Enable **"Cloudflare Managed Ruleset"**
4. Enable **"OWASP Core Rule Set"**
5. Set sensitivity to **"High"**
6. Click **"Deploy"**

### Step 4: Create Custom Rules

1. Go to **Security** > **WAF** > **Custom rules**
2. Click **"Create rule"**
3. Import rules from `infra/cloudflare/waf-rules.json`:

#### Rule 1: Block SQL Injection
- **Rule name:** Block SQL Injection
- **Expression:**
  ```
  (http.request.uri.query contains "'" or http.request.body contains "'" or http.request.body contains "--" or http.request.body contains "union select")
  ```
- **Action:** Block
- **Status:** Enabled

#### Rule 2: Block XSS
- **Rule name:** Block XSS Attempts
- **Expression:**
  ```
  (http.request.uri.query contains "<script" or http.request.body contains "<script" or http.request.headers["user-agent"] contains "<script")
  ```
- **Action:** Block
- **Status:** Enabled

#### Rule 3: Block Path Traversal
- **Rule name:** Block Path Traversal
- **Expression:**
  ```
  (http.request.uri.path contains "../" or http.request.uri.path contains ".env")
  ```
- **Action:** Block
- **Status:** Enabled

### Step 5: Configure Rate Limiting

1. Go to **Security** > **WAF** > **Rate limiting rules**
2. Create rules:

#### Login Rate Limit
- **Rule name:** Login Rate Limit
- **Match:**
  - Request URL: `/login` OR `/auth/login`
- **Rate:**
  - Requests: 5
  - Period: 1 minute
- **Action:** Block

#### API Rate Limit
- **Rule name:** API Rate Limit
- **Match:**
  - Request URL: `/api/*`
- **Rate:**
  - Requests: 100
  - Period: 1 minute
- **Action:** Challenge

### Step 6: Enable Bot Fight Mode

1. Go to **Security** > **Bots**
2. Enable **"Bot Fight Mode"**
3. Enable **"Super Bot Fight Mode"** (optional, paid)

### Step 7: Configure Page Rules (Optional)

1. Go to **Rules** > **Page Rules**
2. Create rules:
   - Cache static assets
   - Force HTTPS
   - Security headers

### Step 8: Test WAF Rules

1. Go to **Security** > **Events**
2. Test with malicious payloads (use test mode first)
3. Verify rules are blocking correctly
4. Switch from "Log" to "Block" mode

---

## ✅ Verification Checklist

- [ ] Cloudflare proxy enabled (orange cloud)
- [ ] SSL/TLS mode: Full (strict)
- [ ] TLS 1.3 enabled
- [ ] OWASP Core Rule Set enabled
- [ ] Custom WAF rules created
- [ ] Rate limiting configured
- [ ] Bot Fight Mode enabled
- [ ] Security headers verified
- [ ] Test requests blocked correctly

---

## 🔍 Testing

### Test SQL Injection Blocking
```bash
curl -X POST "https://your-domain.com/api/endpoint" \
  -d "query=' OR '1'='1"
```
**Expected:** 403 Forbidden (blocked by WAF)

### Test XSS Blocking
```bash
curl "https://your-domain.com/search?q=<script>alert('xss')</script>"
```
**Expected:** 403 Forbidden (blocked by WAF)

### Test Rate Limiting
```bash
# Send 10 requests in quick succession
for i in {1..10}; do
  curl -X POST "https://your-domain.com/login" -d "username=test&password=test"
done
```
**Expected:** After 5 requests, 429 Too Many Requests

---

## 📊 Monitoring

### View WAF Events
1. Go to **Security** > **Events**
2. Filter by:
   - Action (Block, Challenge, Log)
   - Rule name
   - IP address
   - Time range

### Review Analytics
1. Go to **Security** > **Analytics**
2. View:
   - Threat types
   - Top blocked countries
   - Top rules triggered

---

## ⚠️ Important Notes

- **Test Mode First:** Always test rules in "Log" mode before "Block"
- **False Positives:** Monitor and adjust sensitivity if needed
- **Geo-Blocking:** Optional - can block non-EU traffic if required
- **Performance:** WAF adds minimal latency (~10-50ms)

---

## 🔄 Maintenance

- **Review Weekly:** Check WAF events for patterns
- **Update Monthly:** Review and update custom rules
- **Test Quarterly:** Run tabletop exercises
- **Audit Annually:** Full security review

---

**Status:** Ready for deployment  
**Next Review:** Quarterly

