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
@click.argument("target_issue", required=False)
@click.option(
    "--type",
    "-t",
    "link_type",
    help="Link type to remove (use with --all to remove all of this type)",
)
@click.option(
    "--all", "-a", "remove_all", is_flag=True, help="Remove all links of specified type"
)
@click.option("--dry-run", "-n", is_flag=True, help="Preview without deleting")
@click.pass_context
def relationships_unlink(
    ctx,
    source_issue: str,
    target_issue: str,
    link_type: str,
    remove_all: bool,
    dry_run: bool,
):
    """Remove a link between two issues.

    Examples:
        jira relationships unlink PROJ-1 PROJ-2           # Remove link between two issues
        jira relationships unlink PROJ-1 --type blocks --all  # Remove all 'blocks' links
        jira relationships unlink PROJ-1 PROJ-2 --dry-run     # Preview removal
    """
    script_path = SKILLS_ROOT_DIR / "jira-relationships" / "scripts" / "unlink_issue.py"

    # Validate usage
    if not target_issue and not (link_type and remove_all):
        raise click.UsageError(
            "Specify TARGET_ISSUE or use --type TYPE with --all to remove all links of a type"
        )

    script_args = [source_issue]
    if target_issue:
        script_args.extend(["--from", target_issue])
    if link_type:
        script_args.extend(["--type", link_type])
    if remove_all:
        script_args.append("--all")
    if dry_run:
        script_args.append("--dry-run")

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
@click.option(
    "--type",
    "-t",
    "link_types",
    help="Comma-separated link types to include (e.g., blocks,relates)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json", "mermaid", "dot", "plantuml", "d2"]),
    default="text",
    help="Output format (text, json, mermaid, dot, plantuml, d2)",
)
@click.pass_context
def relationships_get_dependencies(ctx, issue_key: str, link_types: str, output: str):
    """Get dependency tree for an issue.

    Export formats for visualization:
        mermaid   - Mermaid.js flowchart (GitHub/GitLab markdown)
        dot       - Graphviz DOT format
        plantuml  - PlantUML diagram format
        d2        - D2 diagram format (Terrastruct)

    Examples:
        jira relationships get-dependencies PROJ-123
        jira relationships get-dependencies PROJ-123 --output mermaid
        jira relationships get-dependencies PROJ-123 --output dot > deps.dot
    """
    script_path = (
        SKILLS_ROOT_DIR / "jira-relationships" / "scripts" / "get_dependencies.py"
    )

    script_args = [issue_key]
    if link_types:
        script_args.extend(["--type", link_types])
    if output != "text":
        script_args.extend(["--output", output])

    run_skill_script_subprocess(script_path, script_args, ctx)


@relationships.command(name="link-types")
@click.option(
    "--filter",
    "-f",
    "filter_pattern",
    help="Filter link types by name pattern (case-insensitive)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
def relationships_link_types(ctx, filter_pattern: str, output: str):
    """List available link types.

    Examples:
        jira relationships link-types
        jira relationships link-types --filter block
        jira relationships link-types --output json
    """
    script_path = (
        SKILLS_ROOT_DIR / "jira-relationships" / "scripts" / "get_link_types.py"
    )
    script_args = []
    if filter_pattern:
        script_args.extend(["--filter", filter_pattern])
    if output != "text":
        script_args.extend(["--output", output])

    run_skill_script_subprocess(script_path, script_args, ctx)


@relationships.command(name="clone")
@click.argument("issue_key")
@click.option(
    "--to-project", "-p", help="Target project key (defaults to same project)"
)
@click.option("--summary", "-s", help="Custom summary for cloned issue")
@click.option("--clone-links", "-l", is_flag=True, help="Clone issue links")
@click.option("--clone-subtasks", is_flag=True, help="Clone subtasks")
@click.option("--no-link", is_flag=True, help="Do not create 'clones' link to original")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
def relationships_clone(
    ctx,
    issue_key: str,
    to_project: str,
    summary: str,
    clone_links: bool,
    clone_subtasks: bool,
    no_link: bool,
    output: str,
):
    """Clone an issue with optional links and subtasks."""
    script_path = SKILLS_ROOT_DIR / "jira-relationships" / "scripts" / "clone_issue.py"

    script_args = [issue_key]
    if to_project:
        script_args.extend(["--to-project", to_project])
    if summary:
        script_args.extend(["--summary", summary])
    if clone_links:
        script_args.append("--include-links")
    if clone_subtasks:
        script_args.append("--include-subtasks")
    if no_link:
        script_args.append("--no-link")
    if output != "text":
        script_args.extend(["--output", output])

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
@click.argument("key_or_project", required=False)
@click.option("--project", "-p", help="Project key to analyze all issues")
@click.option("--jql", "-j", help="JQL query to find issues to analyze")
@click.option(
    "--top",
    "-t",
    type=int,
    default=10,
    help="Number of most-connected issues to show (default: 10)",
)
@click.option(
    "--max-results",
    "-m",
    type=int,
    default=500,
    help="Maximum issues to analyze (default: 500)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
def relationships_stats(
    ctx,
    key_or_project: str,
    project: str,
    jql: str,
    top: int,
    max_results: int,
    output: str,
):
    """Get link statistics for an issue or project.

    Can analyze a single issue, all issues in a project, or issues matching JQL.

    Examples:
        jira relationships stats PROJ-123             # Single issue stats
        jira relationships stats --project PROJ       # Project-wide stats
        jira relationships stats --jql "type = Epic"  # JQL-filtered stats
        jira relationships stats --project PROJ --top 20 --output json
    """
    script_path = SKILLS_ROOT_DIR / "jira-relationships" / "scripts" / "link_stats.py"

    # Validate mutual exclusivity
    options_set = sum(1 for opt in [key_or_project, project, jql] if opt)
    if options_set == 0:
        raise click.UsageError("Specify ISSUE_KEY, --project, or --jql")
    if options_set > 1:
        raise click.UsageError("Specify only one of: ISSUE_KEY, --project, or --jql")

    script_args = []
    if key_or_project:
        # Could be issue key (PROJ-123) or project key (PROJ)
        # Let the script handle validation
        script_args.append(key_or_project)
    elif project:
        script_args.extend(["--project", project])
    elif jql:
        script_args.extend(["--jql", jql])

    script_args.extend(["--top", str(top)])
    script_args.extend(["--max-results", str(max_results)])
    if output != "text":
        script_args.extend(["--output", output])

    run_skill_script_subprocess(script_path, script_args, ctx)
