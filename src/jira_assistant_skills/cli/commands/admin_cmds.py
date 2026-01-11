"""JIRA Admin CLI Commands.

Provides CLI commands for JIRA administration including:
- Project management (create, update, delete, archive, restore)
- User and group management
- Permission schemes
- Notification schemes
- Screen management
- Issue types and schemes
- Workflow management
- Automation rules
"""

from typing import Any

import click

from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    format_json,
    format_table,
    get_automation_client,
    get_jira_client,
    validate_project_key,
    validate_project_name,
    validate_project_template,
    validate_project_type,
)

from ..cli_utils import handle_jira_errors

# =============================================================================
# Helper Functions
# =============================================================================


def _parse_comma_list(value: str | None) -> list[str] | None:
    """Parse comma-separated values into a list."""
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


# Known system groups for highlighting
SYSTEM_GROUPS = [
    "jira-administrators",
    "jira-users",
    "jira-software-users",
    "site-admins",
    "atlassian-addons-admin",
]


def _is_system_group(group_name: str) -> bool:
    """Check if a group is a system/built-in group."""
    return group_name in SYSTEM_GROUPS


# =============================================================================
# Project Implementation Functions
# =============================================================================


def _list_projects_impl(
    query: str | None = None,
    project_type: str | None = None,
    category_id: int | None = None,
    include_archived: bool = False,
    expand: list[str] | None = None,
    start_at: int = 0,
    max_results: int = 50,
) -> dict[str, Any]:
    """List and search projects."""
    client = get_jira_client()
    try:
        status = ["live"]
        if include_archived:
            status.append("archived")

        result = client.search_projects(
            query=query,
            type_key=project_type,
            category_id=category_id,
            status=status,
            expand=expand,
            start_at=start_at,
            max_results=max_results,
        )
        return result
    finally:
        client.close()


def _list_trash_projects_impl(
    start_at: int = 0, max_results: int = 50
) -> dict[str, Any]:
    """List projects in trash."""
    client = get_jira_client()
    try:
        result = client.search_projects(
            status=["deleted"], start_at=start_at, max_results=max_results
        )
        return result
    finally:
        client.close()


def _get_project_impl(
    project_key: str, expand: list[str] | None = None
) -> dict[str, Any]:
    """Get project details."""
    client = get_jira_client()
    try:
        return client.get_project(project_key, expand=expand)
    finally:
        client.close()


def _create_project_impl(
    key: str,
    name: str,
    project_type: str,
    template: str | None = None,
    lead: str | None = None,
    description: str | None = None,
    category_id: int | None = None,
) -> dict[str, Any]:
    """Create a new JIRA project."""
    key = validate_project_key(key)
    name = validate_project_name(name)
    project_type = validate_project_type(project_type)

    template_key = None
    if template:
        template_key = validate_project_template(template)
    else:
        default_templates = {
            "software": "com.pyxis.greenhopper.jira:gh-simplified-agility-scrum",
            "business": "com.atlassian.jira-core-project-templates:jira-core-project-management",
            "service_desk": "com.atlassian.servicedesk:simplified-it-service-desk",
        }
        template_key = default_templates.get(project_type)

    client = get_jira_client()
    try:
        lead_account_id = None
        if lead:
            if "@" in lead:
                users = client.search_users(lead, max_results=1)
                if users:
                    lead_account_id = users[0].get("accountId")
                else:
                    raise ValidationError(f"User not found: {lead}")
            else:
                lead_account_id = lead

        result = client.create_project(
            key=key,
            name=name,
            project_type_key=project_type,
            template_key=template_key,
            lead_account_id=lead_account_id,
            description=description,
        )

        if category_id:
            try:
                client.update_project(key, category_id=category_id)
            except JiraError:
                pass

        return result
    finally:
        client.close()


def _update_project_impl(
    project_key: str,
    name: str | None = None,
    description: str | None = None,
    lead: str | None = None,
    category_id: int | None = None,
) -> dict[str, Any]:
    """Update a JIRA project."""
    client = get_jira_client()
    try:
        lead_account_id = None
        if lead:
            if "@" in lead:
                users = client.search_users(lead, max_results=1)
                if users:
                    lead_account_id = users[0].get("accountId")
                else:
                    raise ValidationError(f"User not found: {lead}")
            else:
                lead_account_id = lead

        return client.update_project(
            project_key,
            name=name,
            description=description,
            lead_account_id=lead_account_id,
            category_id=category_id,
        )
    finally:
        client.close()


def _delete_project_impl(project_key: str, dry_run: bool = False) -> dict[str, Any]:
    """Delete a JIRA project."""
    client = get_jira_client()
    try:
        project = client.get_project(project_key)
        if dry_run:
            return {"action": "dry_run", "project": project, "would_delete": True}

        client.delete_project(project_key)
        return {"action": "deleted", "project": project}
    finally:
        client.close()


def _archive_project_impl(project_key: str) -> dict[str, Any]:
    """Archive a JIRA project."""
    client = get_jira_client()
    try:
        client.archive_project(project_key)
        return {"action": "archived", "project_key": project_key}
    finally:
        client.close()


def _restore_project_impl(project_key: str) -> dict[str, Any]:
    """Restore an archived or deleted project."""
    client = get_jira_client()
    try:
        client.restore_project(project_key)
        return {"action": "restored", "project_key": project_key}
    finally:
        client.close()


def _get_project_config_impl(
    project_key: str, show_schemes: bool = False
) -> dict[str, Any]:
    """Get project configuration."""
    client = get_jira_client()
    try:
        project = client.get_project(project_key, expand="description,lead,issueTypes")
        config = {"project": project}

        if show_schemes:
            config["schemes"] = {}
            try:
                config["schemes"]["permission"] = client.get_project_permission_scheme(
                    project_key
                )
            except JiraError:
                config["schemes"]["permission"] = None
            try:
                config["schemes"]["notification"] = (
                    client.get_project_notification_scheme(project_key)
                )
            except JiraError:
                config["schemes"]["notification"] = None

        return config
    finally:
        client.close()


# =============================================================================
# Category Implementation Functions
# =============================================================================


def _list_categories_impl() -> list[dict[str, Any]]:
    """List project categories."""
    client = get_jira_client()
    try:
        return client.get_project_categories()
    finally:
        client.close()


def _create_category_impl(name: str, description: str | None = None) -> dict[str, Any]:
    """Create a project category."""
    client = get_jira_client()
    try:
        return client.create_project_category(name=name, description=description)
    finally:
        client.close()


def _assign_category_impl(project_key: str, category_id: int) -> dict[str, Any]:
    """Assign a category to a project."""
    client = get_jira_client()
    try:
        return client.update_project(project_key, category_id=category_id)
    finally:
        client.close()


# =============================================================================
# User Implementation Functions
# =============================================================================


def _search_users_impl(
    query: str,
    start_at: int = 0,
    max_results: int = 50,
    active_only: bool = True,
    include_groups: bool = False,
    project: str | None = None,
    assignable: bool = False,
) -> list[dict[str, Any]]:
    """Search for users."""
    client = get_jira_client()
    try:
        if assignable and project:
            users = client.find_assignable_users(
                query=query,
                project_key=project,
                start_at=start_at,
                max_results=max_results,
            )
        else:
            users = client.search_users(
                query=query, max_results=max_results, start_at=start_at
            )
            if active_only:
                users = [u for u in users if u.get("active", True)]

        if include_groups:
            for user in users:
                try:
                    groups = client.get_user_groups(user["accountId"])
                    user["groups"] = [g["name"] for g in groups]
                except Exception:
                    user["groups"] = []

        return users
    finally:
        client.close()


def _get_user_impl(account_id: str) -> dict[str, Any]:
    """Get user details."""
    client = get_jira_client()
    try:
        return client.get_user(account_id)
    finally:
        client.close()


# =============================================================================
# Group Implementation Functions
# =============================================================================


def _list_groups_impl(
    query: str | None = None,
    max_results: int = 50,
    include_members: bool = False,
) -> list[dict[str, Any]]:
    """List all groups."""
    client = get_jira_client()
    try:
        result = client.find_groups(
            query=query or "", max_results=max_results, caseInsensitive=True
        )
        groups = result.get("groups", [])

        if include_members:
            for group in groups:
                try:
                    members_result = client.get_group_members(
                        group_name=group["name"], max_results=1
                    )
                    group["memberCount"] = members_result.get("total", 0)
                except Exception:
                    group["memberCount"] = "N/A"

        return groups
    finally:
        client.close()


def _get_group_members_impl(group_name: str, max_results: int = 50) -> dict[str, Any]:
    """Get members of a group."""
    client = get_jira_client()
    try:
        return client.get_group_members(group_name=group_name, max_results=max_results)
    finally:
        client.close()


def _create_group_impl(group_name: str) -> dict[str, Any]:
    """Create a new group."""
    client = get_jira_client()
    try:
        return client.create_group(group_name)
    finally:
        client.close()


