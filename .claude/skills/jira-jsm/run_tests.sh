#!/bin/bash
# Integration test runner for JSM implementation

set -e

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
export PYTHONPATH="/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/jira-jsm/scripts:/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/shared/scripts/lib"

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
