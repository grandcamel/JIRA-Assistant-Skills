#!/usr/bin/env python3
"""
Parse JIRA issue keys from commit messages.

Extracts issue keys in various formats from commit messages,
supporting conventional commits, prefixes (fixes, closes), and more.

Usage:
    python parse_commit_issues.py "PROJ-123: Fix login bug"
    python parse_commit_issues.py "Fix PROJ-123 and PROJ-456" --output json
    git log --oneline -10 | python parse_commit_issues.py --from-stdin
    python parse_commit_issues.py "PROJ-123, OTHER-456" --project PROJ
"""

import sys
import os
import argparse
import json
import re
from pathlib import Path
from typing import List, Optional

# Add shared lib path

# Issue key pattern: PROJECT-NUMBER
# Matches: PROJ-123, ABC-1, MYPROJECT-99999
ISSUE_KEY_PATTERN = re.compile(
    r'\b([A-Z][A-Z0-9]+-[0-9]+)\b',
    re.IGNORECASE
)

# Prefixes that often precede issue keys
COMMIT_PREFIXES = [
    'fixes',
    'fixed',
    'fix',
    'closes',
    'closed',
    'close',
    'resolves',
    'resolved',
    'resolve',
    'refs',
    'ref',
    'references',
    'related to',
    'relates to',
    'see',
]


def parse_issue_keys(
    message: str,
    project_filter: Optional[str] = None
) -> List[str]:
    """
    Extract JIRA issue keys from a commit message.

    Supports various formats:
    - Direct: PROJ-123
    - With prefix: Fixes PROJ-123
    - Conventional commit: feat(PROJ-123): add feature
    - Multiple: PROJ-123, PROJ-456
    - Square brackets: [PROJ-123]
    - Parentheses: (PROJ-123)

    Args:
        message: Commit message to parse
        project_filter: Only return issues from this project

    Returns:
        List of unique issue keys (uppercase)
    """
    if not message:
        return []

    # Find all issue keys in the message
    matches = ISSUE_KEY_PATTERN.findall(message)

    # Normalize to uppercase and deduplicate while preserving order
    seen = set()
    issue_keys = []

    for match in matches:
        key = match.upper()
        if key not in seen:
            seen.add(key)

            # Apply project filter if specified
            if project_filter:
                project = key.split('-')[0]
                if project.upper() != project_filter.upper():
                    continue

            issue_keys.append(key)

    return issue_keys


def parse_from_lines(
    lines: List[str],
    project_filter: Optional[str] = None,
    unique: bool = True
) -> List[str]:
    """
    Parse issue keys from multiple lines.

    Args:
        lines: List of commit message lines
        project_filter: Only return issues from this project
        unique: If True, return unique keys only

    Returns:
        List of issue keys
    """
    all_keys = []

    for line in lines:
        keys = parse_issue_keys(line, project_filter)
        all_keys.extend(keys)

    if unique:
        # Preserve order while deduplicating
        seen = set()
        unique_keys = []
        for key in all_keys:
            if key not in seen:
                seen.add(key)
                unique_keys.append(key)
        return unique_keys

    return all_keys


def format_output(
    issue_keys: List[str],
    output_format: str = 'text'
) -> str:
    """
    Format issue keys for output.

    Args:
        issue_keys: List of issue keys
        output_format: Output format (text, json, csv)

    Returns:
        Formatted output string
    """
    if output_format == 'json':
        return json.dumps({
            'issue_keys': issue_keys,
            'count': len(issue_keys)
        }, indent=2)

    elif output_format == 'csv':
        return ','.join(issue_keys)

    else:  # text
        return '\n'.join(issue_keys)


def main():
    parser = argparse.ArgumentParser(
        description='Parse JIRA issue keys from commit messages',
        epilog='Example: python parse_commit_issues.py "PROJ-123: Fix bug"'
    )

    parser.add_argument('message',
                        nargs='?',
                        help='Commit message to parse')
    parser.add_argument('--from-stdin',
                        action='store_true',
                        help='Read from stdin (for git log pipe)')
    parser.add_argument('--project', '-p',
                        help='Filter by project key')
    parser.add_argument('--output', '-o',
                        choices=['text', 'json', 'csv'],
                        default='text',
                        help='Output format (default: text)')
    parser.add_argument('--unique', '-u',
                        action='store_true',
                        default=True,
                        help='Return unique issue keys only (default: True)')

    args = parser.parse_args()

    # Get input
    if args.from_stdin:
        lines = sys.stdin.read().strip().split('\n')
        issue_keys = parse_from_lines(lines, args.project, args.unique)
    elif args.message:
        issue_keys = parse_issue_keys(args.message, args.project)
    else:
        parser.print_help()
        sys.exit(1)

    # Format and output
    if issue_keys:
        output = format_output(issue_keys, args.output)
        print(output)
    elif args.output == 'json':
        print(format_output([], args.output))
    # For text/csv, print nothing if no keys found


if __name__ == '__main__':
    main()
