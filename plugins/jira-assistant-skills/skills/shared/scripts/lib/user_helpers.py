#!/usr/bin/env python3
"""
User lookup helper functions for JIRA API operations.

Provides reusable utilities for resolving user identifiers
(email addresses, usernames) to JIRA account IDs.
"""

from typing import Any


class UserNotFoundError(Exception):
    """Raised when a user cannot be found in JIRA."""

    def __init__(self, identifier: str, message: str | None = None):
        self.identifier = identifier
        if message:
            super().__init__(message)
        else:
            super().__init__(f"User not found: {identifier}")


def resolve_user_to_account_id(client, user_identifier: str) -> str:
    """
    Resolve a user identifier (email or account ID) to a JIRA account ID.

    If the identifier contains '@', it is treated as an email address and
    a user search is performed. Otherwise, it is assumed to be an account ID.

    Args:
        client: JiraClient instance with active session
        user_identifier: Email address or JIRA account ID

    Returns:
        JIRA account ID

    Raises:
        UserNotFoundError: If user search returns no results

    Example:
        >>> client = get_jira_client()
        >>> account_id = resolve_user_to_account_id(client, "user@example.com")
        >>> print(account_id)  # e.g., "5b10ac8d82e05b22cc7d4ef5"
    """
    if "@" in user_identifier:
        # Treat as email - perform user search
        users = client.search_users(user_identifier, max_results=1)
        if not users:
            raise UserNotFoundError(user_identifier)
        return users[0]["accountId"]
    else:
        # Assume it's already an account ID
        return user_identifier


def get_user_display_info(client, account_id: str) -> dict[str, Any]:
    """
    Get display information for a user by account ID.

    Args:
        client: JiraClient instance with active session
        account_id: JIRA account ID

    Returns:
        Dict containing user display information:
            - accountId: The account ID
            - displayName: User's display name
            - emailAddress: User's email (if visible)
            - active: Whether the account is active

    Raises:
        JiraError: If the user lookup fails

    Example:
        >>> info = get_user_display_info(client, "5b10ac8d82e05b22cc7d4ef5")
        >>> print(info['displayName'])  # e.g., "John Doe"
    """
    return client.get(
        "/rest/api/3/user",
        params={"accountId": account_id},
        operation=f"get user {account_id}",
    )


def resolve_users_batch(client, user_identifiers: list) -> dict[str, str]:
    """
    Resolve multiple user identifiers to account IDs.

    Args:
        client: JiraClient instance with active session
        user_identifiers: List of email addresses or account IDs

    Returns:
        Dict mapping original identifier to resolved account ID.
        Entries that could not be resolved are omitted.

    Example:
        >>> identifiers = ["user1@example.com", "user2@example.com", "5b10ac8d82e05b22cc7d4ef5"]
        >>> resolved = resolve_users_batch(client, identifiers)
        >>> print(resolved)
        # {"user1@example.com": "abc123", "user2@example.com": "def456", "5b10ac8d82e05b22cc7d4ef5": "5b10ac8d82e05b22cc7d4ef5"}
    """
    resolved = {}
    for identifier in user_identifiers:
        try:
            account_id = resolve_user_to_account_id(client, identifier)
            resolved[identifier] = account_id
        except UserNotFoundError:
            # Skip users that cannot be found
            pass
    return resolved
