import click

from jira_assistant_skills.utils import SKILLS_ROOT_DIR, run_skill_script_subprocess


@click.group()
def agile():
    """Commands for Agile/Scrum workflows (epics, sprints, backlog)."""
    pass


# Epic commands
@agile.group()
def epic():
    """Manage epics."""
    pass


@epic.command(name="create")
@click.option("--project", "-p", required=True, help="Project key")
@click.option("--summary", "-s", required=True, help="Epic summary (title)")
@click.option("--epic-name", "-n", help="Epic Name field value")
@click.option("--description", "-d", help="Epic description")
@click.option("--priority", help="Priority")
@click.option("--labels", "-l", help="Comma-separated labels")
@click.option("--color", "-c", help="Epic color (blue, green, red, etc.)")
@click.pass_context
def epic_create(
    ctx,
    project: str,
    summary: str,
    epic_name: str,
    description: str,
    priority: str,
    labels: str,
    color: str,
):
    """Create a new epic.

    Examples:
        jira agile epic create --project PROJ --summary "Mobile App MVP"
        jira agile epic create --project PROJ --summary "MVP" --epic-name "Mobile MVP" --color blue
    """
    script_path = SKILLS_ROOT_DIR / "jira-agile" / "scripts" / "create_epic.py"

    script_args = ["--project", project, "--summary", summary]
    if epic_name:
        script_args.extend(["--epic-name", epic_name])
    if description:
        script_args.extend(["--description", description])
    if priority:
        script_args.extend(["--priority", priority])
    if labels:
        script_args.extend(["--labels", labels])
    if color:
        script_args.extend(["--color", color])

    run_skill_script_subprocess(script_path, script_args, ctx)


@epic.command(name="get")
@click.argument("epic_key")
@click.option(
    "--with-children",
    "-c",
    is_flag=True,
    help="Fetch child issues and calculate progress",
)
@click.pass_context
def epic_get(ctx, epic_key: str, with_children: bool):
    """Get epic details.

    Examples:
        jira agile epic get PROJ-100
        jira agile epic get PROJ-100 --with-children
    """
    script_path = SKILLS_ROOT_DIR / "jira-agile" / "scripts" / "get_epic.py"

    script_args = [epic_key]
    if with_children:
        script_args.append("--with-children")

    run_skill_script_subprocess(script_path, script_args, ctx)


@epic.command(name="add-issues")
@click.option("--epic", "-e", required=True, help="Epic key (e.g., PROJ-100)")
@click.option(
    "--issues", "-i", help="Comma-separated issue keys (e.g., PROJ-101,PROJ-102)"
)
@click.option("--jql", "-j", help="JQL query to find issues")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without making changes")
@click.pass_context
def epic_add_issues(ctx, epic: str, issues: str, jql: str, dry_run: bool):
    """Add issues to an epic.

    Specify issues using either --issues or --jql (mutually exclusive).

    Examples:
        jira agile epic add-issues --epic PROJ-100 --issues PROJ-101,PROJ-102
        jira agile epic add-issues --epic PROJ-100 --jql "type = Story AND status = Open"
    """
    if not issues and not jql:
        raise click.UsageError("Either --issues or --jql is required")
    if issues and jql:
        raise click.UsageError("--issues and --jql are mutually exclusive")

    script_path = SKILLS_ROOT_DIR / "jira-agile" / "scripts" / "add_to_epic.py"

    script_args = ["--epic", epic]
    if issues:
        script_args.extend(["--issues", issues])
    if jql:
        script_args.extend(["--jql", jql])
    if dry_run:
        script_args.append("--dry-run")

    run_skill_script_subprocess(script_path, script_args, ctx)


# Sprint commands
@agile.group()
def sprint():
    """Manage sprints."""
    pass


@sprint.command(name="list")
@click.option("--board", "-b", type=int, help="Board ID")
@click.option("--project", "-p", help="Project key (will find board automatically)")
@click.option(
    "--state",
    "-s",
    type=click.Choice(["active", "closed", "future"]),
    help="Filter by sprint state",
)
@click.option("--max-results", "-m", type=int, default=50, help="Maximum sprints")
@click.pass_context
def sprint_list(ctx, board: int, project: str, state: str, max_results: int):
    """List sprints for a board or project.

    Specify board using either --board (ID) or --project (key).

    Examples:
        jira agile sprint list --project DEMO
        jira agile sprint list --board 123
        jira agile sprint list --project DEMO --state active
    """
    if not board and not project:
        raise click.UsageError("Either --board or --project is required")
    if board and project:
        raise click.UsageError("--board and --project are mutually exclusive")

    script_path = SKILLS_ROOT_DIR / "jira-agile" / "scripts" / "list_sprints.py"

    script_args = ["--max-results", str(max_results)]
    if board:
        script_args.extend(["--board", str(board)])
    if project:
        script_args.extend(["--project", project])
    if state:
        script_args.extend(["--state", state])

    run_skill_script_subprocess(script_path, script_args, ctx)


