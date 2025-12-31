#!/usr/bin/env python3
"""
Generate Pull Request description from JIRA issue.

Creates a formatted PR description using issue details,
with support for templates and checklists.

Usage:
    python create_pr_description.py PROJ-123
    python create_pr_description.py PROJ-123 --include-checklist
    python create_pr_description.py PROJ-123 --include-labels
    python create_pr_description.py PROJ-123 --output json
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add shared lib path

from jira_assistant_skills_lib import get_jira_client, ConfigManager
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import validate_issue_key
from jira_assistant_skills_lib import adf_to_text


def get_jira_base_url(profile: Optional[str] = None) -> str:
    """
    Get JIRA base URL from configuration.

    Args:
        profile: JIRA profile to use

    Returns:
        JIRA base URL
    """
    try:
        config_manager = ConfigManager(profile=profile)
        url, _, _ = config_manager.get_credentials(profile)
        return url
    except Exception:
        return "https://jira.example.com"


def extract_acceptance_criteria(description: str) -> List[str]:
    """
    Extract acceptance criteria from issue description.

    Looks for common patterns like:
    - Acceptance Criteria:
    - AC:
    - Given/When/Then

    Args:
        description: Issue description text

    Returns:
        List of acceptance criteria items
    """
    if not description:
        return []

    criteria = []
    lines = description.split('\n')
    in_ac_section = False

    for line in lines:
        line_lower = line.lower().strip()

        # Check for AC section start
        if 'acceptance criteria' in line_lower or line_lower.startswith('ac:'):
            in_ac_section = True
            continue

        # Check for section end (new header)
        if in_ac_section and line.strip().startswith('#'):
            in_ac_section = False
            continue

        # Collect items in AC section
        if in_ac_section and line.strip():
            # Remove common list markers
            item = line.strip().lstrip('-*').strip()
            if item:
                criteria.append(item)

        # Also look for Given/When/Then patterns
        if line_lower.startswith(('given ', 'when ', 'then ')):
            criteria.append(line.strip())

    return criteria


def create_pr_description(
    issue_key: str,
    include_checklist: bool = False,
    include_labels: bool = False,
    include_components: bool = False,
    profile: Optional[str] = None,
    client=None,
    output_format: str = 'text'
) -> Dict[str, Any]:
    """
    Create a PR description from JIRA issue details.

    Args:
        issue_key: JIRA issue key
        include_checklist: Include testing checklist
        include_labels: Include issue labels
        include_components: Include components
        profile: JIRA profile
        client: Optional JiraClient instance (created if not provided)
        output_format: Output format (text, json)

    Returns:
        Dictionary with markdown, issue_key, issue_type, priority
    """
    issue_key = validate_issue_key(issue_key)

    close_client = False
    if client is None:
        client = get_jira_client(profile)
        close_client = True
    try:
        issue = client.get_issue(
            issue_key,
            fields=['summary', 'description', 'issuetype', 'labels', 'components', 'priority']
        )
    finally:
        if close_client:
            client.close()

    fields = issue.get('fields', {})
    summary = fields.get('summary', '')
    description = fields.get('description')
    issue_type = fields.get('issuetype', {}).get('name', '')
    labels = fields.get('labels', [])
    components = [c.get('name', '') for c in fields.get('components', [])]
    priority = fields.get('priority', {}).get('name', '') if fields.get('priority') else ''

    # Convert ADF description to text
    if isinstance(description, dict):
        desc_text = adf_to_text(description)
    else:
        desc_text = description or ''

    # Get JIRA URL for link
    jira_url = get_jira_base_url(profile)

    # Build PR description
    lines = []

    # Summary section
    lines.append(f"## Summary")
    lines.append("")
    lines.append(summary)
    lines.append("")

    # JIRA Issue link
    lines.append(f"## JIRA Issue")
    lines.append("")
    lines.append(f"[{issue_key}]({jira_url}/browse/{issue_key})")
    lines.append("")

    # Type and priority
    if issue_type or priority:
        lines.append(f"**Type:** {issue_type}")
        if priority:
            lines.append(f"**Priority:** {priority}")
        lines.append("")

    # Description/Changes section
    if desc_text:
        lines.append("## Description")
        lines.append("")
        # Truncate if too long
        if len(desc_text) > 500:
            lines.append(desc_text[:500] + "...")
        else:
            lines.append(desc_text)
        lines.append("")

    # Labels
    if include_labels and labels:
        lines.append("## Labels")
        lines.append("")
        lines.append(", ".join([f"`{label}`" for label in labels]))
        lines.append("")

    # Components
    if include_components and components:
        lines.append("## Components")
        lines.append("")
        lines.append(", ".join(components))
        lines.append("")

    # Acceptance Criteria
    acceptance_criteria = extract_acceptance_criteria(desc_text)
    if acceptance_criteria:
        lines.append("## Acceptance Criteria")
        lines.append("")
        for criterion in acceptance_criteria:
            lines.append(f"- [ ] {criterion}")
        lines.append("")

    # Testing Checklist
    if include_checklist:
        lines.append("## Testing Checklist")
        lines.append("")
        lines.append("- [ ] Unit tests added/updated")
        lines.append("- [ ] Integration tests pass")
        lines.append("- [ ] Manual testing completed")
        lines.append("- [ ] No regressions introduced")
        lines.append("")

    markdown = '\n'.join(lines)

    return {
        'markdown': markdown,
        'issue_key': issue_key,
        'issue_type': issue_type,
        'summary': summary,
        'priority': priority,
        'labels': labels,
        'components': components
    }


def format_output(
    result: Dict[str, Any],
    output_format: str = 'text'
) -> str:
    """
    Format PR description for output.

    Args:
        result: Result dictionary from create_pr_description
        output_format: Output format (text, json)

    Returns:
        Formatted output string
    """
    if output_format == 'json':
        return json.dumps({
            'description': result['markdown'],
            'issue_key': result['issue_key'],
            'summary': result['summary'],
            'issue_type': result['issue_type'],
            'priority': result['priority']
        }, indent=2)
    else:
        return result['markdown']


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='Generate PR description from JIRA issue',
        epilog='Example: python create_pr_description.py PROJ-123 --include-checklist'
    )

    parser.add_argument('issue_key',
                        help='JIRA issue key (e.g., PROJ-123)')
    parser.add_argument('--include-checklist', '-c',
                        action='store_true',
                        help='Include testing checklist')
    parser.add_argument('--include-labels', '-l',
                        action='store_true',
                        help='Include issue labels')
    parser.add_argument('--include-components',
                        action='store_true',
                        help='Include components')
    parser.add_argument('--output', '-o',
                        choices=['text', 'json'],
                        default='text',
                        help='Output format')
    parser.add_argument('--copy',
                        action='store_true',
                        help='Copy to clipboard (requires pyperclip)')
    parser.add_argument('--profile',
                        help='JIRA profile to use')

    args = parser.parse_args(argv)

    try:
        result = create_pr_description(
            issue_key=args.issue_key,
            include_checklist=args.include_checklist,
            include_labels=args.include_labels,
            include_components=args.include_components,
            profile=args.profile
        )

        output = format_output(result, args.output)

        # Copy to clipboard if requested
        if args.copy:
            try:
                import pyperclip
                pyperclip.copy(result['markdown'])
                print("PR description copied to clipboard!", file=sys.stderr)
            except ImportError:
                print("Warning: pyperclip not installed. Cannot copy to clipboard.", file=sys.stderr)

        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
