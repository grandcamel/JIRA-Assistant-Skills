"""
Transition matching helpers for JIRA workflow operations.

Provides functions to find transitions by name with fuzzy matching
support (case-insensitive, exact and partial matching).
"""

from typing import List, Dict, Any, Optional


def find_transition_by_name(transitions: List[Dict[str, Any]], name: str) -> Dict[str, Any]:
    """
    Find a transition by name (case-insensitive, partial match).

    The search uses a two-phase approach:
    1. First, look for an exact match (case-insensitive)
    2. If no exact match, look for partial matches

    Args:
        transitions: List of transition objects from JIRA API
        name: Transition name to find

    Returns:
        Transition object matching the name

    Raises:
        ValidationError: If transition not found or ambiguous
    """
    from error_handler import ValidationError

    if not transitions:
        raise ValidationError(f"No transitions available to match '{name}'")

    name_lower = name.lower()

    # Phase 1: Exact match (case-insensitive)
    exact_matches = [t for t in transitions if t['name'].lower() == name_lower]
    if len(exact_matches) == 1:
        return exact_matches[0]
    elif len(exact_matches) > 1:
        raise ValidationError(
            f"Multiple exact matches for transition '{name}': " +
            ', '.join(t['name'] for t in exact_matches)
        )

    # Phase 2: Partial match (case-insensitive)
    partial_matches = [t for t in transitions if name_lower in t['name'].lower()]
    if len(partial_matches) == 1:
        return partial_matches[0]
    elif len(partial_matches) > 1:
        raise ValidationError(
            f"Ambiguous transition name '{name}'. Matches: " +
            ', '.join(t['name'] for t in partial_matches)
        )

    # No matches found
    raise ValidationError(
        f"Transition '{name}' not found. Available: " +
        ', '.join(t['name'] for t in transitions)
    )


def find_transition_by_keywords(transitions: List[Dict[str, Any]],
                                 keywords: List[str],
                                 prefer_exact: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Find a transition matching any of the given keywords.

    Useful for finding common transitions like "resolve", "reopen", "done" etc.
    Uses case-insensitive partial matching.

    Args:
        transitions: List of transition objects from JIRA API
        keywords: List of keywords to search for in transition names
        prefer_exact: If provided, prefer an exact match for this keyword

    Returns:
        Matching transition or None if not found
    """
    if not transitions:
        return None

    # Find all transitions matching any keyword
    matching = [
        t for t in transitions
        if any(keyword.lower() in t['name'].lower() for keyword in keywords)
    ]

    if not matching:
        return None

    # If prefer_exact is specified, look for exact match first
    if prefer_exact:
        prefer_lower = prefer_exact.lower()
        exact = [t for t in matching if t['name'].lower() == prefer_lower]
        if exact:
            return exact[0]

    # Return first match
    return matching[0]


def format_transition_list(transitions: List[Dict[str, Any]]) -> str:
    """
    Format a list of transitions for display.

    Args:
        transitions: List of transition objects

    Returns:
        Formatted string with transition names and IDs
    """
    if not transitions:
        return "No transitions available"

    lines = []
    for t in transitions:
        target = t.get('to', {}).get('name', 'Unknown')
        lines.append(f"  - {t['name']} (ID: {t['id']}) -> {target}")

    return '\n'.join(lines)
