#!/usr/bin/env bash
# Script to fetch Render build and deployment logs for debugging
# Usage: ./scripts/get_render_logs.sh [service-name] [log-type]

set -euo pipefail

SERVICE_NAME="${1:-complyeur-gold-rc}"
LOG_TYPE="${2:-all}"  # all, build, deploy, runtime

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

# Check if Render CLI is installed
check_render_cli() {
    if ! command -v render &> /dev/null; then
        log_error "Render CLI not found. Please install it first:"
        echo "  brew install render  # macOS"
        echo "  # OR"
        echo "  npm install -g render-cli"
        echo ""
        log_warn "Alternatively, you can get logs from Render dashboard:"
        echo "  1. Go to: https://dashboard.render.com"
        echo "  2. Select your service: $SERVICE_NAME"
        echo "  3. Click 'Logs' tab"
        echo "  4. Copy the logs and share them for debugging"
        exit 1
    fi
    log_info "Render CLI found"
}

# Get build logs
get_build_logs() {
    log_info "Fetching build logs for service: $SERVICE_NAME"
    echo ""
    echo "=== BUILD LOGS ==="
    echo ""
    
    if render logs "$SERVICE_NAME" --type build --tail 100 2>&1; then
        log_info "Build logs fetched successfully"
    else
        log_error "Failed to fetch build logs"
        log_warn "Make sure you're authenticated: render login"
        return 1
    fi
}

# Get deployment logs
get_deploy_logs() {
    log_info "Fetching deployment logs for service: $SERVICE_NAME"
    echo ""
    echo "=== DEPLOYMENT LOGS ==="
    echo ""
    
    if render logs "$SERVICE_NAME" --type deploy --tail 100 2>&1; then
        log_info "Deployment logs fetched successfully"
    else
        log_error "Failed to fetch deployment logs"
        return 1
    fi
}

# Get runtime logs
get_runtime_logs() {
    log_info "Fetching runtime logs for service: $SERVICE_NAME"
    echo ""
    echo "=== RUNTIME LOGS ==="
    echo ""
    
    if render logs "$SERVICE_NAME" --type runtime --tail 100 2>&1; then
        log_info "Runtime logs fetched successfully"
    else
        log_error "Failed to fetch runtime logs"
        return 1
    fi
}

# Get all logs
get_all_logs() {
    log_info "Fetching all logs for service: $SERVICE_NAME"
    echo ""
    
    get_build_logs
    echo ""
    echo "---"
    echo ""
    get_deploy_logs
    echo ""
    echo "---"
    echo ""
    get_runtime_logs
}

# Save logs to file
save_logs_to_file() {
    local output_file="reports/deployment/render_logs_$(date +%Y%m%d_%H%M%S).txt"
    mkdir -p reports/deployment
    
    log_info "Saving logs to: $output_file"
    
    {
        echo "Render Logs for Service: $SERVICE_NAME"
        echo "Date: $(date)"
        echo "========================================"
        echo ""
        case "$LOG_TYPE" in
            build)
                get_build_logs
                ;;
            deploy)
                get_deploy_logs
                ;;
            runtime)
                get_runtime_logs
                ;;
            all|*)
                get_all_logs
                ;;
        esac
    } > "$output_file" 2>&1
    
    log_info "Logs saved to: $output_file"
    echo ""
    log_info "You can share this file for debugging, or paste the contents here"
}

# Main execution
main() {
    echo "🔍 Render Logs Fetcher for ComplyEur"
    echo "======================================"
    echo ""
    
    check_render_cli
    
    # Check authentication
    if ! render whoami &> /dev/null; then
        log_error "Not authenticated with Render"
        log_info "Please run: render login"
        exit 1
    fi
    
    log_info "Authenticated as: $(render whoami 2>&1)"
    echo ""
    
    # Get logs based on type
    case "$LOG_TYPE" in
        build)
            get_build_logs
            ;;
        deploy)
            get_deploy_logs
            ;;
        runtime)
            get_runtime_logs
            ;;
        all|*)
            save_logs_to_file
            ;;
    esac
}

# Run main function
main "$@"





