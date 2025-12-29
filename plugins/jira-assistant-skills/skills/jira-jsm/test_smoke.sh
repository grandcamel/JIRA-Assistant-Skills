#!/bin/bash
# Smoke test suite - quick validation of critical functionality

set -e

echo "Running JSM Smoke Tests..."
echo ""

source venv/bin/activate
export PYTHONPATH="/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/jira-jsm/scripts:/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/shared/scripts/lib"

# Run only critical tests
python3 -m pytest tests/ \
    -k "test_create_service_desk or test_create_customer or test_create_request or test_get_sla or test_search_kb" \
    -v \
    --tb=short

echo ""
echo "✅ Smoke tests passed!"
