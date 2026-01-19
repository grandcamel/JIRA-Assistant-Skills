# claude-devcontainer

A batteries-included developer container optimized for Claude Code, featuring modern CLI tools and instant-start enhanced environments.

## Features

- **Claude Code Optimized**: Pre-installed Claude Code with OAuth and API key authentication support
- **Batteries Included**: Python 3, Node.js 20, Go 1.22, Rust, AWS CLI, GitHub CLI, database clients
- **Modern CLI Tools**: Starship prompt, eza, bat, delta, zoxide, btop, lazygit, tmux, neovim
- **Flexible Modes**: Standard, sandboxed, workspace, and enhanced configurations
- **Private Registry Support**: Build and push custom images to your organization's registry
- **Runtime Customization**: Install additional packages at startup without rebuilding

## Quick Start

```bash
# Clone the repository
git clone https://github.com/grandcamel/claude-devcontainer.git
cd claude-devcontainer

# Run with current directory mounted
./scripts/run.sh

# Run with a specific project
./scripts/run.sh --project ~/myproject

# Run with enhanced CLI tools (runtime installation)
./scripts/run.sh --enhanced

# Use pre-built enhanced image (instant startup)
./scripts/run.sh --use-enhanced
```

## Docker Hub Images

Pre-built images are available on Docker Hub:

```bash
# Base image
docker pull grandcamel/claude-devcontainer:latest

# Enhanced image (with modern CLI tools pre-installed)
docker pull grandcamel/claude-devcontainer:enhanced
```

## Installation Options

### Option 1: Clone Repository

```bash
git clone https://github.com/grandcamel/claude-devcontainer.git
cd claude-devcontainer
./scripts/run.sh
```

### Option 2: Use as Git Submodule

```bash
git submodule add https://github.com/grandcamel/claude-devcontainer.git devcontainer
./devcontainer/scripts/run.sh --project .
```

### Option 3: Pull Docker Image Directly

```bash
docker run -it -v $(pwd):/workspace/project grandcamel/claude-devcontainer:enhanced
```

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/run.sh` | Main developer container runner |
| `scripts/build-enhanced.sh` | Build pre-configured enhanced image |
| `scripts/build-team-image.sh` | Generate team-customized Dockerfile from config |
| `scripts/publish-to-registry.sh` | Publish team image to private registry |

## Configuration Options

### run.sh Options

```
Usage: ./scripts/run.sh [options] [-- command...]

Options:
  --project, -p PATH    Mount project directory (default: current directory)
  --docker              Mount Docker socket for Docker-in-Docker
  --persist-cache       Persist Go, Cargo, npm caches across sessions
  --port, -P PORT       Expose port (can be used multiple times)
  --env, -e VAR=VAL     Set environment variable
  --volume, -v SRC:DST  Mount additional volume
  --name NAME           Container name (for reattaching)
  --detach, -d          Run in background
  --build               Rebuild Docker image before running
  --model NAME          Claude model (sonnet, haiku, opus)
  --claude-version VER  Use specific Claude Code version (e.g., 2.0.69)

Custom Image:
  --image NAME          Custom image name (e.g., registry.company.com/team/dev)
  --tag TAG             Custom image tag (default: latest)
  --push                Push image to registry after building
  --use-enhanced        Use pre-built enhanced image (instant startup)

Additional Packages:
  --pip PKG[,PKG,...]   Install Python packages at startup
  --npm PKG[,PKG,...]   Install npm packages globally at startup
  --apt PKG[,PKG,...]   Install system packages via apt at startup

Enhanced Mode:
  --enhanced            Install enhanced CLI tools at runtime

Authentication:
  (default)             Use OAuth from macOS Keychain
  --api-key             Use ANTHROPIC_API_KEY environment variable
  --api-key-from-config Use primaryApiKey from ~/.claude.json
```

## Enhanced Tools

The enhanced configuration includes these modern CLI replacements:

| Tool | Replaces | Description |
|------|----------|-------------|
| Starship | PS1 | Fast, customizable prompt |
| eza | ls | ls with icons and git status |
| bat | cat | Syntax highlighting |
| delta | diff | Better git diffs |
| zoxide | cd | Smart directory jumping |
| btop | top | Modern system monitor |
| lazygit | - | Git terminal UI |
| tmux | - | Terminal multiplexer (Ctrl-a prefix) |
| neovim | vim | Modern editor + kickstart config |
| direnv | - | Per-directory environments |

## Building Custom Images

### Team Customization

Create a team-specific container with your organization's CA certificate and standard packages:

```bash
# Create a team config file (see examples/team-config.yaml)
cat > team-config.yaml << 'EOF'
image:
  base: grandcamel/claude-devcontainer:enhanced
  name: my-company/dev-container
  tag: latest

