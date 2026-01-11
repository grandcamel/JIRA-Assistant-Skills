"""
Search commands for jira-as CLI.

Commands:
Search Commands:
- query: Search for issues using JQL
- export: Export search results to CSV/JSON
- validate: Validate JQL syntax
- build: Build JQL from components
- suggest: Get field value suggestions
- fields: List JQL fields
- functions: List JQL functions
- bulk-update: Bulk update from search results

Filter Group:
- filter list: List saved filters
- filter create: Create a new filter
- filter run: Run a saved filter
- filter update: Update filter metadata
- filter delete: Delete a filter
- filter share: Manage filter sharing
- filter favourite: Toggle filter favourite
"""

import json
from difflib import get_close_matches
from typing import Any

import click

from jira_assistant_skills_lib import (
    ValidationError,
    export_csv,
    format_search_results,
    format_table,
    get_autocomplete_cache,
    get_jira_client,
    validate_jql,
)

from ..cli_utils import format_json, handle_jira_errors, parse_comma_list

# =============================================================================
# Constants
# =============================================================================

EPIC_LINK_FIELD = "customfield_10014"
STORY_POINTS_FIELD = "customfield_10016"

# Common JQL fields for suggestions
COMMON_FIELDS = [
    "project",
    "status",
    "type",
    "issuetype",
    "priority",
    "assignee",
    "reporter",
    "creator",
    "created",
    "updated",
    "resolved",
    "duedate",
    "summary",
    "description",
    "labels",
    "component",
    "components",
    "fixVersion",
    "affectedVersion",
    "sprint",
    "epic",
    "parent",
    "resolution",
    "watchers",
    "voter",
    "comment",
    "key",
    "id",
]

# Predefined JQL templates
JQL_TEMPLATES = {
    "my-open": "assignee = currentUser() AND status != Done",
    "my-bugs": "assignee = currentUser() AND type = Bug AND status != Done",
    "my-recent": "assignee = currentUser() AND updated >= -7d ORDER BY updated DESC",
    "unassigned": "assignee IS EMPTY AND status != Done",
    "sprint-incomplete": "sprint in openSprints() AND status != Done",
    "sprint-complete": "sprint in openSprints() AND status = Done",
    "blockers": "priority = Highest AND status != Done",
    "overdue": "duedate < now() AND status != Done",
    "created-today": "created >= startOfDay()",
    "updated-today": "updated >= startOfDay()",
    "no-estimate": "timeoriginalestimate IS EMPTY AND type != Epic",
}

# Example usages for JQL functions
FUNCTION_EXAMPLES = {
    "currentUser()": "assignee = currentUser()",
    "membersOf(group)": 'assignee in membersOf("developers")',
    "startOfDay()": "created >= startOfDay(-7)",
    "startOfWeek()": "created >= startOfWeek()",
    "startOfMonth()": "created >= startOfMonth()",
    "endOfDay()": "duedate <= endOfDay()",
    "endOfWeek()": "duedate <= endOfWeek()",
    "endOfMonth()": "duedate <= endOfMonth()",
    "now()": 'updated >= now("-1h")',
    "openSprints()": "sprint in openSprints()",
    "closedSprints()": "sprint in closedSprints()",
    "futureSprints()": "sprint in futureSprints()",
}


# =============================================================================
# Helper Functions
# =============================================================================


def _suggest_correction(
    invalid_field: str, known_fields: list[str] | None = None
) -> str | None:
    """Suggest a correction for an invalid field name."""
    if known_fields is None:
        known_fields = COMMON_FIELDS

    matches = get_close_matches(
        invalid_field.lower(), [f.lower() for f in known_fields], n=1, cutoff=0.6
    )
    if matches:
        for field in known_fields:
            if field.lower() == matches[0]:
                return field
    return None


def _format_value_for_jql(value: str) -> str:
    """Format a value for use in JQL (quote if contains spaces)."""
    if " " in value:
        return f'"{value}"'
    return value


def _get_return_type(func: dict[str, Any]) -> str:
    """Extract human-readable return type from function."""
    types = func.get("types", [])
    if not types:
        return "Unknown"

    simplified = []
    for t in types:
        if "Date" in str(t):
            simplified.append("Date")
        elif "User" in str(t) or "ApplicationUser" in str(t):
            simplified.append("User")
        elif "Issue" in str(t):
            simplified.append("Issue")
        elif "Project" in str(t):
            simplified.append("Project")
        elif "Component" in str(t):
            simplified.append("Component")
        elif "Sprint" in str(t):
            simplified.append("Sprint")
        else:
            simple = str(t).split(".")[-1]
            simplified.append(simple)

    return ", ".join(set(simplified))


# =============================================================================
# Search Implementation Functions
# =============================================================================


