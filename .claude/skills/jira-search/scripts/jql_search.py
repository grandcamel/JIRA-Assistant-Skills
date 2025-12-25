#!/usr/bin/env python3
"""
Search for JIRA issues using JQL.

Usage:
    python jql_search.py "project = PROJ AND status = Open"
    python jql_search.py "assignee = currentUser()" --fields key,summary,status
    python jql_search.py "created >= -7d" --max-results 100
"""

import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError
from validators import validate_jql
from formatters import format_search_results, format_json, print_info

EPIC_LINK_FIELD = 'customfield_10014'
STORY_POINTS_FIELD = 'customfield_10016'


def search_issues(jql: str, fields: list = None, max_results: int = 50,
                 start_at: int = 0, profile: str = None,
                 include_agile: bool = False) -> dict:
    """
    Search for issues using JQL.

    Args:
        jql: JQL query string
        fields: List of fields to return (default: key, summary, status, priority, issuetype)
        max_results: Maximum results per page
        start_at: Starting index for pagination
        profile: JIRA profile to use
        include_agile: If True, include epic link and story points fields

    Returns:
        Search results dictionary
    """
    jql = validate_jql(jql)

    if fields is None:
        fields = ['key', 'summary', 'status', 'priority', 'issuetype', 'assignee']
        if include_agile:
            fields.extend([EPIC_LINK_FIELD, STORY_POINTS_FIELD, 'sprint'])

    client = get_jira_client(profile)
    results = client.search_issues(jql, fields=fields, max_results=max_results, start_at=start_at)
    client.close()

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Search for JIRA issues using JQL',
        epilog='Example: python jql_search.py "project = PROJ AND status = Open"'
    )

    parser.add_argument('jql',
                       help='JQL query string')
    parser.add_argument('--fields', '-f',
                       help='Comma-separated list of fields to return (default: key,summary,status,priority,issuetype,assignee)')
    parser.add_argument('--max-results', '-m',
                       type=int,
                       default=50,
                       help='Maximum number of results (default: 50)')
    parser.add_argument('--start-at', '-s',
                       type=int,
                       default=0,
                       help='Starting index for pagination (default: 0)')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format (default: text)')
    parser.add_argument('--show-agile', '-a',
                       action='store_true',
                       help='Show Agile fields (epic, story points) in results')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        fields = [f.strip() for f in args.fields.split(',')] if args.fields else None

        results = search_issues(
            jql=args.jql,
            fields=fields,
            max_results=args.max_results,
            start_at=args.start_at,
            profile=args.profile,
            include_agile=args.show_agile
        )

        issues = results.get('issues', [])
        total = results.get('total', 0)

        if args.output == 'json':
            print(format_json(results))
        else:
            print_info(f"Found {total} issue(s)")
            if issues:
                print()
                print(format_search_results(issues, show_agile=args.show_agile))

                if total > len(issues):
                    remaining = total - args.start_at - len(issues)
                    print(f"\nShowing {len(issues)} of {total} results (use --start-at and --max-results for pagination)")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
