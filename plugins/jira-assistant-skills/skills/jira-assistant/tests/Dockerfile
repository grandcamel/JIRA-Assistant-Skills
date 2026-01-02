FROM node:20-slim

LABEL maintainer="jasonkrue@gmail.com"
LABEL description="Container for running JIRA Assistant Skills routing tests with Claude Code"
LABEL version="1.0.0"

# =============================================================================
# Optional Corporate CA Certificate Injection (e.g., Zscaler)
#
# Usage:
#   Without cert (default): docker build .
#   With Zscaler cert:      docker build --build-arg EXTRA_CA_CERT=zscaler.crt .
#
# The certificate is injected BEFORE any network operations so that
# apt-get, npm install, and pip install all work behind corporate proxies.
# =============================================================================
ARG EXTRA_CA_CERT=NO_EXTRA_CERTS
COPY ${EXTRA_CA_CERT} /tmp/maybe-cert

# Install ca-certificates first (minimal network, usually cached)
# Then conditionally add custom cert if provided
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && if grep -q "BEGIN CERTIFICATE" /tmp/maybe-cert 2>/dev/null; then \
         cp /tmp/maybe-cert /usr/local/share/ca-certificates/extra-ca.crt && \
         update-ca-certificates && \
         echo "✓ Custom CA certificate installed"; \
       else \
         echo "○ No custom CA certificate (using system defaults)"; \
       fi \
    && rm -f /tmp/maybe-cert \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for tools that need explicit cert paths
# These point to the combined system cert bundle (includes custom CA if added)
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt

# Install remaining system dependencies (TLS now works with corporate proxy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Create non-root user for security
RUN useradd -m -s /bin/bash testrunner
USER testrunner
WORKDIR /home/testrunner

# Create virtual environment
RUN python3 -m venv /home/testrunner/venv
ENV PATH="/home/testrunner/venv/bin:$PATH"

# Install Python test dependencies
COPY --chown=testrunner:testrunner requirements-test.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements-test.txt

# Set up Claude Code config directory
ENV CLAUDE_CONFIG_DIR=/home/testrunner/.claude
RUN mkdir -p $CLAUDE_CONFIG_DIR

# Default environment variables for container operation
ENV CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
ENV CHOKIDAR_USEPOLLING=true

# Working directory for tests
WORKDIR /workspace

# Default command runs pytest
ENTRYPOINT ["pytest"]
CMD ["test_routing.py", "-v"]
