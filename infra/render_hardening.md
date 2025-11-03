# Render Service Hardening Guide
## Phase 4: Network & Infrastructure Security

**Platform:** Render.com  
**Last Updated:** 2025-01-XX

---

## 🔒 Security Hardening Checklist

### 1. Service Configuration ✅

#### Private Service Discovery
- ✅ **Status:** Enabled by default on Render
- ✅ **Description:** Services communicate via private network
- **Configuration:** Automatic - no action required

#### Environment Secrets
- ✅ **Status:** Use Render Secrets (not code)
- ✅ **Required Secrets:**
  - `SECRET_KEY` - Flask session encryption
  - `PEPPER` - Password encryption pepper
  - `ENCRYPTION_KEY` - Database encryption key
  - `GOOGLE_OAUTH_CLIENT_SECRET` (if using OAuth)
  - `MICROSOFT_OAUTH_CLIENT_SECRET` (if using OAuth)
  - `RECAPTCHA_SECRET_KEY` (if using CAPTCHA)
- **Action:** Set all secrets in Render Dashboard > Service > Environment

#### Persistent Disk Encryption
- ✅ **Status:** Enabled by Render (encrypted at rest)
- ✅ **Configuration:** Automatic
- **Location:** `/var/data/` (as configured in render.yaml)

### 2. Network Security ✅

#### Port Management
- ✅ **Public Ports:** 80, 443 (via Cloudflare proxy only)
- ✅ **Blocked Ports:** SSH (22), Database ports (3306, 5432)
- ✅ **Database:** Accessible only via private network
- **Note:** Render manages all port access

#### Private Database Connections
- ✅ **Status:** Database on private network
- ✅ **Configuration:** 
  - Use private service discovery
  - Database internal URL (not public)
  - No internet exposure

### 3. Access Control ✅

#### SSH Access
- ✅ **Method:** Via Render Dashboard only
- ✅ **Authentication:** Render account (2FA required)
- ✅ **No Direct SSH:** Render manages access
- **Note:** Render provides SSH access through dashboard

#### Account Security
- ✅ **Two-Factor Authentication:** Required for Render account
- ✅ **Team Access:** Role-based (Admin, Member)
- ✅ **Audit Logs:** Available in Render dashboard

### 4. Monitoring & Logging ✅

#### Health Checks
- ✅ **Endpoint:** `/health` (recommended)
- ✅ **Configuration:** Add to Render service
- **Implementation:**
  ```python
  @app.route('/health')
  def health_check():
      return jsonify({'status': 'healthy'}), 200
  ```

#### Log Aggregation
- ✅ **Method:** Render logs + application logs
- ✅ **Retention:** Configured in application
- ✅ **SIEM Integration:** Optional (Logtail, Datadog)

### 5. Backup Security ✅

#### Encrypted Backups
- ✅ **Location:** `/var/data/backups/`
- ✅ **Encryption:** AES-256-GCM
- ✅ **Automation:** Daily encrypted backups
- ✅ **Retention:** 30 daily, 12 weekly, 12 monthly

---

## 🛡️ Cloudflare WAF Configuration

### Prerequisites
1. Domain configured with Cloudflare
2. DNS records pointing to Render
3. Cloudflare proxy enabled (orange cloud)

### Deployment Steps

1. **Enable WAF**
   - Cloudflare Dashboard > Security > WAF
   - Enable "Managed Ruleset"
   - Select "OWASP Core Rule Set"

2. **Create Custom Rules**
   - Import rules from `infra/cloudflare/waf-rules.json`
   - Test in "Log" mode first
   - Switch to "Block" mode after validation

3. **Configure Rate Limiting**
   - Security > Rate Limiting
   - Create rules:
     - `/login`: 5 requests/minute
     - `/api/*`: 100 requests/minute
     - `/*`: 1000 requests/minute

4. **Enable Bot Fight Mode**
   - Security > Bots
   - Enable "Bot Fight Mode"

5. **SSL/TLS Settings**
   - SSL/TLS > Overview
   - Set mode to "Full (strict)"
   - Minimum TLS Version: 1.3

---

## 🔍 Security Verification

### Run Network Scan
```bash
./scripts/network_scan.sh
```

### Verify Security Headers
```bash
curl -I https://your-domain.com | grep -iE "(strict-transport|content-security|x-frame)"
```

### Check Firewall Status
- Render Dashboard > Service > Network
- Verify no public database ports
- Confirm private service links only

---

## 📋 Render-Specific Security Features

### Automatic Security
- ✅ DDoS Protection (built-in)
- ✅ TLS Termination (automatic)
- ✅ Private Networking (automatic)
- ✅ Disk Encryption (automatic)

### Manual Configuration Required
- ⚙️ Environment Secrets (via Dashboard)
- ⚙️ Health Check Endpoint (application code)
- ⚙️ Backup Automation (application code)
- ⚙️ Cloudflare WAF (external configuration)

---

## 🚨 Incident Response

### Render Platform Issues
1. Check Render Status: https://status.render.com
2. Review Render logs: Dashboard > Service > Logs
3. Contact Render Support if needed

### Application Security Issues
1. Review application logs
2. Check audit logs: `/var/data/logs/audit.log`
3. Run network scan: `./scripts/network_scan.sh`
4. Escalate per `infra/security_policy.yml`

---

**Last Reviewed:** 2025-01-XX  
**Next Review:** Quarterly

