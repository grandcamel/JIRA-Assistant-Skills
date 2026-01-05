"""
JIRA Assistant Skills - Shared Library

Core modules for JIRA API interaction, configuration management,
error handling, and formatting.
"""

__version__ = "1.0.0"

from .adf_helper import adf_to_text, markdown_to_adf, text_to_adf
from .config_manager import ConfigManager, get_jira_client
from .error_handler import (
    AuthenticationError,
    JiraError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    ValidationError,
    handle_jira_error,
)
from .formatters import export_csv, format_issue, format_json, format_table
from .jira_client import JiraClient
from .validators import (
    validate_file_path,
    validate_issue_key,
    validate_jql,
    validate_project_key,
)

__all__ = [
    "AuthenticationError",
    "ConfigManager",
    "JiraClient",
    "JiraError",
    "NotFoundError",
    "PermissionError",
    "RateLimitError",
    "ValidationError",
    "adf_to_text",
    "export_csv",
    "format_issue",
    "format_json",
    "format_table",
    "get_jira_client",
    "handle_jira_error",
    "markdown_to_adf",
    "text_to_adf",
    "validate_file_path",
    "validate_issue_key",
    "validate_jql",
    "validate_project_key",
]
