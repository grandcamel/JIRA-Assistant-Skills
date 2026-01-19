FROM node:20-bookworm

LABEL maintainer="jasonkrue@gmail.com"
LABEL description="Batteries-included developer container with Claude Code and common toolchains"
LABEL version="1.0.0"

# =============================================================================
# Optional Corporate CA Certificate Injection (e.g., Zscaler)
#
# Usage:
#   Without cert (default): docker build .
#   With Zscaler cert:      docker build --build-arg EXTRA_CA_CERT=zscaler.crt .
# =============================================================================
ARG EXTRA_CA_CERT=NO_EXTRA_CERTS
COPY ${EXTRA_CA_CERT} /tmp/maybe-cert

# Install ca-certificates and conditionally add custom cert
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

# Set certificate environment variables
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt

# =============================================================================
# Core Development Tools
# =============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Python ecosystem
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    # Build essentials
    build-essential \
    cmake \
    pkg-config \
    # Version control
    git \
    git-lfs \
    # Network tools
    curl \
    wget \
    httpie \
    openssh-client \
    # JSON/YAML processing
    jq \
    yq \
    # Text processing
    ripgrep \
    fd-find \
    fzf \
    tree \
    less \
    vim-tiny \
    # System utilities
    htop \
    procps \
    lsof \
    # Archive tools
    zip \
    unzip \
    tar \
    gzip \
    # Shell utilities
    bash-completion \
    shellcheck \
    # Database clients
    postgresql-client \
    default-mysql-client \
    redis-tools \
    sqlite3 \
    # Misc
    gnupg \
    ca-certificates \
    sudo \
    && rm -rf /var/lib/apt/lists/* \
    # Create symlinks for Debian package naming differences
    && ln -sf /usr/bin/fdfind /usr/local/bin/fd

# =============================================================================
# Go Language
# =============================================================================
ARG GO_VERSION=1.22.0
RUN curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" | tar -C /usr/local -xzf -
ENV PATH="/usr/local/go/bin:$PATH"
ENV GOPATH="/home/devuser/go"
ENV PATH="$GOPATH/bin:$PATH"

# =============================================================================
# Rust Language
# =============================================================================
ENV RUSTUP_HOME=/usr/local/rustup
ENV CARGO_HOME=/usr/local/cargo
ENV PATH="/usr/local/cargo/bin:$PATH"
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable --profile minimal \
    && chmod -R a+rwx $RUSTUP_HOME $CARGO_HOME

# =============================================================================
# Node.js Global Tools (Node already in base image)
# =============================================================================
# Note: yarn is already included in node:20-bookworm base image
RUN npm install -g \
    @anthropic-ai/claude-code \
    typescript \
    ts-node \
    eslint \
    prettier \
    pnpm

# =============================================================================
# Python Global Tools
# =============================================================================
RUN pip3 install --no-cache-dir --break-system-packages \
    pipx \
    uv \
    poetry \
    black \
    ruff \
    mypy \
    pytest \
    pytest-asyncio \
    pytest-xdist \
    httpx \
    rich \
    typer \
    pyyaml \
    tabulate

# Add pipx and uv paths
ENV PATH="/root/.local/bin:$PATH"

# =============================================================================
# Cloud CLI Tools (optional, comment out to reduce image size)
# =============================================================================
# AWS CLI v2
RUN curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" \
    && unzip -q /tmp/awscliv2.zip -d /tmp \
    && /tmp/aws/install \
    && rm -rf /tmp/aws /tmp/awscliv2.zip

# GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Docker CLI (for Docker-in-Docker or Docker socket mounting)
# =============================================================================
RUN curl -fsSL https://get.docker.com | sh \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Create non-root user (handle existing GID/UID from base image)
# =============================================================================
ARG USERNAME=devuser
ARG USER_UID=1000
ARG USER_GID=1000

# Create group if it doesn't exist, create user if it doesn't exist
# The node:20-bookworm image already has uid/gid 1000 (node user)
RUN if ! getent group $USER_GID >/dev/null; then groupadd --gid $USER_GID $USERNAME; fi \
    && if ! id -u $USER_UID >/dev/null 2>&1; then \
         useradd --uid $USER_UID --gid $USER_GID -m -s /bin/bash $USERNAME; \
       else \
         # User exists, just rename if needed and ensure home dir setup
         existing_user=$(getent passwd $USER_UID | cut -d: -f1); \
         if [ "$existing_user" != "$USERNAME" ]; then \
           usermod -l $USERNAME -d /home/$USERNAME -m $existing_user 2>/dev/null || true; \
         fi; \
       fi \
    && mkdir -p /home/$USERNAME/.claude \
    && mkdir -p /home/$USERNAME/go \
    && chown -R $USER_UID:$USER_GID /home/$USERNAME

# Add user to docker group if it exists
RUN usermod -aG docker $USERNAME 2>/dev/null || true

# Enable passwordless sudo for the user (for runtime package installation)
RUN echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

USER $USERNAME
WORKDIR /home/$USERNAME

# =============================================================================
# User Python Environment
# =============================================================================
RUN python3 -m venv /home/$USERNAME/venv
ENV PATH="/home/$USERNAME/venv/bin:$PATH"
ENV VIRTUAL_ENV="/home/$USERNAME/venv"

# Install common Python packages in user venv
RUN pip install --no-cache-dir \
    ipython \
    jupyter \
    requests \
    httpx \
    aiohttp \
    boto3 \
    pandas \
    numpy

# =============================================================================
# Shell Configuration
# =============================================================================
RUN echo 'export PS1="\[\033[01;32m\]dev\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ "' >> ~/.bashrc \
    && echo 'alias ll="ls -la"' >> ~/.bashrc \
    && echo 'alias la="ls -A"' >> ~/.bashrc \
    && echo 'alias l="ls -CF"' >> ~/.bashrc \
    && echo 'alias ..="cd .."' >> ~/.bashrc \
    && echo 'alias ...="cd ../.."' >> ~/.bashrc \
    && echo 'alias gs="git status"' >> ~/.bashrc \
    && echo 'alias gd="git diff"' >> ~/.bashrc \
    && echo 'alias gl="git log --oneline -20"' >> ~/.bashrc \
    && echo 'alias k="kubectl"' >> ~/.bashrc \
    && echo '[ -f /usr/share/bash-completion/bash_completion ] && . /usr/share/bash-completion/bash_completion' >> ~/.bashrc

# Claude Code config
ENV CLAUDE_CONFIG_DIR=/home/$USERNAME/.claude
ENV CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1

# =============================================================================
# Working Directory & Entrypoint
# =============================================================================
WORKDIR /workspace

# Default to interactive bash
ENTRYPOINT ["/bin/bash"]
CMD ["-l"]
