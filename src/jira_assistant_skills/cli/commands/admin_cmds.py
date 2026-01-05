"""
JIRA Admin CLI Commands

Provides CLI commands for JIRA administration including:
- Project management
- User and group management
- Permission schemes
- Notification schemes
- Screen management
- Issue types and schemes
- Workflow management
- Automation rules
"""

import importlib.util
import sys

import click

from jira_assistant_skills.utils import SKILLS_ROOT_DIR, run_skill_script_subprocess


def _run_admin_script(ctx, script_name: str, script_args: list):
    """Helper to run an admin script with proper error handling.

    Note: Output format is NOT automatically appended because admin scripts
    have inconsistent format arguments (--output vs --format, 'text' vs 'table').
    Each CLI command should explicitly add output format if needed.
    """
    script_module_path = SKILLS_ROOT_DIR / "jira-admin" / "scripts" / script_name
    module_name = f"jira_admin_{script_name.replace('.py', '')}"

    try:
        spec = importlib.util.spec_from_file_location(
            module_name, str(script_module_path)
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
            f"Warning: Falling back to subprocess for {script_name} ({e})", err=True
        )
        run_skill_script_subprocess(
            script_path=script_module_path, args=script_args, ctx=ctx
        )
    except click.exceptions.Exit:
        raise
    except Exception as e:
        click.echo(f"Error calling {script_name}: {e}", err=True)
        ctx.exit(1)


# =============================================================================
# Main admin group
# =============================================================================


@click.group()
def admin():
    """Commands for JIRA administration (projects, users, permissions, etc.)."""
    pass


# =============================================================================
# Project Management
# =============================================================================


@admin.group(name="project")
def project_group():
    """Project management commands."""
    pass


@project_group.command(name="list")
@click.option("--search", "-s", help="Search projects by name or key")
@click.option(
    "--type",
    "-t",
    "project_type",
    type=click.Choice(["software", "business", "service_desk"]),
    help="Filter by project type",
)
@click.option("--category", "-c", type=int, help="Filter by category ID")
@click.option("--include-archived", is_flag=True, help="Include archived projects")
@click.option("--trash", is_flag=True, help="List projects in trash instead")
@click.option("--expand", "-e", help="Fields to expand (description, lead, issueTypes)")
@click.option("--start-at", type=int, default=0, help="Starting index for pagination")
@click.option("--max-results", type=int, default=50, help="Maximum results per page")
@click.pass_context
def project_list(
    ctx,
    search,
    project_type,
    category,
    include_archived,
    trash,
    expand,
    start_at,
    max_results,
):
    """List and search JIRA projects."""
    args = []
    if search:
        args.extend(["--search", search])
    if project_type:
        args.extend(["--type", project_type])
    if category:
        args.extend(["--category", str(category)])
    if include_archived:
        args.append("--include-archived")
    if trash:
        args.append("--trash")
    if expand:
        args.extend(["--expand", expand])
    if start_at:
        args.extend(["--start-at", str(start_at)])
    if max_results != 50:
        args.extend(["--max-results", str(max_results)])
    _run_admin_script(ctx, "list_projects.py", args)


@project_group.command(name="get")
@click.argument("project_key")
@click.option("--expand", "-e", help="Fields to expand (description, lead, issueTypes)")
@click.pass_context
def project_get(ctx, project_key, expand):
    """Get project details."""
    args = [project_key]
    if expand:
        args.extend(["--expand", expand])
    _run_admin_script(ctx, "get_project.py", args)


@project_group.command(name="create")
@click.option(
    "--key", "-k", required=True, help="Project key (2-10 uppercase letters/numbers)"
)
@click.option("--name", "-n", required=True, help="Project name")
@click.option(
    "--type",
    "-t",
    "project_type",
    required=True,
    type=click.Choice(["software", "business", "service_desk"]),
    help="Project type",
)
@click.option("--template", help="Template (scrum, kanban, basic) or full template key")
@click.option("--lead", "-l", help="Project lead (email or account ID)")
@click.option("--description", "-d", help="Project description")
@click.option("--category", type=int, help="Category ID to assign")
@click.pass_context
def project_create(ctx, key, name, project_type, template, lead, description, category):
    """Create a new JIRA project."""
    args = ["--key", key, "--name", name, "--type", project_type]
    if template:
        args.extend(["--template", template])
    if lead:
        args.extend(["--lead", lead])
    if description:
        args.extend(["--description", description])
    if category:
        args.extend(["--category", str(category)])
    _run_admin_script(ctx, "create_project.py", args)


