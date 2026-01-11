"""
CLI commands for developer workflow integration (Git, PRs, commits).

This module contains all logic for jira-dev operations.
All implementation functions are inlined for direct CLI usage.
"""

import re
import sys
from typing import Any
from urllib.parse import urlparse

import click

from jira_assistant_skills.cli.cli_utils import format_json, handle_jira_errors
from jira_assistant_skills_lib import (
    ConfigManager,
    ValidationError,
    adf_to_text,
    format_table,
    get_jira_client,
    validate_issue_key,
    wiki_markup_to_adf,
)

# =============================================================================
# Constants
# =============================================================================

# Maximum length for branch names
MAX_BRANCH_LENGTH = 80

# Issue type to prefix mapping
ISSUE_TYPE_PREFIXES = {
    "bug": "bugfix",
    "defect": "bugfix",
    "hotfix": "hotfix",
    "story": "feature",
    "feature": "feature",
    "new feature": "feature",
    "improvement": "feature",
    "enhancement": "feature",
    "task": "task",
    "sub-task": "task",
    "subtask": "task",
    "epic": "epic",
    "spike": "spike",
    "research": "spike",
    "chore": "chore",
    "maintenance": "chore",
    "documentation": "docs",
    "doc": "docs",
}

DEFAULT_PREFIX = "feature"

# Issue key pattern: PROJECT-NUMBER
ISSUE_KEY_PATTERN = re.compile(r"\b([A-Z][A-Z0-9]+-[0-9]+)\b", re.IGNORECASE)

# Commit prefixes (for documentation)
COMMIT_PREFIXES = [
    "fixes",
    "fixed",
    "fix",
    "closes",
    "closed",
    "close",
    "resolves",
    "resolved",
    "resolve",
    "refs",
    "ref",
    "references",
    "related to",
    "relates to",
    "see",
]


# =============================================================================
# Helper Functions - Branch Name
# =============================================================================


def _sanitize_for_branch(text: str) -> str:
    """
    Sanitize text for use in git branch name.

    Converts to lowercase, replaces special chars with hyphens,
    removes consecutive/leading/trailing hyphens.
    """
    if not text:
        return ""

    result = text.lower()
    result = re.sub(r"[^a-z0-9]+", "-", result)
    result = re.sub(r"-+", "-", result)
    result = result.strip("-")
    return result


def _get_prefix_for_issue_type(issue_type: str) -> str:
    """Get branch prefix based on issue type."""
    if not issue_type:
        return DEFAULT_PREFIX
    return ISSUE_TYPE_PREFIXES.get(issue_type.lower(), DEFAULT_PREFIX)


# =============================================================================
# Helper Functions - PR Description
# =============================================================================


def _get_jira_base_url() -> str:
    """Get JIRA base URL from configuration."""
    try:
        config_manager = ConfigManager()
        url, _, _ = config_manager.get_credentials()
        return url
    except Exception:
        return "https://jira.example.com"


def _extract_acceptance_criteria(description: str) -> list[str]:
    """
    Extract acceptance criteria from issue description.

    Looks for patterns like:
    - Acceptance Criteria:
    - AC:
    - Given/When/Then
    """
    if not description:
        return []

    criteria = []
    lines = description.split("\n")
    in_ac_section = False

    for line in lines:
        line_lower = line.lower().strip()

        if "acceptance criteria" in line_lower or line_lower.startswith("ac:"):
            in_ac_section = True
            continue

        if in_ac_section and line.strip().startswith("#"):
            in_ac_section = False
            continue

        if in_ac_section and line.strip():
            item = line.strip().lstrip("-*").strip()
            if item:
                criteria.append(item)

        if line_lower.startswith(("given ", "when ", "then ")):
            criteria.append(line.strip())

    return criteria


# =============================================================================
# Helper Functions - Link Commit/PR
# =============================================================================


def _detect_repo_type(repo_url: str) -> str:
    """Detect repository type from URL."""
    if not repo_url:
        return "generic"

    parsed = urlparse(repo_url)
    host = parsed.netloc.lower()

    if "github" in host:
        return "github"
    elif "gitlab" in host:
        return "gitlab"
    elif "bitbucket" in host:
        return "bitbucket"
    else:
        return "generic"


