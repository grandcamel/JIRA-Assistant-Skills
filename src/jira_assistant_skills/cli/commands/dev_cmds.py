import click

from jira_assistant_skills.utils import SKILLS_ROOT_DIR, run_skill_script_subprocess


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
def dev_branch_name(
    ctx, issue_key: str, prefix: str, auto_prefix: bool, output: str
):
    """Generate a Git branch name from an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-dev" / "scripts" / "create_branch_name.py"

    script_args = [issue_key]
    if prefix:
        script_args.extend(["--prefix", prefix])
    if auto_prefix:
        script_args.append("--auto-prefix")
    if output and output != "text":
        script_args.extend(["--output", output])

    run_skill_script_subprocess(script_path, script_args, ctx)


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
    script_path = SKILLS_ROOT_DIR / "jira-dev" / "scripts" / "create_pr_description.py"

    script_args = [issue_key]
    if include_checklist:
        script_args.append("--include-checklist")
    if include_labels:
        script_args.append("--include-labels")
    if include_components:
        script_args.append("--include-components")
    if output and output != "text":
        script_args.extend(["--output", output])
    if copy:
        script_args.append("--copy")

    run_skill_script_subprocess(script_path, script_args, ctx)


@dev.command(name="parse-commits")
@click.argument("message", required=False)
@click.option(
    "--from-stdin", is_flag=True, help="Read from stdin (for git log pipe)"
)
@click.option("--project", "-p", help="Filter by project key")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json", "csv"]),
    default="text",
    help="Output format (default: text)",
)
@click.pass_context
def dev_parse_commits(
    ctx, message: str, from_stdin: bool, project: str, output: str
):
    """Parse commit messages to extract JIRA issue keys.

    Examples:
        jira dev parse-commits "PROJ-123: Fix login bug"
        git log --oneline -10 | jira dev parse-commits --from-stdin
        jira dev parse-commits "Fix PROJ-123 and OTHER-456" --project PROJ
    """
    script_path = SKILLS_ROOT_DIR / "jira-dev" / "scripts" / "parse_commit_issues.py"

    script_args = []
    if message:
        script_args.append(message)
    if from_stdin:
        script_args.append("--from-stdin")
    if project:
        script_args.extend(["--project", project])
    if output and output != "text":
        script_args.extend(["--output", output])

    run_skill_script_subprocess(script_path, script_args, ctx)


@dev.command(name="link-commit")
@click.argument("issue_key")
@click.option("--commit", "-c", required=True, help="Commit SHA (required)")
@click.option("--message", "-m", help="Commit message")
@click.option("--repo", "-r", help="Repository URL")
@click.option("--author", "-a", help="Commit author")
@click.option("--branch", "-b", help="Branch name")
@click.pass_context
def dev_link_commit(
    ctx, issue_key: str, commit: str, message: str, repo: str, author: str, branch: str
):
    """Link a Git commit to a JIRA issue."""
    script_path = SKILLS_ROOT_DIR / "jira-dev" / "scripts" / "link_commit.py"

    script_args = [issue_key, "--commit", commit]
    if message:
        script_args.extend(["--message", message])
    if repo:
        script_args.extend(["--repo", repo])
    if author:
        script_args.extend(["--author", author])
    if branch:
        script_args.extend(["--branch", branch])

    run_skill_script_subprocess(script_path, script_args, ctx)


@dev.command(name="link-pr")
@click.argument("issue_key")
@click.option("--pr", "-p", required=True, help="Pull request URL (required)")
@click.option("--title", "-t", help="PR title")
@click.option(
    "--status", "-s", type=click.Choice(["open", "merged", "closed"]), help="PR status"
)
@click.option("--author", "-a", help="PR author")
@click.pass_context
def dev_link_pr(
    ctx, issue_key: str, pr: str, title: str, status: str, author: str
):
    """Link a Pull Request to a JIRA issue."""
    script_path = SKILLS_ROOT_DIR / "jira-dev" / "scripts" / "link_pr.py"

    script_args = [issue_key, "--pr", pr]
    if title:
        script_args.extend(["--title", title])
    if status:
        script_args.extend(["--status", status])
    if author:
        script_args.extend(["--author", author])

    run_skill_script_subprocess(script_path, script_args, ctx)


@dev.command(name="get-commits")
@click.argument("issue_key")
@click.option("--detailed", "-d", is_flag=True, help="Include commit message and author details")
@click.option("--repo", "-r", help="Filter by repository name")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json", "table"]),
    default="text",
    help="Output format (default: text)",
)
@click.pass_context
def dev_get_commits(ctx, issue_key: str, detailed: bool, repo: str, output: str):
    """Get commits linked to an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-dev" / "scripts" / "get_issue_commits.py"

    script_args = [issue_key]
    if detailed:
        script_args.append("--detailed")
    if repo:
        script_args.extend(["--repo", repo])
    if output and output != "text":
        script_args.extend(["--output", output])

    run_skill_script_subprocess(script_path, script_args, ctx)