@project_group.command(name="update")
@click.argument("project_key")
@click.option("--name", "-n", help="New project name")
@click.option("--description", "-d", help="New description")
@click.option("--lead", "-l", help="New project lead")
@click.option("--category", type=int, help="New category ID")
@click.pass_context
def project_update(ctx, project_key, name, description, lead, category):
    """Update a JIRA project."""
    args = [project_key]
    if name:
        args.extend(["--name", name])
    if description:
        args.extend(["--description", description])
    if lead:
        args.extend(["--lead", lead])
    if category:
        args.extend(["--category", str(category)])
    _run_admin_script(ctx, "update_project.py", args)


@project_group.command(name="delete")
@click.argument("project_key")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.option("--dry-run", is_flag=True, help="Preview without executing")
@click.pass_context
def project_delete(ctx, project_key, force, dry_run):
    """Delete a JIRA project."""
    args = [project_key]
    if force:
        args.append("--force")
    if dry_run:
        args.append("--dry-run")
    _run_admin_script(ctx, "delete_project.py", args)


@project_group.command(name="archive")
@click.argument("project_key")
@click.pass_context
def project_archive(ctx, project_key):
    """Archive a JIRA project."""
    _run_admin_script(ctx, "archive_project.py", [project_key])


@project_group.command(name="restore")
@click.argument("project_key")
@click.pass_context
def project_restore(ctx, project_key):
    """Restore an archived or deleted project."""
    _run_admin_script(ctx, "restore_project.py", [project_key])


@admin.group(name="config")
def config_group():
    """Project configuration commands."""
    pass


@config_group.command(name="get")
@click.argument("project_key")
@click.option("--show-schemes", is_flag=True, help="Show assigned schemes")
@click.pass_context
def config_get(ctx, project_key, show_schemes):
    """Get project configuration."""
    args = [project_key]
    if show_schemes:
        args.append("--show-schemes")
    _run_admin_script(ctx, "get_config.py", args)


# =============================================================================
# Category Management
# =============================================================================


@admin.group(name="category")
def category_group():
    """Project category commands."""
    pass


@category_group.command(name="list")
@click.pass_context
def category_list(ctx):
    """List project categories."""
    _run_admin_script(ctx, "list_categories.py", [])


@category_group.command(name="create")
@click.option("--name", "-n", required=True, help="Category name")
@click.option("--description", "-d", help="Category description")
@click.pass_context
def category_create(ctx, name, description):
    """Create a project category."""
    args = ["--name", name]
    if description:
        args.extend(["--description", description])
    _run_admin_script(ctx, "create_category.py", args)


@category_group.command(name="assign")
@click.argument("project_key")
@click.option("--category-id", "-c", type=int, required=True, help="Category ID")
@click.pass_context
def category_assign(ctx, project_key, category_id):
    """Assign a category to a project."""
    _run_admin_script(
        ctx, "assign_category.py", [project_key, "--category-id", str(category_id)]
    )


# =============================================================================
# User Management
# =============================================================================


@admin.group(name="user")
def user_group():
    """User management commands."""
    pass


@user_group.command(name="search")
@click.option("--query", "-q", help="Search query (name, email, username)")
@click.option("--me", is_flag=True, help="Get current user info")
@click.option("--include-groups", is_flag=True, help="Include group memberships")
@click.option("--max-results", type=int, default=50, help="Maximum results")
@click.pass_context
def user_search(ctx, query, me, include_groups, max_results):
    """Search for users."""
    args = []
    if query:
        args.extend(["--query", query])
    if me:
        args.append("--me")
    if include_groups:
        args.append("--include-groups")
    if max_results != 50:
        args.extend(["--max-results", str(max_results)])
    _run_admin_script(ctx, "search_users.py", args)


@user_group.command(name="get")
@click.argument("account_id")
@click.pass_context
def user_get(ctx, account_id):
    """Get user details by account ID."""
    _run_admin_script(ctx, "get_user.py", [account_id])


# =============================================================================
# Group Management
# =============================================================================


@admin.group(name="group")
def group_group():
    """Group management commands."""
    pass


