#!/usr/bin/env python3
"""
Search for JIRA issues using JQL.

Usage:
    python jql_search.py "project = PROJ AND status = Open"
    python jql_search.py "assignee = currentUser()" --fields key,summary,status
    python jql_search.py "created >= -7d" --max-results 100
    python jql_search.py "project = PROJ" --show-links
    python jql_search.py "project = PROJ" --show-time
    python jql_search.py --filter 10042
    python jql_search.py "project = PROJ" --save-as "My Filter"
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Optional


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import validate_jql
from jira_assistant_skills_lib import format_search_results, format_json, print_info

EPIC_LINK_FIELD = 'customfield_10014'
STORY_POINTS_FIELD = 'customfield_10016'


def get_jql_from_filter(client, filter_id: str) -> tuple:
    """
    Get JQL from a saved filter.

    Args:
        client: JIRA client
        filter_id: Filter ID

    Returns:
        Tuple of (jql, filter_name)
    """
    filter_data = client.get_filter(filter_id)
    return filter_data.get('jql', ''), filter_data.get('name', f'Filter {filter_id}')


def save_search_as_filter(client, jql: str, name: str,
                          description: str = None,
                          favourite: bool = False) -> dict:
    """
    Save a JQL search as a new filter.

    Args:
        client: JIRA client
        jql: JQL query string
        name: Filter name
        description: Optional description
        favourite: Add to favourites

    Returns:
        Created filter object
    """
    return client.create_filter(name, jql, description=description, favourite=favourite)


def search_issues(jql: str, fields: list = None, max_results: int = 50,
                 next_page_token: str = None, profile: str = None,
                 include_agile: bool = False, include_links: bool = False,
                 include_time: bool = False) -> dict:
    """
    Search for issues using JQL.

    Args:
        jql: JQL query string
        fields: List of fields to return (default: key, summary, status, priority, issuetype)
        max_results: Maximum results per page
        next_page_token: Token for fetching next page (from previous response)
        profile: JIRA profile to use
        include_agile: If True, include epic link and story points fields
        include_links: If True, include issue links
        include_time: If True, include time tracking fields

    Returns:
        Search results dictionary with nextPageToken for pagination
    """
    jql = validate_jql(jql)

    if fields is None:
        fields = ['key', 'summary', 'status', 'priority', 'issuetype', 'assignee', 'reporter']
        if include_agile:
            fields.extend([EPIC_LINK_FIELD, STORY_POINTS_FIELD, 'sprint'])
        if include_links:
            fields.append('issuelinks')
        if include_time:
            fields.append('timetracking')

    client = get_jira_client(profile)
    results = client.search_issues(jql, fields=fields, max_results=max_results,
                                   next_page_token=next_page_token)
    client.close()

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Search for JIRA issues using JQL',
        epilog='''
Examples:
  %(prog)s "project = PROJ AND status = Open"
  %(prog)s "assignee = currentUser()" --fields key,summary,status
  %(prog)s --filter 10042                    # Run saved filter
  %(prog)s "project = PROJ" --save-as "My Filter"  # Save as filter
        '''
    )

    parser.add_argument('jql', nargs='?',
                       help='JQL query string (not required with --filter)')
    parser.add_argument('--filter',
                       help='Run a saved filter by ID instead of JQL')
    parser.add_argument('--save-as',
                       help='Save the search as a new filter with this name')
    parser.add_argument('--save-description',
                       help='Description for the saved filter (use with --save-as)')
    parser.add_argument('--save-favourite', action='store_true',
                       help='Add saved filter to favourites (use with --save-as)')
    parser.add_argument('--fields', '-f',
                       help='Comma-separated list of fields to return (default: key,summary,status,priority,issuetype,assignee,reporter)')
    parser.add_argument('--max-results', '-m',
                       type=int,
                       default=50,
                       help='Maximum number of results (default: 50)')
    parser.add_argument('--page-token', '-p',
                       help='Next page token from previous response (for pagination)')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format (default: text)')
    parser.add_argument('--show-agile', '-a',
                       action='store_true',
                       help='Show Agile fields (epic, story points) in results')
    parser.add_argument('--show-links', '-l',
                       action='store_true',
                       help='Show issue links in results')
    parser.add_argument('--show-time', '-t',
                       action='store_true',
                       help='Show time tracking fields in results')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    # Validate: need either jql or --filter
    if not args.jql and not args.filter:
        parser.error("Either JQL query or --filter is required")

    try:
        client = get_jira_client(args.profile)
        jql = args.jql
        filter_name = None

        # If using --filter, get JQL from saved filter
        if args.filter:
            jql, filter_name = get_jql_from_filter(client, args.filter)
            if args.output != 'json':
                print_info(f"Running filter: {filter_name}")
                print_info(f"JQL: {jql}")
                print()

        # Validate JQL
        jql = validate_jql(jql)

        # Build fields list
        fields = [f.strip() for f in args.fields.split(',')] if args.fields else None
        if fields is None:
            fields = ['key', 'summary', 'status', 'priority', 'issuetype', 'assignee', 'reporter']
            if args.show_agile:
                fields.extend([EPIC_LINK_FIELD, STORY_POINTS_FIELD, 'sprint'])
            if args.show_links:
                fields.append('issuelinks')
            if args.show_time:
                fields.append('timetracking')

        # Execute search
        results = client.search_issues(jql, fields=fields,
                                       max_results=args.max_results,
                                       next_page_token=args.page_token)

        issues = results.get('issues', [])
        total = results.get('total', 0)

        # Save as filter if requested
        if args.save_as:
            saved_filter = save_search_as_filter(
                client, jql, args.save_as,
                description=args.save_description,
                favourite=args.save_favourite
            )
            if args.output != 'json':
                print_info(f"Saved as filter: {saved_filter.get('name')} (ID: {saved_filter.get('id')})")
                print()

        client.close()

        if args.output == 'json':
            output = results
            if args.save_as:
                output['savedFilter'] = saved_filter
            print(format_json(output))
        else:
            print_info(f"Found {total} issue(s)")
            if issues:
                print()
                print(format_search_results(issues, show_agile=args.show_agile,
                                           show_links=args.show_links,
                                           show_time=args.show_time))

                # Show pagination info if more results available
                next_token = results.get('nextPageToken')
                if next_token:
                    print(f"\nShowing {len(issues)} of {total} results")
                    print(f"Next page token: {next_token}")
                    print("Use --page-token to fetch next page")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
