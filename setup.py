#!/usr/bin/env python3
"""
JIRA Assistant Skills - Interactive Setup Wizard

Cross-platform setup wizard for configuring JIRA credentials.
Supports system keychain, settings.local.json, and environment variables.

Usage:
    python setup.py                    # Interactive setup
    python setup.py --profile dev      # Set up specific profile
    python setup.py --validate-only    # Test existing credentials
    python setup.py --json-only        # Store in JSON only (skip keychain)
    python setup.py --env-only         # Show environment variable commands
"""

import argparse
import getpass
import os
import platform
import subprocess
import sys
import webbrowser
from pathlib import Path

# Add shared lib to path
SCRIPT_DIR = Path(__file__).parent
LIB_PATH = SCRIPT_DIR / '.claude' / 'skills' / 'shared' / 'scripts' / 'lib'
sys.path.insert(0, str(LIB_PATH))

# Version requirements
MIN_PYTHON_VERSION = (3, 8)
ATLASSIAN_TOKEN_URL = "https://id.atlassian.com/manage-profile/security/api-tokens"


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 50}")
    print(f" {text}")
    print('=' * 50)


def print_step(num: int, text: str) -> None:
    """Print a step header."""
    print(f"\nStep {num}: {text}")
    print("-" * 40)


def print_ok(text: str) -> None:
    """Print success message."""
    print(f"  [OK] {text}")


