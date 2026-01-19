#!/bin/bash
# Smoke test suite - quick validation of critical functionality

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Running JSM Smoke Tests..."
echo ""

source venv/bin/activate
export PYTHONPATH="${SCRIPT_DIR}/scripts:${SCRIPT_DIR}/../shared/scripts/lib"

# Run only critical tests
python3 -m pytest tests/ \
    -k "test_create_service_desk or test_create_customer or test_create_request or test_get_sla or test_search_kb" \
    -v \
    --tb=short

echo ""
echo "✅ Smoke tests passed!"