@group_group.command(name="list")
@click.option("--query", "-q", help="Filter groups by name")
@click.pass_context
def group_list(ctx, query):
    """List all groups."""
    args = []
    if query:
        args.extend(["--query", query])
    _run_admin_script(ctx, "list_groups.py", args)


@group_group.command(name="members")
@click.argument("group_name")
@click.option("--max-results", type=int, default=50, help="Maximum results")
@click.pass_context
def group_members(ctx, group_name, max_results):
    """Get members of a group."""
    args = [group_name]
    if max_results != 50:
        args.extend(["--max-results", str(max_results)])
    _run_admin_script(ctx, "get_group_members.py", args)


@group_group.command(name="create")
@click.argument("group_name")
@click.pass_context
def group_create(ctx, group_name):
    """Create a new group."""
    _run_admin_script(ctx, "create_group.py", [group_name])


@group_group.command(name="delete")
@click.argument("group_name")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def group_delete(ctx, group_name, force):
    """Delete a group."""
    args = [group_name]
    if force:
        args.append("--force")
    _run_admin_script(ctx, "delete_group.py", args)


@group_group.command(name="add-user")
@click.argument("group_name")
@click.option("--user", "-u", required=True, help="User account ID or email")
@click.pass_context
def group_add_user(ctx, group_name, user):
    """Add a user to a group."""
    _run_admin_script(ctx, "add_user_to_group.py", [group_name, "--user", user])


@group_group.command(name="remove-user")
@click.argument("group_name")
@click.option("--user", "-u", required=True, help="User account ID or email")
@click.pass_context
def group_remove_user(ctx, group_name, user):
    """Remove a user from a group."""
    _run_admin_script(ctx, "remove_user_from_group.py", [group_name, "--user", user])


# =============================================================================
# Automation Rules
# =============================================================================


@admin.group(name="automation")
def automation_group():
    """Automation rule commands."""
    pass


@automation_group.command(name="list")
@click.option("--project", "-p", help="Filter by project key")
@click.option("--enabled-only", is_flag=True, help="Show only enabled rules")
@click.pass_context
def automation_list(ctx, project, enabled_only):
    """List automation rules."""
    args = []
    if project:
        args.extend(["--project", project])
    if enabled_only:
        args.append("--enabled-only")
    _run_admin_script(ctx, "list_automation_rules.py", args)


@automation_group.command(name="get")
@click.argument("rule_id")
@click.pass_context
def automation_get(ctx, rule_id):
    """Get automation rule details."""
    _run_admin_script(ctx, "get_automation_rule.py", [rule_id])


@automation_group.command(name="search")
@click.option("--query", "-q", required=True, help="Search query")
@click.option("--project", "-p", help="Filter by project")
@click.pass_context
def automation_search(ctx, query, project):
    """Search automation rules."""
    args = ["--query", query]
    if project:
        args.extend(["--project", project])
    _run_admin_script(ctx, "search_automation_rules.py", args)


@automation_group.command(name="enable")
@click.argument("rule_id")
@click.pass_context
def automation_enable(ctx, rule_id):
    """Enable an automation rule."""
    _run_admin_script(ctx, "enable_automation_rule.py", [rule_id])


@automation_group.command(name="disable")
@click.argument("rule_id")
@click.pass_context
def automation_disable(ctx, rule_id):
    """Disable an automation rule."""
    _run_admin_script(ctx, "disable_automation_rule.py", [rule_id])


@automation_group.command(name="toggle")
@click.argument("rule_id")
@click.pass_context
def automation_toggle(ctx, rule_id):
    """Toggle an automation rule's enabled state."""
    _run_admin_script(ctx, "toggle_automation_rule.py", [rule_id])


@automation_group.command(name="invoke")
@click.argument("rule_id")
@click.option("--issue", "-i", help="Issue key to run rule against")
@click.pass_context
def automation_invoke(ctx, rule_id, issue):
    """Invoke a manual automation rule."""
    args = [rule_id]
    if issue:
        args.extend(["--issue", issue])
    _run_admin_script(ctx, "invoke_manual_rule.py", args)


@admin.group(name="automation-template")
def automation_template_group():
    """Automation rule template commands."""
    pass


@automation_template_group.command(name="list")
@click.pass_context
def automation_template_list(ctx):
    """List available automation templates."""
    _run_admin_script(ctx, "list_automation_templates.py", [])


@automation_template_group.command(name="get")
@click.argument("template_id")
@click.pass_context
def automation_template_get(ctx, template_id):
    """Get automation template details."""
    _run_admin_script(ctx, "get_automation_template.py", [template_id])


