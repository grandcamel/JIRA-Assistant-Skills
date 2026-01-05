import click

from jira_assistant_skills.utils import SKILLS_ROOT_DIR, run_skill_script_subprocess


@click.group()
def search():
    """Commands for searching Jira issues with JQL."""
    pass


@search.command(name="query")
@click.argument("jql", required=False)
@click.option("--filter", "-f", "filter_id", help="Run a saved filter by ID")
@click.option("--fields", help="Comma-separated list of fields to retrieve")
@click.option(
    "--max-results", "-m", type=int, default=50, help="Maximum results (default: 50)"
)
@click.option("--show-links", "-l", is_flag=True, help="Show issue links")
@click.option("--show-time", "-t", is_flag=True, help="Show time tracking info")
@click.option(
    "--show-agile", "-a", is_flag=True, help="Show agile fields (epic, points)"
)
@click.option("--save-as", help="Save search as a new filter with this name")
@click.pass_context
def search_query(
    ctx,
    jql: str,
    filter_id: str,
    fields: str,
    max_results: int,
    show_links: bool,
    show_time: bool,
    show_agile: bool,
    save_as: str,
):
    """Search for issues using JQL query."""
    script_path = SKILLS_ROOT_DIR / "jira-search" / "scripts" / "jql_search.py"

    script_args = []
    if jql:
        script_args.append(jql)
    if filter_id:
        script_args.extend(["--filter", filter_id])
    if fields:
        script_args.extend(["--fields", fields])
    if max_results:
        script_args.extend(["--max-results", str(max_results)])
    if show_links:
        script_args.append("--show-links")
    if show_time:
        script_args.append("--show-time")
    if show_agile:
        script_args.append("--show-agile")
    if save_as:
        script_args.extend(["--save-as", save_as])

    run_skill_script_subprocess(script_path, script_args, ctx)


@search.command(name="export")
@click.argument("jql")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["csv", "json"]),
    default="csv",
    help="Export format (default: csv)",
)
@click.option("--output", "-o", "output_file", required=True, help="Output file path")
@click.option("--fields", help="Comma-separated list of fields to export")
@click.option("--max-results", "-m", type=int, help="Maximum results to export")
@click.pass_context
def search_export(
    ctx, jql: str, output_format: str, output_file: str, fields: str, max_results: int
):
    """Export search results to CSV or JSON."""
    script_path = SKILLS_ROOT_DIR / "jira-search" / "scripts" / "export_results.py"

    script_args = [jql, "--format", output_format]
    if output_file:
        script_args.extend(["--output", output_file])
    if fields:
        script_args.extend(["--fields", fields])
    if max_results:
        script_args.extend(["--max-results", str(max_results)])

    run_skill_script_subprocess(script_path, script_args, ctx)


@search.command(name="validate")
@click.argument("jql")
@click.pass_context
def search_validate(ctx, jql: str):
    """Validate a JQL query for syntax errors."""
    script_path = SKILLS_ROOT_DIR / "jira-search" / "scripts" / "jql_validate.py"
    run_skill_script_subprocess(script_path, [jql], ctx)


@search.command(name="build")
@click.option("--project", "-p", help="Project key")
@click.option("--type", "-t", "issue_type", help="Issue type")
@click.option("--status", "-s", help="Status")
@click.option("--assignee", "-a", help="Assignee")
@click.option("--reporter", "-r", help="Reporter")
@click.option("--priority", help="Priority")
@click.option("--labels", "-l", help="Labels (comma-separated)")
@click.option("--created", help='Created date range (e.g., "-7d", "2024-01-01")')
@click.option("--updated", help="Updated date range")
@click.option("--text", help="Text search across summary and description")
@click.pass_context
def search_build(
    ctx,
    project: str,
    issue_type: str,
    status: str,
    assignee: str,
    reporter: str,
    priority: str,
    labels: str,
    created: str,
    updated: str,
    text: str,
):
    """Build a JQL query interactively from options."""
    script_path = SKILLS_ROOT_DIR / "jira-search" / "scripts" / "jql_build.py"

    script_args = []
    if project:
        script_args.extend(["--project", project])
    if issue_type:
        script_args.extend(["--type", issue_type])
    if status:
        script_args.extend(["--status", status])
    if assignee:
        script_args.extend(["--assignee", assignee])
    if reporter:
        script_args.extend(["--reporter", reporter])
    if priority:
        script_args.extend(["--priority", priority])
    if labels:
        script_args.extend(["--labels", labels])
    if created:
        script_args.extend(["--created", created])
    if updated:
        script_args.extend(["--updated", updated])
    if text:
        script_args.extend(["--text", text])

    run_skill_script_subprocess(script_path, script_args, ctx)