def _delete_group_impl(group_name: str, dry_run: bool = False) -> dict[str, Any]:
    """Delete a group."""
    client = get_jira_client()
    try:
        if dry_run:
            return {"action": "dry_run", "group_name": group_name, "would_delete": True}

        client.delete_group(group_name)
        return {"action": "deleted", "group_name": group_name}
    finally:
        client.close()


def _add_user_to_group_impl(group_name: str, user: str) -> dict[str, Any]:
    """Add a user to a group."""
    client = get_jira_client()
    try:
        account_id = user
        if "@" in user:
            users = client.search_users(user, max_results=1)
            if users:
                account_id = users[0].get("accountId")
            else:
                raise ValidationError(f"User not found: {user}")

        client.add_user_to_group(group_name=group_name, account_id=account_id)
        return {"action": "added", "group_name": group_name, "account_id": account_id}
    finally:
        client.close()


def _remove_user_from_group_impl(group_name: str, user: str) -> dict[str, Any]:
    """Remove a user from a group."""
    client = get_jira_client()
    try:
        account_id = user
        if "@" in user:
            users = client.search_users(user, max_results=1)
            if users:
                account_id = users[0].get("accountId")
            else:
                raise ValidationError(f"User not found: {user}")

        client.remove_user_from_group(group_name=group_name, account_id=account_id)
        return {"action": "removed", "group_name": group_name, "account_id": account_id}
    finally:
        client.close()


# =============================================================================
# Automation Implementation Functions
# =============================================================================


def _list_automation_rules_impl(
    project: str | None = None,
    state: str | None = None,
    limit: int = 50,
    fetch_all: bool = False,
) -> list[dict[str, Any]]:
    """List automation rules."""
    client = get_automation_client()
    all_rules = []
    cursor = None
    use_search = project is not None or state is not None

    while True:
        if use_search:
            scope = None
            if project:
                scope = (
                    f"ari:cloud:jira:*:project/{project}"
                    if not project.startswith("ari:")
                    else project
                )

            response = client.search_rules(
                state=state.upper() if state else None,
                scope=scope,
                limit=limit,
                cursor=cursor,
            )
        else:
            response = client.get_rules(limit=limit, cursor=cursor)

        rules = response.get("values", [])
        all_rules.extend(rules)

        if not fetch_all or not response.get("hasMore", False):
            break

        links = response.get("links", {})
        next_link = links.get("next", "")
        if "?cursor=" in next_link:
            cursor = next_link.split("?cursor=")[-1]
        else:
            break

    return all_rules


def _get_automation_rule_impl(rule_id: str) -> dict[str, Any]:
    """Get automation rule details."""
    client = get_automation_client()
    return client.get_rule(rule_id)


def _search_automation_rules_impl(
    query: str, project: str | None = None
) -> list[dict[str, Any]]:
    """Search automation rules."""
    rules = _list_automation_rules_impl(project=project, fetch_all=True)
    query_lower = query.lower()
    return [r for r in rules if query_lower in r.get("name", "").lower()]


def _enable_automation_rule_impl(rule_id: str) -> dict[str, Any]:
    """Enable an automation rule."""
    client = get_automation_client()
    return client.enable_rule(rule_id)


def _disable_automation_rule_impl(rule_id: str) -> dict[str, Any]:
    """Disable an automation rule."""
    client = get_automation_client()
    return client.disable_rule(rule_id)


def _toggle_automation_rule_impl(rule_id: str) -> dict[str, Any]:
    """Toggle an automation rule's state."""
    client = get_automation_client()
    rule = client.get_rule(rule_id)
    current_state = rule.get("state", "").upper()
    if current_state == "ENABLED":
        return client.disable_rule(rule_id)
    else:
        return client.enable_rule(rule_id)


def _invoke_manual_rule_impl(
    rule_id: str, issue_key: str | None = None
) -> dict[str, Any]:
    """Invoke a manual automation rule."""
    client = get_automation_client()
    return client.invoke_rule(rule_id, issue_key=issue_key)


def _list_automation_templates_impl() -> list[dict[str, Any]]:
    """List automation templates."""
    client = get_automation_client()
    return client.get_templates()


def _get_automation_template_impl(template_id: str) -> dict[str, Any]:
    """Get automation template details."""
    client = get_automation_client()
    return client.get_template(template_id)


# =============================================================================
# Permission Scheme Implementation Functions
# =============================================================================


def _list_permission_schemes_impl(
    name_filter: str | None = None, show_grants: bool = False
) -> list[dict[str, Any]]:
    """List permission schemes."""
    client = get_jira_client()
    try:
        expand = "permissions" if show_grants else None
        response = client.get_permission_schemes(expand=expand)
        schemes = response.get("permissionSchemes", [])

        if name_filter:
            filter_lower = name_filter.lower()
            schemes = [s for s in schemes if filter_lower in s.get("name", "").lower()]

        return schemes
    finally:
        client.close()


def _get_permission_scheme_impl(
    scheme_id: str, show_projects: bool = False
) -> dict[str, Any]:
    """Get permission scheme details."""
    client = get_jira_client()
    try:
        scheme = client.get_permission_scheme(scheme_id, expand="permissions")
        result = {"scheme": scheme}

        if show_projects:
            projects = client.get_projects_for_permission_scheme(scheme_id)
            result["projects"] = projects

        return result
    finally:
        client.close()


def _create_permission_scheme_impl(
    name: str, description: str | None = None
) -> dict[str, Any]:
    """Create a permission scheme."""
    client = get_jira_client()
    try:
        return client.create_permission_scheme(name=name, description=description)
    finally:
        client.close()


def _assign_permission_scheme_impl(
    project_key: str, scheme_id: str, dry_run: bool = False
) -> dict[str, Any]:
    """Assign a permission scheme to a project."""
    client = get_jira_client()
    try:
        if dry_run:
            scheme = client.get_permission_scheme(scheme_id)
            project = client.get_project(project_key)
            return {
                "action": "dry_run",
                "project": project,
                "scheme": scheme,
                "would_assign": True,
            }

        result = client.assign_permission_scheme(project_key, scheme_id)
        return {
            "action": "assigned",
            "project_key": project_key,
            "scheme_id": scheme_id,
            "result": result,
        }
    finally:
        client.close()


def _list_permissions_impl() -> list[dict[str, Any]]:
    """List available permissions."""
    client = get_jira_client()
    try:
        response = client.get_all_permissions()
        return response.get("permissions", {})
    finally:
        client.close()


# =============================================================================
# Notification Scheme Implementation Functions
# =============================================================================


def _list_notification_schemes_impl() -> list[dict[str, Any]]:
    """List notification schemes."""
    client = get_jira_client()
    try:
        response = client.get_notification_schemes()
        return response.get("values", [])
    finally:
        client.close()


def _get_notification_scheme_impl(scheme_id: str) -> dict[str, Any]:
    """Get notification scheme details."""
    client = get_jira_client()
    try:
        return client.get_notification_scheme(scheme_id, expand="all")
    finally:
        client.close()


def _create_notification_scheme_impl(
    name: str, description: str | None = None
) -> dict[str, Any]:
    """Create a notification scheme."""
    client = get_jira_client()
    try:
        return client.create_notification_scheme(name=name, description=description)
    finally:
        client.close()


def _add_notification_impl(
    scheme_id: str, event: str, recipient: str
) -> dict[str, Any]:
    """Add a notification to a scheme."""
    client = get_jira_client()
    try:
        return client.add_notification(
            scheme_id, event_type=event, notification_type=recipient
        )
    finally:
        client.close()


def _remove_notification_impl(scheme_id: str, notification_id: str) -> dict[str, Any]:
    """Remove a notification from a scheme."""
    client = get_jira_client()
    try:
        client.remove_notification(scheme_id, notification_id)
        return {
            "action": "removed",
            "scheme_id": scheme_id,
            "notification_id": notification_id,
        }
    finally:
        client.close()


# =============================================================================
# Screen Implementation Functions
# =============================================================================


def _list_screens_impl(
    filter_pattern: str | None = None,
    scope: list[str] | None = None,
    fetch_all: bool = False,
    max_results: int = 100,
) -> list[dict[str, Any]]:
    """List all screens."""
    client = get_jira_client()
    try:
        screens = []
        start_at = 0

        while True:
            result = client.get_screens(
                start_at=start_at,
                max_results=max_results,
                scope=scope,
                query_string=filter_pattern,
            )

            page_screens = result.get("values", [])
            screens.extend(page_screens)

            if not fetch_all or result.get("isLast", True):
                break

            total = result.get("total", 0)
            if start_at + len(page_screens) >= total:
                break

            start_at += len(page_screens)

        if filter_pattern:
            screens = [
                s
                for s in screens
                if filter_pattern.lower() in s.get("name", "").lower()
            ]

        return screens
    finally:
        client.close()