# =============================================================================
# Permission Schemes
# =============================================================================


@admin.group(name="permission-scheme")
def permission_scheme_group():
    """Permission scheme commands."""
    pass


@permission_scheme_group.command(name="list")
@click.pass_context
def permission_scheme_list(ctx):
    """List permission schemes."""
    _run_admin_script(ctx, "list_permission_schemes.py", [])


@permission_scheme_group.command(name="get")
@click.argument("scheme_id")
@click.option("--show-projects", is_flag=True, help="Show projects using this scheme")
@click.pass_context
def permission_scheme_get(ctx, scheme_id, show_projects):
    """Get permission scheme details."""
    args = [scheme_id]
    if show_projects:
        args.append("--show-projects")
    _run_admin_script(ctx, "get_permission_scheme.py", args)


@permission_scheme_group.command(name="create")
@click.option("--name", "-n", required=True, help="Scheme name")
@click.option("--description", "-d", help="Scheme description")
@click.pass_context
def permission_scheme_create(ctx, name, description):
    """Create a permission scheme."""
    args = ["--name", name]
    if description:
        args.extend(["--description", description])
    _run_admin_script(ctx, "create_permission_scheme.py", args)


@permission_scheme_group.command(name="assign")
@click.option("--project", "-p", required=True, help="Project key")
@click.option("--scheme", "-s", required=True, help="Scheme ID")
@click.option("--dry-run", is_flag=True, help="Preview without executing")
@click.pass_context
def permission_scheme_assign(ctx, project, scheme, dry_run):
    """Assign a permission scheme to a project."""
    args = ["--project", project, "--scheme", scheme]
    if dry_run:
        args.append("--dry-run")
    _run_admin_script(ctx, "assign_permission_scheme.py", args)


@admin.group(name="permission")
def permission_group():
    """Permission commands."""
    pass


@permission_group.command(name="list")
@click.pass_context
def permission_list(ctx):
    """List available permissions."""
    _run_admin_script(ctx, "list_permissions.py", [])


# =============================================================================
# Notification Schemes
# =============================================================================


@admin.group(name="notification-scheme")
def notification_scheme_group():
    """Notification scheme commands."""
    pass


@notification_scheme_group.command(name="list")
@click.pass_context
def notification_scheme_list(ctx):
    """List notification schemes."""
    _run_admin_script(ctx, "list_notification_schemes.py", [])


@notification_scheme_group.command(name="get")
@click.argument("scheme_id")
@click.pass_context
def notification_scheme_get(ctx, scheme_id):
    """Get notification scheme details."""
    _run_admin_script(ctx, "get_notification_scheme.py", [scheme_id])


@notification_scheme_group.command(name="create")
@click.option("--name", "-n", required=True, help="Scheme name")
@click.option("--description", "-d", help="Scheme description")
@click.pass_context
def notification_scheme_create(ctx, name, description):
    """Create a notification scheme."""
    args = ["--name", name]
    if description:
        args.extend(["--description", description])
    _run_admin_script(ctx, "create_notification_scheme.py", args)


@admin.group(name="notification")
def notification_group():
    """Notification commands."""
    pass


@notification_group.command(name="add")
@click.option("--scheme", "-s", required=True, help="Scheme ID")
@click.option("--event", "-e", required=True, help="Event type")
@click.option("--recipient", "-r", required=True, help="Recipient type")
@click.pass_context
def notification_add(ctx, scheme, event, recipient):
    """Add a notification to a scheme."""
    _run_admin_script(
        ctx,
        "add_notification.py",
        ["--scheme", scheme, "--event", event, "--recipient", recipient],
    )


@notification_group.command(name="remove")
@click.option("--scheme", "-s", required=True, help="Scheme ID")
@click.option("--notification-id", "-n", required=True, help="Notification ID")
@click.pass_context
def notification_remove(ctx, scheme, notification_id):
    """Remove a notification from a scheme."""
    _run_admin_script(
        ctx,
        "remove_notification.py",
        ["--scheme", scheme, "--notification-id", notification_id],
    )


# =============================================================================
# Screen Management
# =============================================================================


@admin.group(name="screen")
def screen_group():
    """Screen management commands."""
    pass


