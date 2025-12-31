#!/usr/bin/env python3
"""
Generate Git branch name from JIRA issue.

Creates standardized branch names from issue keys and summaries,
with support for auto-prefixing based on issue type.

Usage:
    python create_branch_name.py PROJ-123
    python create_branch_name.py PROJ-123 --prefix bugfix
    python create_branch_name.py PROJ-123 --auto-prefix
    python create_branch_name.py PROJ-123 --output git
    python create_branch_name.py PROJ-123 --output json
"""

import sys
import os
import argparse
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, Union

# Add shared lib path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import validate_issue_key

# Maximum length for branch names
MAX_BRANCH_LENGTH = 80

# Issue type to prefix mapping
ISSUE_TYPE_PREFIXES = {
    'bug': 'bugfix',
    'defect': 'bugfix',
    'hotfix': 'hotfix',
    'story': 'feature',
    'feature': 'feature',
    'new feature': 'feature',
    'improvement': 'feature',
    'enhancement': 'feature',
    'task': 'task',
    'sub-task': 'task',
    'subtask': 'task',
    'epic': 'epic',
    'spike': 'spike',
    'research': 'spike',
    'chore': 'chore',
    'maintenance': 'chore',
    'documentation': 'docs',
    'doc': 'docs',
}

DEFAULT_PREFIX = 'feature'


def sanitize_for_branch(text: str) -> str:
    """
    Sanitize text for use in git branch name.

    - Converts to lowercase
    - Replaces special characters with hyphens
    - Removes consecutive hyphens
    - Removes leading/trailing hyphens

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text suitable for branch name
    """
    if not text:
        return ""

    # Convert to lowercase
    result = text.lower()

    # Replace special characters with hyphen
    # Keep only alphanumeric and hyphen
    result = re.sub(r'[^a-z0-9]+', '-', result)

    # Remove consecutive hyphens
    result = re.sub(r'-+', '-', result)

    # Remove leading/trailing hyphens
    result = result.strip('-')

    return result


def get_prefix_for_issue_type(issue_type: str) -> str:
    """
    Get branch prefix based on issue type.

    Args:
        issue_type: JIRA issue type name

    Returns:
        Appropriate branch prefix
    """
    if not issue_type:
        return DEFAULT_PREFIX

    issue_type_lower = issue_type.lower()

    return ISSUE_TYPE_PREFIXES.get(issue_type_lower, DEFAULT_PREFIX)


def create_branch_name(
    issue_key: str,
    prefix: Optional[str] = None,
    auto_prefix: bool = False,
    profile: Optional[str] = None,
    client=None,
    output_format: str = 'text'
) -> Dict[str, Any]:
    """
    Create a standardized branch name from JIRA issue.

    Args:
        issue_key: JIRA issue key (e.g., PROJ-123)
        prefix: Custom prefix (feature, bugfix, hotfix, task)
        auto_prefix: If True, determine prefix from issue type
        profile: JIRA profile to use
        client: Optional JiraClient instance (created if not provided)
        output_format: Output format (text, json, git)

    Returns:
        Dictionary with branch_name, issue_key, issue_type, git_command
    """
    issue_key = validate_issue_key(issue_key)

    # Get issue from JIRA
    close_client = False
    if client is None:
        client = get_jira_client(profile)
        close_client = True
    try:
        issue = client.get_issue(issue_key, fields=['summary', 'issuetype'])
    finally:
        if close_client:
            client.close()

    fields = issue.get('fields', {})
    summary = fields.get('summary', '')
    issue_type = fields.get('issuetype', {}).get('name', '')

    # Determine prefix
    if prefix:
        branch_prefix = prefix.lower()
    elif auto_prefix:
        branch_prefix = get_prefix_for_issue_type(issue_type)
    else:
        branch_prefix = DEFAULT_PREFIX

    # Sanitize summary for branch name
    sanitized_summary = sanitize_for_branch(summary)

    # Build branch name: prefix/issue-key-summary
    issue_key_lower = issue_key.lower()

    # Handle edge case: empty sanitized summary
    # This can happen if the summary contains only special characters
    if not sanitized_summary:
        # Fall back to just the issue key without a summary
        branch_name = f"{branch_prefix}/{issue_key_lower}"
    else:
        # Calculate max summary length
        # prefix/ + issue-key + - + summary
        prefix_part_len = len(branch_prefix) + 1  # +1 for /
        key_part_len = len(issue_key_lower) + 1    # +1 for -
        max_summary_len = MAX_BRANCH_LENGTH - prefix_part_len - key_part_len

        if len(sanitized_summary) > max_summary_len:
            # Truncate at word boundary if possible
            truncated = sanitized_summary[:max_summary_len]
            # Try to end at a word boundary (hyphen)
            last_hyphen = truncated.rfind('-')
            if last_hyphen > max_summary_len // 2:  # Only if we keep more than half
                truncated = truncated[:last_hyphen]
            sanitized_summary = truncated.rstrip('-')

        branch_name = f"{branch_prefix}/{issue_key_lower}-{sanitized_summary}"

    return {
        'branch_name': branch_name,
        'issue_key': issue_key,
        'issue_type': issue_type,
        'summary': summary,
        'git_command': f"git checkout -b {branch_name}"
    }