def _get_screen_impl(screen_id: str) -> dict[str, Any]:
    """Get screen details."""
    client = get_jira_client()
    try:
        return client.get_screen(screen_id)
    finally:
        client.close()


def _list_screen_tabs_impl(screen_id: str) -> list[dict[str, Any]]:
    """List screen tabs."""
    client = get_jira_client()
    try:
        return client.get_screen_tabs(screen_id)
    finally:
        client.close()


def _get_screen_fields_impl(
    screen_id: str, tab_id: str | None = None
) -> list[dict[str, Any]]:
    """Get fields on a screen."""
    client = get_jira_client()
    try:
        if tab_id:
            return client.get_screen_tab_fields(screen_id, tab_id)
        else:
            tabs = client.get_screen_tabs(screen_id)
            all_fields = []
            for tab in tabs:
                fields = client.get_screen_tab_fields(screen_id, tab["id"])
                for field in fields:
                    field["tab"] = tab["name"]
                all_fields.extend(fields)
            return all_fields
    finally:
        client.close()


def _add_field_to_screen_impl(
    screen_id: str, field_id: str, tab_id: str | None = None
) -> dict[str, Any]:
    """Add a field to a screen."""
    client = get_jira_client()
    try:
        if not tab_id:
            tabs = client.get_screen_tabs(screen_id)
            if tabs:
                tab_id = tabs[0]["id"]
            else:
                raise ValidationError("No tabs found on screen")

        return client.add_field_to_screen_tab(screen_id, tab_id, field_id)
    finally:
        client.close()


def _remove_field_from_screen_impl(
    screen_id: str, field_id: str, tab_id: str | None = None
) -> dict[str, Any]:
    """Remove a field from a screen."""
    client = get_jira_client()
    try:
        if not tab_id:
            tabs = client.get_screen_tabs(screen_id)
            for tab in tabs:
                fields = client.get_screen_tab_fields(screen_id, tab["id"])
                if any(f["id"] == field_id for f in fields):
                    tab_id = tab["id"]
                    break

        if not tab_id:
            raise ValidationError(f"Field {field_id} not found on any tab")

        client.remove_field_from_screen_tab(screen_id, tab_id, field_id)
        return {"action": "removed", "screen_id": screen_id, "field_id": field_id}
    finally:
        client.close()


def _list_screen_schemes_impl() -> list[dict[str, Any]]:
    """List screen schemes."""
    client = get_jira_client()
    try:
        response = client.get_screen_schemes()
        return response.get("values", [])
    finally:
        client.close()


def _get_screen_scheme_impl(scheme_id: str) -> dict[str, Any]:
    """Get screen scheme details."""
    client = get_jira_client()
    try:
        return client.get_screen_scheme(scheme_id)
    finally:
        client.close()


# =============================================================================
# Issue Type Implementation Functions
# =============================================================================


def _list_issue_types_impl(
    subtask_only: bool = False,
    standard_only: bool = False,
    hierarchy_level: int | None = None,
) -> list[dict[str, Any]]:
    """List issue types."""
    client = get_jira_client()
    try:
        issue_types = client.get_issue_types()

        if subtask_only:
            issue_types = [t for t in issue_types if t.get("subtask", False)]
        elif standard_only:
            issue_types = [t for t in issue_types if not t.get("subtask", False)]

        if hierarchy_level is not None:
            issue_types = [
                t for t in issue_types if t.get("hierarchyLevel") == hierarchy_level
            ]

        return issue_types
    finally:
        client.close()


def _get_issue_type_impl(issue_type_id: str) -> dict[str, Any]:
    """Get issue type details."""
    client = get_jira_client()
    try:
        return client.get_issue_type(issue_type_id)
    finally:
        client.close()


def _create_issue_type_impl(
    name: str, description: str | None = None, issue_type: str = "standard"
) -> dict[str, Any]:
    """Create an issue type."""
    client = get_jira_client()
    try:
        return client.create_issue_type(
            name=name,
            description=description,
            type=issue_type,
        )
    finally:
        client.close()


def _update_issue_type_impl(
    issue_type_id: str, name: str | None = None, description: str | None = None
) -> dict[str, Any]:
    """Update an issue type."""
    client = get_jira_client()
    try:
        return client.update_issue_type(
            issue_type_id, name=name, description=description
        )
    finally:
        client.close()


def _delete_issue_type_impl(issue_type_id: str) -> dict[str, Any]:
    """Delete an issue type."""
    client = get_jira_client()
    try:
        client.delete_issue_type(issue_type_id)
        return {"action": "deleted", "issue_type_id": issue_type_id}
    finally:
        client.close()


# =============================================================================
# Issue Type Scheme Implementation Functions
# =============================================================================


def _list_issue_type_schemes_impl() -> list[dict[str, Any]]:
    """List issue type schemes."""
    client = get_jira_client()
    try:
        response = client.get_issue_type_schemes()
        return response.get("values", [])
    finally:
        client.close()


def _get_issue_type_scheme_impl(scheme_id: str) -> dict[str, Any]:
    """Get issue type scheme details."""
    client = get_jira_client()
    try:
        return client.get_issue_type_scheme(scheme_id)
    finally:
        client.close()


def _create_issue_type_scheme_impl(
    name: str, description: str | None = None
) -> dict[str, Any]:
    """Create an issue type scheme."""
    client = get_jira_client()
    try:
        return client.create_issue_type_scheme(name=name, description=description)
    finally:
        client.close()


def _assign_issue_type_scheme_impl(project_key: str, scheme_id: str) -> dict[str, Any]:
    """Assign an issue type scheme to a project."""
    client = get_jira_client()
    try:
        return client.assign_issue_type_scheme(project_key, scheme_id)
    finally:
        client.close()


def _get_project_issue_type_scheme_impl(project_id: str) -> dict[str, Any]:
    """Get the issue type scheme for a project."""
    client = get_jira_client()
    try:
        return client.get_project_issue_type_scheme(project_id)
    finally:
        client.close()


# =============================================================================
# Workflow Implementation Functions
# =============================================================================