def _build_commit_url(commit_sha: str, repo_url: str | None = None) -> str | None:
    """Build URL to commit on the repository."""
    if not repo_url:
        return None

    repo_url = repo_url.rstrip("/")
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]

    repo_type = _detect_repo_type(repo_url)

    if repo_type == "github":
        return f"{repo_url}/commit/{commit_sha}"
    elif repo_type == "gitlab":
        return f"{repo_url}/-/commit/{commit_sha}"
    elif repo_type == "bitbucket":
        return f"{repo_url}/commits/{commit_sha}"
    else:
        return f"{repo_url}/commit/{commit_sha}"


def _parse_pr_url(pr_url: str) -> dict[str, Any]:
    """
    Parse pull request URL to extract provider and details.

    Supports GitHub, GitLab, and Bitbucket.
    """
    if not pr_url:
        raise ValidationError("PR URL cannot be empty")

    parsed = urlparse(pr_url)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")

    # GitHub: /owner/repo/pull/123
    if "github" in host:
        match = re.match(r"^([^/]+)/([^/]+)/pull/(\d+)", path)
        if match:
            return {
                "provider": "github",
                "owner": match.group(1),
                "repo": match.group(2),
                "pr_number": int(match.group(3)),
                "url": pr_url,
            }

    # GitLab: /owner/repo/-/merge_requests/123
    elif "gitlab" in host:
        match = re.match(r"^([^/]+)/([^/]+)/-/merge_requests/(\d+)", path)
        if match:
            return {
                "provider": "gitlab",
                "owner": match.group(1),
                "repo": match.group(2),
                "pr_number": int(match.group(3)),
                "url": pr_url,
            }

    # Bitbucket: /owner/repo/pull-requests/123
    elif "bitbucket" in host:
        match = re.match(r"^([^/]+)/([^/]+)/pull-requests/(\d+)", path)
        if match:
            return {
                "provider": "bitbucket",
                "owner": match.group(1),
                "repo": match.group(2),
                "pr_number": int(match.group(3)),
                "url": pr_url,
            }

    raise ValidationError(
        f"Unrecognized PR URL format: {pr_url}. Supported: GitHub, GitLab, Bitbucket"
    )


# =============================================================================
# Implementation Functions
# =============================================================================


