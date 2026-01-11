"""
Unit tests for credential_manager.py

Tests credential storage, retrieval, and validation across multiple backends:
- System keychain (mocked)
- settings.local.json
- Environment variables
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add lib to path for imports
LIB_PATH = Path(__file__).parent.parent.parent / "scripts" / "lib"
sys.path.insert(0, str(LIB_PATH))

from assistant_skills_lib.error_handler import AuthenticationError, ValidationError

from jira_assistant_skills_lib import (
    CredentialBackend,
    CredentialManager,
    CredentialNotFoundError,
    get_credentials,
    is_keychain_available,
    validate_credentials,
)


class TestCredentialBackend:
    """Test CredentialBackend enum."""

    def test_backend_values(self):
        """Test backend enum values."""
        assert CredentialBackend.KEYCHAIN.value == "keychain"
        assert CredentialBackend.JSON_FILE.value == "json_file"
        assert CredentialBackend.ENVIRONMENT.value == "environment"


class TestKeychainAvailability:
    """Test keychain availability detection."""

    def test_keychain_available_when_keyring_works(self):
        """Test keychain is available when keyring works."""
        import jira_assistant_skills_lib.credential_manager as cm

        original_available = cm.KEYRING_AVAILABLE

        try:
            cm.KEYRING_AVAILABLE = True
            with patch.object(cm, "keyring", create=True) as mock_keyring:
                mock_keyring.get_keyring.return_value = MagicMock()
                assert CredentialManager.is_keychain_available() is True
        finally:
            cm.KEYRING_AVAILABLE = original_available

    def test_keychain_unavailable_when_not_installed(self):
        """Test keychain unavailable when keyring not installed."""
        import jira_assistant_skills_lib.credential_manager as cm

        original_available = cm.KEYRING_AVAILABLE

        try:
            cm.KEYRING_AVAILABLE = False
            assert CredentialManager.is_keychain_available() is False
        finally:
            cm.KEYRING_AVAILABLE = original_available

    def test_keychain_unavailable_when_backend_fails(self):
        """Test keychain unavailable when backend fails."""
        import jira_assistant_skills_lib.credential_manager as cm

        original_available = cm.KEYRING_AVAILABLE

        try:
            cm.KEYRING_AVAILABLE = True
            with patch.object(cm, "keyring", create=True) as mock_keyring:
                mock_keyring.get_keyring.side_effect = Exception("Backend error")
                assert CredentialManager.is_keychain_available() is False
        finally:
            cm.KEYRING_AVAILABLE = original_available


class TestCredentialManagerInit:
    """Test CredentialManager initialization."""

    def test_initialization(self):
        """Test CredentialManager initializes correctly."""
        manager = CredentialManager()
        assert manager is not None


class TestEnvironmentCredentials:
    """Test environment variable credential retrieval."""

    def test_get_credentials_from_env_all_set(self):
        """Test getting all credentials from environment."""
        with patch.dict(
            os.environ,
            {
                "JIRA_SITE_URL": "https://test.atlassian.net",
                "JIRA_EMAIL": "test@example.com",
                "JIRA_API_TOKEN": "test-token-123",
            },
            clear=False,
        ):
            manager = CredentialManager()
            url, email, token = manager.get_credentials_from_env()

            assert url == "https://test.atlassian.net"
            assert email == "test@example.com"
            assert token == "test-token-123"

    def test_get_credentials_from_env_uses_generic_token(self):
        """Test credentials use JIRA_API_TOKEN environment variable."""
        with patch.dict(
            os.environ,
            {
                "JIRA_SITE_URL": "https://test.atlassian.net",
                "JIRA_EMAIL": "test@example.com",
                "JIRA_API_TOKEN": "generic-token",
            },
            clear=False,
        ):
            manager = CredentialManager()
            _url, _email, token = manager.get_credentials_from_env()

            assert token == "generic-token"

    def test_get_credentials_from_env_partial(self):
        """Test getting partial credentials from environment."""
        with patch.dict(
            os.environ, {"JIRA_SITE_URL": "https://test.atlassian.net"}, clear=False
        ):
            # Clear other vars if they exist
            for var in ["JIRA_EMAIL", "JIRA_API_TOKEN"]:
                os.environ.pop(var, None)

            manager = CredentialManager()
            url, email, token = manager.get_credentials_from_env()

            assert url == "https://test.atlassian.net"
            assert email is None
            assert token is None


class TestKeychainCredentials:
    """Test keychain credential retrieval."""

    def test_get_credentials_from_keychain_success(self):
        """Test successful keychain retrieval."""
        import jira_assistant_skills_lib.credential_manager as cm

        original_available = cm.KEYRING_AVAILABLE

        try:
            cm.KEYRING_AVAILABLE = True
            with patch.object(cm, "keyring", create=True) as mock_keyring:
                mock_keyring.get_keyring.return_value = MagicMock()
                mock_keyring.get_password.return_value = json.dumps(
                    {
                        "url": "https://keychain.atlassian.net",
                        "email": "keychain@example.com",
                        "api_token": "keychain-token",
                    }
                )

                manager = CredentialManager()
                url, email, token = manager.get_credentials_from_keychain()

                assert url == "https://keychain.atlassian.net"
                assert email == "keychain@example.com"
                assert token == "keychain-token"

                mock_keyring.get_password.assert_called_once_with(
                    "jira-assistant", "credentials"
                )
        finally:
            cm.KEYRING_AVAILABLE = original_available

    def test_get_credentials_from_keychain_not_found(self):
        """Test keychain returns None when no credentials stored."""
        import jira_assistant_skills_lib.credential_manager as cm

        original_available = cm.KEYRING_AVAILABLE

        try:
            cm.KEYRING_AVAILABLE = True
            with patch.object(cm, "keyring", create=True) as mock_keyring:
                mock_keyring.get_keyring.return_value = MagicMock()
                mock_keyring.get_password.return_value = None

                manager = CredentialManager()
                url, email, token = manager.get_credentials_from_keychain()

                assert url is None
                assert email is None
                assert token is None
        finally:
            cm.KEYRING_AVAILABLE = original_available

    def test_get_credentials_from_keychain_not_available(self):
        """Test keychain returns None when not available."""
        import jira_assistant_skills_lib.credential_manager as cm

        original_available = cm.KEYRING_AVAILABLE

        try:
            cm.KEYRING_AVAILABLE = False
            manager = CredentialManager()
            url, email, token = manager.get_credentials_from_keychain()

            assert url is None
            assert email is None
            assert token is None
        finally:
            cm.KEYRING_AVAILABLE = original_available


class TestJsonCredentials:
    """Test JSON file credential retrieval."""

    def test_get_credentials_from_json_success(self, tmp_path):
        """Test successful JSON file retrieval."""
        # Create mock .claude directory structure
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        settings = {
            "jira": {
                "credentials": {
                    "url": "https://json.atlassian.net",
                    "email": "json@example.com",
                    "api_token": "json-token",
                }
            }
        }

        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text(json.dumps(settings))

        # Patch _find_claude_dir to return our temp directory
        manager = CredentialManager()
        manager._claude_dir = claude_dir

        url, email, token = manager.get_credentials_from_json()

        assert url == "https://json.atlassian.net"
        assert email == "json@example.com"
        assert token == "json-token"

    def test_get_credentials_from_json_no_file(self, tmp_path):
        """Test JSON returns None when file doesn't exist."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        manager = CredentialManager()
        manager._claude_dir = claude_dir

        url, email, token = manager.get_credentials_from_json()

        assert url is None
        assert email is None
        assert token is None

    def test_get_credentials_from_json_no_claude_dir(self):
        """Test JSON returns None when no .claude directory."""
        manager = CredentialManager()
        manager._claude_dir = None

        url, email, token = manager.get_credentials_from_json()

        assert url is None
        assert email is None
        assert token is None