@sprint.command(name="create")
@click.option("--board", "-b", "board_id", type=int, required=True, help="Board ID")
@click.option("--name", "-n", required=True, help="Sprint name")
@click.option("--goal", "-g", help="Sprint goal")
@click.option("--start-date", "-s", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", "-e", help="End date (YYYY-MM-DD)")
@click.pass_context
def sprint_create(
    ctx, board_id: int, name: str, goal: str, start_date: str, end_date: str
):
    """Create a new sprint.

    Examples:
        jira agile sprint create --board 123 --name "Sprint 42"
        jira agile sprint create --board 123 --name "Sprint 42" --goal "Launch MVP"
    """
    script_path = SKILLS_ROOT_DIR / "jira-agile" / "scripts" / "create_sprint.py"

    script_args = ["--board", str(board_id), "--name", name]
    if goal:
        script_args.extend(["--goal", goal])
    if start_date:
        script_args.extend(["--start", start_date])
    if end_date:
        script_args.extend(["--end", end_date])

    run_skill_script_subprocess(script_path, script_args, ctx)


@sprint.command(name="get")
@click.argument("sprint_id", type=int, required=False)
@click.option("--board", "-b", type=int, help="Board ID (use with --active)")
@click.option("--active", "-a", is_flag=True, help="Get active sprint for board")
@click.option("--include-issues", "-i", is_flag=True, help="Include issues in sprint")
@click.pass_context
def sprint_get(ctx, sprint_id: int, board: int, active: bool, include_issues: bool):
    """Get sprint details.

    Get a specific sprint by ID, or find the active sprint for a board.

    Examples:
        jira agile sprint get 456
        jira agile sprint get 456 --include-issues
        jira agile sprint get --board 123 --active
    """
    if active:
        if not board:
            raise click.UsageError("--board is required with --active")
        if sprint_id:
            raise click.UsageError("Cannot specify both SPRINT_ID and --active")
    elif not sprint_id:
        raise click.UsageError("SPRINT_ID is required (or use --board with --active)")

    script_path = SKILLS_ROOT_DIR / "jira-agile" / "scripts" / "get_sprint.py"

    script_args = []
    if active:
        script_args.extend(["--board", str(board), "--active"])
    else:
        script_args.append(str(sprint_id))
    if include_issues:
        script_args.append("--with-issues")

    run_skill_script_subprocess(script_path, script_args, ctx)


@sprint.command(name="manage")
@click.option("--sprint", "-s", type=int, required=True, help="Sprint ID to manage")
@click.option("--start", is_flag=True, help="Start the sprint")
@click.option("--close", is_flag=True, help="Close the sprint")
@click.option("--name", "-n", help="Update sprint name")
@click.option("--goal", "-g", help="Update sprint goal")
@click.option(
    "--move-incomplete-to",
    type=int,
    help="Sprint ID to move incomplete issues to (with --close)",
)
@click.option("--start-date", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", help="End date (YYYY-MM-DD)")
@click.pass_context
def sprint_manage(
    ctx,
    sprint: int,
    start: bool,
    close: bool,
    name: str,
    goal: str,
    move_incomplete_to: int,
    start_date: str,
    end_date: str,
):
    """Manage sprint lifecycle (start, close, update).

    Examples:
        jira agile sprint manage --sprint 456 --start
        jira agile sprint manage --sprint 456 --close
        jira agile sprint manage --sprint 456 --close --move-incomplete-to 457
        jira agile sprint manage --sprint 456 --name "Sprint 42 - Updated"
    """
    script_path = SKILLS_ROOT_DIR / "jira-agile" / "scripts" / "manage_sprint.py"

    script_args = ["--sprint", str(sprint)]
    if start:
        script_args.append("--start")
    if close:
        script_args.append("--close")
    if name:
        script_args.extend(["--name", name])
    if goal:
        script_args.extend(["--goal", goal])
    if move_incomplete_to:
        script_args.extend(["--move-incomplete-to", str(move_incomplete_to)])
    if start_date:
        script_args.extend(["--start-date", start_date])
    if end_date:
        script_args.extend(["--end-date", end_date])

    run_skill_script_subprocess(script_path, script_args, ctx)


@sprint.command(name="move-issues")
@click.option("--sprint", "-s", type=int, help="Target sprint ID")
@click.option("--backlog", "-b", is_flag=True, help="Move to backlog instead of sprint")
@click.option(
    "--issues", "-i", help="Comma-separated issue keys (e.g., PROJ-101,PROJ-102)"
)
@click.option("--jql", "-j", help="JQL query to find issues")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without making changes")
@click.pass_context
def sprint_move_issues(
    ctx, sprint: int, backlog: bool, issues: str, jql: str, dry_run: bool
):
    """Move issues to a sprint or backlog.

    Specify target using either --sprint or --backlog.
    Specify issues using either --issues or --jql.

    Examples:
        jira agile sprint move-issues --sprint 456 --issues PROJ-101,PROJ-102
        jira agile sprint move-issues --backlog --jql "sprint = 456 AND status = Done"
    """
    if not sprint and not backlog:
        raise click.UsageError("Either --sprint or --backlog is required")
    if sprint and backlog:
        raise click.UsageError("--sprint and --backlog are mutually exclusive")
    if not issues and not jql:
        raise click.UsageError("Either --issues or --jql is required")
    if issues and jql:
        raise click.UsageError("--issues and --jql are mutually exclusive")

    script_path = SKILLS_ROOT_DIR / "jira-agile" / "scripts" / "move_to_sprint.py"

    script_args = []
    if sprint:
        script_args.extend(["--sprint", str(sprint)])
    if backlog:
        script_args.append("--backlog")
    if issues:
        script_args.extend(["--issues", issues])
    if jql:
        script_args.extend(["--jql", jql])
    if dry_run:
        script_args.append("--dry-run")

    run_skill_script_subprocess(script_path, script_args, ctx)


# Backlog commands
@agile.command(name="backlog")
@click.option("--board", "-b", type=int, help="Board ID")
@click.option("--project", "-p", help="Project key (alternative to --board)")
@click.option("--max-results", "-m", type=int, default=50, help="Maximum results")
@click.pass_context
def agile_backlog(ctx, board: int, project: str, max_results: int):
    """Get backlog issues for a board.

    Specify board using either --board (ID) or --project (key).

    Examples:
        jira agile backlog --project DEMO
        jira agile backlog --board 123
        jira agile backlog --project DEMO --max-results 100
    """
    if not board and not project:
        raise click.UsageError("Either --board or --project is required")
    if board and project:
        raise click.UsageError("--board and --project are mutually exclusive")

    script_path = SKILLS_ROOT_DIR / "jira-agile" / "scripts" / "get_backlog.py"

    script_args = ["--max-results", str(max_results)]
    if board:
        script_args.extend(["--board", str(board)])
    if project:
        script_args.extend(["--project", project])

    run_skill_script_subprocess(script_path, script_args, ctx)


# Ranking
@agile.command(name="rank")
@click.argument("issue_key")
@click.option("--before", "-b", help="Rank before this issue")
@click.option("--after", "-a", help="Rank after this issue")
@click.option("--top", is_flag=True, help="Move to top of backlog")
@click.option("--bottom", is_flag=True, help="Move to bottom of backlog")
@click.option("--board", type=int, help="Board ID (required for --top/--bottom)")
@click.pass_context
def agile_rank(
    ctx, issue_key: str, before: str, after: str, top: bool, bottom: bool, board: int
):
    """Rank an issue in the backlog.

    Position the issue using one of: --before, --after, --top, or --bottom.

    Examples:
        jira agile rank PROJ-1 --before PROJ-2
        jira agile rank PROJ-1 --after PROJ-3
        jira agile rank PROJ-1 --top --board 123
        jira agile rank PROJ-1 --bottom --board 123
    """
    # Validate mutually exclusive options
    position_count = sum([bool(before), bool(after), top, bottom])
    if position_count == 0:
        raise click.UsageError(
            "Must specify one of: --before, --after, --top, or --bottom"
        )
    if position_count > 1:
        raise click.UsageError(
            "--before, --after, --top, and --bottom are mutually exclusive"
        )
    if (top or bottom) and not board:
        raise click.UsageError("--board is required with --top or --bottom")

    script_path = SKILLS_ROOT_DIR / "jira-agile" / "scripts" / "rank_issue.py"

    script_args = [issue_key]
    if before:
        script_args.extend(["--before", before])
    if after:
        script_args.extend(["--after", after])
    if top:
        script_args.append("--top")
    if bottom:
        script_args.append("--bottom")
    if board:
        script_args.extend(["--board", str(board)])

    run_skill_script_subprocess(script_path, script_args, ctx)


# Estimation
@agile.command(name="estimate")
@click.argument("issue_key")
@click.option("--points", "-p", type=float, required=True, help="Story points value")
@click.pass_context
def agile_estimate(ctx, issue_key: str, points: float):
    """Set story points for an issue.

    Examples:
        jira agile estimate PROJ-123 --points 5
        jira agile estimate PROJ-123 --points 3
    """
    script_path = SKILLS_ROOT_DIR / "jira-agile" / "scripts" / "estimate_issue.py"
    run_skill_script_subprocess(script_path, [issue_key, "--points", str(points)], ctx)


@agile.command(name="estimates")
@click.option("--sprint", "-s", type=int, help="Sprint ID")
@click.option("--project", "-p", help="Project key (finds active sprint)")
@click.option("--epic", "-e", help="Epic key")
@click.option(
    "--group-by", "-g", type=click.Choice(["assignee", "status"]), help="Group results"
)
@click.pass_context
def agile_estimates(ctx, sprint: int, project: str, epic: str, group_by: str):
    """Get story point estimates for a sprint, project, or epic.

    Specify source using one of: --sprint, --project, or --epic.

    Examples:
        jira agile estimates --project DEMO
        jira agile estimates --sprint 456
        jira agile estimates --epic PROJ-100
        jira agile estimates --project DEMO --group-by assignee
    """
    if not sprint and not project and not epic:
        raise click.UsageError("One of --sprint, --project, or --epic is required")

    # Count how many options were provided
    provided = sum(1 for opt in [sprint, project, epic] if opt)
    if provided > 1:
        raise click.UsageError("--sprint, --project, and --epic are mutually exclusive")

    script_path = SKILLS_ROOT_DIR / "jira-agile" / "scripts" / "get_estimates.py"

    script_args = []
    if sprint:
        script_args.extend(["--sprint", str(sprint)])
    if project:
        script_args.extend(["--project", project])
    if epic:
        script_args.extend(["--epic", epic])
    if group_by:
        script_args.extend(["--group-by", group_by])

    run_skill_script_subprocess(script_path, script_args, ctx)


@agile.command(name="velocity")
@click.option("--board", "-b", type=int, help="Board ID")
@click.option("--project", "-p", help="Project key (will find board automatically)")
@click.option(
    "--sprints",
    "-n",
    type=int,
    default=3,
    help="Number of closed sprints to analyze (default: 3)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
def agile_velocity(ctx, board: int, project: str, sprints: int, output: str):
    """Calculate velocity from completed sprints.

    Shows average story points completed per sprint based on historical data.

    Examples:
        jira agile velocity --project DEMO
        jira agile velocity --project DEMO --sprints 5
        jira agile velocity --board 123 --sprints 3
        jira agile velocity --project DEMO --output json
    """
    if not board and not project:
        raise click.UsageError("Either --board or --project is required")
    if board and project:
        raise click.UsageError("--board and --project are mutually exclusive")

    script_path = SKILLS_ROOT_DIR / "jira-agile" / "scripts" / "get_velocity.py"

    script_args = ["--sprints", str(sprints), "--output", output]
    if board:
        script_args.extend(["--board", str(board)])
    if project:
        script_args.extend(["--project", project])

    run_skill_script_subprocess(script_path, script_args, ctx)


# Subtasks
@agile.command(name="subtask")
@click.option("--parent", "-p", required=True, help="Parent issue key (e.g., PROJ-101)")
@click.option("--summary", "-s", required=True, help="Subtask summary")
@click.option("--description", "-d", help="Subtask description")
@click.option("--assignee", "-a", help="Assignee (account ID, email, or 'self')")
@click.option("--estimate", "-e", help="Time estimate (e.g., 4h, 2d, 1w)")
@click.option("--priority", help="Priority (Highest, High, Medium, Low, Lowest)")
@click.option("--labels", "-l", help="Comma-separated labels")
@click.pass_context
def agile_subtask(
    ctx,
    parent: str,
    summary: str,
    description: str,
    assignee: str,
    estimate: str,
    priority: str,
    labels: str,
):
    """Create a subtask under a parent issue.

    Examples:
        jira agile subtask --parent PROJ-101 --summary "Implement login API"
        jira agile subtask --parent PROJ-101 --summary "Task" --assignee self --estimate 4h
    """
    script_path = SKILLS_ROOT_DIR / "jira-agile" / "scripts" / "create_subtask.py"

    script_args = ["--parent", parent, "--summary", summary]
    if description:
        script_args.extend(["--description", description])
    if assignee:
        script_args.extend(["--assignee", assignee])
    if estimate:
        script_args.extend(["--estimate", estimate])
    if priority:
        script_args.extend(["--priority", priority])
    if labels:
        script_args.extend(["--labels", labels])

    run_skill_script_subprocess(script_path, script_args, ctx)