def _list_workflows_impl(
    details: bool = False,
    name_filter: str | None = None,
    scope: str | None = None,
    show_usage: bool = False,
    max_results: int = 50,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """List all workflows."""
    client = get_jira_client()
    try:
        all_workflows = []
        start_at = 0
        has_more = True

        while has_more:
            if details:
                expand = "transitions,statuses"
                response = client.search_workflows(
                    workflow_name=name_filter,
                    expand=expand,
                    start_at=start_at,
                    max_results=max_results,
                )
                workflows_data = response.get("values", [])
                is_paginated = True
            else:
                response = client.get_workflows(
                    start_at=start_at, max_results=max_results
                )
                if isinstance(response, list):
                    workflows_data = response
                    is_paginated = False
                else:
                    workflows_data = response.get("values", [])
                    is_paginated = True

            for wf_data in workflows_data:
                workflow = _parse_workflow(wf_data, details)

                if name_filter and name_filter.lower() not in workflow["name"].lower():
                    continue

                if scope:
                    wf_scope = workflow.get("scope_type", "GLOBAL")
                    if scope.lower() == "global" and wf_scope != "GLOBAL":
                        continue
                    if scope.lower() == "project" and wf_scope != "PROJECT":
                        continue

                all_workflows.append(workflow)

            if is_paginated:
                total = response.get("total", len(workflows_data))
                is_last = response.get("isLast", True)
                if fetch_all and not is_last:
                    start_at += max_results
                else:
                    has_more = False
            else:
                total = len(workflows_data)
                is_last = True
                has_more = False

        if show_usage:
            for workflow in all_workflows:
                try:
                    entity_id = workflow.get("entity_id")
                    if entity_id:
                        schemes = client.get_workflow_schemes_for_workflow(
                            entity_id, max_results=100
                        )
                        workflow["scheme_count"] = schemes.get("total", 0)
                        workflow["schemes"] = [
                            s.get("name", "Unknown") for s in schemes.get("values", [])
                        ]
                except JiraError:
                    workflow["scheme_count"] = 0
                    workflow["schemes"] = []

        return {
            "workflows": all_workflows,
            "total": len(all_workflows) if fetch_all else total,
            "has_more": not is_last if not fetch_all else False,
        }
    finally:
        client.close()


def _parse_workflow(
    wf_data: dict[str, Any], include_details: bool = False
) -> dict[str, Any]:
    """Parse workflow data from API response."""
    if "id" in wf_data and isinstance(wf_data["id"], dict):
        workflow = {
            "name": wf_data["id"].get("name", "Unknown"),
            "entity_id": wf_data["id"].get("entityId", ""),
            "description": wf_data.get("description", ""),
            "is_default": wf_data.get("isDefault", False),
        }
    else:
        workflow = {
            "name": wf_data.get("name", wf_data.get("id", {}).get("name", "Unknown")),
            "entity_id": wf_data.get(
                "entityId", wf_data.get("id", {}).get("entityId", "")
            ),
            "description": wf_data.get("description", ""),
            "is_default": wf_data.get("isDefault", False),
        }

    scope = wf_data.get("scope", {})
    workflow["scope_type"] = scope.get("type", "GLOBAL")
    if scope.get("project"):
        workflow["scope_project"] = scope["project"].get("key", "")

    version = wf_data.get("version", {})
    workflow["version"] = version.get("versionNumber", 1) if version else 1

    workflow["created"] = wf_data.get("created", "")
    workflow["updated"] = wf_data.get("updated", "")

    if include_details:
        statuses = wf_data.get("statuses", [])
        transitions = wf_data.get("transitions", [])
        workflow["status_count"] = len(statuses)
        workflow["transition_count"] = len(transitions)
        workflow["statuses"] = statuses
        workflow["transitions"] = transitions

    return workflow


def _get_workflow_impl(name: str) -> dict[str, Any]:
    """Get workflow details."""
    client = get_jira_client()
    try:
        response = client.search_workflows(
            workflow_name=name, expand="transitions,statuses"
        )
        workflows = response.get("values", [])
        if not workflows:
            raise JiraError(f"Workflow not found: {name}")
        return _parse_workflow(workflows[0], include_details=True)
    finally:
        client.close()


def _search_workflows_impl(query: str) -> list[dict[str, Any]]:
    """Search workflows."""
    result = _list_workflows_impl(name_filter=query, fetch_all=True)
    return result["workflows"]


def _get_workflow_for_issue_impl(issue_key: str) -> dict[str, Any]:
    """Get the workflow for an issue."""
    client = get_jira_client()
    try:
        issue = client.get_issue(issue_key, fields="project,issuetype,status")
        project_key = issue["fields"]["project"]["key"]
        issue_type_id = issue["fields"]["issuetype"]["id"]

        workflow_scheme = client.get_project_workflow_scheme(project_key)
        workflow_name = None

        mappings = workflow_scheme.get("issueTypeMappings", {})
        if issue_type_id in mappings:
            workflow_name = mappings[issue_type_id]
        else:
            workflow_name = workflow_scheme.get("defaultWorkflow")

        if workflow_name:
            return _get_workflow_impl(workflow_name)
        else:
            return {"issue_key": issue_key, "workflow": None}
    finally:
        client.close()


# =============================================================================
# Workflow Scheme Implementation Functions
# =============================================================================


def _list_workflow_schemes_impl() -> list[dict[str, Any]]:
    """List workflow schemes."""
    client = get_jira_client()
    try:
        response = client.get_workflow_schemes()
        return response.get("values", [])
    finally:
        client.close()


def _get_workflow_scheme_impl(
    scheme_id: str, show_projects: bool = False
) -> dict[str, Any]:
    """Get workflow scheme details."""
    client = get_jira_client()
    try:
        scheme = client.get_workflow_scheme(scheme_id)
        result = {"scheme": scheme}

        if show_projects:
            projects = client.get_projects_for_workflow_scheme(scheme_id)
            result["projects"] = projects.get("values", [])

        return result
    finally:
        client.close()


def _assign_workflow_scheme_impl(project_key: str, scheme_id: str) -> dict[str, Any]:
    """Assign a workflow scheme to a project."""
    client = get_jira_client()
    try:
        return client.assign_workflow_scheme(project_key, scheme_id)
    finally:
        client.close()


# =============================================================================
# Status Implementation Functions
# =============================================================================


def _list_statuses_impl() -> list[dict[str, Any]]:
    """List all statuses."""
    client = get_jira_client()
    try:
        return client.get_statuses()
    finally:
        client.close()


# =============================================================================
# Formatting Functions
# =============================================================================


def _format_projects(result: dict[str, Any]) -> str:
    """Format projects for display."""
    projects = result.get("values", [])
    if not projects:
        return "No projects found."

    data = []
    for proj in projects:
        category = proj.get("projectCategory", {})
        category_name = category.get("name", "-") if category else "-"
        lead = proj.get("lead", {})
        lead_name = lead.get("displayName", "-") if lead else "-"

        data.append(
            {
                "Key": proj.get("key", "-"),
                "Name": proj.get("name", "-")[:40],
                "Type": proj.get("projectTypeKey", "-"),
                "Category": category_name,
                "Lead": lead_name[:20],
            }
        )

    output = format_table(data, columns=["Key", "Name", "Type", "Category", "Lead"])

    total = result.get("total", len(projects))
    start_at = result.get("startAt", 0)

    if total > len(projects):
        output += (
            f"\n\nShowing {start_at + 1}-{start_at + len(projects)} of {total} projects"
        )
        if not result.get("isLast", True):
            output += f"\nUse --start-at {start_at + len(projects)} to see more"

    return output


def _format_trash_projects(result: dict[str, Any]) -> str:
    """Format trash projects for display."""
    projects = result.get("values", [])
    if not projects:
        return "No projects in trash."

    data = []
    for proj in projects:
        data.append(
            {
                "Key": proj.get("key", "-"),
                "Name": proj.get("name", "-")[:30],
                "Deleted": proj.get("deletedDate", "-")[:10],
                "Restore By": proj.get("retentionTillDate", "-")[:10],
            }
        )

    return format_table(data, columns=["Key", "Name", "Deleted", "Restore By"])


def _format_project(project: dict[str, Any]) -> str:
    """Format a single project."""
    lines = [
        f"Key:         {project.get('key', 'N/A')}",
        f"ID:          {project.get('id', 'N/A')}",
        f"Name:        {project.get('name', 'N/A')}",
        f"Type:        {project.get('projectTypeKey', 'N/A')}",
        f"Description: {project.get('description', 'N/A')[:100]}",
    ]

    lead = project.get("lead", {})
    if lead:
        lines.append(f"Lead:        {lead.get('displayName', 'N/A')}")

    category = project.get("projectCategory", {})
    if category:
        lines.append(f"Category:    {category.get('name', 'N/A')}")

    return "\n".join(lines)


def _format_categories(categories: list[dict[str, Any]]) -> str:
    """Format categories for display."""
    if not categories:
        return "No categories found."

    data = []
    for cat in categories:
        data.append(
            {
                "ID": cat.get("id", ""),
                "Name": cat.get("name", ""),
                "Description": (cat.get("description", "") or "")[:50],
            }
        )

    return format_table(data, columns=["ID", "Name", "Description"])


def _format_users(users: list[dict[str, Any]], show_groups: bool = False) -> str:
    """Format users for display."""
    if not users:
        return "No users found."

    data = []
    for user in users:
        row = {
            "Account ID": user.get("accountId", "N/A"),
            "Name": user.get("displayName", "N/A"),
            "Email": user.get("emailAddress", "[hidden]") or "[hidden]",
            "Status": "Active" if user.get("active", True) else "Inactive",
        }
        if show_groups:
            groups = user.get("groups", [])
            row["Groups"] = ", ".join(groups) if groups else "[none]"
        data.append(row)

    columns = ["Account ID", "Name", "Email", "Status"]
    if show_groups:
        columns.append("Groups")

    return format_table(data, columns=columns)


def _format_groups(
    groups: list[dict[str, Any]],
    show_member_count: bool = False,
    show_system: bool = False,
) -> str:
    """Format groups for display."""
    if not groups:
        return "No groups found."

    data = []
    for group in groups:
        name = group.get("name", "N/A")
        row = {
            "Name": name,
            "Group ID": group.get("groupId", "N/A"),
        }
        if show_member_count:
            row["Members"] = str(group.get("memberCount", "-"))
        if show_system:
            row["Type"] = "System" if _is_system_group(name) else "Custom"
        data.append(row)

    columns = ["Name", "Group ID"]
    if show_member_count:
        columns.append("Members")
    if show_system:
        columns.append("Type")

    return format_table(data, columns=columns)


def _format_group_members(result: dict[str, Any], group_name: str) -> str:
    """Format group members for display."""
    members = result.get("values", [])
    if not members:
        return f"Group '{group_name}' has no members."

    data = []
    for member in members:
        data.append(
            {
                "Account ID": member.get("accountId", "N/A"),
                "Name": member.get("displayName", "N/A"),
                "Email": member.get("emailAddress", "[hidden]") or "[hidden]",
                "Active": "Yes" if member.get("active", True) else "No",
            }
        )

    output = (
        f"Members of '{group_name}' ({result.get('total', len(members))} total):\n\n"
    )
    output += format_table(data, columns=["Account ID", "Name", "Email", "Active"])
    return output


def _format_automation_rules(rules: list[dict[str, Any]]) -> str:
    """Format automation rules for display."""
    if not rules:
        return "No automation rules found."

    data = []
    for rule in rules:
        scope_resources = rule.get("ruleScope", {}).get("resources", [])
        scope = "Global" if not scope_resources else "Project"

        trigger = rule.get("trigger", {})
        trigger_type = trigger.get("type", "Unknown")
        if ":" in trigger_type:
            trigger_display = trigger_type.split(":")[-1]
        else:
            trigger_display = trigger_type

        rule_id = rule.get("id", "")
        if len(rule_id) > 20:
            rule_id = rule_id[:20] + "..."

        data.append(
            {
                "ID": rule_id,
                "Name": rule.get("name", "Unnamed"),
                "State": rule.get("state", "UNKNOWN"),
                "Scope": scope,
                "Trigger": trigger_display,
            }
        )

    output = f"Automation Rules ({len(rules)} found)\n"
    output += "=" * 60 + "\n\n"
    output += format_table(data, columns=["ID", "Name", "State", "Scope", "Trigger"])
    return output


def _format_permission_schemes(
    schemes: list[dict[str, Any]], show_grants: bool = False
) -> str:
    """Format permission schemes for display."""
    if not schemes:
        return "No permission schemes found."

    data = []
    for scheme in schemes:
        row = {
            "ID": scheme.get("id", ""),
            "Name": scheme.get("name", ""),
            "Description": (scheme.get("description", "") or "")[:50],
        }
        if show_grants:
            permissions = scheme.get("permissions", [])
            row["Grants"] = str(len(permissions))
        data.append(row)

    columns = ["ID", "Name", "Description"]
    if show_grants:
        columns.append("Grants")

    return format_table(data, columns=columns)


def _format_notification_schemes(schemes: list[dict[str, Any]]) -> str:
    """Format notification schemes for display."""
    if not schemes:
        return "No notification schemes found."

    data = []
    for scheme in schemes:
        data.append(
            {
                "ID": scheme.get("id", ""),
                "Name": scheme.get("name", ""),
                "Description": (scheme.get("description", "") or "")[:50],
            }
        )

    return format_table(data, columns=["ID", "Name", "Description"])


def _format_screens(screens: list[dict[str, Any]]) -> str:
    """Format screens for display."""
    if not screens:
        return "No screens found."

    data = []
    for screen in screens:
        scope_info = ""
        if screen.get("scope"):
            scope_type = screen["scope"].get("type", "")
            if scope_type == "PROJECT":
                project = screen["scope"].get("project", {})
                scope_info = f"Project: {project.get('id', 'unknown')}"
            else:
                scope_info = scope_type

        data.append(
            {
                "ID": screen.get("id", ""),
                "Name": screen.get("name", ""),
                "Description": (screen.get("description", "") or "")[:50],
                "Scope": scope_info,
            }
        )

    return format_table(data, columns=["ID", "Name", "Description", "Scope"])


def _format_issue_types(issue_types: list[dict[str, Any]]) -> str:
    """Format issue types for display."""
    if not issue_types:
        return "No issue types found."

    data = []
    for issue_type in issue_types:
        scope_type = (
            issue_type.get("scope", {}).get("type", "GLOBAL")
            if issue_type.get("scope")
            else "GLOBAL"
        )
        data.append(
            {
                "ID": issue_type.get("id", ""),
                "Name": issue_type.get("name", ""),
                "Description": (issue_type.get("description", "") or "")[:50],
                "Subtask": "Yes" if issue_type.get("subtask") else "No",
                "Hierarchy": str(issue_type.get("hierarchyLevel", 0)),
                "Scope": scope_type,
            }
        )

    return format_table(
        data, columns=["ID", "Name", "Description", "Subtask", "Hierarchy", "Scope"]
    )


def _format_workflows(workflows: list[dict[str, Any]]) -> str:
    """Format workflows for display."""
    if not workflows:
        return "No workflows found."

    has_details = any("status_count" in wf for wf in workflows)
    has_usage = any("scheme_count" in wf for wf in workflows)

    data = []
    for wf in workflows:
        scope = "Global" if wf.get("scope_type") == "GLOBAL" else "Project"
        row = {
            "Name": wf["name"],
            "Type": scope,
            "Default": "Yes" if wf.get("is_default") else "No",
            "Description": (wf.get("description", "") or "")[:50],
        }
        if has_details:
            row["Statuses"] = str(wf.get("status_count", "-"))
            row["Transitions"] = str(wf.get("transition_count", "-"))
        if has_usage:
            row["Schemes"] = str(wf.get("scheme_count", "-"))
        data.append(row)

    columns = ["Name", "Type", "Default", "Description"]
    if has_details:
        columns.extend(["Statuses", "Transitions"])
    if has_usage:
        columns.append("Schemes")

    output = format_table(data, columns=columns)
    output += f"\n\nTotal: {len(workflows)} workflows"
    return output


def _format_statuses(statuses: list[dict[str, Any]]) -> str:
    """Format statuses for display."""
    if not statuses:
        return "No statuses found."

    data = []
    for status in statuses:
        category = status.get("statusCategory", {})
        data.append(
            {
                "ID": status.get("id", ""),
                "Name": status.get("name", ""),
                "Category": category.get("name", "Unknown"),
                "Description": (status.get("description", "") or "")[:50],
            }
        )

    return format_table(data, columns=["ID", "Name", "Category", "Description"])


# =============================================================================
# CLI Commands - Main admin group
# =============================================================================


@click.group()
def admin():
    """Commands for JIRA administration (projects, users, permissions, etc.)."""
    pass


# =============================================================================
# Project Management Commands
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
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
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
    output,
):
    """List and search JIRA projects."""
    if trash:
        result = _list_trash_projects_impl(start_at=start_at, max_results=max_results)
        if output == "json":
            click.echo(format_json(result))
        else:
            click.echo(_format_trash_projects(result))
    else:
        expand_list = _parse_comma_list(expand)
        result = _list_projects_impl(
            query=search,
            project_type=project_type,
            category_id=category,
            include_archived=include_archived,
            expand=expand_list,
            start_at=start_at,
            max_results=max_results,
        )
        if output == "json":
            click.echo(format_json(result))
        else:
            click.echo(_format_projects(result))