@search.command(name="suggest")
@click.option("--field", "-f", required=True, help="Field name to get suggestions for")
@click.option("--prefix", "-x", default="", help="Filter suggestions by prefix")
@click.option("--no-cache", is_flag=True, help="Bypass cache and fetch from API")
@click.option("--refresh", is_flag=True, help="Force refresh cache from API")
@click.pass_context
def search_suggest(ctx, field: str, prefix: str, no_cache: bool, refresh: bool):
    """Get JQL field value suggestions for autocomplete."""
    script_path = SKILLS_ROOT_DIR / "jira-search" / "scripts" / "jql_suggest.py"

    script_args = ["--field", field]
    if prefix:
        script_args.extend(["--prefix", prefix])
    if no_cache:
        script_args.append("--no-cache")
    if refresh:
        script_args.append("--refresh")

    run_skill_script_subprocess(script_path, script_args, ctx)


@search.command(name="fields")
@click.option("--type", "-t", "field_type", help="Filter by field type")
@click.pass_context
def search_fields(ctx, field_type: str):
    """List available JQL fields and operators."""
    script_path = SKILLS_ROOT_DIR / "jira-search" / "scripts" / "jql_fields.py"

    script_args = []
    if field_type:
        script_args.extend(["--type", field_type])

    run_skill_script_subprocess(script_path, script_args, ctx)


@search.command(name="functions")
@click.pass_context
def search_functions(ctx):
    """List available JQL functions."""
    script_path = SKILLS_ROOT_DIR / "jira-search" / "scripts" / "jql_functions.py"
    run_skill_script_subprocess(script_path, [], ctx)


# Filter management subgroup
@search.group()
def filter():
    """Manage saved filters."""
    pass


@filter.command(name="list")
@click.option("--favourite", "-f", is_flag=True, help="Show only favourite filters")
@click.pass_context
def filter_list(ctx, favourite: bool):
    """List saved filters."""
    script_path = SKILLS_ROOT_DIR / "jira-search" / "scripts" / "get_filters.py"

    script_args = []
    if favourite:
        script_args.append("--favourite")

    run_skill_script_subprocess(script_path, script_args, ctx)


@filter.command(name="create")
@click.argument("name")
@click.argument("jql")
@click.option("--description", "-d", help="Filter description")
@click.option("--favourite", "-f", is_flag=True, help="Add to favourites")
@click.pass_context
def filter_create(ctx, name: str, jql: str, description: str, favourite: bool):
    """Create a new saved filter."""
    script_path = SKILLS_ROOT_DIR / "jira-search" / "scripts" / "create_filter.py"

    script_args = [name, jql]
    if description:
        script_args.extend(["--description", description])
    if favourite:
        script_args.append("--favourite")

    run_skill_script_subprocess(script_path, script_args, ctx)


@filter.command(name="run")
@click.argument("filter_id")
@click.option("--max-results", "-m", type=int, help="Maximum results")
@click.pass_context
def filter_run(ctx, filter_id: str, max_results: int):
    """Run a saved filter."""
    script_path = SKILLS_ROOT_DIR / "jira-search" / "scripts" / "run_filter.py"

    script_args = [filter_id]
    if max_results:
        script_args.extend(["--max-results", str(max_results)])

    run_skill_script_subprocess(script_path, script_args, ctx)


@filter.command(name="delete")
@click.argument("filter_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def filter_delete(ctx, filter_id: str, force: bool):
    """Delete a saved filter."""
    script_path = SKILLS_ROOT_DIR / "jira-search" / "scripts" / "delete_filter.py"

    script_args = [filter_id]
    if force:
        script_args.append("--force")

    run_skill_script_subprocess(script_path, script_args, ctx)


@filter.command(name="share")
@click.argument("filter_id")
@click.option("--project", "-p", help="Share with project")
@click.option("--group", "-g", help="Share with group")
@click.option("--user", "-u", help="Share with user")
@click.option("--public", is_flag=True, help="Make filter public")
@click.pass_context
def filter_share(
    ctx, filter_id: str, project: str, group: str, user: str, public: bool
):
    """Share a filter with users, groups, or projects."""
    script_path = SKILLS_ROOT_DIR / "jira-search" / "scripts" / "share_filter.py"

    script_args = [filter_id]
    if project:
        script_args.extend(["--project", project])
    if group:
        script_args.extend(["--group", group])
    if user:
        script_args.extend(["--user", user])
    if public:
        script_args.append("--public")

    run_skill_script_subprocess(script_path, script_args, ctx)