class TestGetCredentials:
    """Test combined credential retrieval with priority."""

    def test_env_vars_take_precedence(self, tmp_path):
        """Test environment variables override other sources."""
        # Set up JSON credentials
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        settings = {
            "jira": {
                "url": "https://json.atlassian.net",
                "credentials": {
                    "email": "json@example.com",
                    "api_token": "json-token",
                },
            }
        }
        (claude_dir / "settings.local.json").write_text(json.dumps(settings))

        # Set environment variables (should take precedence)
        with patch.dict(
            os.environ,
            {
                "JIRA_SITE_URL": "https://env.atlassian.net",
                "JIRA_EMAIL": "env@example.com",
                "JIRA_API_TOKEN": "env-token",
            },
            clear=False,
        ):
            manager = CredentialManager()
            manager._claude_dir = claude_dir

            url, email, token = manager.get_credentials()

            assert url == "https://env.atlassian.net"
            assert email == "env@example.com"
            assert token == "env-token"

    def test_raises_when_no_credentials(self):
        """Test raises CredentialNotFoundError when no credentials found."""
        # Clear environment variables
        env_vars = ["JIRA_SITE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"]
        with patch.dict(os.environ, {}, clear=True):
            for var in env_vars:
                os.environ.pop(var, None)

            manager = CredentialManager()
            manager._claude_dir = None

            with pytest.raises(CredentialNotFoundError):
                manager.get_credentials()


