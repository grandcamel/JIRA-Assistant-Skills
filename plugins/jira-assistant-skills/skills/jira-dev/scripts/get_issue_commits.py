#!/usr/bin/env python3
"""
Get commits linked to a JIRA issue.

Retrieves development information from JIRA's Development Information API,
which shows commits linked via integrations like GitHub for JIRA.

Usage:
    python get_issue_commits.py PROJ-123
    python get_issue_commits.py PROJ-123 --detailed
    python get_issue_commits.py PROJ-123 --repo "org/repo"
    python get_issue_commits.py PROJ-123 --output json
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add shared lib path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError
from validators import validate_issue_key
from formatters import format_table


def get_issue_commits(
    issue_key: str,
    detailed: bool = False,
    repo_filter: Optional[str] = None,
    profile: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get commits linked to a JIRA issue via Development Information API.

    Args:
        issue_key: JIRA issue key
        detailed: Include commit message and author details
        repo_filter: Only return commits from this repository
        profile: JIRA profile to use

    Returns:
        List of commit dictionaries
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client(profile)
    try:
        # First, get the issue ID (numeric)
        issue = client.get_issue(issue_key, fields=['id'])
        issue_id = issue.get('id')

        # Query Development Information API
        # Note: This API requires the "View Development Information" permission
        dev_info = client.get(
            '/rest/dev-status/latest/issue/detail',
            params={
                'issueId': issue_id,
                'applicationType': 'stash',  # Generic VCS type
                'dataType': 'repository'
            },
            operation=f"get development info for {issue_key}"
        )

        commits = []

        # Parse the response
        detail = dev_info.get('detail', [])

        for detail_item in detail:
            repositories = detail_item.get('repositories', [])

            for repo in repositories:
                repo_name = repo.get('name', '')
                repo_url = repo.get('url', '')

                # Apply repository filter
                if repo_filter:
                    if repo_filter.lower() not in repo_name.lower():
                        continue

                repo_commits = repo.get('commits', [])

                for commit in repo_commits:
                    commit_data = {
                        'id': commit.get('id', ''),
                        'sha': commit.get('id', ''),
                        'display_id': commit.get('displayId', commit.get('id', '')[:7]),
                        'repository': repo_name,
                        'url': commit.get('url', '')
                    }

                    if detailed:
                        commit_data.update({
                            'message': commit.get('message', ''),
                            'author': commit.get('author', {}).get('name', ''),
                            'author_email': commit.get('author', {}).get('email', ''),
                            'timestamp': commit.get('authorTimestamp', '')
                        })

                    commits.append(commit_data)

        return commits

    finally:
        client.close()


def format_output(
    commits: List[Dict[str, Any]],
    output_format: str = 'text',
    detailed: bool = False
) -> str:
    """
    Format commits for output.

    Args:
        commits: List of commit dictionaries
        output_format: Output format (text, json, table)
        detailed: Include detailed information

    Returns:
        Formatted output string
    """
    if output_format == 'json':
        return json.dumps({
            'commits': commits,
            'count': len(commits)
        }, indent=2)

    elif output_format == 'table':
        if not commits:
            return "No commits found"

        if detailed:
            columns = ['display_id', 'message', 'author', 'repository']
            headers = ['SHA', 'Message', 'Author', 'Repository']
        else:
            columns = ['display_id', 'repository', 'url']
            headers = ['SHA', 'Repository', 'URL']

        return format_table(commits, columns=columns, headers=headers)

    else:  # text
        if not commits:
            return "No commits linked to this issue"

        lines = [f"Found {len(commits)} commit(s):"]
        lines.append("")

        for commit in commits:
            sha = commit.get('display_id', commit.get('id', '')[:7])
            repo = commit.get('repository', '')
            url = commit.get('url', '')

            if detailed:
                message = commit.get('message', '').split('\n')[0][:60]
                author = commit.get('author', '')
                lines.append(f"  {sha} - {message}")
                lines.append(f"    Author: {author}")
                lines.append(f"    Repo: {repo}")
                if url:
                    lines.append(f"    URL: {url}")
                lines.append("")
            else:
                lines.append(f"  {sha} ({repo})")
                if url:
                    lines.append(f"    {url}")

        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Get commits linked to a JIRA issue',
        epilog='Example: python get_issue_commits.py PROJ-123 --detailed'
    )

    parser.add_argument('issue_key',
                        help='JIRA issue key (e.g., PROJ-123)')
    parser.add_argument('--detailed', '-d',
                        action='store_true',
                        help='Include commit message and author details')
    parser.add_argument('--repo', '-r',
                        help='Filter by repository name')
    parser.add_argument('--output', '-o',
                        choices=['text', 'json', 'table'],
                        default='text',
                        help='Output format (default: text)')
    parser.add_argument('--profile',
                        help='JIRA profile to use')

    args = parser.parse_args()

    try:
        commits = get_issue_commits(
            issue_key=args.issue_key,
            detailed=args.detailed,
            repo_filter=args.repo,
            profile=args.profile
        )

        output = format_output(commits, args.output, args.detailed)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
