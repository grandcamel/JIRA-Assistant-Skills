#!/bin/bash
# Integration test runner for JSM implementation

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "JSM Integration Test Suite"
echo "========================================"
echo ""

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q pytest pytest-cov requests requests-mock jira

# Set PYTHONPATH
export PYTHONPATH="${SCRIPT_DIR}/scripts:${SCRIPT_DIR}/../shared/scripts/lib"

echo ""
echo "Running test suite..."
echo ""

# Run tests with coverage
python3 -m pytest tests/ \
    --tb=short \
    -v \
    --cov=scripts \
    --cov-report=term-missing \
    --cov-report=html \
    "$@"

echo ""
echo "========================================"
echo "Test execution complete!"
echo "Coverage report: htmlcov/index.html"
echo "========================================"