class TestStoreCredentials:
    """Test credential storage."""

    def test_store_to_keychain(self):
        """Test storing credentials to keychain."""
        import jira_assistant_skills_lib.credential_manager as cm

        original_available = cm.KEYRING_AVAILABLE

        try:
            cm.KEYRING_AVAILABLE = True
            with patch.object(cm, "keyring", create=True) as mock_keyring:
                mock_keyring.get_keyring.return_value = MagicMock()

                manager = CredentialManager()
                backend = manager.store_credentials(
                    "https://test.atlassian.net",
                    "test@example.com",
                    "test-token",
                    backend=CredentialBackend.KEYCHAIN,
                )

                assert backend == CredentialBackend.KEYCHAIN
                mock_keyring.set_password.assert_called_once()

                # Verify the call arguments
                call_args = mock_keyring.set_password.call_args
                assert call_args[0][0] == "jira-assistant"
                assert call_args[0][1] == "credentials"

                # Verify JSON content
                stored_json = json.loads(call_args[0][2])
                assert stored_json["url"] == "https://test.atlassian.net"
                assert stored_json["email"] == "test@example.com"
                assert stored_json["api_token"] == "test-token"
        finally:
            cm.KEYRING_AVAILABLE = original_available

    def test_store_to_json(self, tmp_path):
        """Test storing credentials to JSON file."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        manager = CredentialManager()
        manager._claude_dir = claude_dir

        backend = manager.store_credentials(
            "https://test.atlassian.net",
            "test@example.com",
            "test-token",
            backend=CredentialBackend.JSON_FILE,
        )

        assert backend == CredentialBackend.JSON_FILE

        # Verify file was created
        settings_file = claude_dir / "settings.local.json"
        assert settings_file.exists()

        # Verify content
        content = json.loads(settings_file.read_text())
        assert content["jira"]["credentials"]["url"] == "https://test.atlassian.net"
        assert content["jira"]["credentials"]["email"] == "test@example.com"
        assert content["jira"]["credentials"]["api_token"] == "test-token"

    def test_store_validates_url(self):
        """Test store validates URL format - rejects HTTP (requires HTTPS)."""
        manager = CredentialManager()

        with pytest.raises(ValidationError):
            manager.store_credentials(
                "http://insecure.atlassian.net",  # HTTP is rejected, HTTPS required
                "test@example.com",
                "test-token",
            )

    def test_store_validates_email(self):
        """Test store validates email format."""
        manager = CredentialManager()

        with pytest.raises(ValidationError):
            manager.store_credentials(
                "https://test.atlassian.net", "invalid-email", "test-token"
            )

    def test_store_validates_token_not_empty(self):
        """Test store validates token is not empty."""
        manager = CredentialManager()

        with pytest.raises(ValidationError):
            manager.store_credentials(
                "https://test.atlassian.net", "test@example.com", ""
            )


class TestDeleteCredentials:
    """Test credential deletion."""

    def test_delete_from_keychain(self):
        """Test deleting credentials from keychain."""
        import jira_assistant_skills_lib.credential_manager as cm

        original_available = cm.KEYRING_AVAILABLE

        try:
            cm.KEYRING_AVAILABLE = True
            with patch.object(cm, "keyring", create=True) as mock_keyring:
                mock_keyring.get_keyring.return_value = MagicMock()

                manager = CredentialManager()
                result = manager.delete_credentials()

                assert result is True
                mock_keyring.delete_password.assert_called_once_with(
                    "jira-assistant", "credentials"
                )
        finally:
            cm.KEYRING_AVAILABLE = original_available

    def test_delete_from_json(self, tmp_path):
        """Test deleting credentials from JSON file."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        # Create settings file with credentials
        settings = {
            "jira": {
                "credentials": {
                    "email": "test@example.com",
                    "api_token": "test-token",
                }
            }
        }
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text(json.dumps(settings))

        manager = CredentialManager()
        manager._claude_dir = claude_dir

        # Mock keychain as unavailable
        with patch.object(manager, "is_keychain_available", return_value=False):
            result = manager.delete_credentials()

        assert result is True

        # Verify credentials removed
        content = json.loads(settings_file.read_text())
        assert "credentials" not in content.get("jira", {})


