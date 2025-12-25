"""
Configuration management for JIRA Assistant Skills.

Handles loading and merging configuration from multiple sources:
1. Environment variables (highest priority)
2. .claude/settings.local.json (personal settings, gitignored)
3. .claude/settings.json (team defaults, committed)
4. Hardcoded defaults (fallbacks)
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from error_handler import ValidationError
from validators import validate_url, validate_email
from jira_client import JiraClient


class ConfigManager:
    """
    Manages JIRA configuration from multiple sources with profile support.
    """

    def __init__(self, profile: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            profile: Profile name to use (default: from config or 'production')
        """
        self.config = self._load_config()
        self.profile = profile or self._get_default_profile()

    def _find_claude_dir(self) -> Optional[Path]:
        """
        Find .claude directory by walking up from current directory.

        Returns:
            Path to .claude directory or None if not found
        """
        current = Path.cwd()

        while current != current.parent:
            claude_dir = current / '.claude'
            if claude_dir.is_dir():
                return claude_dir
            current = current.parent

        return None

    def _load_config(self) -> Dict[str, Any]:
        """
        Load and merge configuration from all sources.

        Returns:
            Merged configuration dictionary
        """
        config = {
            'jira': {
                'default_profile': 'production',
                'profiles': {},
                'api': {
                    'version': '3',
                    'timeout': 30,
                    'max_retries': 3,
                    'retry_backoff': 2.0
                }
            }
        }

        claude_dir = self._find_claude_dir()

        if claude_dir:
            team_settings = claude_dir / 'settings.json'
            if team_settings.exists():
                with open(team_settings, 'r') as f:
                    team_config = json.load(f)
                    config = self._merge_config(config, team_config)

            local_settings = claude_dir / 'settings.local.json'
            if local_settings.exists():
                with open(local_settings, 'r') as f:
                    local_config = json.load(f)
                    config = self._merge_config(config, local_config)

        return config

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge override config into base config.

        Args:
            base: Base configuration
            override: Override configuration

        Returns:
            Merged configuration
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value

        return result

    def _get_default_profile(self) -> str:
        """
        Get default profile from config or environment.

        Returns:
            Profile name
        """
        env_profile = os.getenv('JIRA_PROFILE')
        if env_profile:
            return env_profile

        return self.config.get('jira', {}).get('default_profile', 'production')

    def get_profile_config(self, profile: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration for a specific profile.

        Args:
            profile: Profile name (default: self.profile)

        Returns:
            Profile configuration

        Raises:
            ValidationError: If profile doesn't exist
        """
        profile = profile or self.profile
        profiles = self.config.get('jira', {}).get('profiles', {})

        if profile not in profiles:
            raise ValidationError(
                f"Profile '{profile}' not found. Available profiles: {list(profiles.keys())}"
            )

        return profiles[profile]

    def get_credentials(self, profile: Optional[str] = None) -> tuple:
        """
        Get JIRA credentials (URL, email, API token) for a profile.

        Merges from environment variables and configuration files.

        Args:
            profile: Profile name (default: self.profile)

        Returns:
            Tuple of (url, email, api_token)

        Raises:
            ValidationError: If required credentials are missing
        """
        profile = profile or self.profile
        profile_config = self.get_profile_config(profile)

        url = os.getenv('JIRA_SITE_URL')
        if not url:
            url = profile_config.get('url')

        if not url:
            raise ValidationError(
                f"JIRA URL not configured for profile '{profile}'. "
                "Set JIRA_SITE_URL environment variable or configure in .claude/settings.json"
            )

        url = validate_url(url)

        api_token = os.getenv(f'JIRA_API_TOKEN_{profile.upper()}')
        if not api_token:
            api_token = os.getenv('JIRA_API_TOKEN')

        if not api_token:
            credentials = self.config.get('jira', {}).get('credentials', {})
            profile_creds = credentials.get(profile, {})
            api_token = profile_creds.get('api_token')

        if not api_token:
            raise ValidationError(
                f"JIRA API token not configured for profile '{profile}'. "
                "Set JIRA_API_TOKEN environment variable or configure in .claude/settings.local.json\n"
                "Get a token at: https://id.atlassian.com/manage-profile/security/api-tokens"
            )

        email = os.getenv('JIRA_EMAIL')
        if not email:
            credentials = self.config.get('jira', {}).get('credentials', {})
            profile_creds = credentials.get(profile, {})
            email = profile_creds.get('email')

        if not email:
            raise ValidationError(
                f"JIRA email not configured for profile '{profile}'. "
                "Set JIRA_EMAIL environment variable or configure in .claude/settings.local.json"
            )

        email = validate_email(email)

        return url, email, api_token

    def get_api_config(self) -> Dict[str, Any]:
        """
        Get API configuration (timeout, retries, etc.).

        Returns:
            API configuration dictionary
        """
        return self.config.get('jira', {}).get('api', {
            'version': '3',
            'timeout': 30,
            'max_retries': 3,
            'retry_backoff': 2.0
        })

    def get_client(self, profile: Optional[str] = None) -> JiraClient:
        """
        Create a configured JIRA client for a profile.

        Args:
            profile: Profile name (default: self.profile)

        Returns:
            Configured JiraClient instance

        Raises:
            ValidationError: If configuration is invalid or incomplete
        """
        profile = profile or self.profile
        url, email, api_token = self.get_credentials(profile)
        api_config = self.get_api_config()

        return JiraClient(
            base_url=url,
            email=email,
            api_token=api_token,
            timeout=api_config.get('timeout', 30),
            max_retries=api_config.get('max_retries', 3),
            retry_backoff=api_config.get('retry_backoff', 2.0)
        )

    def get_default_project(self, profile: Optional[str] = None) -> Optional[str]:
        """
        Get default project key for a profile.

        Args:
            profile: Profile name (default: self.profile)

        Returns:
            Default project key or None
        """
        profile = profile or self.profile
        try:
            profile_config = self.get_profile_config(profile)
            return profile_config.get('default_project')
        except ValidationError:
            return None

    def list_profiles(self) -> list:
        """
        List all available profiles.

        Returns:
            List of profile names
        """
        return list(self.config.get('jira', {}).get('profiles', {}).keys())


def get_jira_client(profile: Optional[str] = None) -> JiraClient:
    """
    Convenience function to get a configured JIRA client.

    Args:
        profile: Profile name (default: from config or environment)

    Returns:
        Configured JiraClient instance

    Raises:
        ValidationError: If configuration is invalid or incomplete
    """
    config_manager = ConfigManager(profile=profile)
    return config_manager.get_client()
