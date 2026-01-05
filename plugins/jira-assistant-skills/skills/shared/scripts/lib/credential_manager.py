"""
Credential management for JIRA Assistant Skills.

Provides secure credential retrieval from multiple sources:
1. Environment variables (JIRA_API_TOKEN, JIRA_EMAIL, JIRA_SITE_URL) - primary
2. System keychain (via keyring library) - fallback

Security considerations:
- Never logs or prints credentials
- Uses sanitize_error_message() from error_handler for exception messages
- Keychain service name includes profile for multi-instance support
"""

import gc
import json
import os
import stat
from enum import Enum
from pathlib import Path
from typing import Any

from validators import validate_email, validate_url

from jira_assistant_skills_lib import (
    AuthenticationError,
    JiraError,
    ValidationError,
    sanitize_error_message,
)

# Try to import keyring, gracefully handle if not installed
try:
    import keyring

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


class CredentialBackend(Enum):
    """Available credential storage backends."""

    KEYCHAIN = (
        "keychain"  # macOS Keychain, Windows Credential Manager, Linux Secret Service
    )
    JSON_FILE = "json_file"  # settings.local.json
    ENVIRONMENT = "environment"  # Environment variables (read-only for retrieval)


class CredentialNotFoundError(JiraError):
    """Raised when credentials cannot be found in any backend."""

    def __init__(self, profile: str = "default", **kwargs):
        message = f"No credentials found for profile '{profile}'"
        hint = "\n\nTo set up credentials, run:\n"
        hint += "  python setup.py\n\n"
        hint += "Or set environment variables:\n"
        hint += "  export JIRA_API_TOKEN='your-token'\n"
        hint += "  export JIRA_EMAIL='your-email'\n"
        hint += "  export JIRA_SITE_URL='https://your-site.atlassian.net'\n\n"
        hint += "Get an API token at:\n"
        hint += "  https://id.atlassian.com/manage-profile/security/api-tokens"
        super().__init__(message + hint, **kwargs)


