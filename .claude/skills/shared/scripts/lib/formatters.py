"""
Output formatting utilities for JIRA data.

Provides functions to format JIRA API responses as tables, JSON,
CSV, and human-readable text.
"""

import json
import csv
import sys
from typing import Dict, Any, List, Optional
from io import StringIO
from .adf_helper import adf_to_text

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False
    print("Warning: 'tabulate' not installed. Table formatting will be basic.", file=sys.stderr)


def format_issue(issue: Dict[str, Any], detailed: bool = False) -> str:
    """
    Format a JIRA issue for display.

    Args:
        issue: Issue data from JIRA API
        detailed: If True, include all fields

    Returns:
        Formatted issue string
    """
    fields = issue.get('fields', {})
    key = issue.get('key', 'N/A')
    summary = fields.get('summary', 'N/A')
    status = fields.get('status', {}).get('name', 'N/A')
    issue_type = fields.get('issuetype', {}).get('name', 'N/A')
    priority = fields.get('priority', {}).get('name', 'N/A') if fields.get('priority') else 'None'
    assignee = fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'
    reporter = fields.get('reporter', {}).get('displayName', 'N/A') if fields.get('reporter') else 'N/A'
    created = fields.get('created', 'N/A')
    updated = fields.get('updated', 'N/A')

    output = []
    output.append(f"Key:      {key}")
    output.append(f"Type:     {issue_type}")
    output.append(f"Summary:  {summary}")
    output.append(f"Status:   {status}")
    output.append(f"Priority: {priority}")
    output.append(f"Assignee: {assignee}")

    if detailed:
        output.append(f"Reporter: {reporter}")
        output.append(f"Created:  {created}")
        output.append(f"Updated:  {updated}")

        description = fields.get('description')
        if description:
            if isinstance(description, dict):
                desc_text = adf_to_text(description)
            else:
                desc_text = str(description)

            if desc_text:
                output.append(f"\nDescription:")
                for line in desc_text.split('\n'):
                    output.append(f"  {line}")

        labels = fields.get('labels', [])
        if labels:
            output.append(f"\nLabels: {', '.join(labels)}")

        components = fields.get('components', [])
        if components:
            comp_names = [c.get('name', '') for c in components]
            output.append(f"Components: {', '.join(comp_names)}")

    return '\n'.join(output)


def format_table(data: List[Dict[str, Any]], columns: Optional[List[str]] = None,
                 headers: Optional[List[str]] = None) -> str:
    """
    Format data as a table.

    Args:
        data: List of dictionaries to format
        columns: Column keys to include (default: all keys from first item)
        headers: Column headers (default: use column keys)

    Returns:
        Formatted table string
    """
    if not data:
        return "No data to display"

    if columns is None:
        columns = list(data[0].keys())

    if headers is None:
        headers = columns

    rows = []
    for item in data:
        row = []
        for col in columns:
            value = item.get(col, '')

            if isinstance(value, dict):
                value = value.get('name', str(value))
            elif isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            elif value is None:
                value = ''

            value_str = str(value)
            if len(value_str) > 50:
                value_str = value_str[:47] + '...'

            row.append(value_str)
        rows.append(row)

    if HAS_TABULATE:
        return tabulate(rows, headers=headers, tablefmt='simple')
    else:
        return _format_basic_table(rows, headers)


def _format_basic_table(rows: List[List[str]], headers: List[str]) -> str:
    """
    Basic table formatting without tabulate library.

    Args:
        rows: Table rows
        headers: Column headers

    Returns:
        Formatted table string
    """
    col_widths = [len(h) for h in headers]

    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    separator = '-' * (sum(col_widths) + len(col_widths) * 3 + 1)

    lines = []
    lines.append(separator)

    header_line = '| ' + ' | '.join(
        h.ljust(col_widths[i]) for i, h in enumerate(headers)
    ) + ' |'
    lines.append(header_line)
    lines.append(separator)

    for row in rows:
        row_line = '| ' + ' | '.join(
            str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)
        ) + ' |'
        lines.append(row_line)

    lines.append(separator)
    return '\n'.join(lines)


def format_json(data: Any, pretty: bool = True) -> str:
    """
    Format data as JSON.

    Args:
        data: Data to format
        pretty: If True, use indentation

    Returns:
        JSON string
    """
    if pretty:
        return json.dumps(data, indent=2, ensure_ascii=False)
    else:
        return json.dumps(data, ensure_ascii=False)


