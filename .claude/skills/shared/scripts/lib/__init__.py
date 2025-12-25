"""
JIRA Assistant Skills - Shared Library

Core modules for JIRA API interaction, configuration management,
error handling, and formatting.
"""

__version__ = "1.0.0"

from .error_handler import (
    JiraError,
    AuthenticationError,
    PermissionError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    handle_jira_error
)

from .jira_client import JiraClient
from .config_manager import ConfigManager, get_jira_client
from .validators import (
    validate_issue_key,
    validate_jql,
    validate_project_key,
    validate_file_path
)
from .formatters import (
    format_issue,
    format_table,
    format_json,
    export_csv
)
from .adf_helper import (
    markdown_to_adf,
    text_to_adf,
    adf_to_text
)

__all__ = [
    'JiraError',
    'AuthenticationError',
    'PermissionError',
    'ValidationError',
    'NotFoundError',
    'RateLimitError',
    'handle_jira_error',
    'JiraClient',
    'ConfigManager',
    'get_jira_client',
    'validate_issue_key',
    'validate_jql',
    'validate_project_key',
    'validate_file_path',
    'format_issue',
    'format_table',
    'format_json',
    'export_csv',
    'markdown_to_adf',
    'text_to_adf',
    'adf_to_text',
]
