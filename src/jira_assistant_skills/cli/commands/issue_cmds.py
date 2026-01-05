import importlib.util
import sys

import click

from jira_assistant_skills.utils import SKILLS_ROOT_DIR, run_skill_script_subprocess


@click.group()
def issue():
    """Commands for interacting with Jira issues."""
    pass


@issue.command(name="get")
@click.argument("issue_key")
@click.option("--fields", "-f", help="Comma-separated list of fields to retrieve")
@click.option(
    "--detailed",
    "-d",
    is_flag=True,
    help="Show detailed information including description",
)
@click.option(
    "--show-links",
    "-l",
    is_flag=True,
    help="Show issue links (blocks, relates to, etc.)",
)
@click.option("--show-time", "-t", is_flag=True, help="Show time tracking information")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    help="Output format (text, json)",
)
@click.pass_context
def get_issue(
    ctx,
    issue_key: str,
    fields: str,
    detailed: bool,
    show_links: bool,
    show_time: bool,
    output: str,
):
    """Get the details of a specific issue."""
    script_module_path = SKILLS_ROOT_DIR / "jira-issue" / "scripts" / "get_issue.py"

    # Arguments for the script's main(argv)
    script_args = [issue_key]
    if fields:
        script_args.extend(["--fields", fields])
    if detailed:
        script_args.append("--detailed")
    if show_links:
        script_args.append("--show-links")
    if show_time:
        script_args.append("--show-time")

    # Use explicit --output if provided, otherwise fall back to global OUTPUT
    output_format = output if output else ctx.obj.get("OUTPUT", "text")
    script_args.extend(["--output", output_format])

    try:
        # --- Primary: Direct call to callable API ---
        # Dynamically import the script as a module
        spec = importlib.util.spec_from_file_location(
            "jira_issue_get_script", str(script_module_path)
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        # Check if the script has a main() function
        if hasattr(module, "main") and callable(module.main):
            # Call script's main with mapped args
            module.main(script_args)
            # Success - exit cleanly (don't use ctx.exit inside try block)
        else:
            # Fallback to subprocess if main is not found or not callable.
            raise ImportError("Callable 'main' function not found in script.")

    except ImportError as e:
        # --- Fallback: Subprocess call to main(argv=...) ---
        click.echo(
            f"Warning: Falling back to subprocess for {script_module_path.name} ({e})",
            err=True,
        )
        run_skill_script_subprocess(
            script_path=script_module_path, args=script_args, ctx=ctx
        )
    except click.exceptions.Exit:
        # Script called sys.exit(0) or similar - this is expected, re-raise
        raise
    except Exception as e:
        click.echo(f"Error calling get_issue directly: {e}", err=True)
        ctx.exit(1)


@issue.command(name="create")
@click.option("--project", "-p", required=True, help="Project key (e.g., PROJ, DEV)")
@click.option("--type", "-t", required=True, help="Issue type (Bug, Task, Story, etc.)")
@click.option("--summary", "-s", required=True, help="Issue summary (title)")
@click.option("--description", "-d", help="Issue description (supports markdown)")
@click.option("--priority", help="Priority (Highest, High, Medium, Low, Lowest)")
@click.option("--assignee", "-a", help='Assignee (account ID, email, or "self")')
@click.option("--labels", "-l", help="Comma-separated labels")
@click.option("--components", "-c", help="Comma-separated component names")
@click.option("--template", help="Use a predefined template")
@click.option("--custom-fields", help="Custom fields as JSON string")
@click.option("--epic", "-e", help="Epic key to link this issue to (e.g., PROJ-100)")
@click.option("--sprint", type=int, help="Sprint ID to add this issue to")
@click.option("--story-points", type=float, help="Story point estimate")
@click.option("--blocks", help="Comma-separated issue keys this issue blocks")
@click.option("--relates-to", help="Comma-separated issue keys this issue relates to")
@click.option("--estimate", help="Original time estimate (e.g., 2d, 4h, 1w)")
@click.option("--no-defaults", is_flag=True, help="Disable project context defaults")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    help="Output format (text, json)",
)
@click.pass_context
def create_issue(
    ctx,
    project: str,
    type: str,
    summary: str,
    description: str,
    priority: str,
    assignee: str,
    labels: str,
    components: str,
    template: str,
    custom_fields: str,
    epic: str,
    sprint: int,
    story_points: float,
    blocks: str,
    relates_to: str,
    estimate: str,
    no_defaults: bool,
    output: str,
):
    """Create a new JIRA issue."""
    script_module_path = SKILLS_ROOT_DIR / "jira-issue" / "scripts" / "create_issue.py"

    script_args = ["--project", project, "--type", type, "--summary", summary]
    if description:
        script_args.extend(["--description", description])
    if priority:
        script_args.extend(["--priority", priority])
    if assignee:
        script_args.extend(["--assignee", assignee])
    if labels:
        script_args.extend(["--labels", labels])
    if components:
        script_args.extend(["--components", components])
    if template:
        script_args.extend(["--template", template])
    if custom_fields:
        script_args.extend(["--custom-fields", custom_fields])
    if epic:
        script_args.extend(["--epic", epic])
    if sprint:
        script_args.extend(["--sprint", str(sprint)])
    if story_points:
        script_args.extend(["--story-points", str(story_points)])
    if blocks:
        script_args.extend(["--blocks", blocks])
    if relates_to:
        script_args.extend(["--relates-to", relates_to])
    if estimate:
        script_args.extend(["--estimate", estimate])
    if no_defaults:
        script_args.append("--no-defaults")

    # Use explicit --output if provided, otherwise fall back to global OUTPUT
    output_format = output if output else ctx.obj.get("OUTPUT", "text")
    script_args.extend(["--output", output_format])

    try:
        spec = importlib.util.spec_from_file_location(
            "jira_issue_create_script", str(script_module_path)
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        if hasattr(module, "main") and callable(module.main):
            module.main(script_args)
        else:
            raise ImportError("Callable 'main' function not found in script.")

    except ImportError as e:
        click.echo(
            f"Warning: Falling back to subprocess for {script_module_path.name} ({e})",
            err=True,
        )
        run_skill_script_subprocess(
            script_path=script_module_path, args=script_args, ctx=ctx
        )
    except click.exceptions.Exit:
        raise
    except Exception as e:
        click.echo(f"Error calling create_issue directly: {e}", err=True)
        ctx.exit(1)


@issue.command(name="update")
@click.argument("issue_key")
@click.option("--summary", "-s", help="New summary (title)")
@click.option("--description", "-d", help="New description (supports markdown)")
@click.option("--priority", help="New priority (Highest, High, Medium, Low, Lowest)")
@click.option(
    "--assignee", "-a", help='New assignee (account ID, email, "self", or "none")'
)
@click.option("--labels", "-l", help="Comma-separated labels (replaces existing)")
@click.option(
    "--components", "-c", help="Comma-separated component names (replaces existing)"
)
@click.option("--custom-fields", help="Custom fields as JSON string")
@click.option("--no-notify", is_flag=True, help="Do not send notifications to watchers")
@click.pass_context
def update_issue(
    ctx,
    issue_key: str,
    summary: str,
    description: str,
    priority: str,
    assignee: str,
    labels: str,
    components: str,
    custom_fields: str,
    no_notify: bool,
):
    """Update a JIRA issue."""
    script_module_path = SKILLS_ROOT_DIR / "jira-issue" / "scripts" / "update_issue.py"

    script_args = [issue_key]
    if summary:
        script_args.extend(["--summary", summary])
    if description:
        script_args.extend(["--description", description])
    if priority:
        script_args.extend(["--priority", priority])
    if assignee:
        script_args.extend(["--assignee", assignee])
    if labels:
        script_args.extend(["--labels", labels])
    if components:
        script_args.extend(["--components", components])
    if custom_fields:
        script_args.extend(["--custom-fields", custom_fields])
    if no_notify:
        script_args.append("--no-notify")

    try:
        spec = importlib.util.spec_from_file_location(
            "jira_issue_update_script", str(script_module_path)
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        if hasattr(module, "main") and callable(module.main):
            module.main(script_args)
        else:
            raise ImportError("Callable 'main' function not found in script.")

    except ImportError as e:
        click.echo(
            f"Warning: Falling back to subprocess for {script_module_path.name} ({e})",
            err=True,
        )
        run_skill_script_subprocess(
            script_path=script_module_path, args=script_args, ctx=ctx
        )
    except click.exceptions.Exit:
        raise
    except Exception as e:
        click.echo(f"Error calling update_issue directly: {e}", err=True)
        ctx.exit(1)


@issue.command(name="delete")
@click.argument("issue_key")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete_issue(ctx, issue_key: str, force: bool):
    """Delete a JIRA issue."""
    script_module_path = SKILLS_ROOT_DIR / "jira-issue" / "scripts" / "delete_issue.py"

    script_args = [issue_key]
    if force:
        script_args.append("--force")

    try:
        spec = importlib.util.spec_from_file_location(
            "jira_issue_delete_script", str(script_module_path)
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        if hasattr(module, "main") and callable(module.main):
            module.main(script_args)
        else:
            raise ImportError("Callable 'main' function not found in script.")

    except ImportError as e:
        click.echo(
            f"Warning: Falling back to subprocess for {script_module_path.name} ({e})",
            err=True,
        )
        run_skill_script_subprocess(
            script_path=script_module_path, args=script_args, ctx=ctx
        )
    except click.exceptions.Exit:
        raise
    except Exception as e:
        click.echo(f"Error calling delete_issue directly: {e}", err=True)
        ctx.exit(1)