@screen_group.command(name="list")
@click.pass_context
def screen_list(ctx):
    """List screens."""
    _run_admin_script(ctx, "list_screens.py", [])


@screen_group.command(name="get")
@click.argument("screen_id")
@click.pass_context
def screen_get(ctx, screen_id):
    """Get screen details."""
    _run_admin_script(ctx, "get_screen.py", [screen_id])


@screen_group.command(name="tabs")
@click.argument("screen_id")
@click.pass_context
def screen_tabs(ctx, screen_id):
    """List screen tabs."""
    _run_admin_script(ctx, "list_screen_tabs.py", [screen_id])


@screen_group.command(name="fields")
@click.argument("screen_id")
@click.option("--tab", "-t", help="Tab ID (optional)")
@click.pass_context
def screen_fields(ctx, screen_id, tab):
    """Get fields on a screen."""
    args = [screen_id]
    if tab:
        args.extend(["--tab", tab])
    _run_admin_script(ctx, "get_screen_fields.py", args)


@screen_group.command(name="add-field")
@click.argument("screen_id")
@click.option("--field", "-f", required=True, help="Field ID")
@click.option("--tab", "-t", help="Tab ID")
@click.pass_context
def screen_add_field(ctx, screen_id, field, tab):
    """Add a field to a screen."""
    args = [screen_id, "--field", field]
    if tab:
        args.extend(["--tab", tab])
    _run_admin_script(ctx, "add_field_to_screen.py", args)


@screen_group.command(name="remove-field")
@click.argument("screen_id")
@click.option("--field", "-f", required=True, help="Field ID")
@click.option("--tab", "-t", help="Tab ID")
@click.pass_context
def screen_remove_field(ctx, screen_id, field, tab):
    """Remove a field from a screen."""
    args = [screen_id, "--field", field]
    if tab:
        args.extend(["--tab", tab])
    _run_admin_script(ctx, "remove_field_from_screen.py", args)


@admin.group(name="screen-scheme")
def screen_scheme_group():
    """Screen scheme commands."""
    pass


@screen_scheme_group.command(name="list")
@click.pass_context
def screen_scheme_list(ctx):
    """List screen schemes."""
    _run_admin_script(ctx, "list_screen_schemes.py", [])


@screen_scheme_group.command(name="get")
@click.argument("scheme_id")
@click.pass_context
def screen_scheme_get(ctx, scheme_id):
    """Get screen scheme details."""
    _run_admin_script(ctx, "get_screen_scheme.py", [scheme_id])


# =============================================================================
# Issue Types
# =============================================================================


@admin.group(name="issue-type")
def issue_type_group():
    """Issue type commands."""
    pass


@issue_type_group.command(name="list")
@click.pass_context
def issue_type_list(ctx):
    """List issue types."""
    _run_admin_script(ctx, "list_issue_types.py", [])


@issue_type_group.command(name="get")
@click.argument("issue_type_id")
@click.pass_context
def issue_type_get(ctx, issue_type_id):
    """Get issue type details."""
    _run_admin_script(ctx, "get_issue_type.py", [issue_type_id])


@issue_type_group.command(name="create")
@click.option("--name", "-n", required=True, help="Issue type name")
@click.option("--description", "-d", help="Description")
@click.option(
    "--type",
    "-t",
    type=click.Choice(["standard", "subtask"]),
    default="standard",
    help="Issue type category",
)
@click.pass_context
def issue_type_create(ctx, name, description, type):
    """Create an issue type."""
    args = ["--name", name, "--type", type]
    if description:
        args.extend(["--description", description])
    _run_admin_script(ctx, "create_issue_type.py", args)


@issue_type_group.command(name="update")
@click.argument("issue_type_id")
@click.option("--name", "-n", help="New name")
@click.option("--description", "-d", help="New description")
@click.pass_context
def issue_type_update(ctx, issue_type_id, name, description):
    """Update an issue type."""
    args = [issue_type_id]
    if name:
        args.extend(["--name", name])
    if description:
        args.extend(["--description", description])
    _run_admin_script(ctx, "update_issue_type.py", args)