def format_output(
    branch_name: str,
    issue_key: str,
    issue: Dict[str, Any],
    output_format: str = 'text'
) -> str:
    """
    Format branch name output.

    Args:
        branch_name: Generated branch name
        issue_key: JIRA issue key
        issue: Issue data from JIRA
        output_format: Output format (text, json, git)

    Returns:
        Formatted output string
    """
    if output_format == 'json':
        data = {
            'branch_name': branch_name,
            'issue_key': issue_key,
            'summary': issue.get('fields', {}).get('summary', ''),
            'issue_type': issue.get('fields', {}).get('issuetype', {}).get('name', '')
        }
        return json.dumps(data, indent=2)

    elif output_format == 'git':
        return f"git checkout -b {branch_name}"

    else:  # text
        return branch_name


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='Generate Git branch name from JIRA issue',
        epilog='Example: python create_branch_name.py PROJ-123 --auto-prefix'
    )

    parser.add_argument('issue_key',
                        help='JIRA issue key (e.g., PROJ-123)')
    parser.add_argument('--prefix', '-p',
                        choices=['feature', 'bugfix', 'hotfix', 'task', 'epic', 'spike', 'chore', 'docs'],
                        help='Branch prefix (default: feature)')
    parser.add_argument('--auto-prefix', '-a',
                        action='store_true',
                        help='Auto-detect prefix from issue type')
    parser.add_argument('--output', '-o',
                        choices=['text', 'json', 'git'],
                        default='text',
                        help='Output format (default: text)')
    parser.add_argument('--profile',
                        help='JIRA profile to use')

    args = parser.parse_args(argv)

    try:
        issue_key = validate_issue_key(args.issue_key)

        # Get issue for full output
        client = get_jira_client(args.profile)
        try:
            issue = client.get_issue(issue_key, fields=['summary', 'issuetype'])
        finally:
            client.close()

        # Determine prefix
        prefix = args.prefix
        if args.auto_prefix and not prefix:
            issue_type = issue.get('fields', {}).get('issuetype', {}).get('name', '')
            prefix = get_prefix_for_issue_type(issue_type)
        elif not prefix:
            prefix = DEFAULT_PREFIX

        # Generate branch name
        fields = issue.get('fields', {})
        summary = fields.get('summary', '')
        sanitized = sanitize_for_branch(summary)

        issue_key_lower = issue_key.lower()

        # Handle edge case: empty sanitized summary
        if not sanitized:
            branch_name = f"{prefix}/{issue_key_lower}"
        else:
            prefix_part_len = len(prefix) + 1
            key_part_len = len(issue_key_lower) + 1
            max_summary_len = MAX_BRANCH_LENGTH - prefix_part_len - key_part_len

            if len(sanitized) > max_summary_len:
                truncated = sanitized[:max_summary_len]
                last_hyphen = truncated.rfind('-')
                if last_hyphen > max_summary_len // 2:
                    truncated = truncated[:last_hyphen]
                sanitized = truncated.rstrip('-')

            branch_name = f"{prefix}/{issue_key_lower}-{sanitized}"

        # Format and print output
        output = format_output(branch_name, issue_key, issue, args.output)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
