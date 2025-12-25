#!/usr/bin/env python3
"""
Find all dependencies for a JIRA issue.

Usage:
    python get_dependencies.py PROJ-123
    python get_dependencies.py PROJ-123 --type blocks,relates
    python get_dependencies.py PROJ-123 --output mermaid
    python get_dependencies.py PROJ-123 --output dot > deps.dot
"""

import sys
import argparse
import json
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError
from validators import validate_issue_key


def get_dependencies(issue_key: str, link_types: Optional[List[str]] = None,
                     profile: str = None) -> Dict[str, Any]:
    """
    Get all dependencies for an issue.

    Args:
        issue_key: Issue key
        link_types: Optional list of link type names to filter
        profile: JIRA profile

    Returns:
        Dict with dependencies info
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client(profile)

    try:
        links = client.get_issue_links(issue_key)
    finally:
        client.close()

    dependencies = []
    status_counts = defaultdict(int)

    for link in links:
        link_type = link['type']['name']

        # Filter by link type if specified
        if link_types and link_type.lower() not in [t.lower() for t in link_types]:
            continue

        if 'outwardIssue' in link:
            issue = link['outwardIssue']
            direction = 'outward'
            direction_label = link['type']['outward']
        else:
            issue = link['inwardIssue']
            direction = 'inward'
            direction_label = link['type']['inward']

        status = issue.get('fields', {}).get('status', {}).get('name', 'Unknown')
        status_counts[status] += 1

        dependencies.append({
            'key': issue['key'],
            'summary': issue.get('fields', {}).get('summary', ''),
            'status': status,
            'link_type': link_type,
            'direction': direction,
            'direction_label': direction_label,
            'link_id': link['id']
        })

    return {
        'issue_key': issue_key,
        'dependencies': dependencies,
        'total': len(dependencies),
        'status_summary': dict(status_counts)
    }


def format_dependencies(result: Dict[str, Any], output_format: str = 'text') -> str:
    """
    Format dependencies for output.

    Args:
        result: Dependencies result dict
        output_format: 'text', 'json', 'mermaid', or 'dot'

    Returns:
        Formatted string
    """
    if output_format == 'json':
        return json.dumps(result, indent=2)

    issue_key = result['issue_key']
    dependencies = result.get('dependencies', [])

    if output_format == 'mermaid':
        return format_mermaid(issue_key, dependencies)
    elif output_format == 'dot':
        return format_dot(issue_key, dependencies)

    # Text format
    if not dependencies:
        return f"No dependencies found for {issue_key}"

    lines = []
    lines.append(f"Dependencies for {issue_key}:")
    lines.append("")

    # Group by link type
    by_type = defaultdict(list)
    for dep in dependencies:
        by_type[dep['link_type']].append(dep)

    for link_type, deps in by_type.items():
        lines.append(f"{link_type}:")
        for dep in deps:
            status = dep['status']
            summary = dep['summary'][:45] if dep['summary'] else ''
            arrow = "->" if dep['direction'] == 'outward' else "<-"
            lines.append(f"  {arrow} {dep['key']} [{status}] {summary}")
        lines.append("")

    # Status summary
    status_summary = result.get('status_summary', {})
    if status_summary:
        lines.append("Status Summary:")
        for status, count in sorted(status_summary.items()):
            lines.append(f"  {status}: {count}")
        lines.append("")

    lines.append(f"Total: {result['total']} dependency(ies)")

    return "\n".join(lines)


def format_mermaid(issue_key: str, dependencies: list) -> str:
    """Format as Mermaid flowchart."""
    lines = []
    lines.append("flowchart TD")

    # Define the main issue
    lines.append(f"    {sanitize_key(issue_key)}[{issue_key}]")

    # Add nodes and edges
    seen_nodes = {issue_key}
    for dep in dependencies:
        dep_key = dep['key']
        if dep_key not in seen_nodes:
            seen_nodes.add(dep_key)
            # Node with summary
            summary = dep['summary'][:30].replace('"', "'") if dep['summary'] else dep_key
            lines.append(f"    {sanitize_key(dep_key)}[\"{dep_key}: {summary}\"]")

        # Edge
        label = dep['direction_label']
        if dep['direction'] == 'outward':
            lines.append(f"    {sanitize_key(issue_key)} -->|{label}| {sanitize_key(dep_key)}")
        else:
            lines.append(f"    {sanitize_key(dep_key)} -->|{label}| {sanitize_key(issue_key)}")

    return "\n".join(lines)


def format_dot(issue_key: str, dependencies: list) -> str:
    """Format as DOT/Graphviz."""
    lines = []
    lines.append("digraph Dependencies {")
    lines.append("    rankdir=LR;")
    lines.append("    node [shape=box];")
    lines.append("")

    # Main issue
    lines.append(f'    "{issue_key}" [style=filled, fillcolor=lightblue];')

    # Dependencies
    for dep in dependencies:
        dep_key = dep['key']
        status = dep['status']

        # Color by status
        color = 'lightgreen' if status == 'Done' else 'lightyellow' if status == 'In Progress' else 'white'
        lines.append(f'    "{dep_key}" [style=filled, fillcolor={color}];')

        # Edge
        label = dep['direction_label']
        if dep['direction'] == 'outward':
            lines.append(f'    "{issue_key}" -> "{dep_key}" [label="{label}"];')
        else:
            lines.append(f'    "{dep_key}" -> "{issue_key}" [label="{label}"];')

    lines.append("}")
    return "\n".join(lines)


def sanitize_key(key: str) -> str:
    """Sanitize issue key for Mermaid node ID."""
    return key.replace('-', '_')


def main():
    parser = argparse.ArgumentParser(
        description='Find all dependencies for a JIRA issue',
        epilog='Example: python get_dependencies.py PROJ-123 --output mermaid'
    )

    parser.add_argument('issue_key',
                       help='Issue key (e.g., PROJ-123)')

    parser.add_argument('--type', '-t',
                       dest='link_types',
                       help='Comma-separated link types to include (e.g., blocks,relates)')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json', 'mermaid', 'dot'],
                       default='text',
                       help='Output format (default: text)')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        link_types = args.link_types.split(',') if args.link_types else None

        result = get_dependencies(
            issue_key=args.issue_key,
            link_types=link_types,
            profile=args.profile
        )
        output = format_dependencies(result, output_format=args.output)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