@project_group.command(name="get")
@click.argument("project_key")
@click.option("--expand", "-e", help="Fields to expand (description, lead, issueTypes)")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def project_get(ctx, project_key, expand, output):
    """Get project details."""
    expand_list = _parse_comma_list(expand)
    result = _get_project_impl(project_key, expand=expand_list)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_project(result))


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
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def project_create(
    ctx, key, name, project_type, template, lead, description, category, output
):
    """Create a new JIRA project."""
    result = _create_project_impl(
        key=key,
        name=name,
        project_type=project_type,
        template=template,
        lead=lead,
        description=description,
        category_id=category,
    )
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo("Project created successfully!")
        click.echo(f"  Key:  {result.get('key')}")
        click.echo(f"  ID:   {result.get('id')}")
        click.echo(f"  Name: {result.get('name', 'N/A')}")


@project_group.command(name="update")
@click.argument("project_key")
@click.option("--name", "-n", help="New project name")
@click.option("--description", "-d", help="New description")
@click.option("--lead", "-l", help="New project lead")
@click.option("--category", type=int, help="New category ID")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def project_update(ctx, project_key, name, description, lead, category, output):
    """Update a JIRA project."""
    result = _update_project_impl(
        project_key, name=name, description=description, lead=lead, category_id=category
    )
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Project {project_key} updated successfully.")


@project_group.command(name="delete")
@click.argument("project_key")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--dry-run", is_flag=True, help="Preview without executing")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def project_delete(ctx, project_key, yes, dry_run, output):
    """Delete a JIRA project."""
    if not dry_run and not yes:
        click.confirm(
            f"Are you sure you want to delete project {project_key}?", abort=True
        )

    result = _delete_project_impl(project_key, dry_run=dry_run)
    if output == "json":
        click.echo(format_json(result))
    else:
        if dry_run:
            click.echo(f"Would delete project {project_key}")
        else:
            click.echo(f"Project {project_key} deleted.")


@project_group.command(name="archive")
@click.argument("project_key")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def project_archive(ctx, project_key, output):
    """Archive a JIRA project."""
    result = _archive_project_impl(project_key)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Project {project_key} archived.")


@project_group.command(name="restore")
@click.argument("project_key")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def project_restore(ctx, project_key, output):
    """Restore an archived or deleted project."""
    result = _restore_project_impl(project_key)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Project {project_key} restored.")


@admin.group(name="config")
def config_group():
    """Project configuration commands."""
    pass


@config_group.command(name="get")
@click.argument("project_key")
@click.option("--show-schemes", is_flag=True, help="Show assigned schemes")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def config_get(ctx, project_key, show_schemes, output):
    """Get project configuration."""
    result = _get_project_config_impl(project_key, show_schemes=show_schemes)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_project(result["project"]))
        if show_schemes and "schemes" in result:
            click.echo("\nAssigned Schemes:")
            for scheme_type, scheme in result["schemes"].items():
                if scheme:
                    click.echo(f"  {scheme_type}: {scheme.get('name', 'N/A')}")


# =============================================================================
# Category Management Commands
# =============================================================================


