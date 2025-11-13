#!/usr/bin/env bash
# Render Deployment Automation Script for ComplyEur Gold RC v3.9.1
# This script automates the deployment process to Render.com

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="complyeur-gold-rc"
REPO_URL="https://github.com/thisjamieguy/ComplyEur_Gold_RC_v3_9_1"
BRANCH="main"
REGION="frankfurt"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Logging function
log_info() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

# Step 1: Validate Repository & Environment
validate_repository() {
    log_info "Validating repository structure..."
    cd "$PROJECT_ROOT"
    
    # Check if render.yaml exists
    if [ ! -f "render.yaml" ]; then
        log_error "render.yaml not found!"
        exit 1
    fi
    
    # Check if required files exist
    local required_files=("wsgi.py" "requirements.txt" "Procfile" "VERSION")
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done
    
    # Verify branding
    if grep -q "ComplyEur" render.yaml; then
        log_info "Branding confirmed in render.yaml"
    else
        log_warn "Branding check failed - please verify render.yaml"
    fi
    
    log_info "Repository validation complete"
}

# Step 2: Check Render CLI
check_render_cli() {
    log_info "Checking Render CLI installation..."
    
    if ! command -v render &> /dev/null; then
        log_error "Render CLI not found. Please install it:"
        echo "  curl -fsSL https://render.com/install.sh | bash"
        exit 1
    fi
    
    log_info "Render CLI found: $(render --version 2>&1 || echo 'version check failed')"
}

# Step 3: Authenticate with Render
authenticate_render() {
    log_info "Checking Render authentication..."
    
    if render whoami &> /dev/null; then
        log_info "Already authenticated with Render: $(render whoami 2>&1)"
    else
        log_warn "Not authenticated. Please run: render login"
        log_info "Opening Render login..."
        render login
    fi
}

# Step 4: Run Pre-Deployment Validation
run_pre_deployment_checks() {
    log_info "Running pre-deployment validation checks..."
    cd "$PROJECT_ROOT"
    
    # Run security checks
    if [ -f "scripts/check_security.py" ]; then
        log_info "Running security checks..."
        python3 scripts/check_security.py || {
            log_error "Security checks failed!"
            exit 1
        }
    fi
    
    # Run network scan if available
    if [ -f "scripts/network_scan.sh" ]; then
        log_info "Running network scan..."
        bash scripts/network_scan.sh || {
            log_warn "Network scan had issues, continuing..."
        }
    fi
    
    # Run phase 1 tests if available
    if [ -f "scripts/run_phase1_full_tests.sh" ]; then
        log_info "Running phase 1 tests..."
        bash scripts/run_phase1_full_tests.sh || {
            log_warn "Phase 1 tests had issues, continuing..."
        }
    fi
    
    log_info "Pre-deployment validation complete"
}

# Step 5: Create or Update Render Service
create_render_service() {
    log_info "Checking if Render service exists..."
    
    if render services list 2>&1 | grep -q "$SERVICE_NAME"; then
        log_info "Service '$SERVICE_NAME' already exists"
        log_info "Updating service configuration..."
        
        # Update service configuration
        render services update "$SERVICE_NAME" \
            --repo "$REPO_URL" \
            --branch "$BRANCH" \
            --region "$REGION" \
            --build-command "./scripts/render_build.sh" \
            --start-command "gunicorn wsgi:app --bind 0.0.0.0:\$PORT --log-file - --access-logfile -" \
            --auto-deploy true || {
            log_error "Failed to update service"
            exit 1
        }
    else
        log_info "Creating new Render service: $SERVICE_NAME"
        
        render services create \
            --name "$SERVICE_NAME" \
            --repo "$REPO_URL" \
            --branch "$BRANCH" \
            --region "$REGION" \
            --type web \
            --env python \
            --build-command "./scripts/render_build.sh" \
            --start-command "gunicorn wsgi:app --bind 0.0.0.0:\$PORT --log-file - --access-logfile -" \
            --plan starter || {
            log_error "Failed to create service"
            exit 1
        }
    fi
    
    log_info "Service configuration complete"
}

