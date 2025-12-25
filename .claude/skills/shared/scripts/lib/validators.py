"""
Input validation utilities for JIRA operations.

Provides functions to validate issue keys, JQL queries, project keys,
and other inputs before making API calls.
"""

import re
import os
from typing import Optional
from .error_handler import ValidationError


def validate_issue_key(issue_key: str) -> str:
    """
    Validate JIRA issue key format (e.g., PROJ-123).

    Args:
        issue_key: Issue key to validate

    Returns:
        Normalized issue key (uppercase)

    Raises:
        ValidationError: If format is invalid
    """
    if not issue_key:
        raise ValidationError("Issue key cannot be empty")

    issue_key = issue_key.strip().upper()

    pattern = r'^[A-Z][A-Z0-9]*-[0-9]+$'
    if not re.match(pattern, issue_key):
        raise ValidationError(
            f"Invalid issue key format: '{issue_key}'. "
            "Expected format: PROJECT-123 (e.g., PROJ-42, DEV-1234)"
        )

    return issue_key


def validate_project_key(project_key: str) -> str:
    """
    Validate JIRA project key format.

    Args:
        project_key: Project key to validate

    Returns:
        Normalized project key (uppercase)

    Raises:
        ValidationError: If format is invalid
    """
    if not project_key:
        raise ValidationError("Project key cannot be empty")

    project_key = project_key.strip().upper()

    pattern = r'^[A-Z][A-Z0-9]*$'
    if not re.match(pattern, project_key):
        raise ValidationError(
            f"Invalid project key format: '{project_key}'. "
            "Expected format: 2-10 uppercase letters/numbers, starting with a letter "
            "(e.g., PROJ, DEV, SUPPORT)"
        )

    if len(project_key) < 2 or len(project_key) > 10:
        raise ValidationError(
            f"Project key must be 2-10 characters long (got {len(project_key)})"
        )

    return project_key


def validate_jql(jql: str) -> str:
    """
    Basic JQL syntax validation.

    Args:
        jql: JQL query string to validate

    Returns:
        Normalized JQL query (stripped)

    Raises:
        ValidationError: If JQL appears invalid
    """
    if not jql:
        raise ValidationError("JQL query cannot be empty")

    jql = jql.strip()

    dangerous_patterns = [
        r';\s*DROP',
        r';\s*DELETE',
        r';\s*INSERT',
        r';\s*UPDATE',
        r'<script',
        r'javascript:',
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, jql, re.IGNORECASE):
            raise ValidationError(
                f"JQL query contains potentially dangerous pattern: {pattern}"
            )

    if len(jql) > 10000:
        raise ValidationError(
            f"JQL query is too long ({len(jql)} characters). Maximum is 10000."
        )

    return jql


def validate_file_path(file_path: str, must_exist: bool = True) -> str:
    """
    Validate file path for attachments.

    Args:
        file_path: Path to file
        must_exist: If True, verify file exists

    Returns:
        Absolute file path

    Raises:
        ValidationError: If file doesn't exist or path is invalid
    """
    if not file_path:
        raise ValidationError("File path cannot be empty")

    file_path = os.path.expanduser(file_path.strip())

    if must_exist and not os.path.exists(file_path):
        raise ValidationError(f"File not found: {file_path}")

    if must_exist and not os.path.isfile(file_path):
        raise ValidationError(f"Path is not a file: {file_path}")

    abs_path = os.path.abspath(file_path)

    if must_exist:
        file_size = os.path.getsize(abs_path)
        max_size = 10 * 1024 * 1024
        if file_size > max_size:
            raise ValidationError(
                f"File is too large ({file_size / 1024 / 1024:.1f}MB). "
                f"Maximum size is {max_size / 1024 / 1024}MB."
            )

    return abs_path


def validate_url(url: str) -> str:
    """
    Validate JIRA instance URL.

    Args:
        url: URL to validate

    Returns:
        Normalized URL (no trailing slash)

    Raises:
        ValidationError: If URL format is invalid
    """
    if not url:
        raise ValidationError("URL cannot be empty")

    url = url.strip().rstrip('/')

    if not url.startswith(('http://', 'https://')):
        raise ValidationError(
            f"Invalid URL format: '{url}'. Must start with http:// or https://"
        )

    if not url.startswith('https://'):
        raise ValidationError(
            f"Insecure URL: '{url}'. HTTPS is required for JIRA API access"
        )

    pattern = r'^https://[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*'
    if not re.match(pattern, url):
        raise ValidationError(f"Invalid URL format: '{url}'")

    return url


def validate_email(email: str) -> str:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        Normalized email (lowercase)

    Raises:
        ValidationError: If email format is invalid
    """
    if not email:
        raise ValidationError("Email cannot be empty")

    email = email.strip().lower()

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError(f"Invalid email format: '{email}'")

    return email


def validate_transition_id(transition_id: str) -> str:
    """
    Validate transition ID (numeric string).

    Args:
        transition_id: Transition ID to validate

    Returns:
        Validated transition ID

    Raises:
        ValidationError: If not a valid numeric ID
    """
    if not transition_id:
        raise ValidationError("Transition ID cannot be empty")

    transition_id = transition_id.strip()

    if not transition_id.isdigit():
        raise ValidationError(
            f"Invalid transition ID: '{transition_id}'. Must be a numeric value"
        )

    return transition_id
