import click

from jira_assistant_skills.utils import SKILLS_ROOT_DIR, run_skill_script_subprocess


@click.group()
def dev():
    """Commands for developer workflow integration (Git, PRs, commits)."""
    pass


@dev.command(name="branch-name")
@click.argument("issue_key")
@click.option(
    "--format",
    "-f",
    "branch_format",
    help="Branch name format (feature, bugfix, hotfix)",
)
@click.option("--max-length", "-m", type=int, help="Maximum branch name length")
@click.pass_context
def dev_branch_name(ctx, issue_key: str, branch_format: str, max_length: int):
    """Generate a Git branch name from an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-dev" / "scripts" / "create_branch_name.py"

    script_args = [issue_key]
    if branch_format:
        script_args.extend(["--format", branch_format])
    if max_length:
        script_args.extend(["--max-length", str(max_length)])

    run_skill_script_subprocess(script_path, script_args, ctx)


@dev.command(name="pr-description")
@click.argument("issue_key")
@click.option("--template", "-t", help="PR description template")
@click.option("--include-commits", "-c", is_flag=True, help="Include linked commits")
@click.pass_context
def dev_pr_description(ctx, issue_key: str, template: str, include_commits: bool):
    """Generate a PR description from an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-dev" / "scripts" / "create_pr_description.py"

    script_args = [issue_key]
    if template:
        script_args.extend(["--template", template])
    if include_commits:
        script_args.append("--include-commits")

    run_skill_script_subprocess(script_path, script_args, ctx)


@dev.command(name="parse-commits")
@click.argument("commit_messages", nargs=-1)
@click.option("--file", "-f", "input_file", help="Read commit messages from file")
@click.pass_context
def dev_parse_commits(ctx, commit_messages: tuple, input_file: str):
    """Parse commit messages to extract JIRA issue keys."""
    script_path = SKILLS_ROOT_DIR / "jira-dev" / "scripts" / "parse_commit_issues.py"

    script_args = list(commit_messages)
    if input_file:
        script_args.extend(["--file", input_file])

    run_skill_script_subprocess(script_path, script_args, ctx)


@dev.command(name="link-commit")
@click.argument("issue_key")
@click.argument("commit_hash")
@click.option("--message", "-m", help="Commit message")
@click.option("--repo", "-r", help="Repository name")
@click.pass_context
def dev_link_commit(ctx, issue_key: str, commit_hash: str, message: str, repo: str):
    """Link a Git commit to a JIRA issue."""
    script_path = SKILLS_ROOT_DIR / "jira-dev" / "scripts" / "link_commit.py"

    script_args = [issue_key, commit_hash]
    if message:
        script_args.extend(["--message", message])
    if repo:
        script_args.extend(["--repo", repo])

    run_skill_script_subprocess(script_path, script_args, ctx)


@dev.command(name="link-pr")
@click.argument("issue_key")
@click.argument("pr_url")
@click.option("--title", "-t", help="PR title")
@click.option("--status", "-s", help="PR status (open, merged, closed)")
@click.pass_context
def dev_link_pr(ctx, issue_key: str, pr_url: str, title: str, status: str):
    """Link a Pull Request to a JIRA issue."""
    script_path = SKILLS_ROOT_DIR / "jira-dev" / "scripts" / "link_pr.py"

    script_args = [issue_key, pr_url]
    if title:
        script_args.extend(["--title", title])
    if status:
        script_args.extend(["--status", status])

    run_skill_script_subprocess(script_path, script_args, ctx)


@dev.command(name="get-commits")
@click.argument("issue_key")
@click.option("--limit", "-l", type=int, help="Maximum commits to show")
@click.pass_context
def dev_get_commits(ctx, issue_key: str, limit: int):
    """Get commits linked to an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-dev" / "scripts" / "get_issue_commits.py"

    script_args = [issue_key]
    if limit:
        script_args.extend(["--limit", str(limit)])

    run_skill_script_subprocess(script_path, script_args, ctx)
