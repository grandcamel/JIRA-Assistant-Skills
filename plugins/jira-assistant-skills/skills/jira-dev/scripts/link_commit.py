#!/usr/bin/env python3
"""
Link Git commit to JIRA issue via comment.

Adds a formatted comment to JIRA issue with commit information,
including links to the commit on GitHub, GitLab, or Bitbucket.

Usage:
    python link_commit.py PROJ-123 --commit abc123 --repo https://github.com/org/repo
    python link_commit.py PROJ-123 --commit abc123 --message "Fixed bug"
    python link_commit.py --from-message "PROJ-123: Fix login bug" --commit abc123
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

# Add shared lib path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import validate_issue_key
from jira_assistant_skills_lib import wiki_markup_to_adf

# Import parse_commit_issues for --from-message functionality
from parse_commit_issues import parse_issue_keys


def detect_repo_type(repo_url: str) -> str:
    """
    Detect repository type from URL.

    Args:
        repo_url: Repository URL

    Returns:
        Repository type: 'github', 'gitlab', 'bitbucket', or 'generic'
    """
    if not repo_url:
        return 'generic'

    parsed = urlparse(repo_url)
    host = parsed.netloc.lower()

    if 'github' in host:
        return 'github'
    elif 'gitlab' in host:
        return 'gitlab'
    elif 'bitbucket' in host:
        return 'bitbucket'
    else:
        return 'generic'


def build_commit_url(
    commit_sha: str,
    repo_url: Optional[str] = None
) -> Optional[str]:
    """
    Build URL to commit on the repository.

    Args:
        commit_sha: Full or short commit SHA
        repo_url: Repository URL

    Returns:
        URL to the commit, or None if repo_url not provided
    """
    if not repo_url:
        return None

    # Clean up repo URL
    repo_url = repo_url.rstrip('/')
    if repo_url.endswith('.git'):
        repo_url = repo_url[:-4]

    repo_type = detect_repo_type(repo_url)

    if repo_type == 'github':
        return f"{repo_url}/commit/{commit_sha}"
    elif repo_type == 'gitlab':
        return f"{repo_url}/-/commit/{commit_sha}"
    elif repo_type == 'bitbucket':
        return f"{repo_url}/commits/{commit_sha}"
    else:
        # Generic: try GitHub-style URL
        return f"{repo_url}/commit/{commit_sha}"


def build_commit_comment(
    commit_sha: str,
    message: Optional[str] = None,
    repo_url: Optional[str] = None,
    author: Optional[str] = None,
    branch: Optional[str] = None
) -> str:
    """
    Build formatted commit comment for JIRA.

    Args:
        commit_sha: Commit SHA
        message: Commit message
        repo_url: Repository URL (for creating link)
        author: Commit author name
        branch: Branch name

    Returns:
        Formatted comment text
    """
    lines = ["Commit linked to this issue:"]
    lines.append("")

    # Commit SHA with link if possible
    short_sha = commit_sha[:7] if len(commit_sha) >= 7 else commit_sha
    commit_url = build_commit_url(commit_sha, repo_url)

    if commit_url:
        lines.append(f"*Commit:* [{short_sha}|{commit_url}]")
    else:
        lines.append(f"*Commit:* {commit_sha}")

    # Add optional fields
    if message:
        lines.append(f"*Message:* {message}")

    if author:
        lines.append(f"*Author:* {author}")

    if branch:
        lines.append(f"*Branch:* {branch}")

    if repo_url:
        lines.append(f"*Repository:* {repo_url}")

    return '\n'.join(lines)


def link_commit(
    issue_key: str,
    commit_sha: str = None,
    message: Optional[str] = None,
    repo_url: Optional[str] = None,
    author: Optional[str] = None,
    branch: Optional[str] = None,
    profile: Optional[str] = None,
    client=None,
    # Aliases for parameter names
    commit: str = None,
    repo: str = None
) -> Dict[str, Any]:
    """
    Link a commit to a JIRA issue by adding a comment.

    Args:
        issue_key: JIRA issue key
        commit_sha: Git commit SHA
        message: Commit message
        repo_url: Repository URL
        author: Commit author
        branch: Branch name
        profile: JIRA profile
        client: Optional JiraClient instance (created if not provided)
        commit: Alias for commit_sha
        repo: Alias for repo_url

    Returns:
        Result dictionary with success status
    """
    # Handle parameter aliases
    if commit_sha is None and commit is not None:
        commit_sha = commit
    if repo_url is None and repo is not None:
        repo_url = repo

    issue_key = validate_issue_key(issue_key)

    # Build comment
    comment_body = build_commit_comment(
        commit_sha=commit_sha,
        message=message,
        repo_url=repo_url,
        author=author,
        branch=branch
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
            operation=f"link commit to {issue_key}"
        )

        return {
            'success': True,
            'issue_key': issue_key,
            'commit_sha': commit_sha,
            'comment_id': result.get('id')
        }

    finally:
        if close_client:
            client.close()


def link_commit_to_issues(
    issue_keys: List[str],
    commit_sha: str,
    message: Optional[str] = None,
    repo_url: Optional[str] = None,
    author: Optional[str] = None,
    branch: Optional[str] = None,
    profile: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Link a commit to multiple JIRA issues.

    Args:
        issue_keys: List of JIRA issue keys
        commit_sha: Git commit SHA
        message: Commit message
        repo_url: Repository URL
        author: Commit author
        branch: Branch name
        profile: JIRA profile

    Returns:
        List of results for each issue
    """
    results = []

    for issue_key in issue_keys:
        try:
            result = link_commit(
                issue_key=issue_key,
                commit_sha=commit_sha,
                message=message,
                repo_url=repo_url,
                author=author,
                branch=branch,
                profile=profile
            )
            results.append(result)
        except JiraError as e:
            results.append({
                'success': False,
                'issue_key': issue_key,
                'commit_sha': commit_sha,
                'error': str(e)
            })

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Link Git commit to JIRA issue',
        epilog='Example: python link_commit.py PROJ-123 --commit abc123 --repo https://github.com/org/repo'
    )

    parser.add_argument('issue_key',
                        nargs='?',
                        help='JIRA issue key (e.g., PROJ-123)')
    parser.add_argument('--commit', '-c',
                        required=True,
                        help='Commit SHA')
    parser.add_argument('--message', '-m',
                        help='Commit message')
    parser.add_argument('--repo', '-r',
                        help='Repository URL')
    parser.add_argument('--author', '-a',
                        help='Commit author')
    parser.add_argument('--branch', '-b',
                        help='Branch name')
    parser.add_argument('--from-message',
                        help='Extract issue keys from commit message')
    parser.add_argument('--output', '-o',
                        choices=['text', 'json'],
                        default='text',
                        help='Output format')
    parser.add_argument('--profile',
                        help='JIRA profile to use')

    args = parser.parse_args()

    try:
        # Determine issue keys
        if args.from_message:
            issue_keys = parse_issue_keys(args.from_message)
            message = args.message or args.from_message
            if not issue_keys:
                print("No issue keys found in message", file=sys.stderr)
                sys.exit(1)
        elif args.issue_key:
            issue_keys = [validate_issue_key(args.issue_key)]
            message = args.message
        else:
            parser.print_help()
            sys.exit(1)

        # Link commit to issues
        results = link_commit_to_issues(
            issue_keys=issue_keys,
            commit_sha=args.commit,
            message=message,
            repo_url=args.repo,
            author=args.author,
            branch=args.branch,
            profile=args.profile
        )

        # Output results
        if args.output == 'json':
            print(json.dumps(results, indent=2))
        else:
            for result in results:
                if result['success']:
                    print(f"Linked commit {args.commit[:7]} to {result['issue_key']}")
                else:
                    print(f"Failed to link to {result['issue_key']}: {result.get('error')}",
                          file=sys.stderr)

        # Exit with error if any failed
        if not all(r['success'] for r in results):
            sys.exit(1)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