def export_csv(data: List[Dict[str, Any]], file_path: str,
               columns: Optional[List[str]] = None) -> None:
    """
    Export data to CSV file.

    Args:
        data: List of dictionaries to export
        file_path: Output file path
        columns: Column keys to include (default: all keys from first item)
    """
    if not data:
        raise ValueError("No data to export")

    if columns is None:
        columns = list(data[0].keys())

    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()

        for item in data:
            row = {}
            for col in columns:
                value = item.get(col, '')

                if isinstance(value, dict):
                    value = value.get('name', str(value))
                elif isinstance(value, list):
                    value = ', '.join(str(v) for v in value)
                elif value is None:
                    value = ''

                row[col] = str(value)

            writer.writerow(row)


def get_csv_string(data: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> str:
    """
    Get CSV formatted string.

    Args:
        data: List of dictionaries to format
        columns: Column keys to include (default: all keys from first item)

    Returns:
        CSV string
    """
    if not data:
        return ""

    if columns is None:
        columns = list(data[0].keys())

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()

    for item in data:
        row = {}
        for col in columns:
            value = item.get(col, '')

            if isinstance(value, dict):
                value = value.get('name', str(value))
            elif isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            elif value is None:
                value = ''

            row[col] = str(value)

        writer.writerow(row)

    return output.getvalue()


def format_transitions(transitions: List[Dict[str, Any]]) -> str:
    """
    Format available transitions for display.

    Args:
        transitions: List of transition objects from JIRA API

    Returns:
        Formatted transitions string
    """
    if not transitions:
        return "No transitions available"

    data = []
    for t in transitions:
        data.append({
            'ID': t.get('id', ''),
            'Name': t.get('name', ''),
            'To Status': t.get('to', {}).get('name', '')
        })

    return format_table(data, columns=['ID', 'Name', 'To Status'])


def format_comments(comments: List[Dict[str, Any]], limit: Optional[int] = None) -> str:
    """
    Format issue comments for display.

    Args:
        comments: List of comment objects from JIRA API
        limit: Maximum number of comments to display

    Returns:
        Formatted comments string
    """
    if not comments:
        return "No comments"

    if limit:
        comments = comments[:limit]

    output = []
    for i, comment in enumerate(comments, 1):
        author = comment.get('author', {}).get('displayName', 'Unknown')
        created = comment.get('created', 'N/A')
        body = comment.get('body')

        if isinstance(body, dict):
            body_text = adf_to_text(body)
        else:
            body_text = str(body) if body else ''

        output.append(f"Comment #{i} by {author} at {created}:")
        for line in body_text.split('\n'):
            output.append(f"  {line}")
        output.append("")

    return '\n'.join(output)


def format_search_results(issues: List[Dict[str, Any]]) -> str:
    """
    Format search results as a table.

    Args:
        issues: List of issue objects from JIRA API

    Returns:
        Formatted table string
    """
    if not issues:
        return "No issues found"

    data = []
    for issue in issues:
        fields = issue.get('fields', {})
        data.append({
            'Key': issue.get('key', ''),
            'Type': fields.get('issuetype', {}).get('name', ''),
            'Status': fields.get('status', {}).get('name', ''),
            'Priority': fields.get('priority', {}).get('name', '') if fields.get('priority') else '',
            'Summary': fields.get('summary', '')[:60]
        })

    return format_table(data, columns=['Key', 'Type', 'Status', 'Priority', 'Summary'])


def print_success(message: str) -> None:
    """
    Print success message in green (if colorama available).

    Args:
        message: Success message
    """
    try:
        from colorama import Fore, Style, init
        init(autoreset=True)
        print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")
    except ImportError:
        print(f"✓ {message}")


def print_warning(message: str) -> None:
    """
    Print warning message in yellow (if colorama available).

    Args:
        message: Warning message
    """
    try:
        from colorama import Fore, Style, init
        init(autoreset=True)
        print(f"{Fore.YELLOW}Warning: {message}{Style.RESET_ALL}")
    except ImportError:
        print(f"⚠ Warning: {message}")


def print_info(message: str) -> None:
    """
    Print info message in blue (if colorama available).

    Args:
        message: Info message
    """
    try:
        from colorama import Fore, Style, init
        init(autoreset=True)
        print(f"{Fore.BLUE}{message}{Style.RESET_ALL}")
    except ImportError:
        print(f"ℹ {message}")
