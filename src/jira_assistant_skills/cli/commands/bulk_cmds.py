import click

from jira_assistant_skills.utils import SKILLS_ROOT_DIR, run_skill_script_subprocess


@click.group()
def bulk():
    """Commands for bulk operations on multiple issues."""
    pass


@bulk.command(name="transition")
@click.option("--jql", "-q", help="JQL query to find issues")
@click.option("--issues", "-i", help="Comma-separated issue keys (e.g., PROJ-1,PROJ-2)")
@click.option(
    "--to",
    "-t",
    "target_status",
    required=True,
    help='Target status name (e.g., "Done", "In Progress")',
)
@click.option("--comment", "-c", help="Add comment with transition")
@click.option("--resolution", "-r", help="Resolution for Done transitions")
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    help="Show what would be changed without making changes",
)
@click.option(
    "--max-issues", "-m", type=int, default=50, help="Maximum issues to process"
)
@click.option(
    "--batch-size", type=int, help="Issues per batch (auto-calculated if not specified)"
)
@click.option(
    "--enable-checkpoint",
    is_flag=True,
    help="Enable checkpoint/resume for large operations",
)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def bulk_transition(
    ctx,
    jql: str,
    issues: str,
    target_status: str,
    comment: str,
    resolution: str,
    dry_run: bool,
    max_issues: int,
    batch_size: int,
    enable_checkpoint: bool,
    force: bool,
):
    """Transition multiple issues to a new status.

    Specify issues using either --jql or --issues (mutually exclusive).

    Examples:
        jira bulk transition --jql "project=PROJ AND status='Open'" --to "Done"
        jira bulk transition --issues PROJ-1,PROJ-2 --to "In Progress"
    """
    if not jql and not issues:
        raise click.UsageError("Either --jql or --issues is required")
    if jql and issues:
        raise click.UsageError("--jql and --issues are mutually exclusive")

    script_path = SKILLS_ROOT_DIR / "jira-bulk" / "scripts" / "bulk_transition.py"

    script_args = []
    if jql:
        script_args.extend(["--jql", jql])
    if issues:
        script_args.extend(["--issues", issues])
    script_args.extend(["--to", target_status])
    if comment:
        script_args.extend(["--comment", comment])
    if resolution:
        script_args.extend(["--resolution", resolution])
    if dry_run:
        script_args.append("--dry-run")
    if max_issues:
        script_args.extend(["--max-issues", str(max_issues)])
    if batch_size:
        script_args.extend(["--batch-size", str(batch_size)])
    if enable_checkpoint:
        script_args.append("--enable-checkpoint")
    if force:
        script_args.append("--yes")

    run_skill_script_subprocess(script_path, script_args, ctx)


@bulk.command(name="assign")
@click.option("--jql", "-q", help="JQL query to find issues")
@click.option("--issues", "-i", help="Comma-separated issue keys (e.g., PROJ-1,PROJ-2)")
@click.option("--assignee", "-a", help='User to assign (account ID, email, or "self")')
@click.option("--unassign", is_flag=True, help="Unassign all matching issues")
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    help="Show what would be changed without making changes",
)
@click.option(
    "--max-issues", "-m", type=int, default=50, help="Maximum issues to process"
)
@click.option(
    "--batch-size", type=int, help="Issues per batch (auto-calculated if not specified)"
)
@click.option(
    "--enable-checkpoint",
    is_flag=True,
    help="Enable checkpoint/resume for large operations",
)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def bulk_assign(
    ctx,
    jql: str,
    issues: str,
    assignee: str,
    unassign: bool,
    dry_run: bool,
    max_issues: int,
    batch_size: int,
    enable_checkpoint: bool,
    force: bool,
):
    """Assign or unassign multiple issues.

    Specify issues using either --jql or --issues (mutually exclusive).
    Specify target using either --assignee or --unassign.

    Examples:
        jira bulk assign --jql "project=PROJ AND status=Open" --assignee john.doe
        jira bulk assign --jql "assignee=leaving.user" --unassign
        jira bulk assign --issues PROJ-1,PROJ-2 --assignee self
    """
    if not jql and not issues:
        raise click.UsageError("Either --jql or --issues is required")
    if jql and issues:
        raise click.UsageError("--jql and --issues are mutually exclusive")
    if not assignee and not unassign:
        raise click.UsageError("Either --assignee or --unassign is required")
    if assignee and unassign:
        raise click.UsageError("--assignee and --unassign are mutually exclusive")

    script_path = SKILLS_ROOT_DIR / "jira-bulk" / "scripts" / "bulk_assign.py"

    script_args = []
    if jql:
        script_args.extend(["--jql", jql])
    if issues:
        script_args.extend(["--issues", issues])
    if assignee:
        script_args.extend(["--assignee", assignee])
    if unassign:
        script_args.append("--unassign")
    if dry_run:
        script_args.append("--dry-run")
    if max_issues:
        script_args.extend(["--max-issues", str(max_issues)])
    if batch_size:
        script_args.extend(["--batch-size", str(batch_size)])
    if enable_checkpoint:
        script_args.append("--enable-checkpoint")
    if force:
        script_args.append("--yes")

    run_skill_script_subprocess(script_path, script_args, ctx)


