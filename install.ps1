#Requires -Version 5.1
<#
.SYNOPSIS
    JIRA Assistant Skills - Windows Installer

.DESCRIPTION
    One-liner installation for Windows PowerShell.

.EXAMPLE
    # Run directly from GitHub
    iwr -useb https://raw.githubusercontent.com/YOUR_REPO/main/install.ps1 | iex

    # Or download and run
    .\install.ps1
#>

$ErrorActionPreference = "Stop"

# Configuration
$MinPythonMajor = 3
$MinPythonMinor = 8
$RepoUrl = "https://github.com/YOUR_ORG/jira-assistant-skills.git"
$InstallDir = "jira-assistant-skills"

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host " $Text" -ForegroundColor Cyan
    Write-Host "======================================" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Text)
    Write-Host "  [OK] $Text" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Text)
    Write-Host "  [!] $Text" -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Text)
    Write-Host "  [ERROR] $Text" -ForegroundColor Red
}

function Write-Info {
    param([string]$Text)
    Write-Host "  [i] $Text" -ForegroundColor Blue
}

function Get-PythonCommand {
    <#
    .SYNOPSIS
        Detect available Python interpreter
    #>

    # Try python3 first
    try {
        $version = & python3 -c "import sys; print(sys.version_info.major)" 2>$null
        if ($version -eq "3") {
            return "python3"
        }
    } catch {}

    # Try python
    try {
        $version = & python -c "import sys; print(sys.version_info.major)" 2>$null
        if ($version -eq "3") {
            return "python"
        }
    } catch {}

    # Try py launcher (Windows)
    try {
        $version = & py -3 -c "import sys; print(sys.version_info.major)" 2>$null
        if ($version -eq "3") {
            return "py -3"
        }
    } catch {}

    return $null
}

function Test-PythonVersion {
    param([string]$PythonCmd)

    try {
        $versionStr = & $PythonCmd.Split()[0] $PythonCmd.Split()[1..99] -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        $parts = $versionStr.Split('.')
        $major = [int]$parts[0]
        $minor = [int]$parts[1]

        if ($major -lt $MinPythonMajor) {
            return $null
        }
        if ($major -eq $MinPythonMajor -and $minor -lt $MinPythonMinor) {
            return $null
        }

        return $versionStr
    } catch {
        return $null
    }
}

function Test-InRepository {
    return (Test-Path "setup.py") -and (Test-Path ".claude\skills")
}

function Get-Repository {
    if (Test-InRepository) {
        Write-Info "Already in JIRA Assistant Skills directory"
        return $true
    }

    if (Test-Path $InstallDir) {
        Write-Info "Directory $InstallDir already exists"
        Set-Location $InstallDir
        return $true
    }

    # Try git clone
    if (Get-Command git -ErrorAction SilentlyContinue) {
        Write-Info "Cloning repository..."
        try {
            git clone $RepoUrl $InstallDir 2>$null
            Set-Location $InstallDir
            return $true
        } catch {
            Write-Warn "Git clone failed. The repository URL may need to be updated."
            Write-Info "Please clone the repository manually and run setup.py"
            return $false
        }
    } else {
        Write-Warn "Git not found. Please install git or clone the repository manually."
        Write-Info "Then run: python setup.py"
        return $false
    }
}

function Install-Dependencies {
    param([string]$PythonCmd)

    $requirements = ".claude\skills\shared\scripts\lib\requirements.txt"

    if (-not (Test-Path $requirements)) {
        Write-Err "Cannot find requirements.txt"
        Write-Info "Expected at: $requirements"
        return $false
    }

    Write-Info "Installing Python dependencies..."

    try {
        # Handle "py -3" style commands
        $cmdParts = $PythonCmd.Split()
        if ($cmdParts.Length -gt 1) {
            & $cmdParts[0] $cmdParts[1..99] -m pip install --user -r $requirements 2>$null
        } else {
            & $PythonCmd -m pip install --user -r $requirements 2>$null
        }

        if ($LASTEXITCODE -eq 0) {
            Write-Ok "Dependencies installed"
            return $true
        }
    } catch {}

    # Try without --user flag
    Write-Warn "Retrying without --user flag..."
    try {
        $cmdParts = $PythonCmd.Split()
        if ($cmdParts.Length -gt 1) {
            & $cmdParts[0] $cmdParts[1..99] -m pip install -r $requirements 2>$null
        } else {
            & $PythonCmd -m pip install -r $requirements 2>$null
        }

        if ($LASTEXITCODE -eq 0) {
            Write-Ok "Dependencies installed"
            return $true
        }
    } catch {}

    Write-Err "Failed to install dependencies"
    Write-Info "Try manually: $PythonCmd -m pip install -r $requirements"
    return $false
}

function Main {
    Write-Header "JIRA Assistant Skills - Installer"

    Write-Host ""
    Write-Host "This installer will:"
    Write-Host "  1. Check Python version (3.8+ required)"
    Write-Host "  2. Install Python dependencies"
    Write-Host "  3. Run the interactive setup wizard"
    Write-Host ""

    # Detect Python
    Write-Info "Detecting Python..."
    $pythonCmd = Get-PythonCommand

    if (-not $pythonCmd) {
        Write-Err "Python 3 not found"
        Write-Host ""
        Write-Host "Please install Python 3.8 or higher:"
        Write-Host ""
        Write-Host "  Download from: https://www.python.org/downloads/"
        Write-Host ""
        Write-Host "  During installation, check 'Add Python to PATH'"
        Write-Host ""
        exit 1
    }

    # Check version
    $version = Test-PythonVersion $pythonCmd
    if (-not $version) {
        Write-Err "Python $MinPythonMajor.$MinPythonMinor+ required"
        Write-Host ""
        Write-Host "Please upgrade Python: https://www.python.org/downloads/"
        exit 1
    }
    Write-Ok "Python $version found ($pythonCmd)"

    # Get repository
    if (-not (Get-Repository)) {
        Write-Host ""
        Write-Host "Please clone the repository manually and run:"
        Write-Host "  cd jira-assistant-skills"
        Write-Host "  $pythonCmd setup.py"
        exit 1
    }

    # Install dependencies
    if (-not (Install-Dependencies $pythonCmd)) {
        exit 1
    }

    # Run setup wizard
    Write-Header "Starting Setup Wizard"
    Write-Host ""

    $cmdParts = $pythonCmd.Split()
    if ($cmdParts.Length -gt 1) {
        & $cmdParts[0] $cmdParts[1..99] setup.py
    } else {
        & $pythonCmd setup.py
    }
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Ok "Installation complete!"
        Write-Host ""
        Write-Host "Quick test:"
        Write-Host "  $pythonCmd .claude\skills\jira-issue\scripts\get_issue.py PROJ-123"
        Write-Host ""
        Write-Host "Or ask Claude Code:"
        Write-Host '  "Show me my open issues"'
    } else {
        Write-Host ""
        Write-Warn "Setup wizard exited with code $exitCode"
        Write-Host ""
        Write-Host "You can run setup again with:"
        Write-Host "  $pythonCmd setup.py"
    }

    exit $exitCode
}

# Run main
Main
