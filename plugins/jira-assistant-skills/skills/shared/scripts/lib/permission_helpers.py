"""
Helper utilities for permission scheme operations.

Provides functions for parsing, formatting, and validating permission grants.
"""

import re
from typing import Dict, Any, Optional, List, Tuple

from jira_assistant_skills_lib import ValidationError


# Valid holder types for permission grants
VALID_HOLDER_TYPES = [
    'anyone',
    'group',
    'projectRole',
    'user',
    'projectLead',
    'reporter',
    'currentAssignee',
    'applicationRole'
]

# Holder types that require a parameter
HOLDER_TYPES_WITH_PARAMETER = ['group', 'projectRole', 'user', 'applicationRole']

# Holder types that don't require a parameter
HOLDER_TYPES_WITHOUT_PARAMETER = ['anyone', 'projectLead', 'reporter', 'currentAssignee']


def parse_grant_string(grant_string: str) -> Tuple[str, str, Optional[str]]:
    """
    Parse a grant string in the format PERMISSION:HOLDER_TYPE[:HOLDER_PARAMETER].

    Args:
        grant_string: Grant string (e.g., 'BROWSE_PROJECTS:anyone',
                     'CREATE_ISSUES:group:jira-developers')

    Returns:
        Tuple of (permission, holder_type, holder_parameter)

    Raises:
        ValidationError: If the grant string format is invalid

    Examples:
        >>> parse_grant_string('BROWSE_PROJECTS:anyone')
        ('BROWSE_PROJECTS', 'anyone', None)

        >>> parse_grant_string('CREATE_ISSUES:group:jira-developers')
        ('CREATE_ISSUES', 'group', 'jira-developers')

        >>> parse_grant_string('EDIT_ISSUES:projectRole:Developers')
        ('EDIT_ISSUES', 'projectRole', 'Developers')
    """
    if not grant_string:
        raise ValidationError("Grant string cannot be empty")

    parts = grant_string.split(':')

    if len(parts) < 2:
        raise ValidationError(
            f"Invalid grant format: '{grant_string}'. "
            "Expected format: PERMISSION:HOLDER_TYPE[:HOLDER_PARAMETER]"
        )

    permission = parts[0].upper()
    holder_type = parts[1]
    holder_parameter = ':'.join(parts[2:]) if len(parts) > 2 else None

    # Validate holder type
    if holder_type not in VALID_HOLDER_TYPES:
        raise ValidationError(
            f"Invalid holder type: '{holder_type}'. "
            f"Valid types are: {', '.join(VALID_HOLDER_TYPES)}"
        )

    # Check if holder type requires parameter
    if holder_type in HOLDER_TYPES_WITH_PARAMETER and not holder_parameter:
        raise ValidationError(
            f"Holder type '{holder_type}' requires a parameter. "
            f"Format: PERMISSION:{holder_type}:PARAMETER"
        )

    if holder_type in HOLDER_TYPES_WITHOUT_PARAMETER and holder_parameter:
        raise ValidationError(
            f"Holder type '{holder_type}' does not accept a parameter. "
            f"Format: PERMISSION:{holder_type}"
        )

    return permission, holder_type, holder_parameter


def format_grant(grant: Dict[str, Any]) -> str:
    """
    Format a permission grant for display.

    Args:
        grant: Permission grant object from JIRA API

    Returns:
        Human-readable grant string (e.g., 'group: jira-developers')
    """
    holder = grant.get('holder', {})
    holder_type = holder.get('type', 'unknown')
    parameter = holder.get('parameter')

    if holder_type in HOLDER_TYPES_WITHOUT_PARAMETER:
        return holder_type
    elif parameter:
        return f"{holder_type}: {parameter}"
    else:
        return holder_type


def format_grant_for_export(grant: Dict[str, Any]) -> str:
    """
    Format a permission grant as a grant string for export/template.

    Args:
        grant: Permission grant object from JIRA API

    Returns:
        Grant string (e.g., 'BROWSE_PROJECTS:group:jira-developers')
    """
    permission = grant.get('permission', 'UNKNOWN')
    holder = grant.get('holder', {})
    holder_type = holder.get('type', 'anyone')
    parameter = holder.get('parameter')

    if parameter:
        return f"{permission}:{holder_type}:{parameter}"
    else:
        return f"{permission}:{holder_type}"


def build_grant_payload(permission: str, holder_type: str,
                        holder_parameter: Optional[str] = None) -> Dict[str, Any]:
    """
    Build a permission grant payload for the JIRA API.

    Args:
        permission: Permission key (e.g., 'BROWSE_PROJECTS')
        holder_type: Holder type (e.g., 'group', 'anyone')
        holder_parameter: Optional parameter for the holder

    Returns:
        Dict suitable for JIRA API permission grant creation
    """
    holder = {'type': holder_type}
    if holder_parameter:
        holder['parameter'] = holder_parameter

    return {
        'permission': permission,
        'holder': holder
    }


