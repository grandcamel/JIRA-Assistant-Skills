"""
Error handling for JIRA API operations.

Provides custom exception hierarchy and utilities for handling
JIRA API errors with user-friendly messages.

Security Note: Error messages may contain sensitive data from JIRA responses.
Use sanitize_error_message() before logging errors in production environments.
"""

import re
import sys
import functools
from typing import Optional, Dict, Any, Callable


class JiraError(Exception):
    """Base exception for all JIRA-related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_data: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(JiraError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        hint = "\n\nTroubleshooting:\n"
        hint += "  1. Verify JIRA_API_TOKEN is set correctly\n"
        hint += "  2. Check that your email matches your JIRA account\n"
        hint += "  3. Ensure the API token hasn't expired\n"
        hint += "  4. Get a new token at: https://id.atlassian.com/manage-profile/security/api-tokens"
        super().__init__(message + hint, **kwargs)


class PermissionError(JiraError):
    """Raised when the user lacks permissions for an operation."""

    def __init__(self, message: str = "Permission denied", **kwargs):
        hint = "\n\nTroubleshooting:\n"
        hint += "  1. Check your JIRA permissions for this project\n"
        hint += "  2. Verify you have the required role (e.g., Developer, Admin)\n"
        hint += "  3. Contact your JIRA administrator if access is needed"
        super().__init__(message + hint, **kwargs)


class ValidationError(JiraError):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation failed", field: Optional[str] = None, **kwargs):
        self.field = field
        if field:
            message = f"{message} (field: {field})"
        super().__init__(message, **kwargs)


class NotFoundError(JiraError):
    """Raised when a resource is not found."""

    def __init__(self, resource_type: str = "Resource", resource_id: str = "", **kwargs):
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(message, **kwargs)


class RateLimitError(JiraError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, retry_after: Optional[int] = None, **kwargs):
        self.retry_after = retry_after
        message = "API rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        else:
            message += ". Please wait before retrying"
        super().__init__(message, **kwargs)


class ConflictError(JiraError):
    """Raised when there's a conflict (e.g., duplicate, concurrent modification)."""
    pass


class ServerError(JiraError):
    """Raised when the JIRA server encounters an error."""

    def __init__(self, message: str = "JIRA server error", **kwargs):
        hint = "\n\nThe JIRA server encountered an error. Please try again later."
        super().__init__(message + hint, **kwargs)


# -----------------------------------------------------------------------------
# Automation API Errors
# -----------------------------------------------------------------------------

class AutomationError(JiraError):
    """Base exception for Automation API errors."""

    def __init__(self, message: str = "Automation API error", **kwargs):
        hint = "\n\nTroubleshooting:\n"
        hint += "  1. Verify you have Jira Administrator permissions\n"
        hint += "  2. Ensure the Cloud ID is correct\n"
        hint += "  3. Check API token scopes include 'manage:jira-automation'"
        super().__init__(message + hint, **kwargs)


class AutomationNotFoundError(AutomationError):
    """Raised when an automation rule or template is not found."""

    def __init__(self, resource_type: str = "Automation resource", resource_id: str = "", **kwargs):
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        # Call grandparent to avoid adding AutomationError hints
        JiraError.__init__(self, message, **kwargs)


class AutomationPermissionError(AutomationError):
    """Raised when the user lacks permissions for automation management."""

    def __init__(self, message: str = "Automation permission denied", **kwargs):
        hint = "\n\nTroubleshooting:\n"
        hint += "  1. You need Jira Administrator permission for full rule management\n"
        hint += "  2. Project Administrator is needed for project-scoped rules\n"
        hint += "  3. Ensure API token has 'manage:jira-automation' scope"
        # Call grandparent to avoid adding AutomationError hints
        JiraError.__init__(self, message + hint, **kwargs)


class AutomationValidationError(AutomationError):
    """Raised when automation rule configuration is invalid."""

    def __init__(self, message: str = "Automation validation failed", field: Optional[str] = None, **kwargs):
        self.field = field
        if field:
            message = f"{message} (field: {field})"
        # Call grandparent to avoid adding AutomationError hints
        JiraError.__init__(self, message, **kwargs)


