#!/usr/bin/env python3
"""
Export timesheets to CSV/JSON formats.

Creates exportable timesheet files for billing, reporting, or import into other systems.
"""

import argparse
import json
import csv
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from io import StringIO

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import format_seconds, parse_relative_date


def format_csv(data: Dict[str, Any]) -> str:
    """
    Format timesheet data as CSV.

    Args:
        data: Timesheet data with entries

    Returns:
        CSV formatted string
    """
    output = StringIO()
    fieldnames = ['Issue Key', 'Issue Summary', 'Author', 'Email', 'Date', 'Time Spent', 'Seconds', 'Comment']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for entry in data.get('entries', []):
        writer.writerow({
            'Issue Key': entry.get('issue_key', ''),
            'Issue Summary': entry.get('issue_summary', ''),
            'Author': entry.get('author', ''),
            'Email': entry.get('author_email', ''),
            'Date': entry.get('started_date', ''),
            'Time Spent': entry.get('time_spent', ''),
            'Seconds': entry.get('time_seconds', 0),
            'Comment': entry.get('comment', '')
        })

    return output.getvalue()


def format_json(data: Dict[str, Any]) -> str:
    """
    Format timesheet data as JSON.

    Args:
        data: Timesheet data with entries

    Returns:
        JSON formatted string
    """
    return json.dumps(data, indent=2)


def write_export(data: Dict[str, Any], output_file: str, format_type: str) -> None:
    """
    Write export to file.

    Args:
        data: Timesheet data
        output_file: Path to output file
        format_type: Export format (csv or json)
    """
    if format_type == 'csv':
        content = format_csv(data)
    else:
        content = format_json(data)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)


def fetch_timesheet_data(client, project: Optional[str] = None,
                         author: Optional[str] = None,
                         since: Optional[str] = None,
                         until: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch timesheet data from JIRA.

    Args:
        client: JiraClient instance
        project: Project key to filter by
        author: Author email/accountId to filter by
        since: Start date
        until: End date

    Returns:
        Timesheet data dict
    """
    # Build JQL query
    jql_parts = []
    if project:
        jql_parts.append(f'project = {project}')
    jql_parts.append('timespent > 0')

    jql = ' AND '.join(jql_parts) if jql_parts else 'timespent > 0'

    # Parse date filters
    since_dt = None
    until_dt = None
    if since:
        since_dt = parse_relative_date(since)
    if until:
        until_dt = parse_relative_date(until)
        until_dt = until_dt.replace(hour=23, minute=59, second=59)

    # Fetch issues with worklogs
    search_result = client.search_issues(jql, fields=['summary'], max_results=100)
    issues = search_result.get('issues', [])

    # Collect all worklog entries
    entries = []
    for issue in issues:
        issue_key = issue['key']
        issue_summary = issue['fields'].get('summary', '')

        worklogs_result = client.get_worklogs(issue_key)
        worklogs = worklogs_result.get('worklogs', [])

        for worklog in worklogs:
            # Parse started date
            started_str = worklog.get('started', '')
            try:
                started_dt = datetime.fromisoformat(started_str.replace('+0000', '+00:00').replace('Z', '+00:00'))
                started_dt = started_dt.replace(tzinfo=None)
            except (ValueError, AttributeError):
                continue

            # Apply date filters
            if since_dt and started_dt.date() < since_dt.date():
                continue
            if until_dt and started_dt.date() > until_dt.date():
                continue

            # Apply author filter
            worklog_author = worklog.get('author', {})
            author_email = worklog_author.get('emailAddress', '')
            author_id = worklog_author.get('accountId', '')

            if author:
                if author not in (author_email, author_id):
                    continue

            # Extract comment text
            comment_text = ''
            comment = worklog.get('comment')
            if comment and isinstance(comment, dict):
                # ADF format - extract text
                for content in comment.get('content', []):
                    for child in content.get('content', []):
                        if child.get('type') == 'text':
                            comment_text += child.get('text', '')

            entries.append({
                'issue_key': issue_key,
                'issue_summary': issue_summary,
                'worklog_id': worklog.get('id'),
                'author': worklog_author.get('displayName', author_email),
                'author_email': author_email,
                'started': started_str,
                'started_date': started_dt.strftime('%Y-%m-%d'),
                'time_spent': worklog.get('timeSpent', ''),
                'time_seconds': worklog.get('timeSpentSeconds', 0),
                'comment': comment_text
            })

    # Calculate totals
    total_seconds = sum(e['time_seconds'] for e in entries)

    return {
        'entries': entries,
        'entry_count': len(entries),
        'total_seconds': total_seconds,
        'total_formatted': format_seconds(total_seconds) if total_seconds else '0m',
        'generated_at': datetime.now().isoformat(),
        'filters': {
            'project': project,
            'author': author,
            'since': since,
            'until': until
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description='Export timesheets to CSV/JSON formats.',
        epilog='''
Examples:
  %(prog)s --project PROJ --period 2025-01 --output timesheets.csv
  %(prog)s --project PROJ --period last-month --format json --output timesheets.json
  %(prog)s --user alice@company.com --period this-month
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--project', '-P',
                        help='Project key to filter by')
    parser.add_argument('--user', '-u',
                        help='User email or accountId to filter by')
    parser.add_argument('--since', '-s',
                        help='Start date (e.g., 2025-01-01)')
    parser.add_argument('--until', '-e',
                        help='End date (e.g., 2025-01-31)')
    parser.add_argument('--period',
                        help='Month period (e.g., 2025-01) or named period (last-month, this-month)')
    parser.add_argument('--format', '-f',
                        choices=['csv', 'json'],
                        default='csv',
                        help='Export format (default: csv)')
    parser.add_argument('--output', '-o',
                        help='Output file path (stdout if not specified)')
    parser.add_argument('--profile', '-p',
                        help='JIRA profile to use')

    args = parser.parse_args()

    # Handle period argument
    if args.period:
        today = datetime.now().date()
        if args.period == 'this-month':
            args.since = str(today.replace(day=1))
            args.until = str(today)
        elif args.period == 'last-month':
            first_of_month = today.replace(day=1)
            last_month_end = first_of_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            args.since = str(last_month_start)
            args.until = str(last_month_end)
        elif '-' in args.period and len(args.period) == 7:
            # Year-month format like 2025-01
            year, month = args.period.split('-')
            year = int(year)
            month = int(month)
            start = datetime(year, month, 1).date()
            if month == 12:
                end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end = datetime(year, month + 1, 1).date() - timedelta(days=1)
            args.since = str(start)
            args.until = str(end)

    try:
        # Get client
        client = get_jira_client(args.profile)

        # Fetch data
        data = fetch_timesheet_data(
            client,
            project=args.project,
            author=args.user,
            since=args.since,
            until=args.until
        )

        # Output
        if args.output:
            write_export(data, args.output, args.format)
            print(f"Exported {data['entry_count']} entries to {args.output}")
            print(f"Total time: {data['total_formatted']}")
        else:
            if args.format == 'csv':
                print(format_csv(data))
            else:
                print(format_json(data))

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)


if __name__ == '__main__':
    main()