def _search_issues_impl(
    jql: str | None = None,
    filter_id: str | None = None,
    fields: list[str] | None = None,
    max_results: int = 50,
    page_token: str | None = None,
    include_agile: bool = False,
    include_links: bool = False,
    include_time: bool = False,
    save_as: str | None = None,
    save_description: str | None = None,
    save_favourite: bool = False,
) -> dict[str, Any]:
    """Search for issues using JQL."""
    if not jql and not filter_id:
        raise ValidationError("Either JQL query or filter_id is required")

    client = get_jira_client()
    try:
        actual_jql = jql
        filter_name = None

        if filter_id:
            filter_data = client.get_filter(filter_id)
            actual_jql = filter_data.get("jql", "")
            filter_name = filter_data.get("name", f"Filter {filter_id}")

        actual_jql = validate_jql(actual_jql)

        if fields is None:
            fields = [
                "key",
                "summary",
                "status",
                "priority",
                "issuetype",
                "assignee",
                "reporter",
            ]
            if include_agile:
                fields.extend([EPIC_LINK_FIELD, STORY_POINTS_FIELD, "sprint"])
            if include_links:
                fields.append("issuelinks")
            if include_time:
                fields.append("timetracking")

        results = client.search_issues(
            actual_jql,
            fields=fields,
            max_results=max_results,
            next_page_token=page_token,
        )

        saved_filter = None
        if save_as:
            saved_filter = client.create_filter(
                save_as,
                actual_jql,
                description=save_description,
                favourite=save_favourite,
            )
            results["savedFilter"] = saved_filter

        results["_filter_name"] = filter_name
        results["_jql"] = actual_jql

        return results
    finally:
        client.close()


def _export_results_impl(
    jql: str,
    output_file: str,
    format_type: str = "csv",
    fields: list[str] | None = None,
    max_results: int = 1000,
) -> dict[str, Any]:
    """Export search results to file."""
    jql = validate_jql(jql)

    if fields is None:
        fields = [
            "key",
            "summary",
            "status",
            "priority",
            "issuetype",
            "assignee",
            "reporter",
            "created",
            "updated",
        ]

    client = get_jira_client()
    try:
        results = client.search_issues(
            jql, fields=fields, max_results=max_results, start_at=0
        )
        issues = results.get("issues", [])

        if not issues:
            return {"exported": 0, "message": "No issues found to export"}

        export_data = []
        for issue in issues:
            row = {"key": issue.get("key", "")}
            issue_fields = issue.get("fields", {})

            for field in fields:
                if field == "key":
                    continue

                value = issue_fields.get(field, "")

                if isinstance(value, dict):
                    if "displayName" in value:
                        value = value["displayName"]
                    elif "name" in value:
                        value = value["name"]
                    else:
                        value = str(value)
                elif isinstance(value, list):
                    value = ", ".join(
                        item.get("name", str(item))
                        if isinstance(item, dict)
                        else str(item)
                        for item in value
                    )

                row[field] = value

            export_data.append(row)

        if format_type == "csv":
            export_csv(
                export_data,
                output_file,
                columns=["key"] + [f for f in fields if f != "key"],
            )
        else:
            with open(output_file, "w") as f:
                json.dump(
                    {"issues": export_data, "total": len(export_data)}, f, indent=2
                )

        return {
            "exported": len(export_data),
            "output_file": output_file,
            "format": format_type,
        }
    finally:
        client.close()


def _validate_jql_impl(
    queries: list[str], show_structure: bool = False
) -> list[dict[str, Any]]:
    """Validate JQL queries."""
    if not queries:
        raise ValidationError("At least one query is required")

    client = get_jira_client()
    try:
        result = client.parse_jql(queries)
        results = []

        for i, parsed in enumerate(result.get("queries", [])):
            query = queries[i] if i < len(queries) else parsed.get("query", "")
            errors = parsed.get("errors", [])
            structure = parsed.get("structure") if show_structure else None

            results.append(
                {
                    "valid": len(errors) == 0,
                    "query": query,
                    "errors": errors,
                    "structure": structure,
                }
            )

        return results
    finally:
        client.close()


def _build_jql_impl(
    clauses: list[str] | None = None,
    template: str | None = None,
    operator: str = "AND",
    order_by: str | None = None,
    order_desc: bool = False,
    validate: bool = False,
) -> dict[str, Any]:
    """Build JQL from clauses or template."""
    if template:
        if template not in JQL_TEMPLATES:
            raise ValidationError(
                f"Unknown template: {template}. Available: {', '.join(JQL_TEMPLATES.keys())}"
            )
        jql = JQL_TEMPLATES[template]
    elif clauses:
        jql = f" {operator} ".join(clauses)
        if order_by:
            direction = "DESC" if order_desc else "ASC"
            jql = f"{jql} ORDER BY {order_by} {direction}"
    else:
        raise ValidationError("Either clauses or template is required")

    result = {"jql": jql}

    if validate:
        client = get_jira_client()
        try:
            parse_result = client.parse_jql([jql])
            parsed = parse_result.get("queries", [{}])[0]
            errors = parsed.get("errors", [])
            result["valid"] = len(errors) == 0
            result["errors"] = errors
        finally:
            client.close()

    return result


def _get_suggestions_impl(
    field_name: str,
    prefix: str = "",
    use_cache: bool = True,
    refresh_cache: bool = False,
) -> list[dict[str, Any]]:
    """Get autocomplete suggestions for a field value."""
    client = get_jira_client()
    try:
        if use_cache:
            cache = get_autocomplete_cache()
            return cache.get_suggestions(
                field_name, prefix, client, force_refresh=refresh_cache
            )
        else:
            result = client.get_jql_suggestions(field_name, prefix)
            return result.get("results", [])
    finally:
        client.close()


def _get_fields_impl(
    name_filter: str | None = None,
    custom_only: bool = False,
    system_only: bool = False,
    use_cache: bool = True,
    refresh_cache: bool = False,
) -> list[dict[str, Any]]:
    """Get JQL searchable fields."""
    client = get_jira_client()
    try:
        if use_cache:
            cache = get_autocomplete_cache()
            fields = cache.get_fields(client, force_refresh=refresh_cache)
        else:
            data = client.get_jql_autocomplete()
            fields = data.get("visibleFieldNames", [])

        if name_filter:
            name_lower = name_filter.lower()
            fields = [
                f
                for f in fields
                if name_lower in f.get("value", "").lower()
                or name_lower in f.get("displayName", "").lower()
            ]

        if custom_only:
            fields = [f for f in fields if f.get("cfid") is not None]
        elif system_only:
            fields = [f for f in fields if f.get("cfid") is None]

        return fields
    finally:
        client.close()