def _create_branch_name_impl(
    issue_key: str,
    prefix: str | None = None,
    auto_prefix: bool = False,
) -> dict[str, Any]:
    """
    Create a standardized branch name from JIRA issue.

    Args:
        issue_key: JIRA issue key
        prefix: Custom prefix (feature, bugfix, etc.)
        auto_prefix: If True, determine prefix from issue type

    Returns:
        Dictionary with branch_name, issue_key, git_command
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        issue = client.get_issue(issue_key, fields=["summary", "issuetype"])
    finally:
        client.close()

    fields = issue.get("fields", {})
    summary = fields.get("summary", "")
    issue_type = fields.get("issuetype", {}).get("name", "")

    # Determine prefix
    if prefix:
        branch_prefix = prefix.lower()
    elif auto_prefix:
        branch_prefix = _get_prefix_for_issue_type(issue_type)
    else:
        branch_prefix = DEFAULT_PREFIX

    # Sanitize summary
    sanitized_summary = _sanitize_for_branch(summary)
    issue_key_lower = issue_key.lower()

    # Build branch name
    if not sanitized_summary:
        branch_name = f"{branch_prefix}/{issue_key_lower}"
    else:
        prefix_part_len = len(branch_prefix) + 1
        key_part_len = len(issue_key_lower) + 1
        max_summary_len = MAX_BRANCH_LENGTH - prefix_part_len - key_part_len

        if len(sanitized_summary) > max_summary_len:
            truncated = sanitized_summary[:max_summary_len]
            last_hyphen = truncated.rfind("-")
            if last_hyphen > max_summary_len // 2:
                truncated = truncated[:last_hyphen]
            sanitized_summary = truncated.rstrip("-")

        branch_name = f"{branch_prefix}/{issue_key_lower}-{sanitized_summary}"

    return {
        "branch_name": branch_name,
        "issue_key": issue_key,
        "issue_type": issue_type,
        "summary": summary,
        "git_command": f"git checkout -b {branch_name}",
    }


def _create_pr_description_impl(
    issue_key: str,
    include_checklist: bool = False,
    include_labels: bool = False,
    include_components: bool = False,
) -> dict[str, Any]:
    """
    Create a PR description from JIRA issue details.

    Args:
        issue_key: JIRA issue key
        include_checklist: Include testing checklist
        include_labels: Include issue labels
        include_components: Include components

    Returns:
        Dictionary with markdown, issue_key, issue_type, etc.
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        issue = client.get_issue(
            issue_key,
            fields=[
                "summary",
                "description",
                "issuetype",
                "labels",
                "components",
                "priority",
            ],
        )
    finally:
        client.close()

    fields = issue.get("fields", {})
    summary = fields.get("summary", "")
    description = fields.get("description")
    issue_type = fields.get("issuetype", {}).get("name", "")
    labels = fields.get("labels", [])
    components = [c.get("name", "") for c in fields.get("components", [])]
    priority = (
        fields.get("priority", {}).get("name", "") if fields.get("priority") else ""
    )

    # Convert ADF description to text
    if isinstance(description, dict):
        desc_text = adf_to_text(description)
    else:
        desc_text = description or ""

    jira_url = _get_jira_base_url()

    # Build PR description
    lines = []

    lines.append("## Summary")
    lines.append("")
    lines.append(summary)
    lines.append("")

    lines.append("## JIRA Issue")
    lines.append("")
    lines.append(f"[{issue_key}]({jira_url}/browse/{issue_key})")
    lines.append("")

    if issue_type or priority:
        lines.append(f"**Type:** {issue_type}")
        if priority:
            lines.append(f"**Priority:** {priority}")
        lines.append("")

    if desc_text:
        lines.append("## Description")
        lines.append("")
        if len(desc_text) > 500:
            lines.append(desc_text[:500] + "...")
        else:
            lines.append(desc_text)
        lines.append("")

    if include_labels and labels:
        lines.append("## Labels")
        lines.append("")
        lines.append(", ".join([f"`{label}`" for label in labels]))
        lines.append("")

    if include_components and components:
        lines.append("## Components")
        lines.append("")
        lines.append(", ".join(components))
        lines.append("")

    acceptance_criteria = _extract_acceptance_criteria(desc_text)
    if acceptance_criteria:
        lines.append("## Acceptance Criteria")
        lines.append("")
        for criterion in acceptance_criteria:
            lines.append(f"- [ ] {criterion}")
        lines.append("")

    if include_checklist:
        lines.append("## Testing Checklist")
        lines.append("")
        lines.append("- [ ] Unit tests added/updated")
        lines.append("- [ ] Integration tests pass")
        lines.append("- [ ] Manual testing completed")
        lines.append("- [ ] No regressions introduced")
        lines.append("")

    markdown = "\n".join(lines)

    return {
        "markdown": markdown,
        "issue_key": issue_key,
        "issue_type": issue_type,
        "summary": summary,
        "priority": priority,
        "labels": labels,
        "components": components,
    }


def _parse_commit_issues_impl(
    message: str | None = None,
    project_filter: str | None = None,
    from_stdin: bool = False,
) -> dict[str, Any]:
    """
    Parse JIRA issue keys from commit messages.

    Args:
        message: Commit message to parse
        project_filter: Only return issues from this project
        from_stdin: Read from stdin instead

    Returns:
        Dictionary with issue_keys and count
    """
    if from_stdin:
        lines = sys.stdin.read().strip().split("\n")
        all_keys = []
        seen = set()

        for line in lines:
            matches = ISSUE_KEY_PATTERN.findall(line)
            for match in matches:
                key = match.upper()
                if key not in seen:
                    seen.add(key)
                    if project_filter:
                        project = key.split("-")[0]
                        if project.upper() != project_filter.upper():
                            continue
                    all_keys.append(key)

        return {"issue_keys": all_keys, "count": len(all_keys)}

    if not message:
        return {"issue_keys": [], "count": 0}

    matches = ISSUE_KEY_PATTERN.findall(message)
    seen = set()
    issue_keys = []

    for match in matches:
        key = match.upper()
        if key not in seen:
            seen.add(key)
            if project_filter:
                project = key.split("-")[0]
                if project.upper() != project_filter.upper():
                    continue
            issue_keys.append(key)

    return {"issue_keys": issue_keys, "count": len(issue_keys)}


