#!/bin/bash
#
# JIRA Assistant Skills - Unix Installer
#
# One-liner installation:
#   curl -sSL https://raw.githubusercontent.com/YOUR_REPO/main/install.sh | bash
#
# Or clone and run:
#   git clone https://github.com/YOUR_REPO/jira-assistant-skills.git
#   cd jira-assistant-skills
#   ./install.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=8
REPO_URL="https://github.com/YOUR_ORG/jira-assistant-skills.git"
INSTALL_DIR="jira-assistant-skills"

print_header() {
    echo ""
    echo "======================================"
    echo " $1"
    echo "======================================"
}

print_ok() {
    echo -e "  ${GREEN}[OK]${NC} $1"
}

print_warn() {
    echo -e "  ${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "  ${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "  ${BLUE}[i]${NC} $1"
}

# Detect Python interpreter
detect_python() {
    if command -v python3 &> /dev/null; then
        echo "python3"
    elif command -v python &> /dev/null; then
        # Check if python is python3
        local version=$(python -c "import sys; print(sys.version_info.major)" 2>/dev/null)
        if [ "$version" = "3" ]; then
            echo "python"
        else
            echo ""
        fi
    else
        echo ""
    fi
}

# Check Python version
check_python_version() {
    local python_cmd=$1

    local version=$($python_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
    local major=$($python_cmd -c "import sys; print(sys.version_info.major)" 2>/dev/null)
    local minor=$($python_cmd -c "import sys; print(sys.version_info.minor)" 2>/dev/null)

    if [ "$major" -lt "$MIN_PYTHON_MAJOR" ]; then
        return 1
    elif [ "$major" -eq "$MIN_PYTHON_MAJOR" ] && [ "$minor" -lt "$MIN_PYTHON_MINOR" ]; then
        return 1
    fi

    echo "$version"
    return 0
}

# Check if we're in the repo already
check_in_repo() {
    if [ -f "pyproject.toml" ] && [ -d "skills" ]; then
        return 0
    fi
    return 1
}

# Clone or download repository
get_repository() {
    if check_in_repo; then
        print_info "Already in JIRA Assistant Skills directory"
        return 0
    fi

    if [ -d "$INSTALL_DIR" ]; then
        print_info "Directory $INSTALL_DIR already exists"
        cd "$INSTALL_DIR"
        return 0
    fi

    if command -v git &> /dev/null; then
        print_info "Cloning repository..."
        git clone "$REPO_URL" "$INSTALL_DIR" 2>/dev/null || {
            print_warn "Git clone failed. The repository URL may need to be updated."
            print_info "Please clone the repository manually and run setup.py"
            return 1
        }
        cd "$INSTALL_DIR"
    else
        print_warn "Git not found. Please install git or clone the repository manually."
        print_info "Then run: python setup.py"
        return 1
    fi

    return 0
}

# Install Python dependencies
install_dependencies() {
    local python_cmd=$1

    print_info "Installing Python dependencies..."

    # Install the package and its dependencies
    if $python_cmd -m pip install --user -e . 2>/dev/null; then
        print_ok "Package installed"
        # Also install the library
        if $python_cmd -m pip install --user jira-assistant-skills-lib 2>/dev/null; then
            print_ok "Library installed"
            return 0
        fi
    else
        print_warn "pip install failed, trying without --user flag..."
        if $python_cmd -m pip install -e . 2>/dev/null; then
            print_ok "Package installed"
            $python_cmd -m pip install jira-assistant-skills-lib 2>/dev/null
            return 0
        else
            print_error "Failed to install dependencies"
            print_info "Try manually: $python_cmd -m pip install -e . && pip install jira-assistant-skills-lib"
            return 1
        fi
    fi
}

# Main installation
main() {
    print_header "JIRA Assistant Skills - Installer"

    echo ""
    echo "This installer will:"
    echo "  1. Check Python version (3.8+ required)"
    echo "  2. Install Python dependencies"
    echo "  3. Run the interactive setup wizard"
    echo ""

    # Detect Python
    print_info "Detecting Python..."
    PYTHON_CMD=$(detect_python)

    if [ -z "$PYTHON_CMD" ]; then
        print_error "Python 3 not found"
        echo ""
        echo "Please install Python 3.8 or higher:"
        echo ""
        case "$(uname -s)" in
            Darwin)
                echo "  macOS: brew install python3"
                echo "  or download from: https://www.python.org/downloads/"
                ;;
            Linux)
                echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
                echo "  Fedora: sudo dnf install python3 python3-pip"
                echo "  Arch: sudo pacman -S python python-pip"
                ;;
            *)
                echo "  Download from: https://www.python.org/downloads/"
                ;;
        esac
        exit 1
    fi

    # Check version
    VERSION=$(check_python_version "$PYTHON_CMD")
    if [ $? -ne 0 ]; then
        print_error "Python $MIN_PYTHON_MAJOR.$MIN_PYTHON_MINOR+ required (found older version)"
        echo ""
        echo "Please upgrade Python: https://www.python.org/downloads/"
        exit 1
    fi
    print_ok "Python $VERSION found ($PYTHON_CMD)"

    # Get repository
    if ! get_repository; then
        echo ""
        echo "Please clone the repository manually and run:"
        echo "  cd jira-assistant-skills"
        echo "  $PYTHON_CMD setup.py"
        exit 1
    fi

    # Install dependencies
    if ! install_dependencies "$PYTHON_CMD"; then
        exit 1
    fi

    # Run setup wizard
    print_header "Starting Setup Wizard"
    echo ""

    $PYTHON_CMD setup.py
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        print_ok "Installation complete!"
        echo ""
        echo "Quick test:"
        echo "  jira-as issue get PROJ-123"
        echo ""
        echo "Or ask Claude Code:"
        echo '  "Show me my open issues"'
    else
        echo ""
        print_warn "Setup wizard exited with code $EXIT_CODE"
        echo ""
        echo "You can run setup again with:"
        echo "  $PYTHON_CMD setup.py"
    fi

    exit $EXIT_CODE
}

# Run main
main "$@"