def handle_jira_error(response, operation: str = "operation") -> None:
    """
    Handle HTTP response errors and raise appropriate exceptions.

    Args:
        response: requests.Response object
        operation: Description of the operation being performed

    Raises:
        Appropriate JiraError subclass based on status code
    """
    if response.ok:
        return

    status_code = response.status_code

    try:
        error_data = response.json()
        error_messages = error_data.get('errorMessages', [])
        errors = error_data.get('errors', {})

        if error_messages:
            message = '; '.join(error_messages)
        elif errors:
            message = '; '.join([f"{k}: {v}" for k, v in errors.items()])
        else:
            message = error_data.get('message', response.text or 'Unknown error')
    except ValueError:
        message = response.text or f"HTTP {status_code} error"
        error_data = {}

    message = f"Failed to {operation}: {message}"

    if status_code == 400:
        raise ValidationError(message, status_code=status_code, response_data=error_data)
    elif status_code == 401:
        raise AuthenticationError(message, status_code=status_code, response_data=error_data)
    elif status_code == 403:
        raise PermissionError(message, status_code=status_code, response_data=error_data)
    elif status_code == 404:
        raise NotFoundError("Resource", message, status_code=status_code, response_data=error_data)
    elif status_code == 409:
        raise ConflictError(message, status_code=status_code, response_data=error_data)
    elif status_code == 429:
        retry_after = response.headers.get('Retry-After')
        raise RateLimitError(
            retry_after=int(retry_after) if retry_after else None,
            status_code=status_code,
            response_data=error_data
        )
    elif status_code >= 500:
        raise ServerError(message, status_code=status_code, response_data=error_data)
    else:
        raise JiraError(message, status_code=status_code, response_data=error_data)


def sanitize_error_message(message: str) -> str:
    """
    Sanitize error messages to remove potentially sensitive information.

    Removes or redacts:
    - Email addresses
    - Account IDs (Atlassian format)
    - API tokens/keys
    - URLs with authentication
    - Issue keys with context (keeps key, redacts description)

    Args:
        message: Raw error message

    Returns:
        Sanitized error message safe for production logging

    Example:
        >>> sanitize_error_message("User john@company.com not found")
        "User [EMAIL REDACTED] not found"
    """
    if not message:
        return message

    sanitized = message

    # Redact email addresses
    sanitized = re.sub(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        '[EMAIL REDACTED]',
        sanitized
    )

    # Redact Atlassian account IDs (24-character hex strings)
    sanitized = re.sub(
        r'[0-9a-f]{24}',
        '[ACCOUNT_ID REDACTED]',
        sanitized,
        flags=re.IGNORECASE
    )

    # Redact longer UUIDs/tokens (32+ chars of hex)
    sanitized = re.sub(
        r'[0-9a-f]{32,}',
        '[TOKEN REDACTED]',
        sanitized,
        flags=re.IGNORECASE
    )

    # Redact API tokens (typical formats)
    sanitized = re.sub(
        r'(ATATT[A-Za-z0-9+/=]+)',
        '[API_TOKEN REDACTED]',
        sanitized
    )

    # Redact URLs with credentials
    sanitized = re.sub(
        r'(https?://)[^:]+:[^@]+@',
        r'\1[CREDENTIALS REDACTED]@',
        sanitized
    )

    # Redact bearer tokens
    sanitized = re.sub(
        r'(Bearer\s+)[A-Za-z0-9._-]+',
        r'\1[TOKEN REDACTED]',
        sanitized,
        flags=re.IGNORECASE
    )

    return sanitized


def print_error(error: Exception, debug: bool = False, sanitize: bool = False) -> None:
    """
    Print error message to stderr with optional debug information.

    Args:
        error: Exception to print
        debug: If True, include full stack trace
        sanitize: If True, sanitize sensitive data from error messages
    """
    error_str = str(error)
    if sanitize:
        error_str = sanitize_error_message(error_str)

    print(f"\nError: {error_str}", file=sys.stderr)

    if debug and hasattr(error, '__traceback__'):
        import traceback
        print("\nDebug traceback:", file=sys.stderr)
        traceback.print_tb(error.__traceback__, file=sys.stderr)

    if isinstance(error, JiraError) and error.response_data:
        response_str = str(error.response_data)
        if sanitize:
            response_str = sanitize_error_message(response_str)
        print(f"\nResponse data: {response_str}", file=sys.stderr)


def handle_errors(func: Callable) -> Callable:
    """
    Decorator to handle errors in CLI scripts.

    Catches all exceptions, prints user-friendly error messages,
    and exits with appropriate status codes.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function with error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.", file=sys.stderr)
            sys.exit(130)  # Standard exit code for SIGINT
        except JiraError as e:
            print_error(e)
            sys.exit(1)
        except Exception as e:
            print(f"\nUnexpected error: {e}", file=sys.stderr)
            print_error(e, debug=True)
            sys.exit(1)

    return wrapper