class CredentialManager:
    """
    Manages JIRA credentials across multiple storage backends.

    Priority for retrieval:
    1. Environment variables (JIRA_API_TOKEN, JIRA_EMAIL, JIRA_SITE_URL)
    2. System keychain (if keyring available)
    3. settings.local.json

    Priority for storage:
    1. System keychain (if keyring available)
    2. settings.local.json (fallback)
    """

    KEYCHAIN_SERVICE = "jira-assistant"

    def __init__(self, profile: str = "production"):
        """
        Initialize credential manager.

        Args:
            profile: Profile name for keychain namespacing (default: production)
        """
        self.profile = profile
        self._claude_dir = self._find_claude_dir()

    def _find_claude_dir(self) -> Path | None:
        """
        Find .claude directory by walking up from current directory.

        Returns:
            Path to .claude directory or None if not found
        """
        current = Path.cwd()

        while current != current.parent:
            claude_dir = current / ".claude"
            if claude_dir.is_dir():
                return claude_dir
            current = current.parent

        return None

    def _get_keychain_service(self, profile: str | None = None) -> str:
        """Get keychain service name for a profile."""
        profile = profile or self.profile
        return f"{self.KEYCHAIN_SERVICE}-{profile}"

    @staticmethod
    def is_keychain_available() -> bool:
        """
        Check if keyring is installed and functional.

        Returns:
            True if keyring is available and working, False otherwise
        """
        if not KEYRING_AVAILABLE:
            return False

        try:
            # Test keyring functionality with a dummy operation
            # This verifies the backend is properly configured
            keyring.get_keyring()
            return True
        except Exception:
            return False

    def get_credentials_from_env(
        self, profile: str | None = None
    ) -> tuple[str | None, str | None, str | None]:
        """
        Get credentials from environment variables.

        Args:
            profile: Profile name (used for profile-specific token lookup)

        Returns:
            Tuple of (url, email, api_token) - any may be None if not set
        """
        profile = profile or self.profile

        url = os.getenv("JIRA_SITE_URL")
        email = os.getenv("JIRA_EMAIL")

        # Try profile-specific token first, then generic
        api_token = os.getenv(f"JIRA_API_TOKEN_{profile.upper()}")
        if not api_token:
            api_token = os.getenv("JIRA_API_TOKEN")

        return url, email, api_token

    def get_credentials_from_keychain(
        self, profile: str | None = None
    ) -> tuple[str | None, str | None, str | None]:
        """
        Get credentials from system keychain.

        Args:
            profile: Profile name

        Returns:
            Tuple of (url, email, api_token) - all None if not found or keychain unavailable
        """
        if not self.is_keychain_available():
            return None, None, None

        profile = profile or self.profile
        service = self._get_keychain_service(profile)

        try:
            # We store as JSON: {"url": "...", "email": "...", "api_token": "..."}
            credential_json = keyring.get_password(service, "credentials")
            if not credential_json:
                return None, None, None

            creds = json.loads(credential_json)
            return creds.get("url"), creds.get("email"), creds.get("api_token")
        except Exception:
            return None, None, None

    def get_credentials_from_json(
        self, profile: str | None = None
    ) -> tuple[str | None, str | None, str | None]:
        """
        Get credentials from settings.local.json.

        Args:
            profile: Profile name

        Returns:
            Tuple of (url, email, api_token) - any may be None if not found
        """
        if not self._claude_dir:
            return None, None, None

        profile = profile or self.profile
        local_settings = self._claude_dir / "settings.local.json"

        if not local_settings.exists():
            return None, None, None

        try:
            with open(local_settings) as f:
                config = json.load(f)

            jira_config = config.get("jira", {})

            # Get URL from profile config
            profiles = jira_config.get("profiles", {})
            profile_config = profiles.get(profile, {})
            url = profile_config.get("url")

            # Get credentials
            credentials = jira_config.get("credentials", {})
            profile_creds = credentials.get(profile, {})
            email = profile_creds.get("email")
            api_token = profile_creds.get("api_token")

            return url, email, api_token
        except Exception:
            return None, None, None

    def get_credentials(self, profile: str | None = None) -> tuple[str, str, str]:
        """
        Retrieve credentials (url, email, api_token) for a profile.

        Checks in priority order:
        1. Environment variables
        2. System keychain
        3. settings.local.json

        Args:
            profile: Profile name (default: instance profile)

        Returns:
            Tuple of (url, email, api_token)

        Raises:
            CredentialNotFoundError: If credentials not found in any backend
            ValidationError: If credentials are invalid
        """
        profile = profile or self.profile

        # Collect credentials from all sources
        url, email, api_token = None, None, None

        # Priority 1: Environment variables (highest priority)
        env_url, env_email, env_token = self.get_credentials_from_env(profile)
        url = url or env_url
        email = email or env_email
        api_token = api_token or env_token

        # Priority 2: Keychain (if available)
        if not (url and email and api_token):
            kc_url, kc_email, kc_token = self.get_credentials_from_keychain(profile)
            url = url or kc_url
            email = email or kc_email
            api_token = api_token or kc_token

        # Priority 3: JSON file
        if not (url and email and api_token):
            json_url, json_email, json_token = self.get_credentials_from_json(profile)
            url = url or json_url
            email = email or json_email
            api_token = api_token or json_token

        # Check if we have all required credentials
        if not url:
            raise CredentialNotFoundError(profile)
        if not email:
            raise CredentialNotFoundError(profile)
        if not api_token:
            raise CredentialNotFoundError(profile)

        # Validate credentials
        try:
            url = validate_url(url)
            email = validate_email(email)
        except ValidationError:
            raise

        return url, email, api_token

    def store_credentials(
        self,
        url: str,
        email: str,
        api_token: str,
        profile: str | None = None,
        backend: CredentialBackend | None = None,
    ) -> CredentialBackend:
        """
        Store credentials in the specified or preferred backend.

        Args:
            url: JIRA site URL
            email: User email
            api_token: API token
            profile: Profile name (default: instance profile)
            backend: Specific backend to use (default: auto-select best available)

        Returns:
            The backend where credentials were stored

        Raises:
            ValidationError: If credentials are invalid
            JiraError: If storage fails
        """
        profile = profile or self.profile

        # Validate inputs
        url = validate_url(url)
        email = validate_email(email)

        if not api_token or not api_token.strip():
            raise ValidationError("API token cannot be empty")

        # Determine backend
        if backend is None:
            if self.is_keychain_available():
                backend = CredentialBackend.KEYCHAIN
            else:
                backend = CredentialBackend.JSON_FILE

        # Store based on backend
        if backend == CredentialBackend.KEYCHAIN:
            return self._store_to_keychain(url, email, api_token, profile)
        elif backend == CredentialBackend.JSON_FILE:
            return self._store_to_json(url, email, api_token, profile)
        else:
            raise ValidationError(f"Cannot store to backend: {backend.value}")

    def _store_to_keychain(
        self, url: str, email: str, api_token: str, profile: str
    ) -> CredentialBackend:
        """Store credentials in system keychain."""
        if not self.is_keychain_available():
            raise JiraError(
                "Keychain is not available. Install keyring: pip install keyring"
            )

        service = self._get_keychain_service(profile)

        try:
            # Store as JSON
            credential_json = json.dumps(
                {"url": url, "email": email, "api_token": api_token}
            )
            keyring.set_password(service, "credentials", credential_json)

            # Clear sensitive data from memory
            del credential_json
            gc.collect()

            return CredentialBackend.KEYCHAIN
        except Exception as e:
            raise JiraError(
                f"Failed to store credentials in keychain: {sanitize_error_message(str(e))}"
            )

    def _store_to_json(
        self, url: str, email: str, api_token: str, profile: str
    ) -> CredentialBackend:
        """Store credentials in settings.local.json."""
        if not self._claude_dir:
            raise JiraError("Cannot find .claude directory. Run from project root.")

        local_settings = self._claude_dir / "settings.local.json"

        try:
            # Load existing config or create new
            if local_settings.exists():
                with open(local_settings) as f:
                    config = json.load(f)
            else:
                config = {}

            # Ensure structure exists
            if "jira" not in config:
                config["jira"] = {}
            if "profiles" not in config["jira"]:
                config["jira"]["profiles"] = {}
            if "credentials" not in config["jira"]:
                config["jira"]["credentials"] = {}

            # Store URL in profile
            if profile not in config["jira"]["profiles"]:
                config["jira"]["profiles"][profile] = {}
            config["jira"]["profiles"][profile]["url"] = url

            # Store credentials
            if profile not in config["jira"]["credentials"]:
                config["jira"]["credentials"][profile] = {}
            config["jira"]["credentials"][profile]["email"] = email
            config["jira"]["credentials"][profile]["api_token"] = api_token

            # Write with secure permissions
            with open(local_settings, "w") as f:
                json.dump(config, f, indent=2)

            # Set restrictive permissions (owner read/write only)
            os.chmod(local_settings, stat.S_IRUSR | stat.S_IWUSR)

            return CredentialBackend.JSON_FILE
        except Exception as e:
            raise JiraError(
                f"Failed to store credentials in JSON: {sanitize_error_message(str(e))}"
            )

    def delete_credentials(self, profile: str | None = None) -> bool:
        """
        Delete credentials from all backends for a profile.

        Args:
            profile: Profile name (default: instance profile)

        Returns:
            True if any credentials were deleted, False otherwise
        """
        profile = profile or self.profile
        deleted = False

        # Delete from keychain
        if self.is_keychain_available():
            service = self._get_keychain_service(profile)
            try:
                keyring.delete_password(service, "credentials")
                deleted = True
            except Exception:
                pass  # May not exist

        # Delete from JSON
        if self._claude_dir:
            local_settings = self._claude_dir / "settings.local.json"
            if local_settings.exists():
                try:
                    with open(local_settings) as f:
                        config = json.load(f)

                    # Remove profile credentials
                    if "jira" in config:
                        if (
                            "credentials" in config["jira"]
                            and profile in config["jira"]["credentials"]
                        ):
                            del config["jira"]["credentials"][profile]
                            deleted = True

                    with open(local_settings, "w") as f:
                        json.dump(config, f, indent=2)
                except Exception:
                    pass

        return deleted

    def list_profiles(self) -> dict[str, CredentialBackend]:
        """
        List all profiles with their storage backend.

        Returns:
            Dict mapping profile names to their storage backend
        """
        profiles = {}

        # Check keychain profiles
        if self.is_keychain_available():
            # Unfortunately keyring doesn't provide a way to list all entries
            # We'd need to check known profile names
            pass

        # Check JSON profiles
        if self._claude_dir:
            local_settings = self._claude_dir / "settings.local.json"
            if local_settings.exists():
                try:
                    with open(local_settings) as f:
                        config = json.load(f)

                    credentials = config.get("jira", {}).get("credentials", {})
                    for profile_name in credentials:
                        profiles[profile_name] = CredentialBackend.JSON_FILE
                except Exception:
                    pass

        return profiles

    def validate_credentials(
        self, url: str, email: str, api_token: str
    ) -> dict[str, Any]:
        """
        Validate credentials by making a test API call.

        Args:
            url: JIRA site URL
            email: User email
            api_token: API token

        Returns:
            User info dict on success

        Raises:
            AuthenticationError: If credentials are invalid
            JiraError: If connection fails
        """
        import requests

        # Validate URL format first
        url = validate_url(url)

        # Test with /rest/api/3/myself endpoint
        test_url = f"{url}/rest/api/3/myself"

        try:
            response = requests.get(
                test_url,
                auth=(email, api_token),
                headers={"Accept": "application/json"},
                timeout=10,
            )

            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid credentials. Please check your email and API token."
                )
            elif response.status_code == 403:
                raise AuthenticationError(
                    "Access forbidden. Your API token may lack required permissions."
                )
            elif not response.ok:
                raise JiraError(
                    f"Connection failed with status {response.status_code}",
                    status_code=response.status_code,
                )

            return response.json()

        except requests.exceptions.ConnectionError:
            raise JiraError(
                f"Cannot connect to {url}. Please check the URL and your network connection."
            )
        except requests.exceptions.Timeout:
            raise JiraError(
                f"Connection to {url} timed out. The server may be slow or unreachable."
            )
        except requests.exceptions.RequestException as e:
            raise JiraError(f"Connection error: {sanitize_error_message(str(e))}")