def validate_permission(permission: str, available_permissions: Dict[str, Any]) -> bool:
    """
    Validate that a permission key exists in the JIRA instance.

    Args:
        permission: Permission key to validate
        available_permissions: Dict of available permissions from JIRA API

    Returns:
        True if valid

    Raises:
        ValidationError: If permission is not valid
    """
    permission_upper = permission.upper()

    if permission_upper not in available_permissions:
        # Get suggestions
        suggestions = [k for k in available_permissions.keys()
                      if permission_upper in k or k in permission_upper]
        msg = f"Invalid permission key: '{permission}'"
        if suggestions:
            msg += f". Did you mean one of: {', '.join(suggestions[:5])}"
        raise ValidationError(msg)

    return True


def validate_holder_type(holder_type: str) -> bool:
    """
    Validate that a holder type is valid.

    Args:
        holder_type: Holder type to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If holder type is not valid
    """
    if holder_type not in VALID_HOLDER_TYPES:
        raise ValidationError(
            f"Invalid holder type: '{holder_type}'. "
            f"Valid types are: {', '.join(VALID_HOLDER_TYPES)}"
        )
    return True


def find_scheme_by_name(schemes: List[Dict[str, Any]], name: str,
                        fuzzy: bool = False) -> Optional[Dict[str, Any]]:
    """
    Find a permission scheme by name.

    Args:
        schemes: List of permission scheme objects
        name: Name to search for
        fuzzy: If True, allow partial matching

    Returns:
        Matching scheme or None

    Raises:
        ValidationError: If fuzzy match returns multiple results
    """
    # Try exact match first
    for scheme in schemes:
        if scheme.get('name', '').lower() == name.lower():
            return scheme

    if not fuzzy:
        return None

    # Try partial match
    matches = []
    name_lower = name.lower()
    for scheme in schemes:
        scheme_name = scheme.get('name', '').lower()
        if name_lower in scheme_name:
            matches.append(scheme)

    if len(matches) == 0:
        return None
    elif len(matches) == 1:
        return matches[0]
    else:
        match_names = [m.get('name') for m in matches]
        raise ValidationError(
            f"Ambiguous scheme name '{name}' matches multiple schemes: "
            f"{', '.join(match_names)}. Please be more specific."
        )


def group_grants_by_permission(grants: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group permission grants by permission key.

    Args:
        grants: List of permission grant objects

    Returns:
        Dict mapping permission keys to lists of grants
    """
    grouped = {}
    for grant in grants:
        permission = grant.get('permission', 'UNKNOWN')
        if permission not in grouped:
            grouped[permission] = []
        grouped[permission].append(grant)
    return grouped


def find_grant_by_spec(grants: List[Dict[str, Any]], permission: str,
                       holder_type: str, holder_parameter: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Find a specific grant by permission and holder specification.

    Args:
        grants: List of permission grant objects
        permission: Permission key
        holder_type: Holder type
        holder_parameter: Optional holder parameter

    Returns:
        Matching grant or None
    """
    permission_upper = permission.upper()

    for grant in grants:
        if grant.get('permission', '').upper() != permission_upper:
            continue

        holder = grant.get('holder', {})
        if holder.get('type') != holder_type:
            continue

        grant_param = holder.get('parameter')
        if holder_parameter:
            if grant_param and grant_param.lower() == holder_parameter.lower():
                return grant
        else:
            if not grant_param:
                return grant

    return None


def get_holder_display(holder: Dict[str, Any]) -> str:
    """
    Get a human-readable display string for a holder.

    Args:
        holder: Holder object from grant

    Returns:
        Display string (e.g., 'group: jira-developers', 'anyone')
    """
    holder_type = holder.get('type', 'unknown')
    parameter = holder.get('parameter')

    if holder_type == 'anyone':
        return 'anyone'
    elif holder_type == 'projectLead':
        return 'project lead'
    elif holder_type == 'reporter':
        return 'reporter'
    elif holder_type == 'currentAssignee':
        return 'current assignee'
    elif holder_type == 'group' and parameter:
        return f"group: {parameter}"
    elif holder_type == 'projectRole' and parameter:
        return f"role: {parameter}"
    elif holder_type == 'user' and parameter:
        return f"user: {parameter}"
    elif holder_type == 'applicationRole' and parameter:
        return f"app role: {parameter}"
    else:
        return holder_type


def format_scheme_summary(scheme: Dict[str, Any]) -> str:
    """
    Format a permission scheme for summary display.

    Args:
        scheme: Permission scheme object

    Returns:
        Summary string
    """
    name = scheme.get('name', 'Unknown')
    scheme_id = scheme.get('id', '?')
    description = scheme.get('description', '')
    permissions = scheme.get('permissions', [])

    summary = f"{name} (ID: {scheme_id})"
    if description:
        summary += f"\n  {description[:80]}{'...' if len(description) > 80 else ''}"
    summary += f"\n  Grants: {len(permissions)}"

    return summary
