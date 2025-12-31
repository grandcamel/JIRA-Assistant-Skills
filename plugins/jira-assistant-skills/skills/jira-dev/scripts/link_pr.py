#!/usr/bin/env python3
"""
Link Pull Request to JIRA issue.

Adds a formatted comment to JIRA issue with PR information,
supporting GitHub, GitLab, and Bitbucket.

Usage:
    python link_pr.py PROJ-123 --pr https://github.com/org/repo/pull/456
    python link_pr.py PROJ-123 --pr https://gitlab.com/org/repo/-/merge_requests/789
    python link_pr.py PROJ-123 --pr https://bitbucket.org/org/repo/pull-requests/101
"""

import sys
import os
import argparse
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse

# Add shared lib path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, ValidationError
from jira_assistant_skills_lib import validate_issue_key
from jira_assistant_skills_lib import wiki_markup_to_adf


def parse_pr_url(pr_url: str) -> Dict[str, Any]:
    """
    Parse pull request URL to extract provider and details.

    Supports:
    - GitHub: https://github.com/org/repo/pull/123
    - GitLab: https://gitlab.com/org/repo/-/merge_requests/123
    - Bitbucket: https://bitbucket.org/org/repo/pull-requests/123

    Args:
        pr_url: Pull request URL

    Returns:
        Dictionary with provider, owner, repo, pr_number

    Raises:
        ValidationError: If URL format is not recognized
    """
    if not pr_url:
        raise ValidationError("PR URL cannot be empty")

    parsed = urlparse(pr_url)
    host = parsed.netloc.lower()
    path = parsed.path.strip('/')

    # GitHub: /owner/repo/pull/123
    if 'github' in host:
        match = re.match(r'^([^/]+)/([^/]+)/pull/(\d+)', path)
        if match:
            return {
                'provider': 'github',
                'owner': match.group(1),
                'repo': match.group(2),
                'pr_number': int(match.group(3)),
                'url': pr_url
            }

    # GitLab: /owner/repo/-/merge_requests/123
    elif 'gitlab' in host:
        match = re.match(r'^([^/]+)/([^/]+)/-/merge_requests/(\d+)', path)
        if match:
            return {
                'provider': 'gitlab',
                'owner': match.group(1),
                'repo': match.group(2),
                'pr_number': int(match.group(3)),
                'url': pr_url
            }

    # Bitbucket: /owner/repo/pull-requests/123
    elif 'bitbucket' in host:
        match = re.match(r'^([^/]+)/([^/]+)/pull-requests/(\d+)', path)
        if match:
            return {
                'provider': 'bitbucket',
                'owner': match.group(1),
                'repo': match.group(2),
                'pr_number': int(match.group(3)),
                'url': pr_url
            }

    raise ValidationError(
        f"Unrecognized PR URL format: {pr_url}. "
        "Supported: GitHub, GitLab, Bitbucket"
    )


def build_pr_comment(
    pr_url: str,
    pr_number: int,
    title: Optional[str] = None,
    status: Optional[str] = None,
    author: Optional[str] = None,
    provider: Optional[str] = None
) -> str:
    """
    Build formatted PR comment for JIRA.

    Args:
        pr_url: Pull request URL
        pr_number: PR number
        title: PR title
        status: PR status (open, merged, closed)
        author: PR author
        provider: Git provider (github, gitlab, bitbucket)

    Returns:
        Formatted comment text
    """
    pr_type = "Merge Request" if provider == "gitlab" else "Pull Request"

    lines = [f"{pr_type} linked to this issue:"]
    lines.append("")

    # PR number with link
    lines.append(f"*{pr_type}:* [#{pr_number}|{pr_url}]")

    if title:
        lines.append(f"*Title:* {title}")

    if status:
        status_emoji = {
            'open': 'OPEN',
            'merged': 'MERGED',
            'closed': 'CLOSED'
        }.get(status.lower(), status.upper())
        lines.append(f"*Status:* {status_emoji}")

    if author:
        lines.append(f"*Author:* {author}")

    return '\n'.join(lines)


def link_pr(
    issue_key: str,
    pr_url: str,
    title: Optional[str] = None,
    status: Optional[str] = None,
    author: Optional[str] = None,
    profile: Optional[str] = None,
    client=None
) -> Dict[str, Any]:
    """
    Link a pull request to a JIRA issue by adding a comment.

    Args:
        issue_key: JIRA issue key
        pr_url: Pull request URL
        title: PR title
        status: PR status
        author: PR author
        profile: JIRA profile
        client: Optional JiraClient instance (created if not provided)

    Returns:
        Result dictionary with success status
    """
    issue_key = validate_issue_key(issue_key)

    # Parse PR URL
    pr_info = parse_pr_url(pr_url)

    # Build comment
    comment_body = build_pr_comment(
        pr_url=pr_url,
        pr_number=pr_info['pr_number'],
        title=title,
        status=status,
        author=author,
        provider=pr_info['provider']
    )

    # Create comment via JIRA API
    close_client = False
    if client is None:
        client = get_jira_client(profile)
        close_client = True
    try:
        # Convert wiki markup to ADF using shared helper
        comment_data = {
            "body": wiki_markup_to_adf(comment_body)
        }

        result = client.post(
            f'/rest/api/3/issue/{issue_key}/comment',
            data=comment_data,
            operation=f"link PR to {issue_key}"
        )

        return {
            'success': True,
            'issue_key': issue_key,
            'pr_url': pr_url,
            'pr_number': pr_info['pr_number'],
            'provider': pr_info['provider'],
            'comment_id': result.get('id')
        }

    finally:
        if close_client:
            client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='Link Pull Request to JIRA issue',
        epilog='Example: python link_pr.py PROJ-123 --pr https://github.com/org/repo/pull/456'
    )

    parser.add_argument('issue_key',
                        help='JIRA issue key (e.g., PROJ-123)')
    parser.add_argument('--pr', '-p',
                        required=True,
                        help='Pull request URL')
    parser.add_argument('--title', '-t',
                        help='PR title')
    parser.add_argument('--status', '-s',
                        choices=['open', 'merged', 'closed'],
                        help='PR status')
    parser.add_argument('--author', '-a',
                        help='PR author')
    parser.add_argument('--output', '-o',
                        choices=['text', 'json'],
                        default='text',
                        help='Output format')
    parser.add_argument('--profile',
                        help='JIRA profile to use')

    args = parser.parse_args(argv)

    try:
        result = link_pr(
            issue_key=args.issue_key,
            pr_url=args.pr,
            title=args.title,
            status=args.status,
            author=args.author,
            profile=args.profile
        )

        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            if result['success']:
                pr_type = "MR" if result['provider'] == 'gitlab' else "PR"
                print(f"Linked {pr_type} #{result['pr_number']} to {result['issue_key']}")
            else:
                print(f"Failed to link PR: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