def print_warn(text: str) -> None:
    """Print warning message."""
    print(f"  [!] {text}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"  [ERROR] {text}")


def check_python_version() -> bool:
    """Check if Python version meets requirements."""
    version = sys.version_info[:2]
    if version >= MIN_PYTHON_VERSION:
        print_ok(f"Python {version[0]}.{version[1]}")
        return True
    else:
        print_error(f"Python {version[0]}.{version[1]} (need {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+)")
        return False


def check_dependencies() -> dict:
    """Check if required dependencies are installed."""
    deps = {
        'requests': False,
        'keyring': False,
    }

    try:
        import requests
        deps['requests'] = True
        print_ok("requests library")
    except ImportError:
        print_warn("requests library not installed")

    try:
        import keyring
        deps['keyring'] = True
        # Detect keychain backend
        backend = keyring.get_keyring()
        backend_name = type(backend).__name__

        # Map to friendly names
        friendly_names = {
            'Keyring': 'macOS Keychain',
            'WinVaultKeyring': 'Windows Credential Manager',
            'SecretService': 'Linux Secret Service',
        }
        friendly = friendly_names.get(backend_name, backend_name)
        print_ok(f"keyring available ({friendly})")
    except ImportError:
        print_warn("keyring not installed (will use JSON storage)")
    except Exception as e:
        print_warn(f"keyring available but backend issue: {e}")

    return deps


def install_dependencies() -> bool:
    """Attempt to install missing dependencies."""
    requirements_path = LIB_PATH / 'requirements.txt'

    if not requirements_path.exists():
        print_error(f"Cannot find requirements.txt at {requirements_path}")
        return False

    print("\nInstalling dependencies...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_path)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_ok("Dependencies installed successfully")
            return True
        else:
            print_error(f"pip install failed: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def get_platform_info() -> dict:
    """Get platform information."""
    info = {
        'system': platform.system(),
        'release': platform.release(),
        'python': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }
    return info


def open_browser_for_token() -> bool:
    """Open browser to Atlassian API token page."""
    print(f"\nOpening browser to: {ATLASSIAN_TOKEN_URL}")
    print("\nInstructions:")
    print("  1. Click 'Create API token'")
    print("  2. Name it 'JIRA Assistant Skills' (or similar)")
    print("  3. Copy the token (you won't see it again!)")

    try:
        webbrowser.open(ATLASSIAN_TOKEN_URL)
        return True
    except Exception as e:
        print_warn(f"Could not open browser: {e}")
        print(f"\nPlease open this URL manually:\n  {ATLASSIAN_TOKEN_URL}")
        return False


def prompt_for_credentials(profile: str) -> tuple:
    """
    Prompt user for JIRA credentials.

    Returns:
        Tuple of (url, email, api_token)
    """
    print(f"\nProfile: {profile}")
    print()

    # URL
    while True:
        url = input("JIRA Site URL (e.g., https://company.atlassian.net): ").strip()
        if url:
            if not url.startswith('https://'):
                if url.startswith('http://'):
                    print_warn("HTTPS is required. Upgrading to HTTPS...")
                    url = 'https://' + url[7:]
                else:
                    url = 'https://' + url
            break
        print("  URL is required. Please enter your JIRA site URL.")

    # Email
    while True:
        email = input("Email address: ").strip()
        if email and '@' in email:
            break
        print("  Please enter a valid email address.")

    # API Token (hidden input)
    while True:
        api_token = getpass.getpass("API Token (hidden): ").strip()
        if api_token:
            break
        print("  API token is required.")

    return url, email, api_token


def validate_and_store(
    url: str,
    email: str,
    api_token: str,
    profile: str,
    json_only: bool = False
) -> bool:
    """
    Validate credentials and store them.

    Returns:
        True if successful, False otherwise
    """
    # Import credential manager
    try:
        from credential_manager import (
            CredentialManager,
            CredentialBackend,
            is_keychain_available,
            validate_credentials
        )
    except ImportError as e:
        print_error(f"Cannot import credential_manager: {e}")
        return False

    # Validate connection
    print("\nValidating connection...")
    try:
        user_info = validate_credentials(url, email, api_token)
        display_name = user_info.get('displayName', 'Unknown')
        account_id = user_info.get('accountId', 'Unknown')
        print_ok(f"Authenticated as: {display_name}")
        print_ok(f"Account ID: {account_id[:8]}...")
    except Exception as e:
        print_error(f"Authentication failed: {e}")
        return False

    # Store credentials
    print("\nStoring credentials...")
    manager = CredentialManager(profile)

    if json_only:
        backend = CredentialBackend.JSON_FILE
    elif is_keychain_available():
        backend = CredentialBackend.KEYCHAIN
    else:
        backend = CredentialBackend.JSON_FILE

    try:
        used_backend = manager.store_credentials(url, email, api_token, profile, backend)
        backend_names = {
            CredentialBackend.KEYCHAIN: "System Keychain",
            CredentialBackend.JSON_FILE: "settings.local.json",
        }
        print_ok(f"Credentials stored in: {backend_names.get(used_backend, used_backend.value)}")
        return True
    except Exception as e:
        print_error(f"Failed to store credentials: {e}")
        return False


def show_env_commands(url: str, email: str, api_token: str, profile: str) -> None:
    """Show environment variable commands for the user's shell."""
    plat = platform.system()

    print("\n" + "=" * 50)
    print(" Environment Variable Commands")
    print("=" * 50)

    if plat == 'Windows':
        print("\nFor PowerShell (current session):")
        print(f'  $env:JIRA_SITE_URL="{url}"')
        print(f'  $env:JIRA_EMAIL="{email}"')
        print(f'  $env:JIRA_API_TOKEN="<your-token>"')

        print("\nFor PowerShell (permanent):")
        print(f'  [Environment]::SetEnvironmentVariable("JIRA_SITE_URL", "{url}", "User")')
        print(f'  [Environment]::SetEnvironmentVariable("JIRA_EMAIL", "{email}", "User")')
        print('  [Environment]::SetEnvironmentVariable("JIRA_API_TOKEN", "<your-token>", "User")')
    else:
        shell = os.environ.get('SHELL', '/bin/bash')

        print(f"\nFor {shell} (current session):")
        print(f'  export JIRA_SITE_URL="{url}"')
        print(f'  export JIRA_EMAIL="{email}"')
        print('  export JIRA_API_TOKEN="<your-token>"')

        if 'zsh' in shell:
            rc_file = '~/.zshrc'
        elif 'bash' in shell:
            rc_file = '~/.bashrc'
        else:
            rc_file = '~/.profile'

        print(f"\nTo make permanent, add to {rc_file}:")
        print(f'  export JIRA_SITE_URL="{url}"')
        print(f'  export JIRA_EMAIL="{email}"')
        print('  export JIRA_API_TOKEN="<your-token>"')

    print("\nNote: Replace <your-token> with your actual API token.")
    print("      Never commit API tokens to version control!")


def validate_existing(profile: str) -> bool:
    """Validate existing credentials without prompting."""
    try:
        from credential_manager import CredentialManager, validate_credentials
    except ImportError as e:
        print_error(f"Cannot import credential_manager: {e}")
        return False

    print(f"\nValidating credentials for profile: {profile}")

    manager = CredentialManager(profile)
    try:
        url, email, api_token = manager.get_credentials(profile)
        print_ok(f"Found credentials for: {email}")
        print_ok(f"Site URL: {url}")

        user_info = validate_credentials(url, email, api_token)
        display_name = user_info.get('displayName', 'Unknown')
        print_ok(f"Authenticated as: {display_name}")
        return True
    except Exception as e:
        print_error(f"Validation failed: {e}")
        return False


def run_setup(args: argparse.Namespace) -> int:
    """Run the setup wizard."""
    print_header("JIRA Assistant Skills - Setup Wizard")

    # Check environment
    print("\nChecking environment...")
    if not check_python_version():
        return 1

    deps = check_dependencies()

    # If requests is missing, we can't continue
    if not deps['requests']:
        print("\nMissing required dependencies. Attempting to install...")
        if not install_dependencies():
            print("\nPlease install dependencies manually:")
            print(f"  pip install -r {LIB_PATH / 'requirements.txt'}")
            return 1
        # Re-check
        deps = check_dependencies()
        if not deps['requests']:
            return 1

    # Validate-only mode
    if args.validate_only:
        success = validate_existing(args.profile)
        return 0 if success else 1

    # Step 1: Get API Token
    print_step(1, "Get JIRA API Token")

    if not args.no_browser:
        open_browser_for_token()
        input("\nPress Enter when you have your API token ready...")
    else:
        print(f"\nGet an API token at:\n  {ATLASSIAN_TOKEN_URL}")

    # Step 2: Enter Credentials
    print_step(2, "Enter Credentials")
    url, email, api_token = prompt_for_credentials(args.profile)

    # Step 3: Validate Connection
    print_step(3, "Validating Connection")

    # Step 4: Store Credentials
    print_step(4, "Storing Credentials")

    if args.env_only:
        show_env_commands(url, email, api_token, args.profile)
        print("\n" + "=" * 50)
        print(" Setup Instructions")
        print("=" * 50)
        print("\nSet the environment variables above, then test with:")
        print(f"  python .claude/skills/jira-issue/scripts/get_issue.py PROJ-123")
        return 0

    success = validate_and_store(url, email, api_token, args.profile, args.json_only)

    if not success:
        return 1

    # Success!
    print("\n" + "=" * 50)
    print(" Setup Complete!")
    print("=" * 50)

    print("\nYou can now use JIRA Assistant Skills:")
    print()
    print("  # Test with a known issue key")
    print("  python .claude/skills/jira-issue/scripts/get_issue.py PROJ-123")
    print()
    print("  # Or ask Claude Code:")
    print('  "Show me my open issues"')
    print('  "What\'s blocking the release?"')
    print('  "Create a bug for the login page crash"')

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="JIRA Assistant Skills - Setup Wizard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py                    # Interactive setup
  python setup.py --profile dev      # Set up 'dev' profile
  python setup.py --validate-only    # Test existing credentials
  python setup.py --json-only        # Use JSON storage (skip keychain)
  python setup.py --env-only         # Show env var commands only
  python setup.py --no-browser       # Don't open browser
        """
    )

    parser.add_argument(
        '--profile',
        default='production',
        help="Profile name (default: production)"
    )
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help="Don't open browser for API token page"
    )
    parser.add_argument(
        '--json-only',
        action='store_true',
        help="Store in settings.local.json only (skip keychain)"
    )
    parser.add_argument(
        '--env-only',
        action='store_true',
        help="Show environment variable commands only"
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help="Validate existing credentials without setup"
    )

    args = parser.parse_args()

    try:
        return run_setup(args)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        return 130


if __name__ == '__main__':
    sys.exit(main())