certificate:
  file: zscaler.crt

pip:
  - flask
  - sqlalchemy
  - boto3

npm:
  - typescript
  - "@types/node"

apt:
  - graphviz
  - libpq-dev

environment:
  TEAM_NAME: "Platform Engineering"

labels:
  maintainer: "platform-team@company.com"
EOF

# Generate Dockerfile.team (for version control)
./scripts/build-team-image.sh --config team-config.yaml

# Generate and build in one step
./scripts/build-team-image.sh --config team-config.yaml --build

# Build and push to registry
./scripts/build-team-image.sh --config team-config.yaml --build --push
```

The generated `Dockerfile.team` can be committed to version control for reproducible builds across your team.

### Publishing to Private Registries

For self-hosted registries (Harbor, Nexus, GitLab Registry), use the publish script:

```bash
# 1. Create your team config (see examples/team-config-private-registry.yaml)
cp examples/team-config-private-registry.yaml team-config.yaml

# 2. Add your corporate CA certificate (if needed)
cp /path/to/corporate-ca.crt .

# 3. Create a git tag for versioning
git tag v1.0.0

# 4. Publish to registry (will prompt for credentials)
./scripts/publish-to-registry.sh \
  --config team-config.yaml \
  --registry harbor.company.com

# Or with credentials for scripting
./scripts/publish-to-registry.sh \
  --config team-config.yaml \
  --registry harbor.company.com \
  --user deployer \
  --token $REGISTRY_TOKEN
```

**Dry run** to see what would happen:
```bash
./scripts/publish-to-registry.sh \
  --config team-config.yaml \
  --registry harbor.company.com \
  --dry-run
```

**Team members** can then pull and use the image:
```bash
# Pull the image
docker pull harbor.company.com/platform/dev-container:1.0.0

# Or use with run.sh
./scripts/run.sh --image harbor.company.com/platform/dev-container --tag 1.0.0
```

### Quick Build for Private Registries

For simpler cases without a config file:

```bash
# Build and push to private registry
./scripts/build-enhanced.sh \
  --image registry.company.com/team/claude-dev \
  --tag v1.0 \
  --push

# Use the custom image
./scripts/run.sh --image registry.company.com/team/claude-dev --tag v1.0
```

### With Corporate CA Certificate

```bash
# Build with Zscaler or other corporate proxy certificate
./scripts/build-enhanced.sh --ca-cert zscaler.crt
```

## Included Toolchains

### Languages
- Python 3.11 with pip, venv, poetry, uv
- Node.js 20 with npm, yarn, pnpm
- Go 1.22
- Rust (stable)

### Cloud & DevOps
- AWS CLI v2
- GitHub CLI (gh)
- Docker CLI

### Database Clients
- PostgreSQL (psql)
- MySQL
- Redis (redis-cli)
- SQLite

### Development Tools
- git, git-lfs
- jq, yq
- ripgrep, fd, fzf
- httpie
- shellcheck
- make, cmake, gcc

### Python Packages
- pytest, black, ruff, mypy
- httpx, rich, typer
- ipython, jupyter
- pandas, numpy

### Node.js Packages
- TypeScript, ts-node
- ESLint, Prettier

## Architecture

```
claude-devcontainer/
├── Dockerfile              # Base image
├── Dockerfile.enhanced     # Pre-built enhanced image
├── lib/
│   └── container.sh        # Shared shell functions
├── scripts/
│   ├── run.sh              # Main runner
│   ├── run-sandboxed.sh    # Sandboxed runner
│   ├── run-workspace.sh    # Workspace runner
│   ├── build-enhanced.sh   # Enhanced image builder
│   └── run-tests.sh        # Test runner
└── config/
    ├── starship.toml       # Starship prompt config
    ├── tmux.conf           # Tmux configuration
    └── setup-enhanced.sh   # Runtime enhancement script
```

## Using as a Submodule

To integrate into your project:

```bash
# Add as submodule
git submodule add https://github.com/grandcamel/claude-devcontainer.git .devcontainer

# Create a wrapper script in your project root
cat > run-dev.sh << 'EOF'
#!/bin/bash
./.devcontainer/scripts/run.sh --project . "$@"
EOF
chmod +x run-dev.sh

# Use it
./run-dev.sh --enhanced
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | API key for Claude (with --api-key flag) |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | Set to 1 in container |
| `CLAUDE_PLUGIN_DIR` | Plugin directory mount point |

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Anthropic](https://anthropic.com) for Claude Code
- [Starship](https://starship.rs) prompt
- [kickstart.nvim](https://github.com/nvim-lua/kickstart.nvim) for neovim configuration