class TestValidateCredentials:
    """Test credential validation."""

    @patch("requests.get")
    def test_validate_success(self, mock_get):
        """Test successful credential validation."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "displayName": "Test User",
            "accountId": "123456",
        }
        mock_get.return_value = mock_response

        manager = CredentialManager()
        result = manager.validate_credentials(
            "https://test.atlassian.net", "test@example.com", "test-token"
        )

        assert result["displayName"] == "Test User"
        assert result["accountId"] == "123456"

    @patch("requests.get")
    def test_validate_401_raises_auth_error(self, mock_get):
        """Test 401 response raises AuthenticationError."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        manager = CredentialManager()

        with pytest.raises(AuthenticationError):
            manager.validate_credentials(
                "https://test.atlassian.net", "test@example.com", "bad-token"
            )

    @patch("requests.get")
    def test_validate_connection_error(self, mock_get):
        """Test connection error handling."""
        import requests as real_requests

        mock_get.side_effect = real_requests.exceptions.ConnectionError()

        manager = CredentialManager()

        from jira_assistant_skills_lib import JiraError

        with pytest.raises(JiraError) as exc_info:
            manager.validate_credentials(
                "https://unreachable.atlassian.net", "test@example.com", "test-token"
            )

        assert "Cannot connect" in str(exc_info.value)


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_is_keychain_available_function(self):
        """Test is_keychain_available convenience function."""
        import jira_assistant_skills_lib.credential_manager as cm

        original_available = cm.KEYRING_AVAILABLE

        try:
            cm.KEYRING_AVAILABLE = True
            with patch.object(cm, "keyring", create=True) as mock_keyring:
                mock_keyring.get_keyring.return_value = MagicMock()
                assert is_keychain_available() is True
        finally:
            cm.KEYRING_AVAILABLE = original_available

    def test_get_credentials_function(self):
        """Test get_credentials convenience function."""
        with patch.dict(
            os.environ,
            {
                "JIRA_SITE_URL": "https://test.atlassian.net",
                "JIRA_EMAIL": "test@example.com",
                "JIRA_API_TOKEN": "test-token",
            },
            clear=False,
        ):
            url, email, token = get_credentials()

            assert url == "https://test.atlassian.net"
            assert email == "test@example.com"
            assert token == "test-token"

    @patch("requests.get")
    def test_validate_credentials_function(self, mock_get):
        """Test validate_credentials convenience function."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"displayName": "Test"}
        mock_get.return_value = mock_response

        result = validate_credentials(
            "https://test.atlassian.net", "test@example.com", "test-token"
        )

        assert result["displayName"] == "Test"