def _link_commit_impl(
    issue_key: str,
    commit: str,
    message: str | None = None,
    repo: str | None = None,
    author: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """
    Link a commit to a JIRA issue by adding a comment.

    Args:
        issue_key: JIRA issue key
        commit: Git commit SHA
        message: Commit message
        repo: Repository URL
        author: Commit author
        branch: Branch name

    Returns:
        Result dictionary with success status
    """
    issue_key = validate_issue_key(issue_key)

    # Build comment
    lines = ["Commit linked to this issue:", ""]

    short_sha = commit[:7] if len(commit) >= 7 else commit
    commit_url = _build_commit_url(commit, repo)

    if commit_url:
        lines.append(f"*Commit:* [{short_sha}|{commit_url}]")
    else:
        lines.append(f"*Commit:* {commit}")

    if message:
        lines.append(f"*Message:* {message}")
    if author:
        lines.append(f"*Author:* {author}")
    if branch:
        lines.append(f"*Branch:* {branch}")
    if repo:
        lines.append(f"*Repository:* {repo}")

    comment_body = "\n".join(lines)

    client = get_jira_client()
    try:
        comment_data = {"body": wiki_markup_to_adf(comment_body)}

        result = client.post(
            f"/rest/api/3/issue/{issue_key}/comment",
            data=comment_data,
            operation=f"link commit to {issue_key}",
        )

        return {
            "success": True,
            "issue_key": issue_key,
            "commit_sha": commit,
            "comment_id": result.get("id"),
        }
    finally:
        client.close()


def _link_pr_impl(
    issue_key: str,
    pr_url: str,
    title: str | None = None,
    status: str | None = None,
    author: str | None = None,
) -> dict[str, Any]:
    """
    Link a pull request to a JIRA issue by adding a comment.

    Args:
        issue_key: JIRA issue key
        pr_url: Pull request URL
        title: PR title
        status: PR status
        author: PR author

    Returns:
        Result dictionary with success status
    """
    issue_key = validate_issue_key(issue_key)

    pr_info = _parse_pr_url(pr_url)
    pr_type = "Merge Request" if pr_info["provider"] == "gitlab" else "Pull Request"

    # Build comment
    lines = [f"{pr_type} linked to this issue:", ""]
    lines.append(f"*{pr_type}:* [#{pr_info['pr_number']}|{pr_url}]")

    if title:
        lines.append(f"*Title:* {title}")
    if status:
        status_emoji = {
            "open": "OPEN",
            "merged": "MERGED",
            "closed": "CLOSED",
        }.get(status.lower(), status.upper())
        lines.append(f"*Status:* {status_emoji}")
    if author:
        lines.append(f"*Author:* {author}")

    comment_body = "\n".join(lines)

    client = get_jira_client()
    try:
        comment_data = {"body": wiki_markup_to_adf(comment_body)}

        result = client.post(
            f"/rest/api/3/issue/{issue_key}/comment",
            data=comment_data,
            operation=f"link PR to {issue_key}",
        )

        return {
            "success": True,
            "issue_key": issue_key,
            "pr_url": pr_url,
            "pr_number": pr_info["pr_number"],
            "provider": pr_info["provider"],
            "comment_id": result.get("id"),
        }
    finally:
        client.close()


def _get_commits_impl(
    issue_key: str,
    detailed: bool = False,
    repo_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get commits linked to a JIRA issue via Development Information API.

    Args:
        issue_key: JIRA issue key
        detailed: Include commit message and author details
        repo_filter: Only return commits from this repository

    Returns:
        List of commit dictionaries
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        issue = client.get_issue(issue_key, fields=["id"])
        issue_id = issue.get("id")

        dev_info = client.get(
            "/rest/dev-status/latest/issue/detail",
            params={
                "issueId": issue_id,
                "applicationType": "stash",
                "dataType": "repository",
            },
            operation=f"get development info for {issue_key}",
        )

        commits = []
        detail = dev_info.get("detail", [])

        for detail_item in detail:
            repositories = detail_item.get("repositories", [])

            for repo in repositories:
                repo_name = repo.get("name", "")

                if repo_filter and repo_filter.lower() not in repo_name.lower():
                    continue

                repo_commits = repo.get("commits", [])

                for commit in repo_commits:
                    commit_data = {
                        "id": commit.get("id", ""),
                        "sha": commit.get("id", ""),
                        "display_id": commit.get("displayId", commit.get("id", "")[:7]),
                        "repository": repo_name,
                        "url": commit.get("url", ""),
                    }

                    if detailed:
                        commit_data.update(
                            {
                                "message": commit.get("message", ""),
                                "author": commit.get("author", {}).get("name", ""),
                                "author_email": commit.get("author", {}).get(
                                    "email", ""
                                ),
                                "timestamp": commit.get("authorTimestamp", ""),
                            }
                        )

                    commits.append(commit_data)

        return commits
    finally:
        client.close()


# =============================================================================
# Formatting Functions
# =============================================================================


def _format_branch_name(result: dict, output: str) -> str:
    """Format branch name output."""
    if output == "git":
        return result["git_command"]
    else:
        return result["branch_name"]


def _format_commits(commits: list[dict], output: str, detailed: bool) -> str:
    """Format commits for text output."""
    if not commits:
        return "No commits linked to this issue"

    if output == "table":
        if detailed:
            columns = ["display_id", "message", "author", "repository"]
            headers = ["SHA", "Message", "Author", "Repository"]
        else:
            columns = ["display_id", "repository", "url"]
            headers = ["SHA", "Repository", "URL"]
        return format_table(commits, columns=columns, headers=headers)

    lines = [f"Found {len(commits)} commit(s):", ""]

    for commit in commits:
        sha = commit.get("display_id", commit.get("id", "")[:7])
        repo = commit.get("repository", "")
        url = commit.get("url", "")

        if detailed:
            message = commit.get("message", "").split("\n")[0][:60]
            author = commit.get("author", "")
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

    return "\n".join(lines)


# =============================================================================
# CLI Commands
# =============================================================================


@click.group()
def dev():
    """Commands for developer workflow integration (Git, PRs, commits)."""
    pass


@dev.command(name="branch-name")
@click.argument("issue_key")
@click.option(
    "--prefix",
    "-p",
    type=click.Choice(
        ["feature", "bugfix", "hotfix", "task", "epic", "spike", "chore", "docs"]
    ),
    help="Branch prefix (default: feature)",
)
@click.option(
    "--auto-prefix", "-a", is_flag=True, help="Auto-detect prefix from issue type"
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json", "git"]),
    default="text",
    help="Output format (default: text)",
)
@click.pass_context
@handle_jira_errors
def dev_branch_name(ctx, issue_key: str, prefix: str, auto_prefix: bool, output: str):
    """Generate a Git branch name from an issue."""
    result = _create_branch_name_impl(
        issue_key=issue_key,
        prefix=prefix,
        auto_prefix=auto_prefix,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_branch_name(result, output))


@dev.command(name="pr-description")
@click.argument("issue_key")
@click.option(
    "--include-checklist", "-c", is_flag=True, help="Include testing checklist"
)
@click.option("--include-labels", "-l", is_flag=True, help="Include issue labels")
@click.option("--include-components", is_flag=True, help="Include components")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.option("--copy", is_flag=True, help="Copy to clipboard (requires pyperclip)")
@click.pass_context
@handle_jira_errors
def dev_pr_description(
    ctx,
    issue_key: str,
    include_checklist: bool,
    include_labels: bool,
    include_components: bool,
    output: str,
    copy: bool,
):
    """Generate a PR description from an issue."""
    result = _create_pr_description_impl(
        issue_key=issue_key,
        include_checklist=include_checklist,
        include_labels=include_labels,
        include_components=include_components,
    )

    if copy:
        try:
            import pyperclip

            pyperclip.copy(result["markdown"])
            click.echo("PR description copied to clipboard!", err=True)
        except ImportError:
            click.echo(
                "Warning: pyperclip not installed. Cannot copy to clipboard.", err=True
            )

    if output == "json":
        click.echo(
            format_json(
                {
                    "description": result["markdown"],
                    "issue_key": result["issue_key"],
                    "summary": result["summary"],
                    "issue_type": result["issue_type"],
                    "priority": result["priority"],
                }
            )
        )
    else:
        click.echo(result["markdown"])


@dev.command(name="parse-commits")
@click.argument("message", required=False)
@click.option("--from-stdin", is_flag=True, help="Read from stdin (for git log pipe)")
@click.option("--project", "-p", help="Filter by project key")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json", "csv"]),
    default="text",
    help="Output format (default: text)",
)
@click.pass_context
@handle_jira_errors
def dev_parse_commits(ctx, message: str, from_stdin: bool, project: str, output: str):
    """Parse commit messages to extract JIRA issue keys.

    Examples:
        jira-as dev parse-commits "PROJ-123: Fix login bug"
        git log --oneline -10 | jira-as dev parse-commits --from-stdin
        jira-as dev parse-commits "Fix PROJ-123 and OTHER-456" --project PROJ
    """
    if not message and not from_stdin:
        click.echo("Error: Must provide message or --from-stdin", err=True)
        ctx.exit(1)

    result = _parse_commit_issues_impl(
        message=message,
        project_filter=project,
        from_stdin=from_stdin,
    )

    if output == "json":
        click.echo(format_json(result))
    elif output == "csv":
        click.echo(",".join(result["issue_keys"]))
    else:
        if result["issue_keys"]:
            click.echo("\n".join(result["issue_keys"]))


@dev.command(name="link-commit")
@click.argument("issue_key")
@click.option("--commit", "-c", required=True, help="Commit SHA (required)")
@click.option("--message", "-m", help="Commit message")
@click.option("--repo", "-r", help="Repository URL")
@click.option("--author", "-a", help="Commit author")
@click.option("--branch", "-b", help="Branch name")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def dev_link_commit(
    ctx,
    issue_key: str,
    commit: str,
    message: str,
    repo: str,
    author: str,
    branch: str,
    output: str,
):
    """Link a Git commit to a JIRA issue."""
    result = _link_commit_impl(
        issue_key=issue_key,
        commit=commit,
        message=message,
        repo=repo,
        author=author,
        branch=branch,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Linked commit {commit[:7]} to {result['issue_key']}")


@dev.command(name="link-pr")
@click.argument("issue_key")
@click.option("--pr", "-p", required=True, help="Pull request URL (required)")
@click.option("--title", "-t", help="PR title")
@click.option(
    "--status", "-s", type=click.Choice(["open", "merged", "closed"]), help="PR status"
)
@click.option("--author", "-a", help="PR author")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def dev_link_pr(
    ctx,
    issue_key: str,
    pr: str,
    title: str,
    status: str,
    author: str,
    output: str,
):
    """Link a Pull Request to a JIRA issue."""
    result = _link_pr_impl(
        issue_key=issue_key,
        pr_url=pr,
        title=title,
        status=status,
        author=author,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        pr_type = "MR" if result["provider"] == "gitlab" else "PR"
        click.echo(f"Linked {pr_type} #{result['pr_number']} to {result['issue_key']}")


@dev.command(name="get-commits")
@click.argument("issue_key")
@click.option(
    "--detailed", "-d", is_flag=True, help="Include commit message and author details"
)
@click.option("--repo", "-r", help="Filter by repository name")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json", "table"]),
    default="text",
    help="Output format (default: text)",
)
@click.pass_context
@handle_jira_errors
def dev_get_commits(ctx, issue_key: str, detailed: bool, repo: str, output: str):
    """Get commits linked to an issue."""
    commits = _get_commits_impl(
        issue_key=issue_key,
        detailed=detailed,
        repo_filter=repo,
    )

    if output == "json":
        click.echo(format_json({"commits": commits, "count": len(commits)}))
    else:
        click.echo(_format_commits(commits, output, detailed))