@admin.group(name="category")
def category_group():
    """Project category commands."""
    pass


@category_group.command(name="list")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def category_list(ctx, output):
    """List project categories."""
    result = _list_categories_impl()
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_categories(result))


@category_group.command(name="create")
@click.option("--name", "-n", required=True, help="Category name")
@click.option("--description", "-d", help="Category description")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def category_create(ctx, name, description, output):
    """Create a project category."""
    result = _create_category_impl(name=name, description=description)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Category '{name}' created with ID {result.get('id')}.")


@category_group.command(name="assign")
@click.argument("project_key")
@click.option("--category-id", "-c", type=int, required=True, help="Category ID")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def category_assign(ctx, project_key, category_id, output):
    """Assign a category to a project."""
    result = _assign_category_impl(project_key, category_id)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Category {category_id} assigned to project {project_key}.")


# =============================================================================
# User Management Commands
# =============================================================================


@admin.group(name="user")
def user_group():
    """User management commands."""
    pass


@user_group.command(name="search")
@click.argument("query")
@click.option("--include-groups", "-g", is_flag=True, help="Include group memberships")
@click.option("--project", "-p", help="Project key for assignable users")
@click.option(
    "--assignable",
    "-a",
    is_flag=True,
    help="Search assignable users (requires --project)",
)
@click.option("--all", "include_inactive", is_flag=True, help="Include inactive users")
@click.option("--max-results", type=int, default=50, help="Maximum results")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def user_search(
    ctx,
    query,
    include_groups,
    project,
    assignable,
    include_inactive,
    max_results,
    output,
):
    """Search for users by name or email."""
    if assignable and not project:
        raise click.UsageError("--assignable requires --project")

    result = _search_users_impl(
        query=query,
        max_results=max_results,
        active_only=not include_inactive,
        include_groups=include_groups,
        project=project,
        assignable=assignable,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        if not result:
            click.echo(f'No users found matching "{query}"')
        else:
            click.echo(f'Found {len(result)} user(s) matching "{query}"\n')
            click.echo(_format_users(result, show_groups=include_groups))


@user_group.command(name="get")
@click.argument("account_id")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def user_get(ctx, account_id, output):
    """Get user details by account ID."""
    result = _get_user_impl(account_id)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_users([result]))


# =============================================================================
# Group Management Commands
# =============================================================================


@admin.group(name="group")
def group_group():
    """Group management commands."""
    pass


@group_group.command(name="list")
@click.option("--query", "-q", help="Filter groups by name")
@click.option(
    "--include-members", "-m", is_flag=True, help="Include member counts (slower)"
)
@click.option("--show-system", "-s", is_flag=True, help="Highlight system groups")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def group_list(ctx, query, include_members, show_system, output):
    """List all groups."""
    result = _list_groups_impl(query=query, include_members=include_members)
    if output == "json":
        click.echo(format_json(result))
    else:
        if not result:
            click.echo("No groups found.")
        else:
            click.echo(f"Found {len(result)} group(s)\n")
            click.echo(
                _format_groups(
                    result, show_member_count=include_members, show_system=show_system
                )
            )


@group_group.command(name="members")
@click.argument("group_name")
@click.option("--max-results", type=int, default=50, help="Maximum results")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def group_members(ctx, group_name, max_results, output):
    """Get members of a group."""
    result = _get_group_members_impl(group_name, max_results=max_results)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_group_members(result, group_name))


@group_group.command(name="create")
@click.argument("group_name")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def group_create(ctx, group_name, output):
    """Create a new group."""
    result = _create_group_impl(group_name)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Group '{group_name}' created.")


@group_group.command(name="delete")
@click.argument("group_name")
@click.option("--confirm", "-y", is_flag=True, help="Confirm deletion (required)")
@click.option("--dry-run", is_flag=True, help="Preview without deleting")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def group_delete(ctx, group_name, confirm, dry_run, output):
    """Delete a group."""
    if not dry_run and not confirm:
        raise click.UsageError("--confirm is required to delete a group")

    result = _delete_group_impl(group_name, dry_run=dry_run)
    if output == "json":
        click.echo(format_json(result))
    else:
        if dry_run:
            click.echo(f"Would delete group '{group_name}'")
        else:
            click.echo(f"Group '{group_name}' deleted.")


@group_group.command(name="add-user")
@click.argument("group_name")
@click.option("--user", "-u", required=True, help="User account ID or email")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def group_add_user(ctx, group_name, user, output):
    """Add a user to a group."""
    result = _add_user_to_group_impl(group_name, user)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"User added to group '{group_name}'.")


@group_group.command(name="remove-user")
@click.argument("group_name")
@click.option("--user", "-u", required=True, help="User account ID or email")
@click.option("--confirm", "-y", is_flag=True, help="Confirm removal (required)")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def group_remove_user(ctx, group_name, user, confirm, output):
    """Remove a user from a group."""
    if not confirm:
        raise click.UsageError("--confirm is required to remove a user from a group")

    result = _remove_user_from_group_impl(group_name, user)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"User removed from group '{group_name}'.")


# =============================================================================
# Automation Rules Commands
# =============================================================================


@admin.group(name="automation")
def automation_group():
    """Automation rule commands."""
    pass


@automation_group.command(name="list")
@click.option("--project", "-p", help="Filter by project key")
@click.option(
    "--state", "-s", type=click.Choice(["enabled", "disabled"]), help="Filter by state"
)
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all pages")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def automation_list(ctx, project, state, fetch_all, output):
    """List automation rules."""
    result = _list_automation_rules_impl(
        project=project, state=state, fetch_all=fetch_all
    )
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_automation_rules(result))


@automation_group.command(name="get")
@click.argument("rule_id")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def automation_get(ctx, rule_id, output):
    """Get automation rule details."""
    result = _get_automation_rule_impl(rule_id)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Rule: {result.get('name', 'N/A')}")
        click.echo(f"State: {result.get('state', 'N/A')}")
        click.echo(f"ID: {result.get('id', 'N/A')}")


@automation_group.command(name="search")
@click.option("--query", "-q", required=True, help="Search query")
@click.option("--project", "-p", help="Filter by project")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def automation_search(ctx, query, project, output):
    """Search automation rules."""
    result = _search_automation_rules_impl(query, project=project)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_automation_rules(result))


@automation_group.command(name="enable")
@click.argument("rule_id")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def automation_enable(ctx, rule_id, output):
    """Enable an automation rule."""
    result = _enable_automation_rule_impl(rule_id)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Rule {rule_id} enabled.")


@automation_group.command(name="disable")
@click.argument("rule_id")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def automation_disable(ctx, rule_id, output):
    """Disable an automation rule."""
    result = _disable_automation_rule_impl(rule_id)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Rule {rule_id} disabled.")


@automation_group.command(name="toggle")
@click.argument("rule_id")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def automation_toggle(ctx, rule_id, output):
    """Toggle an automation rule's enabled state."""
    result = _toggle_automation_rule_impl(rule_id)
    if output == "json":
        click.echo(format_json(result))
    else:
        new_state = result.get("state", "unknown")
        click.echo(f"Rule {rule_id} toggled to {new_state}.")


@automation_group.command(name="invoke")
@click.argument("rule_id")
@click.option("--issue", "-i", help="Issue key to run rule against")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def automation_invoke(ctx, rule_id, issue, output):
    """Invoke a manual automation rule."""
    result = _invoke_manual_rule_impl(rule_id, issue_key=issue)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Rule {rule_id} invoked.")


@admin.group(name="automation-template")
def automation_template_group():
    """Automation rule template commands."""
    pass


@automation_template_group.command(name="list")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def automation_template_list(ctx, output):
    """List available automation templates."""
    result = _list_automation_templates_impl()
    if output == "json":
        click.echo(format_json(result))
    else:
        if not result:
            click.echo("No automation templates found.")
        else:
            for template in result:
                click.echo(
                    f"- {template.get('name', 'N/A')} ({template.get('id', 'N/A')})"
                )


@automation_template_group.command(name="get")
@click.argument("template_id")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def automation_template_get(ctx, template_id, output):
    """Get automation template details."""
    result = _get_automation_template_impl(template_id)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Template: {result.get('name', 'N/A')}")
        click.echo(f"ID: {result.get('id', 'N/A')}")
        click.echo(f"Description: {result.get('description', 'N/A')}")


# =============================================================================
# Permission Scheme Commands
# =============================================================================


@admin.group(name="permission-scheme")
def permission_scheme_group():
    """Permission scheme commands."""
    pass


@permission_scheme_group.command(name="list")
@click.option("--filter", "-f", "name_filter", help="Filter by name")
@click.option("--show-grants", "-g", is_flag=True, help="Include grant counts")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def permission_scheme_list(ctx, name_filter, show_grants, output):
    """List permission schemes."""
    result = _list_permission_schemes_impl(
        name_filter=name_filter, show_grants=show_grants
    )
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_permission_schemes(result, show_grants=show_grants))