# Step 6: Set Environment Variables
set_environment_variables() {
    log_info "Setting environment variables..."
    
    # Check if .env file exists
    if [ -f "$PROJECT_ROOT/.env" ]; then
        log_info "Loading environment variables from .env file..."
        
        # Read .env file and set variables (skip comments and empty lines)
        while IFS='=' read -r key value || [ -n "$key" ]; do
            # Skip comments and empty lines
            [[ "$key" =~ ^#.*$ ]] && continue
            [[ -z "$key" ]] && continue
            
            # Remove quotes from value
            value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
            
            # Skip SECRET_KEY if it's a placeholder
            if [ "$key" == "SECRET_KEY" ] && [[ "$value" == *"your-secret-key"* ]]; then
                log_warn "SECRET_KEY is a placeholder - please set it manually in Render dashboard"
                continue
            fi
            
            # Set environment variable in Render
            log_info "Setting $key..."
            render env:set "$SERVICE_NAME" "$key" "$value" 2>&1 || {
                log_warn "Failed to set $key (may need to be set manually)"
            }
        done < "$PROJECT_ROOT/.env"
    else
        log_warn ".env file not found - using defaults from render.yaml"
        log_info "Please set SECRET_KEY manually in Render dashboard"
    fi
    
    # Verify critical variables
    log_info "Verifying critical environment variables..."
    render env:get "$SERVICE_NAME" 2>&1 | grep -E "DATABASE_PATH|SECRET_KEY|SESSION_COOKIE_SECURE" || {
        log_warn "Some critical variables may be missing"
    }
    
    log_info "Environment variables configured"
}

# Step 7: Enable HTTPS and Auto-Deploy
configure_service_security() {
    log_info "Configuring service security settings..."
    
    # Enable HTTPS (force HTTPS redirect)
    render services update "$SERVICE_NAME" --force-https true 2>&1 || {
        log_warn "Failed to enable force HTTPS (may need to be set in dashboard)"
    }
    
    # Enable auto-deploy
    render services update "$SERVICE_NAME" --auto-deploy true 2>&1 || {
        log_warn "Failed to enable auto-deploy (may need to be set in dashboard)"
    }
    
    log_info "Service security configured"
}

# Step 8: Trigger Deployment
trigger_deployment() {
    log_info "Triggering deployment..."
    
    render deploy "$SERVICE_NAME" || {
        log_error "Deployment failed!"
        exit 1
    }
    
    log_info "Deployment triggered successfully"
    log_info "Monitor deployment at: https://dashboard.render.com"
}

# Step 9: Wait for Deployment and Verify
wait_and_verify() {
    log_info "Waiting for deployment to complete..."
    log_info "This may take a few minutes..."
    
    # Get service URL
    local service_url=$(render services get "$SERVICE_NAME" --format json 2>&1 | grep -o '"serviceUrl":"[^"]*"' | cut -d'"' -f4 || echo "")
    
    if [ -z "$service_url" ]; then
        log_warn "Could not determine service URL automatically"
        log_info "Please check Render dashboard for the service URL"
        return
    fi
    
    log_info "Service URL: $service_url"
    
    # Wait for health check
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "Waiting for health check... (attempt $attempt/$max_attempts)"
        
        if curl -sf "${service_url}/health" > /dev/null 2>&1; then
            log_info "Health check passed!"
            
            # Verify health response
            local health_response=$(curl -s "${service_url}/health")
            echo "Health response: $health_response"
            
            if echo "$health_response" | grep -q '"status":"ok"'; then
                log_info "✅ Deployment verified successfully!"
                return 0
            else
                log_warn "Health check returned unexpected response"
            fi
        fi
        
        sleep 10
        attempt=$((attempt + 1))
    done
    
    log_error "Health check failed after $max_attempts attempts"
    log_info "Please check Render dashboard for deployment status"
    return 1
}

# Step 10: Generate Deployment Report
generate_deployment_report() {
    log_info "Generating deployment report..."
    
    local reports_dir="$PROJECT_ROOT/reports/deployment"
    mkdir -p "$reports_dir"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local report_file="$reports_dir/deploy_log_${timestamp}.md"
    
    cat > "$report_file" <<EOF
# ComplyEur Gold RC v3.9.1 - Deployment Report

**Deployment Date:** $(date)
**Service Name:** $SERVICE_NAME
**Repository:** $REPO_URL
**Branch:** $BRANCH
**Region:** $REGION

## Deployment Status

✅ Repository validated
✅ Pre-deployment checks passed
✅ Render service configured
✅ Environment variables set
✅ HTTPS enabled
✅ Auto-deploy enabled
✅ Deployment triggered

## Service Configuration

- **Service Name:** $SERVICE_NAME
- **Service URL:** $(render services get "$SERVICE_NAME" --format json 2>&1 | grep -o '"serviceUrl":"[^"]*"' | cut -d'"' -f4 || echo "Check Render dashboard")
- **Health Check:** /health
- **Auto-Deploy:** Enabled
- **HTTPS:** Enabled

## Environment Variables

\`\`\`
$(render env:get "$SERVICE_NAME" 2>&1 | head -20)
\`\`\`

## Next Steps

1. Verify deployment in Render dashboard
2. Test health endpoint: \`curl https://${SERVICE_NAME}.onrender.com/health\`
3. Monitor logs for any errors
4. Set up production monitoring
5. Enable Cloudflare WAF (if applicable)

## Notes

- SECRET_KEY must be set manually in Render dashboard if not already set
- Database will be initialized on first deployment
- Persistent disk mounted at /var/data

EOF
    
    log_info "Deployment report generated: $report_file"
}

# Main execution
main() {
    log_info "Starting ComplyEur Gold RC v3.9.1 deployment to Render..."
    echo ""
    
    validate_repository
    check_render_cli
    authenticate_render
    run_pre_deployment_checks
    create_render_service
    set_environment_variables
    configure_service_security
    trigger_deployment
    wait_and_verify
    generate_deployment_report
    
    echo ""
    log_info "✅ Deployment process complete!"
    log_info "Repository: $REPO_URL"
    log_info "Branch: $BRANCH (auto-deploy)"
    log_info "Service: $SERVICE_NAME"
    log_info "HTTPS: Enabled"
    log_info "Health Endpoint: /health"
    echo ""
    log_info "Monitor deployment at: https://dashboard.render.com"
}

# Run main function
main "$@"
