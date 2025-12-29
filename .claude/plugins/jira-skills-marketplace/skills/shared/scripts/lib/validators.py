"""
Input validation utilities for JIRA operations.

Provides functions to validate issue keys, JQL queries, project keys,
and other inputs before making API calls.
"""

import re
import os
from typing import Optional
from error_handler import ValidationError


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


# ========== Project Administration Validators ==========

VALID_PROJECT_TYPES = ['software', 'business', 'service_desk']
VALID_ASSIGNEE_TYPES = ['PROJECT_LEAD', 'UNASSIGNED', 'COMPONENT_LEAD']

# Common project template shortcuts
PROJECT_TEMPLATES = {
    'scrum': 'com.pyxis.greenhopper.jira:gh-simplified-agility-scrum',
    'kanban': 'com.pyxis.greenhopper.jira:gh-simplified-agility-kanban',
    'basic': 'com.pyxis.greenhopper.jira:gh-simplified-basic',
    'simplified-scrum': 'com.pyxis.greenhopper.jira:gh-simplified-agility-scrum',
    'simplified-kanban': 'com.pyxis.greenhopper.jira:gh-simplified-agility-kanban',
    'classic-scrum': 'com.pyxis.greenhopper.jira:gh-scrum-template',
    'classic-kanban': 'com.pyxis.greenhopper.jira:gh-kanban-template',
    'project-management': 'com.atlassian.jira-core-project-templates:jira-core-project-management',
    'task-management': 'com.atlassian.jira-core-project-templates:jira-core-task-management',
    'it-service-desk': 'com.atlassian.servicedesk:simplified-it-service-desk',
    'general-service-desk': 'com.atlassian.servicedesk:simplified-general-service-desk',
}


def validate_project_type(project_type: str) -> str:
    """
    Validate project type.

    Args:
        project_type: Project type (software, business, service_desk)

    Returns:
        Validated project type (lowercase)

    Raises:
        ValidationError: If project type is invalid
    """
    if not project_type:
        raise ValidationError("Project type cannot be empty")

    project_type = project_type.strip().lower()

    if project_type not in VALID_PROJECT_TYPES:
        raise ValidationError(
            f"Invalid project type: '{project_type}'. "
            f"Valid types: {', '.join(VALID_PROJECT_TYPES)}"
        )

    return project_type


def validate_assignee_type(assignee_type: str) -> str:
    """
    Validate default assignee type.

    Args:
        assignee_type: Assignee type (PROJECT_LEAD, UNASSIGNED, COMPONENT_LEAD)

    Returns:
        Validated assignee type (uppercase)

    Raises:
        ValidationError: If assignee type is invalid
    """
    if not assignee_type:
        raise ValidationError("Assignee type cannot be empty")

    assignee_type = assignee_type.strip().upper()

    if assignee_type not in VALID_ASSIGNEE_TYPES:
        raise ValidationError(
            f"Invalid assignee type: '{assignee_type}'. "
            f"Valid types: {', '.join(VALID_ASSIGNEE_TYPES)}"
        )

    return assignee_type


def validate_project_template(template: str) -> str:
    """
    Validate and expand project template.

    Args:
        template: Template shortcut or full template key

    Returns:
        Full template key

    Raises:
        ValidationError: If template is unknown shortcut
    """
    if not template:
        raise ValidationError("Project template cannot be empty")

    template = template.strip().lower()

    # If it's a shortcut, expand it
    if template in PROJECT_TEMPLATES:
        return PROJECT_TEMPLATES[template]

    # If it looks like a full template key, return it
    if '.' in template or ':' in template:
        return template

    # Unknown shortcut
    shortcuts = ', '.join(PROJECT_TEMPLATES.keys())
    raise ValidationError(
        f"Unknown template shortcut: '{template}'. "
        f"Valid shortcuts: {shortcuts}\n"
        "Or provide a full template key (e.g., com.pyxis.greenhopper.jira:gh-scrum-template)"
    )


def validate_project_name(name: str) -> str:
    """
    Validate project name.

    Args:
        name: Project name

    Returns:
        Validated project name (stripped)

    Raises:
        ValidationError: If name is invalid
    """
    if not name:
        raise ValidationError("Project name cannot be empty")

    name = name.strip()

    if len(name) < 2:
        raise ValidationError("Project name must be at least 2 characters long")

    if len(name) > 80:
        raise ValidationError(
            f"Project name is too long ({len(name)} characters). Maximum is 80."
        )

    return name


def validate_category_name(name: str) -> str:
    """
    Validate project category name.

    Args:
        name: Category name

    Returns:
        Validated category name (stripped)

    Raises:
        ValidationError: If name is invalid
    """
    if not name:
        raise ValidationError("Category name cannot be empty")

    name = name.strip()

    if len(name) < 1:
        raise ValidationError("Category name must not be empty")

    if len(name) > 255:
        raise ValidationError(
            f"Category name is too long ({len(name)} characters). Maximum is 255."
        )

    return name


def validate_avatar_file(file_path: str) -> str:
    """
    Validate avatar file for project avatar upload.

    Args:
        file_path: Path to avatar image file

    Returns:
        Absolute path to validated file

    Raises:
        ValidationError: If file is invalid for avatar use
    """
    # Use base file validation
    abs_path = validate_file_path(file_path, must_exist=True)

    # Check file extension
    valid_extensions = ['.png', '.jpg', '.jpeg', '.gif']
    ext = os.path.splitext(abs_path)[1].lower()

    if ext not in valid_extensions:
        raise ValidationError(
            f"Invalid avatar file format: '{ext}'. "
            f"Valid formats: {', '.join(valid_extensions)}"
        )

    # Check file size (1MB max for avatars)
    file_size = os.path.getsize(abs_path)
    max_size = 1 * 1024 * 1024  # 1MB
    if file_size > max_size:
        raise ValidationError(
            f"Avatar file is too large ({file_size / 1024:.1f}KB). "
            f"Maximum size is {max_size / 1024}KB."
        )

    return abs_path
