#!/usr/bin/env bash
#
# Enhanced Developer Environment Setup
#
# Installs and configures modern CLI tools for a superior development experience:
#   - Starship prompt (fast, customizable)
#   - eza (modern ls replacement)
#   - bat (cat with syntax highlighting)
#   - delta (better git diff)
#   - zoxide (smarter cd)
#   - btop (modern system monitor)
#   - lazygit (terminal UI for git)
#   - tmux (terminal multiplexer)
#   - neovim + kickstart (modern editor)
#   - direnv (per-directory environment)
#
# This script is designed to be run once at container startup.

set -e

ENHANCED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASHRC="$HOME/.bashrc"
ENHANCED_MARKER="$HOME/.enhanced-setup-complete"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo_step() {
    echo -e "${BLUE}==>${NC} ${CYAN}$1${NC}"
}

echo_substep() {
    echo -e "    ${GREEN}✓${NC} $1"
}

echo_warn() {
    echo -e "    ${YELLOW}⚠${NC} $1"
}

echo_error() {
    echo -e "    ${RED}✗${NC} $1"
}

# =============================================================================
# Check if already set up
# =============================================================================
if [[ -f "$ENHANCED_MARKER" ]]; then
    echo -e "${GREEN}Enhanced environment already configured.${NC}"
    exit 0
fi

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}       ${YELLOW}Enhanced Developer Environment Setup${NC}                  ${CYAN}║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# =============================================================================
# Install System Packages
# =============================================================================
echo_step "Installing system packages..."

sudo apt-get update -qq

# Core packages
sudo apt-get install -y -qq \
    tmux \
    neovim \
    direnv \
    btop \
    bat \
    > /dev/null 2>&1

echo_substep "tmux, neovim, direnv, btop, bat"

# Create bat symlink (Debian names it batcat)
if [[ -f /usr/bin/batcat ]] && [[ ! -f /usr/local/bin/bat ]]; then
    sudo ln -sf /usr/bin/batcat /usr/local/bin/bat
    echo_substep "bat symlink created"
fi

# =============================================================================
# Install Starship Prompt
# =============================================================================
echo_step "Installing Starship prompt..."

if ! command -v starship &> /dev/null; then
    curl -sS https://starship.rs/install.sh | sh -s -- -y > /dev/null 2>&1
    echo_substep "Starship installed"
else
    echo_substep "Starship already installed"
fi

# Copy starship config
mkdir -p "$HOME/.config"
cp "$ENHANCED_DIR/starship.toml" "$HOME/.config/starship.toml"
echo_substep "Starship config installed"

# =============================================================================
# Install eza (modern ls)
# =============================================================================
echo_step "Installing eza (modern ls)..."

if ! command -v eza &> /dev/null; then
    # Install via cargo (most reliable cross-platform method)
    cargo install eza --quiet 2>/dev/null || {
        echo_warn "eza installation via cargo failed, trying apt..."
        # Fallback: try apt if available in repos
        sudo apt-get install -y -qq eza 2>/dev/null || echo_warn "eza not available, using exa fallback"
    }
fi

if command -v eza &> /dev/null; then
    echo_substep "eza installed"
elif command -v exa &> /dev/null; then
    echo_substep "exa available (eza predecessor)"
else
    echo_warn "eza/exa not available, ls aliases will use standard ls"
fi

# =============================================================================
# Install delta (git diff)
# =============================================================================
echo_step "Installing delta (better git diff)..."

if ! command -v delta &> /dev/null; then
    cargo install git-delta --quiet 2>/dev/null || echo_warn "delta installation failed"
fi

if command -v delta &> /dev/null; then
    echo_substep "delta installed"

    # Configure git to use delta
    git config --global core.pager delta
    git config --global interactive.diffFilter "delta --color-only"
    git config --global delta.navigate true
    git config --global delta.light false
    git config --global delta.line-numbers true
    git config --global delta.side-by-side false
    git config --global merge.conflictStyle diff3
    git config --global diff.colorMoved default
    echo_substep "git configured to use delta"
else
    echo_warn "delta not available, using default git diff"
fi

# =============================================================================
# Install zoxide (smart cd)
# =============================================================================
echo_step "Installing zoxide (smart cd)..."

if ! command -v zoxide &> /dev/null; then
    cargo install zoxide --quiet 2>/dev/null || echo_warn "zoxide installation failed"
fi

if command -v zoxide &> /dev/null; then
    echo_substep "zoxide installed"
else
    echo_warn "zoxide not available"
fi

# =============================================================================
# Install lazygit
# =============================================================================
echo_step "Installing lazygit..."

