# E2E Testing Container for Jira-Assistant-Skills
# Includes Claude Code CLI, Python, and test infrastructure

FROM node:20-slim

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Set up working directory
WORKDIR /workspace

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python test dependencies
COPY requirements-e2e.txt /tmp/requirements-e2e.txt
RUN pip install --no-cache-dir -r /tmp/requirements-e2e.txt

# Copy the plugin source
COPY . /workspace/plugin-source

# Environment variables
ENV CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
ENV CLAUDE_CODE_SKIP_OOBE=1
ENV CI=true

# Default command
CMD ["python", "-m", "pytest", "tests/e2e/", "-v", "--tb=short"]