@permission_scheme_group.command(name="get")
@click.argument("scheme_id")
@click.option("--show-projects", is_flag=True, help="Show projects using this scheme")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def permission_scheme_get(ctx, scheme_id, show_projects, output):
    """Get permission scheme details."""
    result = _get_permission_scheme_impl(scheme_id, show_projects=show_projects)
    if output == "json":
        click.echo(format_json(result))
    else:
        scheme = result["scheme"]
        click.echo(f"Name: {scheme.get('name', 'N/A')}")
        click.echo(f"ID: {scheme.get('id', 'N/A')}")
        click.echo(f"Description: {scheme.get('description', 'N/A')}")
        permissions = scheme.get("permissions", [])
        click.echo(f"Permissions: {len(permissions)} grants")


@permission_scheme_group.command(name="create")
@click.option("--name", "-n", required=True, help="Scheme name")
@click.option("--description", "-d", help="Scheme description")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def permission_scheme_create(ctx, name, description, output):
    """Create a permission scheme."""
    result = _create_permission_scheme_impl(name=name, description=description)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Permission scheme '{name}' created with ID {result.get('id')}.")


@permission_scheme_group.command(name="assign")
@click.option("--project", "-p", required=True, help="Project key")
@click.option("--scheme", "-s", required=True, help="Scheme ID")
@click.option("--dry-run", is_flag=True, help="Preview without executing")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def permission_scheme_assign(ctx, project, scheme, dry_run, output):
    """Assign a permission scheme to a project."""
    result = _assign_permission_scheme_impl(project, scheme, dry_run=dry_run)
    if output == "json":
        click.echo(format_json(result))
    else:
        if dry_run:
            click.echo(f"Would assign scheme {scheme} to project {project}")
        else:
            click.echo(f"Scheme {scheme} assigned to project {project}.")


@admin.group(name="permission")
def permission_group():
    """Permission commands."""
    pass


@permission_group.command(name="list")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def permission_list(ctx, output):
    """List available permissions."""
    result = _list_permissions_impl()
    if output == "json":
        click.echo(format_json(result))
    else:
        if isinstance(result, dict):
            for key, perm in result.items():
                click.echo(f"- {key}: {perm.get('name', key)}")
        else:
            for perm in result:
                click.echo(f"- {perm.get('key', 'N/A')}: {perm.get('name', 'N/A')}")


# =============================================================================
# Notification Scheme Commands
# =============================================================================


@admin.group(name="notification-scheme")
def notification_scheme_group():
    """Notification scheme commands."""
    pass


@notification_scheme_group.command(name="list")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def notification_scheme_list(ctx, output):
    """List notification schemes."""
    result = _list_notification_schemes_impl()
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_notification_schemes(result))


@notification_scheme_group.command(name="get")
@click.argument("scheme_id")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def notification_scheme_get(ctx, scheme_id, output):
    """Get notification scheme details."""
    result = _get_notification_scheme_impl(scheme_id)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Name: {result.get('name', 'N/A')}")
        click.echo(f"ID: {result.get('id', 'N/A')}")
        click.echo(f"Description: {result.get('description', 'N/A')}")


@notification_scheme_group.command(name="create")
@click.option("--name", "-n", required=True, help="Scheme name")
@click.option("--description", "-d", help="Scheme description")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def notification_scheme_create(ctx, name, description, output):
    """Create a notification scheme."""
    result = _create_notification_scheme_impl(name=name, description=description)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Notification scheme '{name}' created with ID {result.get('id')}.")


@admin.group(name="notification")
def notification_group():
    """Notification commands."""
    pass


@notification_group.command(name="add")
@click.option("--scheme", "-s", required=True, help="Scheme ID")
@click.option("--event", "-e", required=True, help="Event type")
@click.option("--recipient", "-r", required=True, help="Recipient type")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def notification_add(ctx, scheme, event, recipient, output):
    """Add a notification to a scheme."""
    result = _add_notification_impl(scheme, event, recipient)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Notification added to scheme {scheme}.")


@notification_group.command(name="remove")
@click.option("--scheme", "-s", required=True, help="Scheme ID")
@click.option("--notification-id", "-n", required=True, help="Notification ID")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def notification_remove(ctx, scheme, notification_id, output):
    """Remove a notification from a scheme."""
    result = _remove_notification_impl(scheme, notification_id)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Notification {notification_id} removed from scheme {scheme}.")


# =============================================================================
# Screen Management Commands
# =============================================================================


@admin.group(name="screen")
def screen_group():
    """Screen management commands."""
    pass


@screen_group.command(name="list")
@click.option("--filter", "-f", "filter_pattern", help="Filter by name pattern")
@click.option(
    "--scope",
    "-s",
    multiple=True,
    type=click.Choice(["PROJECT", "TEMPLATE", "GLOBAL"]),
    help="Filter by scope",
)
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all pages")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def screen_list(ctx, filter_pattern, scope, fetch_all, output):
    """List screens."""
    scope_list = list(scope) if scope else None
    result = _list_screens_impl(
        filter_pattern=filter_pattern, scope=scope_list, fetch_all=fetch_all
    )
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_screens(result))
        click.echo(f"\nTotal: {len(result)} screen(s)")


@screen_group.command(name="get")
@click.argument("screen_id")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def screen_get(ctx, screen_id, output):
    """Get screen details."""
    result = _get_screen_impl(screen_id)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Name: {result.get('name', 'N/A')}")
        click.echo(f"ID: {result.get('id', 'N/A')}")
        click.echo(f"Description: {result.get('description', 'N/A')}")


@screen_group.command(name="tabs")
@click.argument("screen_id")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def screen_tabs(ctx, screen_id, output):
    """List screen tabs."""
    result = _list_screen_tabs_impl(screen_id)
    if output == "json":
        click.echo(format_json(result))
    else:
        if not result:
            click.echo("No tabs found.")
        else:
            for tab in result:
                click.echo(f"- {tab.get('name', 'N/A')} (ID: {tab.get('id', 'N/A')})")


@screen_group.command(name="fields")
@click.argument("screen_id")
@click.option("--tab", "-t", help="Tab ID (optional)")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def screen_fields(ctx, screen_id, tab, output):
    """Get fields on a screen."""
    result = _get_screen_fields_impl(screen_id, tab_id=tab)
    if output == "json":
        click.echo(format_json(result))
    else:
        if not result:
            click.echo("No fields found.")
        else:
            for field in result:
                tab_info = (
                    f" (Tab: {field.get('tab', 'N/A')})" if "tab" in field else ""
                )
                click.echo(f"- {field.get('name', field.get('id', 'N/A'))}{tab_info}")


@screen_group.command(name="add-field")
@click.argument("screen_id")
@click.argument("field_id")
@click.option("--tab", "-t", help="Tab ID")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def screen_add_field(ctx, screen_id, field_id, tab, output):
    """Add a field to a screen."""
    result = _add_field_to_screen_impl(screen_id, field_id, tab_id=tab)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Field {field_id} added to screen {screen_id}.")


@screen_group.command(name="remove-field")
@click.argument("screen_id")
@click.argument("field_id")
@click.option("--tab", "-t", help="Tab ID")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def screen_remove_field(ctx, screen_id, field_id, tab, output):
    """Remove a field from a screen."""
    result = _remove_field_from_screen_impl(screen_id, field_id, tab_id=tab)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Field {field_id} removed from screen {screen_id}.")


@admin.group(name="screen-scheme")
def screen_scheme_group():
    """Screen scheme commands."""
    pass


@screen_scheme_group.command(name="list")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def screen_scheme_list(ctx, output):
    """List screen schemes."""
    result = _list_screen_schemes_impl()
    if output == "json":
        click.echo(format_json(result))
    else:
        if not result:
            click.echo("No screen schemes found.")
        else:
            data = []
            for scheme in result:
                data.append(
                    {
                        "ID": scheme.get("id", ""),
                        "Name": scheme.get("name", ""),
                        "Description": (scheme.get("description", "") or "")[:50],
                    }
                )
            click.echo(format_table(data, columns=["ID", "Name", "Description"]))


@screen_scheme_group.command(name="get")
@click.argument("scheme_id")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def screen_scheme_get(ctx, scheme_id, output):
    """Get screen scheme details."""
    result = _get_screen_scheme_impl(scheme_id)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Name: {result.get('name', 'N/A')}")
        click.echo(f"ID: {result.get('id', 'N/A')}")
        click.echo(f"Description: {result.get('description', 'N/A')}")


# =============================================================================
# Issue Type Commands
# =============================================================================


@admin.group(name="issue-type")
def issue_type_group():
    """Issue type commands."""
    pass