if ! command -v lazygit &> /dev/null; then
    LAZYGIT_VERSION=$(curl -s "https://api.github.com/repos/jesseduffield/lazygit/releases/latest" | grep -Po '"tag_name": "v\K[^"]*' 2>/dev/null || echo "0.44.1")
    curl -sLo /tmp/lazygit.tar.gz "https://github.com/jesseduffield/lazygit/releases/latest/download/lazygit_${LAZYGIT_VERSION}_Linux_x86_64.tar.gz" 2>/dev/null
    if [[ -f /tmp/lazygit.tar.gz ]]; then
        sudo tar -xzf /tmp/lazygit.tar.gz -C /usr/local/bin lazygit 2>/dev/null
        rm /tmp/lazygit.tar.gz
        echo_substep "lazygit installed"
    else
        echo_warn "lazygit download failed"
    fi
else
    echo_substep "lazygit already installed"
fi

# =============================================================================
# Configure tmux
# =============================================================================
echo_step "Configuring tmux..."

cp "$ENHANCED_DIR/tmux.conf" "$HOME/.tmux.conf"
echo_substep "tmux config installed (Ctrl-a prefix, mouse enabled)"

# =============================================================================
# Configure neovim with kickstart
# =============================================================================
echo_step "Configuring neovim with kickstart..."

NVIM_CONFIG="$HOME/.config/nvim"
if [[ ! -d "$NVIM_CONFIG" ]]; then
    git clone --depth 1 https://github.com/nvim-lua/kickstart.nvim.git "$NVIM_CONFIG" 2>/dev/null
    echo_substep "kickstart.nvim installed"
else
    echo_substep "nvim config already exists"
fi

# =============================================================================
# Configure Shell Integration
# =============================================================================
echo_step "Configuring shell integration..."

# Create enhanced bashrc additions
cat >> "$BASHRC" << 'ENHANCED_BASHRC'

# =============================================================================
# Enhanced Developer Environment
# =============================================================================

# Starship prompt
if command -v starship &> /dev/null; then
    eval "$(starship init bash)"
fi

# Zoxide (smart cd)
if command -v zoxide &> /dev/null; then
    eval "$(zoxide init bash)"
    alias cd='z'
fi

# Direnv
if command -v direnv &> /dev/null; then
    eval "$(direnv hook bash)"
fi

# Modern CLI aliases
if command -v eza &> /dev/null; then
    alias ls='eza --icons'
    alias ll='eza -la --icons --git'
    alias la='eza -a --icons'
    alias lt='eza --tree --icons --level=2'
    alias tree='eza --tree --icons'
elif command -v exa &> /dev/null; then
    alias ls='exa --icons'
    alias ll='exa -la --icons --git'
    alias la='exa -a --icons'
    alias lt='exa --tree --icons --level=2'
fi

if command -v bat &> /dev/null; then
    alias cat='bat --paging=never'
    alias catp='bat'  # bat with paging
    export MANPAGER="sh -c 'col -bx | bat -l man -p'"
fi

if command -v btop &> /dev/null; then
    alias top='btop'
fi

# Git aliases (enhanced)
alias lg='lazygit'
alias gst='git status'
alias gd='git diff'
alias gds='git diff --staged'
alias glog='git log --oneline --graph --decorate -20'

# Useful shortcuts
alias cls='clear'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias mkdir='mkdir -pv'
alias path='echo -e ${PATH//:/\\n}'

# Enhanced history
export HISTSIZE=10000
export HISTFILESIZE=20000
export HISTCONTROL=ignoreboth:erasedups
shopt -s histappend

# Better tab completion
bind 'set show-all-if-ambiguous on'
bind 'set completion-ignore-case on'
bind 'TAB:menu-complete'

ENHANCED_BASHRC

echo_substep "Shell aliases and integrations configured"

# =============================================================================
# Mark setup as complete
# =============================================================================
touch "$ENHANCED_MARKER"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}       ${CYAN}Enhanced environment ready!${NC}                            ${GREEN}║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${YELLOW}Quick reference:${NC}"
echo -e "    ${CYAN}ls, ll, lt${NC}     - eza with icons and git status"
echo -e "    ${CYAN}cat${NC}            - bat with syntax highlighting"
echo -e "    ${CYAN}cd / z${NC}         - zoxide smart directory jumping"
echo -e "    ${CYAN}lg${NC}             - lazygit terminal UI"
echo -e "    ${CYAN}top${NC}            - btop system monitor"
echo -e "    ${CYAN}tmux${NC}           - Ctrl-a prefix, mouse enabled"
echo -e "    ${CYAN}nvim${NC}           - neovim with kickstart config"
echo ""