@bulk.command(name="set-priority")
@click.option("--jql", "-q", help="JQL query to find issues")
@click.option("--issues", "-i", help="Comma-separated issue keys (e.g., PROJ-1,PROJ-2)")
@click.option(
    "--priority",
    "-p",
    required=True,
    help="Priority name (Highest, High, Medium, Low, Lowest)",
)
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    help="Show what would be changed without making changes",
)
@click.option(
    "--max-issues", "-m", type=int, default=50, help="Maximum issues to process"
)
@click.option(
    "--batch-size", type=int, help="Issues per batch (auto-calculated if not specified)"
)
@click.option(
    "--enable-checkpoint",
    is_flag=True,
    help="Enable checkpoint/resume for large operations",
)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def bulk_set_priority(
    ctx,
    jql: str,
    issues: str,
    priority: str,
    dry_run: bool,
    max_issues: int,
    batch_size: int,
    enable_checkpoint: bool,
    force: bool,
):
    """Set priority for multiple issues.

    Specify issues using either --jql or --issues (mutually exclusive).

    Examples:
        jira bulk set-priority --jql "type=Bug AND labels=critical" --priority Highest
        jira bulk set-priority --issues PROJ-1,PROJ-2 --priority High
    """
    if not jql and not issues:
        raise click.UsageError("Either --jql or --issues is required")
    if jql and issues:
        raise click.UsageError("--jql and --issues are mutually exclusive")

    script_path = SKILLS_ROOT_DIR / "jira-bulk" / "scripts" / "bulk_set_priority.py"

    script_args = []
    if jql:
        script_args.extend(["--jql", jql])
    if issues:
        script_args.extend(["--issues", issues])
    script_args.extend(["--priority", priority])
    if dry_run:
        script_args.append("--dry-run")
    if max_issues:
        script_args.extend(["--max-issues", str(max_issues)])
    if batch_size:
        script_args.extend(["--batch-size", str(batch_size)])
    if enable_checkpoint:
        script_args.append("--enable-checkpoint")
    if force:
        script_args.append("--yes")

    run_skill_script_subprocess(script_path, script_args, ctx)


@bulk.command(name="clone")
@click.option("--jql", "-q", help="JQL query to find issues")
@click.option("--issues", "-i", help="Comma-separated issue keys (e.g., PROJ-1,PROJ-2)")
@click.option("--target-project", "-t", help="Target project key for clones")
@click.option("--prefix", "-P", help="Prefix for cloned issue summaries")
@click.option("--include-links", "-l", is_flag=True, help="Clone issue links")
@click.option("--include-subtasks", "-s", is_flag=True, help="Clone subtasks")
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    help="Show what would be changed without making changes",
)
@click.option(
    "--max-issues", "-m", type=int, default=50, help="Maximum issues to process"
)
@click.option(
    "--batch-size", type=int, help="Issues per batch (auto-calculated if not specified)"
)
@click.option(
    "--enable-checkpoint",
    is_flag=True,
    help="Enable checkpoint/resume for large operations",
)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def bulk_clone(
    ctx,
    jql: str,
    issues: str,
    target_project: str,
    prefix: str,
    include_links: bool,
    include_subtasks: bool,
    dry_run: bool,
    max_issues: int,
    batch_size: int,
    enable_checkpoint: bool,
    force: bool,
):
    """Clone multiple issues.

    Specify issues using either --jql or --issues (mutually exclusive).

    Examples:
        jira bulk clone --jql "sprint='Sprint 42'" --include-subtasks --include-links
        jira bulk clone --issues PROJ-1,PROJ-2 --target-project NEWPROJ --prefix "[Clone]"
    """
    if not jql and not issues:
        raise click.UsageError("Either --jql or --issues is required")
    if jql and issues:
        raise click.UsageError("--jql and --issues are mutually exclusive")

    script_path = SKILLS_ROOT_DIR / "jira-bulk" / "scripts" / "bulk_clone.py"

    script_args = []
    if jql:
        script_args.extend(["--jql", jql])
    if issues:
        script_args.extend(["--issues", issues])
    if target_project:
        script_args.extend(["--target-project", target_project])
    if prefix:
        script_args.extend(["--prefix", prefix])
    if include_links:
        script_args.append("--include-links")
    if include_subtasks:
        script_args.append("--include-subtasks")
    if dry_run:
        script_args.append("--dry-run")
    if max_issues:
        script_args.extend(["--max-issues", str(max_issues)])
    if batch_size:
        script_args.extend(["--batch-size", str(batch_size)])
    if enable_checkpoint:
        script_args.append("--enable-checkpoint")
    if force:
        script_args.append("--yes")

    run_skill_script_subprocess(script_path, script_args, ctx)
