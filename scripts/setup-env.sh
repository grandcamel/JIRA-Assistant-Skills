#!/usr/bin/env bash
# ============================================================================
# Jira Assistant Skills - Environment Setup Script
# ============================================================================
# Interactively configures environment variables for the project.
# Saves to ~/.env and optionally adds loader to shell config.
# ============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
ENV_FILE="$HOME/.env"
PROJECT_NAME="Jira Assistant Skills"

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ${BOLD}${PROJECT_NAME} - Environment Setup${NC}                       ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Mask a secret value, showing only first 4 and last 4 characters
mask_secret() {
    local value="$1"
    local len=${#value}
    if [[ $len -le 8 ]]; then
        echo "********"
    else
        echo "${value:0:4}...${value: -4}"
    fi
}

# Read existing value from ~/.env file
get_existing_value() {
    local var_name="$1"
    if [[ -f "$ENV_FILE" ]]; then
        grep -E "^${var_name}=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2- | sed 's/^"//;s/"$//' || echo ""
    else
        echo ""
    fi
}

# Prompt for a value with optional default and validation
prompt_value() {
    local var_name="$1"
    local description="$2"
    local default="$3"
    local required="$4"
    local is_secret="$5"
    local validation_func="${6:-}"

    local existing
    existing=$(get_existing_value "$var_name")

    local display_default="$default"
    local display_existing=""

    if [[ -n "$existing" ]]; then
        if [[ "$is_secret" == "yes" ]]; then
            display_existing="[current: $(mask_secret "$existing")]"
        else
            display_existing="[current: $existing]"
        fi
        display_default="$existing"
    elif [[ -n "$default" ]]; then
        display_existing="[default: $default]"
    fi

    echo ""
    echo -e "${BOLD}$var_name${NC} - $description"
    if [[ -n "$display_existing" ]]; then
        echo -e "  ${YELLOW}$display_existing${NC}"
    fi

    local input=""
    while true; do
        if [[ "$is_secret" == "yes" ]]; then
            echo -n "  Enter value (hidden): "
            read -rs input
            echo ""
        else
            echo -n "  Enter value: "
            read -r input
        fi

        # Use default if empty
        if [[ -z "$input" ]]; then
            input="$display_default"
        fi

        # Check required
        if [[ "$required" == "yes" && -z "$input" ]]; then
            print_error "This field is required."
            continue
        fi

        # Run validation if provided
        if [[ -n "$validation_func" && -n "$input" ]]; then
            if ! $validation_func "$input"; then
                continue
            fi
        fi

        break
    done

    echo "$input"
}

# ============================================================================
# Validation Functions
# ============================================================================

validate_url() {
    local url="$1"
    if [[ ! "$url" =~ ^https?:// ]]; then
        print_error "URL must start with http:// or https://"
        return 1
    fi
    # Check for valid URL format (basic check)
    if [[ ! "$url" =~ ^https?://[a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)*\.?[a-zA-Z0-9]*(:[0-9]+)?(/.*)?$ ]]; then
        print_error "Invalid URL format"
        return 1
    fi
    return 0
}

validate_https_url() {
    local url="$1"
    if [[ ! "$url" =~ ^https:// ]]; then
        print_error "URL must use HTTPS (start with https://)"
        return 1
    fi
    # Basic URL format check - allows standard hostnames and Atlassian cloud URLs
    if [[ ! "$url" =~ ^https://[a-zA-Z0-9][-a-zA-Z0-9.]*(:[0-9]+)?(/.*)?$ ]]; then
        print_error "Invalid URL format"
        return 1
    fi
    return 0
}

validate_email() {
    local email="$1"
    if [[ ! "$email" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
        print_error "Invalid email format"
        return 1
    fi
    return 0
}

validate_non_empty() {
    local value="$1"
    if [[ -z "$value" ]]; then
        print_error "Value cannot be empty"
        return 1
    fi
    return 0
}

validate_anthropic_key() {
    local key="$1"
    if [[ -z "$key" ]]; then
        return 0  # Optional, empty is OK
    fi
    if [[ ! "$key" =~ ^sk-ant- ]]; then
        print_warning "Anthropic API keys typically start with 'sk-ant-'"
        echo -n "  Continue anyway? (y/N): "
        read -r confirm
        if [[ ! "$confirm" =~ ^[Yy] ]]; then
            return 1
        fi
    fi
    return 0
}

# ============================================================================
# Connection Test Functions
# ============================================================================

test_jira_connection() {
    local url="$1"
    local email="$2"
    local token="$3"

    echo ""
    print_info "Testing JIRA connection..."

    local endpoint="${url}/rest/api/3/myself"
    local auth
    auth=$(echo -n "${email}:${token}" | base64)

    local response
    local http_code

    # Make request and capture both body and status code
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Basic ${auth}" \
        -H "Content-Type: application/json" \
        "$endpoint" 2>/dev/null) || true

    http_code=$(echo "$response" | tail -n1)
    local body
    body=$(echo "$response" | sed '$d')

    if [[ "$http_code" == "200" ]]; then
        local display_name
        display_name=$(echo "$body" | grep -o '"displayName":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "Unknown")
        print_success "Connected successfully as: $display_name"
        return 0
    elif [[ "$http_code" == "401" ]]; then
        print_error "Authentication failed (HTTP 401)"
        print_info "Check your email and API token"
        print_info "Generate token at: https://id.atlassian.com/manage-profile/security/api-tokens"
        return 1
    elif [[ "$http_code" == "403" ]]; then
        print_error "Access forbidden (HTTP 403)"
        print_info "Your token may not have the required permissions"
        return 1
    elif [[ "$http_code" == "404" ]]; then
        print_error "JIRA instance not found (HTTP 404)"
        print_info "Check your JIRA_SITE_URL"
        return 1
    else
        print_error "Connection failed (HTTP $http_code)"
        return 1
    fi
}

test_anthropic_connection() {
    local api_key="$1"

    if [[ -z "$api_key" ]]; then
        print_warning "No Anthropic API key configured, skipping test"
        return 0
    fi

    echo ""
    print_info "Testing Anthropic API connection..."

    local response
    local http_code

    # Test with a minimal request to check auth
    response=$(curl -s -w "\n%{http_code}" \
        -H "x-api-key: ${api_key}" \
        -H "anthropic-version: 2023-06-01" \
        -H "Content-Type: application/json" \
        "https://api.anthropic.com/v1/messages" \
        -d '{"model":"claude-3-haiku-20240307","max_tokens":1,"messages":[{"role":"user","content":"hi"}]}' 2>/dev/null) || true

    http_code=$(echo "$response" | tail -n1)

    if [[ "$http_code" == "200" ]]; then
        print_success "Anthropic API key is valid"
        return 0
    elif [[ "$http_code" == "401" ]]; then
        print_error "Invalid API key (HTTP 401)"
        print_info "Check your ANTHROPIC_API_KEY"
        return 1
    elif [[ "$http_code" == "400" ]]; then
        # 400 with valid key often means the request was bad but auth worked
        print_success "Anthropic API key appears valid"
        return 0
    else
        print_warning "Could not verify API key (HTTP $http_code)"
        return 0  # Don't block on this
    fi
}

# ============================================================================
# Shell Configuration Functions
# ============================================================================

get_shell_config_file() {
    local shell_name
    shell_name=$(basename "$SHELL")

    case "$shell_name" in
        zsh)
            echo "$HOME/.zshrc"
            ;;
        bash)
            if [[ -f "$HOME/.bash_profile" ]]; then
                echo "$HOME/.bash_profile"
            else
                echo "$HOME/.bashrc"
            fi
            ;;
        *)
            echo "$HOME/.profile"
            ;;
    esac
}

add_env_loader() {
    local config_file
    config_file=$(get_shell_config_file)

    local loader_marker="# Load Environment Variables from ~/.env"

    # Check if loader already exists
    if grep -q "$loader_marker" "$config_file" 2>/dev/null; then
        print_info "Environment loader already present in $config_file"
        return 0
    fi

    echo ""
    echo -e "${BOLD}Shell Configuration${NC}"
    echo "To automatically load ~/.env variables, add a loader to your shell config."
    echo ""
    echo -n "Add loader to $config_file? (Y/n): "
    read -r confirm

    if [[ "$confirm" =~ ^[Nn] ]]; then
        print_warning "Skipped adding loader to shell config"
        print_info "You'll need to manually source ~/.env or add the loader yourself"
        return 0
    fi

    # Backup shell config
    if [[ -f "$config_file" ]]; then
        cp "$config_file" "${config_file}.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    # Add loader
    cat >> "$config_file" << 'EOF'

# ============================================================================
# Load Environment Variables from ~/.env
# ============================================================================
if [ -f ~/.env ]; then
    set -a  # Automatically export all variables
    source ~/.env
    set +a  # Disable automatic export
fi
EOF

    print_success "Added environment loader to $config_file"
    return 0
}

# ============================================================================
# Main Configuration Flow
# ============================================================================

configure_jira() {
    print_section "JIRA Configuration"

    echo ""
    print_info "Configure your Atlassian JIRA credentials."
    print_info "Generate an API token at: https://id.atlassian.com/manage-profile/security/api-tokens"

    JIRA_SITE_URL=$(prompt_value "JIRA_SITE_URL" \
        "Your JIRA Cloud instance URL (e.g., https://company.atlassian.net)" \
        "" \
        "yes" \
        "no" \
        "validate_https_url")

    JIRA_EMAIL=$(prompt_value "JIRA_EMAIL" \
        "Your Atlassian account email" \
        "" \
        "yes" \
        "no" \
        "validate_email")

    JIRA_API_TOKEN=$(prompt_value "JIRA_API_TOKEN" \
        "Your JIRA API token" \
        "" \
        "yes" \
        "yes" \
        "validate_non_empty")

    JIRA_PROFILE=$(prompt_value "JIRA_PROFILE" \
        "Profile name for multi-instance support (optional)" \
        "default" \
        "no" \
        "no" \
        "")
}

configure_anthropic() {
    print_section "Anthropic API Configuration (for E2E tests)"

    echo ""
    print_info "The Anthropic API key is needed for E2E tests that use Claude Code."
    print_info "Get your API key at: https://console.anthropic.com/settings/keys"
    print_warning "This is optional if you only want to use JIRA skills without E2E tests."

    ANTHROPIC_API_KEY=$(prompt_value "ANTHROPIC_API_KEY" \
        "Your Anthropic API key (optional, for E2E tests)" \
        "" \
        "no" \
        "yes" \
        "validate_anthropic_key")
}

run_connection_tests() {
    print_section "Connection Tests"

    echo ""
    echo -n "Would you like to test the connections before saving? (Y/n): "
    read -r confirm

    if [[ "$confirm" =~ ^[Nn] ]]; then
        print_warning "Skipped connection tests"
        return 0
    fi

    local jira_ok=true

    # Test JIRA
    if ! test_jira_connection "$JIRA_SITE_URL" "$JIRA_EMAIL" "$JIRA_API_TOKEN"; then
        jira_ok=false
    fi

    # Test Anthropic (informational only, doesn't block save)
    test_anthropic_connection "$ANTHROPIC_API_KEY"

    # If JIRA test failed, ask to continue
    if [[ "$jira_ok" == "false" ]]; then
        echo ""
        echo -n "JIRA connection failed. Save configuration anyway? (y/N): "
        read -r confirm
        if [[ ! "$confirm" =~ ^[Yy] ]]; then
            print_error "Configuration cancelled"
            exit 1
        fi
    fi
}

save_configuration() {
    print_section "Saving Configuration"

    # Backup existing ~/.env
    if [[ -f "$ENV_FILE" ]]; then
        local backup_file="${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$ENV_FILE" "$backup_file"
        print_success "Backed up existing ~/.env to $backup_file"
    fi

    # Build new env content
    local new_content=""

    # Preserve existing variables not managed by this script
    if [[ -f "$ENV_FILE" ]]; then
        while IFS= read -r line; do
            # Skip our managed variables
            if [[ "$line" =~ ^(JIRA_SITE_URL|JIRA_EMAIL|JIRA_API_TOKEN|JIRA_PROFILE|ANTHROPIC_API_KEY)= ]]; then
                continue
            fi
            # Skip empty lines and comments at the start
            if [[ -n "$line" ]]; then
                new_content+="$line"$'\n'
            fi
        done < "$ENV_FILE"
    fi

    # Add header if this is a new file or section
    if [[ -z "$new_content" ]] || ! echo "$new_content" | grep -q "# Jira Assistant Skills"; then
        new_content+="# ============================================================================"$'\n'
        new_content+="# Jira Assistant Skills Configuration"$'\n'
        new_content+="# Generated by setup-env.sh on $(date)"$'\n'
        new_content+="# ============================================================================"$'\n'
        new_content+=""$'\n'
    fi

    # Add JIRA configuration
    new_content+="# JIRA Configuration"$'\n'
    new_content+="JIRA_SITE_URL=\"${JIRA_SITE_URL}\""$'\n'
    new_content+="JIRA_EMAIL=\"${JIRA_EMAIL}\""$'\n'
    new_content+="JIRA_API_TOKEN=\"${JIRA_API_TOKEN}\""$'\n'
    if [[ -n "$JIRA_PROFILE" && "$JIRA_PROFILE" != "default" ]]; then
        new_content+="JIRA_PROFILE=\"${JIRA_PROFILE}\""$'\n'
    fi
    new_content+=""$'\n'

    # Add Anthropic configuration if provided
    if [[ -n "$ANTHROPIC_API_KEY" ]]; then
        new_content+="# Anthropic API Configuration (for E2E tests)"$'\n'
        new_content+="ANTHROPIC_API_KEY=\"${ANTHROPIC_API_KEY}\""$'\n'
        new_content+=""$'\n'
    fi

    # Write to file
    echo -n "$new_content" > "$ENV_FILE"

    # Set secure permissions
    chmod 600 "$ENV_FILE"

    print_success "Configuration saved to $ENV_FILE"
    print_success "File permissions set to 600 (owner read/write only)"
}

show_summary() {
    print_section "Configuration Summary"

    echo ""
    echo -e "${BOLD}JIRA Settings:${NC}"
    echo -e "  JIRA_SITE_URL:    $JIRA_SITE_URL"
    echo -e "  JIRA_EMAIL:       $JIRA_EMAIL"
    echo -e "  JIRA_API_TOKEN:   $(mask_secret "$JIRA_API_TOKEN")"
    if [[ -n "$JIRA_PROFILE" && "$JIRA_PROFILE" != "default" ]]; then
        echo -e "  JIRA_PROFILE:     $JIRA_PROFILE"
    fi

    echo ""
    echo -e "${BOLD}Anthropic Settings:${NC}"
    if [[ -n "$ANTHROPIC_API_KEY" ]]; then
        echo -e "  ANTHROPIC_API_KEY: $(mask_secret "$ANTHROPIC_API_KEY")"
    else
        echo -e "  ANTHROPIC_API_KEY: ${YELLOW}(not configured)${NC}"
    fi
}

offer_source() {
    echo ""
    echo -n "Would you like to load the configuration now? (Y/n): "
    read -r confirm

    if [[ "$confirm" =~ ^[Nn] ]]; then
        print_info "Run 'source ~/.env' or restart your shell to load the configuration"
        return 0
    fi

    set -a
    # shellcheck source=/dev/null
    source "$ENV_FILE"
    set +a

    print_success "Configuration loaded into current shell"
}

# ============================================================================
# Main Entry Point
# ============================================================================

main() {
    # Check for required dependencies
    if ! command -v curl &> /dev/null; then
        print_error "curl is required but not installed"
        exit 1
    fi

    print_header

    echo "This script will configure environment variables for ${PROJECT_NAME}."
    echo "Variables will be saved to ~/.env and optionally loaded into your shell."
    echo ""
    echo -n "Continue? (Y/n): "
    read -r confirm

    if [[ "$confirm" =~ ^[Nn] ]]; then
        echo "Setup cancelled."
        exit 0
    fi

    # Configure JIRA
    configure_jira

    # Configure Anthropic (optional)
    configure_anthropic

    # Test connections
    run_connection_tests

    # Save configuration
    save_configuration

    # Add shell loader
    add_env_loader

    # Show summary
    show_summary

    # Offer to source
    offer_source

    echo ""
    print_success "Setup complete!"
    echo ""
    print_info "Next steps:"
    echo "  1. Test JIRA connection:"
    echo "     python skills/jira-issue/scripts/get_issue.py PROJ-123"
    echo ""
    echo "  2. Run E2E tests (if Anthropic key configured):"
    echo "     ./scripts/run-e2e-tests.sh --local"
    echo ""
}

# Run main function
main "$@"