@issue_type_group.command(name="list")
@click.option("--subtask-only", is_flag=True, help="Show only subtask types")
@click.option("--standard-only", is_flag=True, help="Show only standard types")
@click.option("--hierarchy", type=int, help="Filter by hierarchy level")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def issue_type_list(ctx, subtask_only, standard_only, hierarchy, output):
    """List issue types."""
    result = _list_issue_types_impl(
        subtask_only=subtask_only,
        standard_only=standard_only,
        hierarchy_level=hierarchy,
    )
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_issue_types(result))
        click.echo(f"\nTotal: {len(result)} issue type(s)")


@issue_type_group.command(name="get")
@click.argument("issue_type_id")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def issue_type_get(ctx, issue_type_id, output):
    """Get issue type details."""
    result = _get_issue_type_impl(issue_type_id)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Name: {result.get('name', 'N/A')}")
        click.echo(f"ID: {result.get('id', 'N/A')}")
        click.echo(f"Description: {result.get('description', 'N/A')}")
        click.echo(f"Subtask: {'Yes' if result.get('subtask') else 'No'}")


@issue_type_group.command(name="create")
@click.option("--name", "-n", required=True, help="Issue type name")
@click.option("--description", "-d", help="Description")
@click.option(
    "--type",
    "-t",
    "issue_type",
    type=click.Choice(["standard", "subtask"]),
    default="standard",
    help="Issue type category",
)
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def issue_type_create(ctx, name, description, issue_type, output):
    """Create an issue type."""
    result = _create_issue_type_impl(
        name=name, description=description, issue_type=issue_type
    )
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Issue type '{name}' created with ID {result.get('id')}.")


@issue_type_group.command(name="update")
@click.argument("issue_type_id")
@click.option("--name", "-n", help="New name")
@click.option("--description", "-d", help="New description")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def issue_type_update(ctx, issue_type_id, name, description, output):
    """Update an issue type."""
    result = _update_issue_type_impl(issue_type_id, name=name, description=description)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Issue type {issue_type_id} updated.")


@issue_type_group.command(name="delete")
@click.argument("issue_type_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def issue_type_delete(ctx, issue_type_id, force, output):
    """Delete an issue type."""
    if not force:
        click.confirm(
            f"Are you sure you want to delete issue type {issue_type_id}?", abort=True
        )

    result = _delete_issue_type_impl(issue_type_id)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Issue type {issue_type_id} deleted.")


# =============================================================================
# Issue Type Scheme Commands
# =============================================================================


@admin.group(name="issue-type-scheme")
def issue_type_scheme_group():
    """Issue type scheme commands."""
    pass


@issue_type_scheme_group.command(name="list")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def issue_type_scheme_list(ctx, output):
    """List issue type schemes."""
    result = _list_issue_type_schemes_impl()
    if output == "json":
        click.echo(format_json(result))
    else:
        if not result:
            click.echo("No issue type schemes found.")
        else:
            data = []
            for scheme in result:
                data.append(
                    {
                        "ID": scheme.get("id", ""),
                        "Name": scheme.get("name", ""),
                        "Description": (scheme.get("description", "") or "")[:50],
                    }
                )
            click.echo(format_table(data, columns=["ID", "Name", "Description"]))


@issue_type_scheme_group.command(name="get")
@click.argument("scheme_id")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def issue_type_scheme_get(ctx, scheme_id, output):
    """Get issue type scheme details."""
    result = _get_issue_type_scheme_impl(scheme_id)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Name: {result.get('name', 'N/A')}")
        click.echo(f"ID: {result.get('id', 'N/A')}")
        click.echo(f"Description: {result.get('description', 'N/A')}")


@issue_type_scheme_group.command(name="create")
@click.option("--name", "-n", required=True, help="Scheme name")
@click.option("--description", "-d", help="Description")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def issue_type_scheme_create(ctx, name, description, output):
    """Create an issue type scheme."""
    result = _create_issue_type_scheme_impl(name=name, description=description)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Issue type scheme '{name}' created with ID {result.get('id')}.")


@issue_type_scheme_group.command(name="assign")
@click.option("--project", "-p", required=True, help="Project key")
@click.option("--scheme", "-s", required=True, help="Scheme ID")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def issue_type_scheme_assign(ctx, project, scheme, output):
    """Assign an issue type scheme to a project."""
    result = _assign_issue_type_scheme_impl(project, scheme)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Scheme {scheme} assigned to project {project}.")


@issue_type_scheme_group.command(name="project")
@click.option("--project-id", "-p", required=True, help="Project ID")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def issue_type_scheme_project(ctx, project_id, output):
    """Get the issue type scheme for a project."""
    result = _get_project_issue_type_scheme_impl(project_id)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(
            f"Project {project_id} uses scheme: {result.get('name', result.get('id', 'N/A'))}"
        )


# =============================================================================
# Workflow Commands
# =============================================================================


@admin.group(name="workflow")
def workflow_group():
    """Workflow commands."""
    pass


@workflow_group.command(name="list")
@click.option("--details", "-d", is_flag=True, help="Include statuses and transitions")
@click.option("--filter", "-f", "name_filter", help="Filter by name")
@click.option(
    "--scope", "-s", type=click.Choice(["global", "project"]), help="Filter by scope"
)
@click.option("--show-usage", "-u", is_flag=True, help="Show scheme usage")
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all pages")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def workflow_list(ctx, details, name_filter, scope, show_usage, fetch_all, output):
    """List workflows."""
    result = _list_workflows_impl(
        details=details,
        name_filter=name_filter,
        scope=scope,
        show_usage=show_usage,
        fetch_all=fetch_all,
    )
    if output == "json":
        click.echo(format_json(result["workflows"]))
    else:
        click.echo(_format_workflows(result["workflows"]))
        if result["has_more"]:
            click.echo("\n(Use --all to fetch all workflows)")


@workflow_group.command(name="get")
@click.option("--name", "-n", required=True, help="Workflow name")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def workflow_get(ctx, name, output):
    """Get workflow details."""
    result = _get_workflow_impl(name)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Name: {result.get('name', 'N/A')}")
        click.echo(f"Scope: {result.get('scope_type', 'GLOBAL')}")
        click.echo(f"Default: {'Yes' if result.get('is_default') else 'No'}")
        click.echo(f"Statuses: {result.get('status_count', 'N/A')}")
        click.echo(f"Transitions: {result.get('transition_count', 'N/A')}")


@workflow_group.command(name="search")
@click.option("--query", "-q", required=True, help="Search query")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def workflow_search(ctx, query, output):
    """Search workflows."""
    result = _search_workflows_impl(query)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_workflows(result))


@workflow_group.command(name="for-issue")
@click.argument("issue_key")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def workflow_for_issue(ctx, issue_key, output):
    """Get the workflow for an issue."""
    result = _get_workflow_for_issue_impl(issue_key)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Issue {issue_key} uses workflow: {result.get('name', 'N/A')}")


@admin.group(name="workflow-scheme")
def workflow_scheme_group():
    """Workflow scheme commands."""
    pass


@workflow_scheme_group.command(name="list")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def workflow_scheme_list(ctx, output):
    """List workflow schemes."""
    result = _list_workflow_schemes_impl()
    if output == "json":
        click.echo(format_json(result))
    else:
        if not result:
            click.echo("No workflow schemes found.")
        else:
            data = []
            for scheme in result:
                data.append(
                    {
                        "ID": scheme.get("id", ""),
                        "Name": scheme.get("name", ""),
                        "Description": (scheme.get("description", "") or "")[:50],
                    }
                )
            click.echo(format_table(data, columns=["ID", "Name", "Description"]))


@workflow_scheme_group.command(name="get")
@click.option("--id", "scheme_id", required=True, help="Scheme ID")
@click.option("--show-projects", is_flag=True, help="Show projects using this scheme")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def workflow_scheme_get(ctx, scheme_id, show_projects, output):
    """Get workflow scheme details."""
    result = _get_workflow_scheme_impl(scheme_id, show_projects=show_projects)
    if output == "json":
        click.echo(format_json(result))
    else:
        scheme = result["scheme"]
        click.echo(f"Name: {scheme.get('name', 'N/A')}")
        click.echo(f"ID: {scheme.get('id', 'N/A')}")
        click.echo(f"Description: {scheme.get('description', 'N/A')}")
        if show_projects and "projects" in result:
            click.echo(f"Projects: {len(result['projects'])}")


@workflow_scheme_group.command(name="assign")
@click.option("--project", "-p", required=True, help="Project key")
@click.option("--scheme", "-s", required=True, help="Scheme ID")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def workflow_scheme_assign(ctx, project, scheme, output):
    """Assign a workflow scheme to a project."""
    result = _assign_workflow_scheme_impl(project, scheme)
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Scheme {scheme} assigned to project {project}.")


# =============================================================================
# Status Commands
# =============================================================================


@admin.group(name="status")
def status_group():
    """Status commands."""
    pass


@status_group.command(name="list")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def status_list(ctx, output):
    """List all statuses."""
    result = _list_statuses_impl()
    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_statuses(result))
        click.echo(f"\nTotal: {len(result)} status(es)")
