import click

from jira_assistant_skills.utils import SKILLS_ROOT_DIR, run_skill_script_subprocess


@click.group()
def relationships():
    """Commands for managing issue links and dependencies."""
    pass


@relationships.command(name="link")
@click.argument("source_issue")
@click.option("--blocks", help="Issue that this issue blocks")
@click.option("--is-blocked-by", help="Issue that blocks this issue")
@click.option("--relates-to", help="Issue that this issue relates to")
@click.option("--duplicates", help="Issue that this issue duplicates")
@click.option("--clones", help="Issue that this issue clones")
@click.option("--type", "-t", "link_type", help="Explicit link type name")
@click.option("--to", "target", help="Target issue (use with --type)")
@click.option("--comment", "-c", help="Add comment with the link")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without making changes")
@click.pass_context
def relationships_link(
    ctx,
    source_issue: str,
    blocks: str,
    is_blocked_by: str,
    relates_to: str,
    duplicates: str,
    clones: str,
    link_type: str,
    target: str,
    comment: str,
    dry_run: bool,
):
    """Create a link between two issues.

    Use one of the shorthand options or --type with --to.

    Examples:
        jira relationships link PROJ-1 --blocks PROJ-2
        jira relationships link PROJ-1 --relates-to PROJ-2
        jira relationships link PROJ-1 --type "Blocks" --to PROJ-2
    """
    # Count how many link options were provided
    link_opts = [blocks, is_blocked_by, relates_to, duplicates, clones]
    explicit_opts = link_type and target
    if sum(1 for opt in link_opts if opt) + (1 if explicit_opts else 0) != 1:
        raise click.UsageError(
            "Specify exactly one link type: --blocks, --relates-to, --duplicates, --clones, --is-blocked-by, or --type with --to"
        )

    script_path = SKILLS_ROOT_DIR / "jira-relationships" / "scripts" / "link_issue.py"

    script_args = [source_issue]
    if blocks:
        script_args.extend(["--blocks", blocks])
    elif is_blocked_by:
        script_args.extend(["--is-blocked-by", is_blocked_by])
    elif relates_to:
        script_args.extend(["--relates-to", relates_to])
    elif duplicates:
        script_args.extend(["--duplicates", duplicates])
    elif clones:
        script_args.extend(["--clones", clones])
    elif link_type and target:
        script_args.extend(["--type", link_type, "--to", target])
    if comment:
        script_args.extend(["--comment", comment])
    if dry_run:
        script_args.append("--dry-run")

    run_skill_script_subprocess(script_path, script_args, ctx)


@relationships.command(name="unlink")
@click.argument("source_issue")
@click.argument("target_issue")
@click.option(
    "--type",
    "-t",
    "link_type",
    help="Link type to remove (removes all if not specified)",
)
@click.pass_context
def relationships_unlink(ctx, source_issue: str, target_issue: str, link_type: str):
    """Remove a link between two issues."""
    script_path = SKILLS_ROOT_DIR / "jira-relationships" / "scripts" / "unlink_issue.py"

    script_args = [source_issue, target_issue]
    if link_type:
        script_args.extend(["--type", link_type])

    run_skill_script_subprocess(script_path, script_args, ctx)