def _get_functions_impl(
    name_filter: str | None = None,
    list_only: bool = False,
    type_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Get JQL functions."""
    client = get_jira_client()
    try:
        data = client.get_jql_autocomplete()
        functions = data.get("visibleFunctionNames", [])

        if name_filter:
            name_lower = name_filter.lower()
            functions = [
                f
                for f in functions
                if name_lower in f.get("value", "").lower()
                or name_lower in f.get("displayName", "").lower()
            ]

        if list_only:
            functions = [f for f in functions if f.get("isList") == "true"]

        if type_filter:
            type_lower = type_filter.lower()
            functions = [
                f
                for f in functions
                if any(type_lower in str(t).lower() for t in f.get("types", []))
            ]

        return functions
    finally:
        client.close()


def _bulk_update_impl(
    jql: str,
    add_labels: list[str] | None = None,
    remove_labels: list[str] | None = None,
    priority: str | None = None,
    max_issues: int = 100,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Bulk update issues from search results."""
    jql = validate_jql(jql)

    client = get_jira_client()
    try:
        results = client.search_issues(
            jql, fields=["key", "summary", "labels"], max_results=max_issues
        )

        issues = results.get("issues", [])
        total = results.get("total", 0)

        if not issues:
            return {"updated": 0, "failed": 0, "message": "No issues found to update"}

        if dry_run:
            return {
                "would_update": len(issues),
                "total_matching": total,
                "issues": [i["key"] for i in issues],
                "changes": {
                    "add_labels": add_labels,
                    "remove_labels": remove_labels,
                    "priority": priority,
                },
            }

        updated = 0
        failed = 0
        failures = []

        for issue in issues:
            try:
                issue_key = issue["key"]
                fields = {}

                if add_labels or remove_labels:
                    current_labels = set(issue.get("fields", {}).get("labels", []))
                    if add_labels:
                        current_labels.update(add_labels)
                    if remove_labels:
                        current_labels.difference_update(remove_labels)
                    fields["labels"] = list(current_labels)

                if priority:
                    fields["priority"] = {"name": priority}

                if fields:
                    client.update_issue(issue_key, fields, notify_users=False)
                    updated += 1

            except Exception as e:
                failed += 1
                failures.append({"issue": issue["key"], "error": str(e)})

        return {"updated": updated, "failed": failed, "failures": failures}
    finally:
        client.close()


# =============================================================================
# Filter Implementation Functions
# =============================================================================


def _get_filters_impl(
    my_filters: bool = False,
    favourites: bool = False,
    search_name: str | None = None,
    filter_id: str | None = None,
    owner: str | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    """Get saved filters."""
    client = get_jira_client()
    try:
        if filter_id:
            filter_data = client.get_filter(filter_id)
            return {"type": "single", "filter": filter_data}

        if my_filters:
            filters = client.get_my_filters()
            return {"type": "my", "filters": filters}

        if favourites:
            filters = client.get_favourite_filters()
            return {"type": "favourites", "filters": filters}

        if search_name:
            account_id = None
            if owner:
                if owner.lower() == "self":
                    account_id = client.get_current_user_id()
                else:
                    account_id = owner

            result = client.search_filters(
                filter_name=search_name if search_name != "*" else None,
                account_id=account_id,
                project_key=project,
            )
            return {"type": "search", "filters": result.get("values", [])}

        raise ValidationError("Specify --my, --favourites, --search, or --id")
    finally:
        client.close()


def _create_filter_impl(
    name: str,
    jql: str,
    description: str | None = None,
    favourite: bool = False,
    share_project: str | None = None,
    share_group: str | None = None,
    share_global: bool = False,
) -> dict[str, Any]:
    """Create a new filter."""
    if not name:
        raise ValidationError("Filter name is required")
    if not jql:
        raise ValidationError("JQL query is required")

    permissions = []
    if share_project:
        permissions.append({"type": "project", "project": {"id": share_project}})
    if share_group:
        permissions.append({"type": "group", "group": {"name": share_group}})
    if share_global:
        permissions.append({"type": "global"})

    client = get_jira_client()
    try:
        return client.create_filter(
            name=name,
            jql=jql,
            description=description,
            favourite=favourite,
            share_permissions=permissions if permissions else None,
        )
    finally:
        client.close()


def _run_filter_impl(
    filter_id: str | None = None,
    filter_name: str | None = None,
    max_results: int = 50,
) -> dict[str, Any]:
    """Run a saved filter."""
    if not filter_id and not filter_name:
        raise ValidationError("Either filter_id or filter_name is required")

    client = get_jira_client()
    try:
        if filter_name:
            filters = client.get("/rest/api/3/filter/my", operation="get filters")
            if isinstance(filters, list):
                matching = [
                    f
                    for f in filters
                    if f.get("name", "").lower() == filter_name.lower()
                ]
                if not matching:
                    raise ValidationError(f"Filter '{filter_name}' not found")
                filter_id = matching[0]["id"]
            else:
                raise ValidationError("Could not retrieve filters")

        filter_data = client.get_filter(filter_id)
        jql = filter_data.get("jql", "")

        if not jql:
            raise ValidationError(f"Filter {filter_id} has no JQL query")

        results = client.search_issues(jql, max_results=max_results)
        results["_filter"] = filter_data

        return results
    finally:
        client.close()


def _update_filter_impl(
    filter_id: str,
    name: str | None = None,
    jql: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Update a filter."""
    if not any([name, jql, description]):
        raise ValidationError("At least one of name, jql, or description is required")

    client = get_jira_client()
    try:
        return client.update_filter(
            filter_id, name=name, jql=jql, description=description
        )
    finally:
        client.close()


def _delete_filter_impl(filter_id: str, dry_run: bool = False) -> dict[str, Any]:
    """Delete a filter."""
    client = get_jira_client()
    try:
        filter_data = client.get_filter(filter_id)

        if dry_run:
            return {
                "would_delete": True,
                "filter_id": filter_id,
                "filter_name": filter_data.get("name"),
                "jql": filter_data.get("jql"),
            }

        client.delete_filter(filter_id)
        return {
            "deleted": True,
            "filter_id": filter_id,
            "filter_name": filter_data.get("name"),
        }
    finally:
        client.close()


def _share_filter_impl(
    filter_id: str,
    project: str | None = None,
    role: str | None = None,
    group: str | None = None,
    share_global: bool = False,
    user: str | None = None,
    list_permissions: bool = False,
    unshare: str | None = None,
) -> dict[str, Any]:
    """Manage filter sharing permissions."""
    client = get_jira_client()
    try:
        if list_permissions:
            permissions = client.get_filter_permissions(filter_id)
            return {"action": "list", "permissions": permissions}

        if unshare:
            client.delete_filter_permission(filter_id, unshare)
            return {"action": "removed", "permission_id": unshare}

        if project:
            if role:
                roles = client.get(f"/rest/api/3/project/{project}/role")
                role_id = None
                for name, url in roles.items():
                    if name.lower() == role.lower():
                        role_id = url.split("/")[-1]
                        break
                if not role_id:
                    raise ValidationError(
                        f"Role '{role}' not found in project {project}"
                    )
                permission = {
                    "type": "projectRole",
                    "projectId": project,
                    "projectRoleId": role_id,
                }
            else:
                permission = {"type": "project", "projectId": project}
            result = client.add_filter_permission(filter_id, permission)
            return {"action": "shared", "type": "project", "permission": result}

        if group:
            permission = {"type": "group", "groupname": group}
            result = client.add_filter_permission(filter_id, permission)
            return {"action": "shared", "type": "group", "permission": result}

        if share_global:
            permission = {"type": "global"}
            result = client.add_filter_permission(filter_id, permission)
            return {"action": "shared", "type": "global", "permission": result}

        if user:
            permission = {"type": "user", "accountId": user}
            result = client.add_filter_permission(filter_id, permission)
            return {"action": "shared", "type": "user", "permission": result}

        raise ValidationError(
            "Specify --project, --group, --global, --user, --list, or --unshare"
        )
    finally:
        client.close()


def _favourite_filter_impl(
    filter_id: str,
    add: bool = False,
    remove: bool = False,
) -> dict[str, Any]:
    """Manage filter favourite status."""
    client = get_jira_client()
    try:
        if add:
            result = client.add_filter_favourite(filter_id)
            return {"action": "added", "filter": result}

        if remove:
            filter_data = client.get_filter(filter_id)
            client.remove_filter_favourite(filter_id)
            return {"action": "removed", "filter_name": filter_data.get("name")}

        # Toggle
        filter_data = client.get_filter(filter_id)
        is_favourite = filter_data.get("favourite", False)

        if is_favourite:
            client.remove_filter_favourite(filter_id)
            return {"action": "removed", "filter": filter_data}
        else:
            result = client.add_filter_favourite(filter_id)
            return {"action": "added", "filter": result}
    finally:
        client.close()


# =============================================================================
# Formatting Functions
# =============================================================================


def _format_search_output(
    results: dict, show_agile: bool, show_links: bool, show_time: bool
) -> str:
    """Format search results for text output."""
    lines = []
    issues = results.get("issues", [])
    total = results.get("total")
    is_last = results.get("isLast", True)

    if total is not None:
        lines.append(f"Found {total} issue(s)")
    else:
        count_msg = f"Found {len(issues)} issue(s)"
        if not is_last:
            count_msg += " (more available)"
        lines.append(count_msg)

    filter_name = results.get("_filter_name")
    if filter_name:
        lines.insert(0, f"Running filter: {filter_name}")
        lines.insert(1, f"JQL: {results.get('_jql', '')}")
        lines.insert(2, "")

    if issues:
        lines.append("")
        lines.append(
            format_search_results(
                issues,
                show_agile=show_agile,
                show_links=show_links,
                show_time=show_time,
            )
        )

        next_token = results.get("nextPageToken")
        if next_token:
            lines.append("")
            if total is not None:
                lines.append(f"Showing {len(issues)} of {total} results")
            else:
                lines.append(f"Showing {len(issues)} results (more available)")
            lines.append(f"Next page token: {next_token}")
            lines.append("Use --page-token to fetch next page")

    saved_filter = results.get("savedFilter")
    if saved_filter:
        lines.append("")
        lines.append(
            f"Saved as filter: {saved_filter.get('name')} (ID: {saved_filter.get('id')})"
        )

    return "\n".join(lines)


def _format_validation_result(result: dict) -> str:
    """Format a validation result."""
    lines = []
    query = result.get("query", "")
    lines.append(f"JQL Query: {query}")
    lines.append("")

    if result["valid"]:
        lines.append("Valid JQL")

        if result.get("structure"):
            lines.append("")
            lines.append("Structure:")
            structure = result["structure"]
            where = structure.get("where", {})
            if where:
                clauses = where.get("clauses", [])
                for clause in clauses:
                    field = clause.get("field", {}).get("name", "?")
                    operator = clause.get("operator", "?")
                    operand = clause.get("operand", {})
                    if isinstance(operand, dict):
                        value = operand.get("value", operand.get("values", "?"))
                    else:
                        value = operand
                    lines.append(f"  {field} {operator} {value}")
    else:
        lines.append("Invalid JQL")
        lines.append("")
        lines.append("Errors:")
        for i, error in enumerate(result["errors"], 1):
            lines.append(f"  {i}. {error}")

            if "does not exist" in error.lower() and "'" in error:
                import re

                match = re.search(r"'(\w+)'", error)
                if match:
                    invalid_field = match.group(1)
                    suggestion = _suggest_correction(invalid_field)
                    if suggestion:
                        lines.append(f"     -> Did you mean '{suggestion}'?")

    return "\n".join(lines)


def _format_suggestions(field_name: str, suggestions: list) -> str:
    """Format suggestions for text output."""
    if not suggestions:
        return f"No suggestions found for '{field_name}'\n\nThis field may be a free-text field or have no configured values."

    data = []
    for s in suggestions:
        value = s.get("value", "")
        display = s.get("displayName", value)
        data.append({"Value": _format_value_for_jql(value), "Display Name": display})

    data.sort(key=lambda x: x["Display Name"].lower())
    table = format_table(data, columns=["Value", "Display Name"])

    example_value = _format_value_for_jql(suggestions[0].get("value", ""))
    example = f"\nUsage: {field_name} = {example_value}"

    return f"Suggestions for '{field_name}':\n\n{table}{example}"


def _format_fields(fields: list) -> str:
    """Format fields for text output."""
    if not fields:
        return "No fields found"

    data = []
    for field in fields:
        operators = field.get("operators", [])
        ops_str = ", ".join(operators)
        if len(ops_str) > 40:
            ops_str = ops_str[:37] + "..."

        data.append(
            {
                "Field": field.get("value", ""),
                "Display Name": field.get("displayName", ""),
                "Type": "Custom" if field.get("cfid") else "System",
                "Operators": ops_str,
            }
        )

    data.sort(key=lambda x: x["Display Name"].lower())

    custom_count = sum(1 for f in fields if f.get("cfid"))
    system_count = len(fields) - custom_count

    table = format_table(data, columns=["Field", "Display Name", "Type", "Operators"])
    return f"JQL Fields:\n\n{table}\n\nTotal: {len(fields)} fields ({system_count} system, {custom_count} custom)"


def _format_functions(functions: list, show_examples: bool = False) -> str:
    """Format functions for text output."""
    if not functions:
        return "No functions found"

    data = []
    for func in functions:
        is_list = func.get("isList") == "true"
        return_type = _get_return_type(func)

        data.append(
            {
                "Function": func.get("value", ""),
                "Returns List": "Yes" if is_list else "No",
                "Type": return_type,
            }
        )

    data.sort(key=lambda x: x["Function"].lower())
    table = format_table(data, columns=["Function", "Returns List", "Type"])

    if show_examples:
        examples = []
        for func in functions:
            func_name = func.get("value", "")
            for key, example in FUNCTION_EXAMPLES.items():
                if key in func_name or func_name in key:
                    examples.append(f"  {example}")
                    break

        if examples:
            examples = examples[:5]
            table += "\n\nExamples:\n" + "\n".join(examples)

    return f"JQL Functions:\n\n{table}\n\nTotal: {len(functions)} functions"


def _format_filters(filters: list) -> str:
    """Format filters for text output."""
    if not filters:
        return "No filters found"

    data = []
    for f in filters:
        jql = f.get("jql", "")
        if len(jql) > 40:
            jql = jql[:37] + "..."

        data.append(
            {
                "ID": f.get("id", ""),
                "Name": f.get("name", ""),
                "Favourite": "Yes" if f.get("favourite") else "No",
                "Owner": f.get("owner", {}).get("displayName", ""),
                "JQL": jql,
            }
        )

    data.sort(key=lambda x: x["Name"].lower())
    table = format_table(data, columns=["ID", "Name", "Favourite", "Owner", "JQL"])

    fav_count = sum(1 for f in filters if f.get("favourite"))
    return f"{table}\n\nTotal: {len(filters)} filters ({fav_count} favourites)"


def _format_filter_detail(filter_data: dict) -> str:
    """Format single filter with full details."""
    lines = []

    lines.append(f"ID:          {filter_data.get('id', 'N/A')}")
    lines.append(f"Name:        {filter_data.get('name', 'N/A')}")

    owner = filter_data.get("owner", {})
    lines.append(f"Owner:       {owner.get('displayName', 'N/A')}")
    lines.append(f"Favourite:   {'Yes' if filter_data.get('favourite') else 'No'}")

    description = filter_data.get("description")
    lines.append(f"Description: {description if description else '(none)'}")

    lines.append("")
    lines.append(f"JQL: {filter_data.get('jql', 'N/A')}")

    permissions = filter_data.get("sharePermissions", [])
    if permissions:
        lines.append("")
        lines.append("Shared With:")
        for p in permissions:
            ptype = p.get("type", "")
            if ptype == "project":
                proj = p.get("project", {})
                lines.append(f"  - Project: {proj.get('name', proj.get('key', '?'))}")
            elif ptype == "group":
                grp = p.get("group", {})
                lines.append(f"  - Group: {grp.get('name', '?')}")
            elif ptype == "global":
                lines.append("  - Global (all users)")

    view_url = filter_data.get("viewUrl", "")
    if view_url:
        lines.append("")
        lines.append(f"View URL: {view_url}")

    return "\n".join(lines)


# =============================================================================
# Click Commands
# =============================================================================


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
@click.option("--page-token", "-p", help="Page token for pagination")
@click.option("--show-links", "-l", is_flag=True, help="Show issue links")
@click.option("--show-time", "-t", is_flag=True, help="Show time tracking info")
@click.option(
    "--show-agile", "-a", is_flag=True, help="Show agile fields (epic, points)"
)
@click.option("--save-as", help="Save search as a new filter with this name")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def search_query(
    ctx,
    jql,
    filter_id,
    fields,
    max_results,
    page_token,
    show_links,
    show_time,
    show_agile,
    save_as,
    output,
):
    """Search for issues using JQL query."""
    if not jql and not filter_id:
        raise click.UsageError("Either JQL query or --filter is required")

    field_list = parse_comma_list(fields)

    result = _search_issues_impl(
        jql=jql,
        filter_id=filter_id,
        fields=field_list,
        max_results=max_results,
        page_token=page_token,
        include_agile=show_agile,
        include_links=show_links,
        include_time=show_time,
        save_as=save_as,
    )

    if output == "json":
        output_data = {k: v for k, v in result.items() if not k.startswith("_")}
        click.echo(format_json(output_data))
    else:
        click.echo(_format_search_output(result, show_agile, show_links, show_time))


@search.command(name="export")
@click.argument("jql")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["csv", "json"]),
    default="csv",
    help="Export format",
)
@click.option("--output", "-o", "output_file", required=True, help="Output file path")
@click.option("--fields", help="Comma-separated list of fields to export")
@click.option(
    "--max-results", "-m", type=int, default=1000, help="Maximum results to export"
)
@click.pass_context
@handle_jira_errors
def search_export(ctx, jql, output_format, output_file, fields, max_results):
    """Export search results to CSV or JSON."""
    field_list = parse_comma_list(fields)

    result = _export_results_impl(
        jql=jql,
        output_file=output_file,
        format_type=output_format,
        fields=field_list,
        max_results=max_results,
    )

    click.echo(f"Exported {result['exported']} issues to {result['output_file']}")


@search.command(name="validate")
@click.argument("jql", nargs=-1, required=True)
@click.option(
    "--show-structure", "-s", is_flag=True, help="Show parsed query structure"
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def search_validate(ctx, jql, show_structure, output):
    """Validate JQL query syntax."""
    queries = list(jql)
    results = _validate_jql_impl(queries, show_structure=show_structure)

    if output == "json":
        click.echo(format_json(results))
    else:
        for i, result in enumerate(results):
            if i > 0:
                click.echo("\n" + "-" * 50 + "\n")
            click.echo(_format_validation_result(result))

    all_valid = all(r["valid"] for r in results)
    if not all_valid:
        ctx.exit(1)


@search.command(name="build")
@click.option("--clause", "-c", multiple=True, help="JQL clause (can be repeated)")
@click.option("--template", "-t", help="Use predefined template")
@click.option(
    "--operator",
    "-op",
    type=click.Choice(["AND", "OR"]),
    default="AND",
    help="Clause join operator",
)
@click.option("--order-by", "-o", help="Field to order by")
@click.option("--desc", is_flag=True, help="Use descending order")
@click.option("--validate", "-v", is_flag=True, help="Validate the built query")
@click.option("--list-templates", "-l", is_flag=True, help="List available templates")
@click.option(
    "--output",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def search_build(
    ctx, clause, template, operator, order_by, desc, validate, list_templates, output
):
    """Build a JQL query from components."""
    if list_templates:
        lines = ["Available Templates:", ""]
        for name, jql in sorted(JQL_TEMPLATES.items()):
            lines.append(f"  {name}")
            lines.append(f"    {jql}")
            lines.append("")
        click.echo("\n".join(lines))
        return

    if not clause and not template:
        raise click.UsageError("Provide --clause or --template to build a query")

    result = _build_jql_impl(
        clauses=list(clause) if clause else None,
        template=template,
        operator=operator,
        order_by=order_by,
        order_desc=desc,
        validate=validate,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo("Built JQL Query:")
        click.echo(f"{result['jql']}")
        click.echo("")
        if validate:
            if result.get("valid"):
                click.echo("Query validated successfully")
            else:
                click.echo("Validation FAILED:")
                for error in result.get("errors", []):
                    click.echo(f"  - {error}")
                ctx.exit(1)
        else:
            click.echo("Use --validate to check syntax against JIRA")


@search.command(name="suggest")
@click.option("--field", "-f", required=True, help="Field name to get suggestions for")
@click.option("--prefix", "-x", default="", help="Filter suggestions by prefix")
@click.option("--no-cache", is_flag=True, help="Bypass cache and fetch from API")
@click.option("--refresh", is_flag=True, help="Force refresh cache from API")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def search_suggest(ctx, field, prefix, no_cache, refresh, output):
    """Get JQL field value suggestions for autocomplete."""
    suggestions = _get_suggestions_impl(
        field_name=field,
        prefix=prefix,
        use_cache=not no_cache,
        refresh_cache=refresh,
    )

    if output == "json":
        click.echo(format_json(suggestions))
    else:
        click.echo(_format_suggestions(field, suggestions))


@search.command(name="fields")
@click.option("--filter", "-f", "name_filter", help="Filter fields by name")
@click.option("--custom-only", is_flag=True, help="Show only custom fields")
@click.option("--system-only", is_flag=True, help="Show only system fields")
@click.option("--no-cache", is_flag=True, help="Bypass cache")
@click.option("--refresh", is_flag=True, help="Refresh cache")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def search_fields(
    ctx, name_filter, custom_only, system_only, no_cache, refresh, output
):
    """List available JQL fields and operators."""
    if custom_only and system_only:
        raise click.UsageError("--custom-only and --system-only are mutually exclusive")

    fields = _get_fields_impl(
        name_filter=name_filter,
        custom_only=custom_only,
        system_only=system_only,
        use_cache=not no_cache,
        refresh_cache=refresh,
    )

    if output == "json":
        click.echo(format_json(fields))
    else:
        click.echo(_format_fields(fields))


@search.command(name="functions")
@click.option("--filter", "-f", "name_filter", help="Filter functions by name")
@click.option("--list-only", is_flag=True, help="Show only functions returning lists")
@click.option("--type", "-t", "type_filter", help="Filter by return type")
@click.option("--with-examples", is_flag=True, help="Include usage examples")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def search_functions(ctx, name_filter, list_only, type_filter, with_examples, output):
    """List available JQL functions."""
    functions = _get_functions_impl(
        name_filter=name_filter,
        list_only=list_only,
        type_filter=type_filter,
    )

    if output == "json":
        click.echo(format_json(functions))
    else:
        click.echo(_format_functions(functions, show_examples=with_examples))


@search.command(name="bulk-update")
@click.argument("jql")
@click.option("--add-labels", help="Comma-separated labels to add")
@click.option("--remove-labels", help="Comma-separated labels to remove")
@click.option("--priority", help="Priority to set")
@click.option("--max-issues", type=int, default=100, help="Maximum issues to update")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without making changes")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def search_bulk_update(
    ctx, jql, add_labels, remove_labels, priority, max_issues, dry_run, yes, output
):
    """Bulk update issues from JQL search results."""
    if not add_labels and not remove_labels and not priority:
        raise click.UsageError(
            "At least one of --add-labels, --remove-labels, or --priority is required"
        )

    add_list = parse_comma_list(add_labels)
    remove_list = parse_comma_list(remove_labels)

    result = _bulk_update_impl(
        jql=jql,
        add_labels=add_list,
        remove_labels=remove_list,
        priority=priority,
        max_issues=max_issues,
        dry_run=dry_run or not yes,  # Require --yes for actual updates
    )

    if output == "json":
        click.echo(format_json(result))
    elif dry_run or not yes:
        click.echo(f"Would update {result.get('would_update', 0)} issue(s)")
        if result.get("issues"):
            click.echo("Issues:")
            for key in result["issues"]:
                click.echo(f"  - {key}")
        click.echo("\nUse --yes to apply changes")
    else:
        click.echo(f"Updated {result['updated']} issue(s)")
        if result["failed"] > 0:
            click.echo(f"Failed: {result['failed']}")


# --- Filter Subgroup ---


@search.group()
def filter():
    """Manage saved filters."""
    pass


@filter.command(name="list")
@click.option("--my", "-m", "my_filters", is_flag=True, help="List your own filters")
@click.option("--favourites", "-f", is_flag=True, help="List favourite filters")
@click.option("--search", "-s", help="Search filters by name")
@click.option("--id", "-i", "filter_id", help="Get specific filter by ID")
@click.option("--owner", help='Filter by owner (account ID or "self")')
@click.option("--project", help="Filter by project key")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def filter_list(ctx, my_filters, favourites, search, filter_id, owner, project, output):
    """List saved filters."""
    if not any([my_filters, favourites, search, filter_id]):
        my_filters = True  # Default to showing user's filters

    result = _get_filters_impl(
        my_filters=my_filters,
        favourites=favourites,
        search_name=search,
        filter_id=filter_id,
        owner=owner,
        project=project,
    )

    if output == "json":
        if result["type"] == "single":
            click.echo(format_json(result["filter"]))
        else:
            click.echo(format_json(result["filters"]))
    else:
        if result["type"] == "single":
            click.echo("Filter Details:\n")
            click.echo(_format_filter_detail(result["filter"]))
        else:
            title = {
                "my": "My Filters",
                "favourites": "Favourite Filters",
                "search": "Search Results",
            }
            click.echo(f"{title.get(result['type'], 'Filters')}:\n")
            click.echo(_format_filters(result["filters"]))


@filter.command(name="create")
@click.option("--name", "-n", required=True, help="Filter name")
@click.option("--jql", "-j", required=True, help="JQL query string")
@click.option("--description", "-d", help="Filter description")
@click.option("--favourite", "-f", is_flag=True, help="Add to favourites")
@click.option("--share-project", help="Share with project (ID or key)")
@click.option("--share-group", help="Share with group")
@click.option("--share-global", is_flag=True, help="Share with all users")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def filter_create(
    ctx,
    name,
    jql,
    description,
    favourite,
    share_project,
    share_group,
    share_global,
    output,
):
    """Create a new saved filter."""
    result = _create_filter_impl(
        name=name,
        jql=jql,
        description=description,
        favourite=favourite,
        share_project=share_project,
        share_group=share_group,
        share_global=share_global,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo("Filter created successfully:\n")
        click.echo(f"  ID:   {result.get('id')}")
        click.echo(f"  Name: {result.get('name')}")
        click.echo(f"  JQL:  {result.get('jql')}")
        if result.get("viewUrl"):
            click.echo(f"\n  View URL: {result.get('viewUrl')}")


@filter.command(name="run")
@click.option("--id", "-i", "filter_id", help="Filter ID")
@click.option("--name", "-n", "filter_name", help="Filter name")
@click.option("--max-results", "-m", type=int, default=50, help="Maximum results")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def filter_run(ctx, filter_id, filter_name, max_results, output):
    """Run a saved filter."""
    if not filter_id and not filter_name:
        raise click.UsageError("Either --id or --name is required")

    result = _run_filter_impl(
        filter_id=filter_id,
        filter_name=filter_name,
        max_results=max_results,
    )

    issues = result.get("issues", [])
    total = result.get("total", 0)

    if output == "json":
        output_data = {k: v for k, v in result.items() if not k.startswith("_")}
        click.echo(format_json(output_data))
    else:
        filter_data = result.get("_filter", {})
        click.echo(f"Filter: {filter_data.get('name')} (ID: {filter_data.get('id')})")
        click.echo(f"Found {total} issue(s)")
        if issues:
            click.echo("")
            click.echo(format_search_results(issues))


@filter.command(name="update")
@click.argument("filter_id")
@click.option("--name", "-n", help="New filter name")
@click.option("--jql", "-j", help="New JQL query")
@click.option("--description", "-d", help="New description")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def filter_update(ctx, filter_id, name, jql, description, output):
    """Update a saved filter."""
    if not any([name, jql, description]):
        raise click.UsageError(
            "At least one of --name, --jql, or --description is required"
        )

    result = _update_filter_impl(
        filter_id=filter_id,
        name=name,
        jql=jql,
        description=description,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo("Filter updated successfully:\n")
        click.echo(f"  ID:   {result.get('id')}")
        click.echo(f"  Name: {result.get('name')}")
        click.echo(f"  JQL:  {result.get('jql')}")


@filter.command(name="delete")
@click.argument("filter_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without deleting")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def filter_delete(ctx, filter_id, yes, dry_run, output):
    """Delete a saved filter."""
    result = _delete_filter_impl(filter_id, dry_run=dry_run or not yes)

    if output == "json":
        click.echo(format_json(result))
    elif dry_run or not yes:
        click.echo("Would delete filter:")
        click.echo(f"  ID:   {result.get('filter_id')}")
        click.echo(f"  Name: {result.get('filter_name')}")
        click.echo("\nUse --yes to confirm deletion")
    else:
        click.echo(f"Filter {result.get('filter_id')} deleted successfully.")


@filter.command(name="share")
@click.argument("filter_id")
@click.option("--project", "-p", help="Share with project")
@click.option("--role", "-r", help="Project role (used with --project)")
@click.option("--group", "-g", help="Share with group")
@click.option("--global", "share_global", is_flag=True, help="Share with all users")
@click.option("--user", "-u", help="Share with user (account ID)")
@click.option(
    "--list", "-l", "list_perms", is_flag=True, help="List current permissions"
)
@click.option("--unshare", help="Remove permission (permission ID)")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def filter_share(
    ctx,
    filter_id,
    project,
    role,
    group,
    share_global,
    user,
    list_perms,
    unshare,
    output,
):
    """Share a filter with users, groups, or projects."""
    if not any([project, group, share_global, user, list_perms, unshare]):
        raise click.UsageError(
            "Specify --project, --group, --global, --user, --list, or --unshare"
        )

    result = _share_filter_impl(
        filter_id=filter_id,
        project=project,
        role=role,
        group=group,
        share_global=share_global,
        user=user,
        list_permissions=list_perms,
        unshare=unshare,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        if result["action"] == "list":
            permissions = result["permissions"]
            if not permissions:
                click.echo(f"Filter {filter_id} has no share permissions (private).")
            else:
                click.echo(f"Share permissions for filter {filter_id}:\n")
                click.echo(f"{'ID':<10} {'Type':<15} {'Shared With':<40}")
                click.echo("-" * 65)
                for perm in permissions:
                    perm_id = perm.get("id", "N/A")
                    perm_type = perm.get("type", "unknown")
                    shared_with = perm_type  # Simplified
                    click.echo(f"{perm_id:<10} {perm_type:<15} {shared_with:<40}")
        elif result["action"] == "removed":
            click.echo(
                f"Permission {result.get('permission_id')} removed from filter {filter_id}."
            )
        else:
            click.echo(f"Filter {filter_id} shared with {result.get('type')}.")


@filter.command(name="favourite")
@click.argument("filter_id")
@click.option("--add", "-a", is_flag=True, help="Add to favourites")
@click.option("--remove", "-r", is_flag=True, help="Remove from favourites")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def filter_favourite(ctx, filter_id, add, remove, output):
    """Toggle filter favourite status."""
    if add and remove:
        raise click.UsageError("--add and --remove are mutually exclusive")

    result = _favourite_filter_impl(filter_id, add=add, remove=remove)

    if output == "json":
        click.echo(format_json(result))
    else:
        filter_name = result.get("filter", {}).get("name") or result.get(
            "filter_name", filter_id
        )
        if result["action"] == "added":
            click.echo(f'Filter {filter_id} "{filter_name}" added to favourites.')
        else:
            click.echo(f'Filter {filter_id} "{filter_name}" removed from favourites.')