@issue_type_group.command(name="delete")
@click.argument("issue_type_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def issue_type_delete(ctx, issue_type_id, force):
    """Delete an issue type."""
    args = [issue_type_id]
    if force:
        args.append("--force")
    _run_admin_script(ctx, "delete_issue_type.py", args)


# =============================================================================
# Issue Type Schemes
# =============================================================================


@admin.group(name="issue-type-scheme")
def issue_type_scheme_group():
    """Issue type scheme commands."""
    pass


@issue_type_scheme_group.command(name="list")
@click.pass_context
def issue_type_scheme_list(ctx):
    """List issue type schemes."""
    _run_admin_script(ctx, "list_issue_type_schemes.py", [])


@issue_type_scheme_group.command(name="get")
@click.argument("scheme_id")
@click.pass_context
def issue_type_scheme_get(ctx, scheme_id):
    """Get issue type scheme details."""
    _run_admin_script(ctx, "get_issue_type_scheme.py", [scheme_id])


@issue_type_scheme_group.command(name="create")
@click.option("--name", "-n", required=True, help="Scheme name")
@click.option("--description", "-d", help="Description")
@click.pass_context
def issue_type_scheme_create(ctx, name, description):
    """Create an issue type scheme."""
    args = ["--name", name]
    if description:
        args.extend(["--description", description])
    _run_admin_script(ctx, "create_issue_type_scheme.py", args)


@issue_type_scheme_group.command(name="assign")
@click.option("--project", "-p", required=True, help="Project key")
@click.option("--scheme", "-s", required=True, help="Scheme ID")
@click.pass_context
def issue_type_scheme_assign(ctx, project, scheme):
    """Assign an issue type scheme to a project."""
    _run_admin_script(
        ctx, "assign_issue_type_scheme.py", ["--project", project, "--scheme", scheme]
    )


@issue_type_scheme_group.command(name="project")
@click.option("--project-id", "-p", required=True, help="Project ID")
@click.pass_context
def issue_type_scheme_project(ctx, project_id):
    """Get the issue type scheme for a project."""
    _run_admin_script(
        ctx, "get_project_issue_type_scheme.py", ["--project-id", project_id]
    )


# =============================================================================
# Workflows
# =============================================================================


@admin.group(name="workflow")
def workflow_group():
    """Workflow commands."""
    pass


@workflow_group.command(name="list")
@click.pass_context
def workflow_list(ctx):
    """List workflows."""
    _run_admin_script(ctx, "list_workflows.py", [])


@workflow_group.command(name="get")
@click.option("--name", "-n", required=True, help="Workflow name")
@click.pass_context
def workflow_get(ctx, name):
    """Get workflow details."""
    _run_admin_script(ctx, "get_workflow.py", ["--name", name])


@workflow_group.command(name="search")
@click.option("--query", "-q", required=True, help="Search query")
@click.pass_context
def workflow_search(ctx, query):
    """Search workflows."""
    _run_admin_script(ctx, "search_workflows.py", ["--query", query])


@workflow_group.command(name="for-issue")
@click.argument("issue_key")
@click.pass_context
def workflow_for_issue(ctx, issue_key):
    """Get the workflow for an issue."""
    _run_admin_script(ctx, "get_workflow_for_issue.py", [issue_key])


@admin.group(name="workflow-scheme")
def workflow_scheme_group():
    """Workflow scheme commands."""
    pass


@workflow_scheme_group.command(name="list")
@click.pass_context
def workflow_scheme_list(ctx):
    """List workflow schemes."""
    _run_admin_script(ctx, "list_workflow_schemes.py", [])


@workflow_scheme_group.command(name="get")
@click.option("--id", "scheme_id", required=True, help="Scheme ID")
@click.option("--show-projects", is_flag=True, help="Show projects using this scheme")
@click.pass_context
def workflow_scheme_get(ctx, scheme_id, show_projects):
    """Get workflow scheme details."""
    args = ["--id", scheme_id]
    if show_projects:
        args.append("--show-projects")
    _run_admin_script(ctx, "get_workflow_scheme.py", args)


@workflow_scheme_group.command(name="assign")
@click.option("--project", "-p", required=True, help="Project key")
@click.option("--scheme", "-s", required=True, help="Scheme ID")
@click.pass_context
def workflow_scheme_assign(ctx, project, scheme):
    """Assign a workflow scheme to a project."""
    _run_admin_script(
        ctx, "assign_workflow_scheme.py", ["--project", project, "--scheme", scheme]
    )


@admin.group(name="status")
def status_group():
    """Status commands."""
    pass


@status_group.command(name="list")
@click.pass_context
def status_list(ctx):
    """List all statuses."""
    _run_admin_script(ctx, "list_statuses.py", [])
