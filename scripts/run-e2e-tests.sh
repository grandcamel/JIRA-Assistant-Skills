#!/bin/bash
# E2E Test Runner for Jira-Assistant-Skills

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

USE_DOCKER=true
VERBOSE=${E2E_VERBOSE:-false}

while [[ $# -gt 0 ]]; do
    case $1 in
        --local) USE_DOCKER=false; shift ;;
        --verbose|-v) VERBOSE=true; export E2E_VERBOSE=true; shift ;;
        --shell)
            cd "$PROJECT_ROOT"
            docker compose -f docker/e2e/docker-compose.yml run --rm e2e-shell
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "  --local     Run locally without Docker"
            echo "  --shell     Open debug shell in Docker"
            echo "  --verbose   Verbose output"
            exit 0
            ;;
        *) echo -e "${RED}Unknown: $1${NC}"; exit 1 ;;
    esac
done

# Check auth
if [[ -n "$ANTHROPIC_API_KEY" ]]; then
    echo -e "${GREEN}✓ API key configured${NC}"
elif [[ -f "$HOME/.claude/credentials.json" ]]; then
    echo -e "${GREEN}✓ OAuth configured${NC}"
else
    echo -e "${RED}✗ No authentication${NC}"
    echo "Set ANTHROPIC_API_KEY or run: claude auth login"
    exit 1
fi

cd "$PROJECT_ROOT"
mkdir -p test-results/e2e

if [[ "$USE_DOCKER" == "true" ]]; then
    echo -e "${YELLOW}Running in Docker...${NC}"
    docker compose -f docker/e2e/docker-compose.yml build e2e-tests
    docker compose -f docker/e2e/docker-compose.yml run --rm e2e-tests
else
    echo -e "${YELLOW}Running locally...${NC}"
    pip install -q -r requirements-e2e.txt
    if [[ "$VERBOSE" == "true" ]]; then
        python -m pytest tests/e2e/ -v --e2e-verbose --tb=short
    else
        python -m pytest tests/e2e/ -v --tb=short
    fi
fi

echo -e "${GREEN}Results: test-results/e2e/${NC}"