@relationships.command(name="get-links")
@click.argument("issue_key")
@click.option("--type", "-t", "link_type", help="Filter by link type")
@click.option(
    "--direction",
    "-d",
    type=click.Choice(["inward", "outward", "both"]),
    default="both",
    help="Link direction",
)
@click.pass_context
def relationships_get_links(ctx, issue_key: str, link_type: str, direction: str):
    """Get all links for an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-relationships" / "scripts" / "get_links.py"

    script_args = [issue_key]
    if link_type:
        script_args.extend(["--type", link_type])
    if direction != "both":
        script_args.extend(["--direction", direction])

    run_skill_script_subprocess(script_path, script_args, ctx)


@relationships.command(name="get-blockers")
@click.argument("issue_key")
@click.option("--recursive", "-r", is_flag=True, help="Show full blocker chain")
@click.option("--include-done", is_flag=True, help="Include completed blockers")
@click.pass_context
def relationships_get_blockers(
    ctx, issue_key: str, recursive: bool, include_done: bool
):
    """Get issues blocking this issue."""
    script_path = SKILLS_ROOT_DIR / "jira-relationships" / "scripts" / "get_blockers.py"

    script_args = [issue_key]
    if recursive:
        script_args.append("--recursive")
    if include_done:
        script_args.append("--include-done")

    run_skill_script_subprocess(script_path, script_args, ctx)


@relationships.command(name="get-dependencies")
@click.argument("issue_key")
@click.option("--depth", "-d", type=int, default=3, help="Maximum depth to traverse")
@click.option("--include-done", is_flag=True, help="Include completed issues")
@click.pass_context
def relationships_get_dependencies(ctx, issue_key: str, depth: int, include_done: bool):
    """Get dependency tree for an issue."""
    script_path = (
        SKILLS_ROOT_DIR / "jira-relationships" / "scripts" / "get_dependencies.py"
    )

    script_args = [issue_key, "--depth", str(depth)]
    if include_done:
        script_args.append("--include-done")

    run_skill_script_subprocess(script_path, script_args, ctx)


@relationships.command(name="link-types")
@click.pass_context
def relationships_link_types(ctx):
    """List available link types."""
    script_path = (
        SKILLS_ROOT_DIR / "jira-relationships" / "scripts" / "get_link_types.py"
    )
    run_skill_script_subprocess(script_path, [], ctx)


@relationships.command(name="clone")
@click.argument("issue_key")
@click.option("--project", "-p", help="Target project key (defaults to same project)")
@click.option("--prefix", help="Prefix for cloned issue summary")
@click.option("--clone-links", "-l", is_flag=True, help="Clone issue links")
@click.option("--clone-subtasks", "-s", is_flag=True, help="Clone subtasks")
@click.pass_context
def relationships_clone(
    ctx,
    issue_key: str,
    project: str,
    prefix: str,
    clone_links: bool,
    clone_subtasks: bool,
):
    """Clone an issue with optional links and subtasks."""
    script_path = SKILLS_ROOT_DIR / "jira-relationships" / "scripts" / "clone_issue.py"

    script_args = [issue_key]
    if project:
        script_args.extend(["--project", project])
    if prefix:
        script_args.extend(["--prefix", prefix])
    if clone_links:
        script_args.append("--clone-links")
    if clone_subtasks:
        script_args.append("--clone-subtasks")

    run_skill_script_subprocess(script_path, script_args, ctx)


@relationships.command(name="bulk-link")
@click.option("--jql", "-j", help="JQL query to find issues")
@click.option("--issues", "-i", help="Comma-separated issue keys")
@click.option("--blocks", help="Issue that source issues block")
@click.option("--is-blocked-by", help="Issue that blocks source issues")
@click.option("--relates-to", help="Issue that source issues relate to")
@click.option("--duplicates", help="Issue that source issues duplicate")
@click.option("--clones", help="Issue that source issues clone")
@click.option("--type", "-t", "link_type", help="Explicit link type name")
@click.option("--to", "target", help="Target issue (use with --type)")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without making changes")
@click.option("--skip-existing", is_flag=True, help="Skip already linked issues")
@click.pass_context
def relationships_bulk_link(
    ctx,
    jql: str,
    issues: str,
    blocks: str,
    is_blocked_by: str,
    relates_to: str,
    duplicates: str,
    clones: str,
    link_type: str,
    target: str,
    dry_run: bool,
    skip_existing: bool,
):
    """Link multiple issues to a target issue.

    Specify source issues using --jql or --issues.
    Specify link type using --blocks, --relates-to, etc., or --type with --to.

    Examples:
        jira relationships bulk-link --jql "project=PROJ AND fixVersion=1.0" --relates-to PROJ-500
        jira relationships bulk-link --issues PROJ-1,PROJ-2 --blocks PROJ-100 --dry-run
    """
    if not jql and not issues:
        raise click.UsageError("Either --jql or --issues is required")
    if jql and issues:
        raise click.UsageError("--jql and --issues are mutually exclusive")

    link_opts = [blocks, is_blocked_by, relates_to, duplicates, clones]
    explicit_opts = link_type and target
    if sum(1 for opt in link_opts if opt) + (1 if explicit_opts else 0) != 1:
        raise click.UsageError(
            "Specify exactly one link type: --blocks, --relates-to, etc., or --type with --to"
        )

    script_path = SKILLS_ROOT_DIR / "jira-relationships" / "scripts" / "bulk_link.py"

    script_args = []
    if jql:
        script_args.extend(["--jql", jql])
    if issues:
        script_args.extend(["--issues", issues])
    if blocks:
        script_args.extend(["--blocks", blocks])
    elif is_blocked_by:
        script_args.extend(["--is-blocked-by", is_blocked_by])
    elif relates_to:
        script_args.extend(["--relates-to", relates_to])
    elif duplicates:
        script_args.extend(["--duplicates", duplicates])
    elif clones:
        script_args.extend(["--clones", clones])
    elif link_type and target:
        script_args.extend(["--type", link_type, "--to", target])
    if dry_run:
        script_args.append("--dry-run")
    if skip_existing:
        script_args.append("--skip-existing")

    run_skill_script_subprocess(script_path, script_args, ctx)


@relationships.command(name="stats")
@click.argument("project_key")
@click.option("--type", "-t", "link_type", help="Filter by link type")
@click.pass_context
def relationships_stats(ctx, project_key: str, link_type: str):
    """Get link statistics for a project."""
    script_path = SKILLS_ROOT_DIR / "jira-relationships" / "scripts" / "link_stats.py"

    script_args = [project_key]
    if link_type:
        script_args.extend(["--type", link_type])

    run_skill_script_subprocess(script_path, script_args, ctx)