# Convenience functions (match config_manager.py pattern)


def is_keychain_available() -> bool:
    """Check if system keychain is available."""
    return CredentialManager.is_keychain_available()


def get_credentials(profile: str | None = None) -> tuple[str, str, str]:
    """
    Get credentials for a profile.

    Args:
        profile: Profile name (default: production)

    Returns:
        Tuple of (url, email, api_token)
    """
    manager = CredentialManager(profile or "production")
    return manager.get_credentials(profile)


def store_credentials(
    url: str,
    email: str,
    api_token: str,
    profile: str | None = None,
    backend: CredentialBackend | None = None,
) -> CredentialBackend:
    """
    Store credentials using preferred backend.

    Args:
        url: JIRA site URL
        email: User email
        api_token: API token
        profile: Profile name (default: production)
        backend: Specific backend to use (default: auto-select)

    Returns:
        The backend where credentials were stored
    """
    manager = CredentialManager(profile or "production")
    return manager.store_credentials(url, email, api_token, profile, backend)


def validate_credentials(url: str, email: str, api_token: str) -> dict[str, Any]:
    """
    Validate credentials by making a test API call.

    Args:
        url: JIRA site URL
        email: User email
        api_token: API token

    Returns:
        User info dict on success
    """
    manager = CredentialManager()
    return manager.validate_credentials(url, email, api_token)
