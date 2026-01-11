"""
Bulk operation commands for jira-as CLI.

Commands:
- transition: Bulk transition issues to a new status
- assign: Bulk assign/unassign issues
- set-priority: Bulk set priority on issues
- clone: Bulk clone issues
- delete: Bulk delete issues (destructive)
"""

import time
from typing import Any

import click

from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    text_to_adf,
    validate_issue_key,
    validate_jql,
    validate_project_key,
)

from ..cli_utils import format_json, handle_jira_errors, parse_comma_list

# =============================================================================
# Constants
# =============================================================================

# Standard JIRA priorities
STANDARD_PRIORITIES = [
    "Highest",
    "High",
    "Medium",
    "Low",
    "Lowest",
    "Blocker",
    "Critical",
    "Major",
    "Minor",
    "Trivial",
]

# Fields to copy when cloning
CLONE_FIELDS = [
    "summary",
    "description",
    "issuetype",
    "priority",
    "labels",
    "components",
    "fixVersions",
    "duedate",
    "environment",
]


# =============================================================================
# Helper Functions
# =============================================================================


def _get_issues_to_process(
    client,
    issue_keys: list[str] | None = None,
    jql: str | None = None,
    max_issues: int = 100,
    fields: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Retrieve issues to process from either issue keys or JQL query.

    Args:
        client: JiraClient instance
        issue_keys: List of issue keys to process
        jql: JQL query to find issues (alternative to issue_keys)
        max_issues: Maximum number of issues to retrieve
        fields: List of fields to retrieve

    Returns:
        List of issue dictionaries
    """
    if fields is None:
        fields = ["key", "summary"]

    if issue_keys:
        validated_keys = [validate_issue_key(k) for k in issue_keys[:max_issues]]
        return [{"key": key} for key in validated_keys]
    elif jql:
        validated_jql = validate_jql(jql)
        result = client.search_issues(
            validated_jql, fields=fields, max_results=max_issues
        )
        return result.get("issues", [])
    else:
        raise ValidationError("Either --issues or --jql must be provided")


def _find_transition(transitions: list[dict], target_status: str) -> dict | None:
    """Find a transition that leads to the target status."""
    target_lower = target_status.lower()

    # First try exact match on transition name
    for t in transitions:
        if t["name"].lower() == target_lower:
            return t

    # Then try matching target status name
    for t in transitions:
        to_status = t.get("to", {}).get("name", "").lower()
        if to_status == target_lower:
            return t

    # Finally try partial match
    for t in transitions:
        if (
            target_lower in t["name"].lower()
            or target_lower in t.get("to", {}).get("name", "").lower()
        ):
            return t

    return None


def _resolve_user_id(client, user_identifier: str) -> str | None:
    """Resolve a user identifier to an account ID."""
    if user_identifier is None:
        return None

    if user_identifier.lower() == "self":
        return client.get_current_user_id()

    # Check if it looks like an email
    if "@" in user_identifier:
        try:
            users = client.get(
                "/rest/api/3/user/search",
                params={"query": user_identifier},
                operation="search users",
            )
            if users and len(users) > 0:
                for user in users:
                    if user.get("emailAddress", "").lower() == user_identifier.lower():
                        return user["accountId"]
                return users[0]["accountId"]
        except JiraError:
            pass

    return user_identifier


def _validate_priority(priority: str) -> str:
    """Validate and normalize priority name."""
    for std in STANDARD_PRIORITIES:
        if std.lower() == priority.lower():
            return std

    raise ValidationError(
        f"Invalid priority: '{priority}'. "
        f"Valid priorities: {', '.join(STANDARD_PRIORITIES)}"
    )


# =============================================================================
# Implementation Functions
# =============================================================================


def _bulk_transition_impl(
    issue_keys: list[str] | None = None,
    jql: str | None = None,
    target_status: str | None = None,
    resolution: str | None = None,
    comment: str | None = None,
    dry_run: bool = False,
    max_issues: int = 100,
    delay: float = 0.1,
) -> dict[str, Any]:
    """Transition multiple issues to a new status."""
    if not target_status:
        raise ValidationError("Target status is required")

    client = get_jira_client()
    try:
        issues = _get_issues_to_process(
            client,
            issue_keys=issue_keys,
            jql=jql,
            max_issues=max_issues,
            fields=["key", "summary", "status"],
        )

        total = len(issues)

        if total == 0:
            return {
                "success": 0,
                "failed": 0,
                "total": 0,
                "errors": {},
                "processed": [],
            }

        if dry_run:
            preview = []
            for issue in issues:
                key = issue.get("key")
                current_status = (
                    issue.get("fields", {}).get("status", {}).get("name", "Unknown")
                )
                preview.append(
                    {
                        "key": key,
                        "from": current_status,
                        "to": target_status,
                    }
                )

            return {
                "dry_run": True,
                "success": 0,
                "failed": 0,
                "would_process": total,
                "total": total,
                "issues": preview,
                "errors": {},
                "processed": [],
            }

        success = 0
        failed = 0
        errors = {}
        processed = []

        for i, issue in enumerate(issues, 1):
            issue_key = issue.get("key")

            try:
                transitions = client.get_transitions(issue_key)
                transition = _find_transition(transitions, target_status)

                if not transition:
                    available = [t["name"] for t in transitions]
                    raise ValidationError(
                        f"Transition to '{target_status}' not available. "
                        f"Available: {', '.join(available)}"
                    )

                fields = {}
                if resolution:
                    fields["resolution"] = {"name": resolution}

                client.transition_issue(
                    issue_key, transition["id"], fields=fields if fields else None
                )

                if comment:
                    client.add_comment(issue_key, text_to_adf(comment))

                success += 1
                processed.append(issue_key)

            except Exception as e:
                failed += 1
                errors[issue_key] = str(e)

            if i < total and delay > 0:
                time.sleep(delay)

        return {
            "success": success,
            "failed": failed,
            "total": total,
            "errors": errors,
            "processed": processed,
        }
    finally:
        client.close()


def _bulk_assign_impl(
    issue_keys: list[str] | None = None,
    jql: str | None = None,
    assignee: str | None = None,
    unassign: bool = False,
    dry_run: bool = False,
    max_issues: int = 100,
    delay: float = 0.1,
) -> dict[str, Any]:
    """Assign or unassign multiple issues."""
    if not assignee and not unassign:
        raise ValidationError("Either --assignee or --unassign must be provided")

    client = get_jira_client()
    try:
        account_id = None
        action = "unassign"
        if not unassign:
            account_id = _resolve_user_id(client, assignee)
            if account_id is None and assignee.lower() != "self":
                raise ValidationError(f"Could not resolve user: {assignee}")
            action = f"assign to {assignee}"

        issues = _get_issues_to_process(
            client,
            issue_keys=issue_keys,
            jql=jql,
            max_issues=max_issues,
            fields=["key", "summary", "assignee"],
        )

        total = len(issues)

        if total == 0:
            return {
                "success": 0,
                "failed": 0,
                "total": 0,
                "errors": {},
                "processed": [],
            }

        if dry_run:
            preview = []
            for issue in issues:
                key = issue.get("key")
                current = issue.get("fields", {}).get("assignee")
                current_name = (
                    current.get("displayName", "Unassigned")
                    if current
                    else "Unassigned"
                )
                preview.append(
                    {
                        "key": key,
                        "current": current_name,
                        "action": action,
                    }
                )

            return {
                "dry_run": True,
                "success": 0,
                "failed": 0,
                "would_process": total,
                "total": total,
                "issues": preview,
                "errors": {},
                "processed": [],
            }

        success = 0
        failed = 0
        errors = {}
        processed = []

        for i, issue in enumerate(issues, 1):
            issue_key = issue.get("key")

            try:
                client.assign_issue(issue_key, account_id)
                success += 1
                processed.append(issue_key)

            except Exception as e:
                failed += 1
                errors[issue_key] = str(e)

            if i < total and delay > 0:
                time.sleep(delay)

        return {
            "success": success,
            "failed": failed,
            "total": total,
            "errors": errors,
            "processed": processed,
            "action": action,
        }
    finally:
        client.close()


def _bulk_set_priority_impl(
    issue_keys: list[str] | None = None,
    jql: str | None = None,
    priority: str | None = None,
    dry_run: bool = False,
    max_issues: int = 100,
    delay: float = 0.1,
) -> dict[str, Any]:
    """Set priority on multiple issues."""
    if not priority:
        raise ValidationError("Priority is required")

    priority = _validate_priority(priority)

    client = get_jira_client()
    try:
        issues = _get_issues_to_process(
            client,
            issue_keys=issue_keys,
            jql=jql,
            max_issues=max_issues,
            fields=["key", "summary", "priority"],
        )

        total = len(issues)

        if total == 0:
            return {
                "success": 0,
                "failed": 0,
                "total": 0,
                "errors": {},
                "processed": [],
            }

        if dry_run:
            preview = []
            for issue in issues:
                key = issue.get("key")
                current = issue.get("fields", {}).get("priority")
                current_name = current.get("name", "None") if current else "None"
                preview.append(
                    {
                        "key": key,
                        "from": current_name,
                        "to": priority,
                    }
                )

            return {
                "dry_run": True,
                "success": 0,
                "failed": 0,
                "would_process": total,
                "total": total,
                "issues": preview,
                "errors": {},
                "processed": [],
            }

        success = 0
        failed = 0
        errors = {}
        processed = []

        for i, issue in enumerate(issues, 1):
            issue_key = issue.get("key")

            try:
                client.update_issue(
                    issue_key,
                    fields={"priority": {"name": priority}},
                    notify_users=False,
                )
                success += 1
                processed.append(issue_key)

            except Exception as e:
                failed += 1
                errors[issue_key] = str(e)

            if i < total and delay > 0:
                time.sleep(delay)

        return {
            "success": success,
            "failed": failed,
            "total": total,
            "errors": errors,
            "processed": processed,
        }
    finally:
        client.close()


def _clone_issue(
    client,
    source_issue: dict[str, Any],
    target_project: str | None = None,
    prefix: str | None = None,
    include_subtasks: bool = False,
    include_links: bool = False,
    created_mapping: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Clone a single issue."""
    if created_mapping is None:
        created_mapping = {}

    source_key = source_issue.get("key")
    source_fields = source_issue.get("fields", {})

    # Build new issue fields
    fields = {}

    # Project
    if target_project:
        fields["project"] = {"key": target_project}
    else:
        fields["project"] = {"key": source_fields.get("project", {}).get("key")}

    # Summary with optional prefix
    summary = source_fields.get("summary", "")
    if prefix:
        fields["summary"] = f"{prefix} {summary}"
    else:
        fields["summary"] = summary

    # Issue type
    if source_fields.get("issuetype"):
        fields["issuetype"] = {"name": source_fields["issuetype"].get("name")}

    # Description
    if source_fields.get("description"):
        fields["description"] = source_fields["description"]

    # Priority
    if source_fields.get("priority"):
        fields["priority"] = {"name": source_fields["priority"].get("name")}

    # Labels
    if source_fields.get("labels"):
        fields["labels"] = source_fields["labels"]

    # Components
    if source_fields.get("components"):
        fields["components"] = [
            {"name": c.get("name")} for c in source_fields["components"]
        ]

    # Fix versions
    if source_fields.get("fixVersions"):
        fields["fixVersions"] = [
            {"name": v.get("name")} for v in source_fields["fixVersions"]
        ]

    # Due date
    if source_fields.get("duedate"):
        fields["duedate"] = source_fields["duedate"]

    # Environment
    if source_fields.get("environment"):
        fields["environment"] = source_fields["environment"]

    # Create the issue
    created = client.create_issue(fields)
    new_key = created.get("key")

    # Track mapping
    created_mapping[source_key] = new_key

    # Clone subtasks if requested
    cloned_subtasks = []
    if include_subtasks:
        subtasks = source_fields.get("subtasks", [])
        for subtask in subtasks:
            subtask_key = subtask.get("key")
            subtask_data = client.get_issue(subtask_key)
            subtask_fields = subtask_data.get("fields", {})

            subtask_new_fields = {
                "project": fields["project"],
                "parent": {"key": new_key},
                "summary": f"{prefix} {subtask_fields.get('summary', '')}"
                if prefix
                else subtask_fields.get("summary", ""),
                "issuetype": {
                    "name": subtask_fields.get("issuetype", {}).get("name", "Sub-task")
                },
            }

            if subtask_fields.get("description"):
                subtask_new_fields["description"] = subtask_fields["description"]
            if subtask_fields.get("priority"):
                subtask_new_fields["priority"] = {
                    "name": subtask_fields["priority"].get("name")
                }

            subtask_created = client.create_issue(subtask_new_fields)
            cloned_subtasks.append(subtask_created.get("key"))
            created_mapping[subtask_key] = subtask_created.get("key")

    # Recreate links if requested
    cloned_links = []
    if include_links:
        issue_links = source_fields.get("issuelinks", [])
        for link in issue_links:
            link_type = link.get("type", {}).get("name")
            if not link_type:
                continue

            try:
                if "outwardIssue" in link:
                    linked_key = link["outwardIssue"].get("key")
                    link_data = {
                        "type": {"name": link_type},
                        "outwardIssue": {"key": linked_key},
                        "inwardIssue": {"key": new_key},
                    }
                elif "inwardIssue" in link:
                    linked_key = link["inwardIssue"].get("key")
                    link_data = {
                        "type": {"name": link_type},
                        "inwardIssue": {"key": linked_key},
                        "outwardIssue": {"key": new_key},
                    }
                else:
                    continue

                client.post(
                    "/rest/api/3/issueLink", data=link_data, operation="create link"
                )
                cloned_links.append(f"{link_type} -> {linked_key}")
            except Exception:
                pass  # Skip links that can't be created

    return {
        "key": new_key,
        "id": created.get("id"),
        "source": source_key,
        "subtasks": cloned_subtasks,
        "links": cloned_links,
    }


def _bulk_clone_impl(
    issue_keys: list[str] | None = None,
    jql: str | None = None,
    target_project: str | None = None,
    prefix: str | None = None,
    include_subtasks: bool = False,
    include_links: bool = False,
    dry_run: bool = False,
    max_issues: int = 100,
    delay: float = 0.2,
) -> dict[str, Any]:
    """Clone multiple issues."""
    if target_project:
        target_project = validate_project_key(target_project)

    client = get_jira_client()
    try:
        # Clone requires full issue data
        if issue_keys:
            issue_keys = [validate_issue_key(k) for k in issue_keys[:max_issues]]
            issues = []
            retrieval_errors = {}
            for key in issue_keys:
                try:
                    issue = client.get_issue(key)
                    issues.append(issue)
                except JiraError as e:
                    retrieval_errors[key] = str(e)
        elif jql:
            jql = validate_jql(jql)
            result = client.search_issues(jql, fields=["*all"], max_results=max_issues)
            issues = result.get("issues", [])
            retrieval_errors = {}
        else:
            raise ValidationError("Either --issues or --jql must be provided")

        total = len(issues)

        if total == 0:
            return {
                "success": 0,
                "failed": 0,
                "total": 0,
                "errors": retrieval_errors,
                "created_issues": [],
                "retrieval_failed": len(retrieval_errors),
            }

        if dry_run:
            preview = []
            for issue in issues:
                key = issue.get("key")
                summary = issue.get("fields", {}).get("summary", "")[:50]
                subtask_count = len(issue.get("fields", {}).get("subtasks", []))
                link_count = len(issue.get("fields", {}).get("issuelinks", []))
                preview.append(
                    {
                        "key": key,
                        "summary": summary,
                        "subtasks": subtask_count if include_subtasks else 0,
                        "links": link_count if include_links else 0,
                        "target_project": target_project
                        or issue.get("fields", {}).get("project", {}).get("key"),
                    }
                )

            return {
                "dry_run": True,
                "success": 0,
                "failed": 0,
                "would_create": total,
                "total": total,
                "issues": preview,
                "errors": retrieval_errors,
                "created_issues": [],
                "retrieval_failed": len(retrieval_errors),
            }

        success = 0
        failed = 0
        errors = {}
        created_issues = []
        created_mapping = {}

        for i, issue in enumerate(issues, 1):
            issue_key = issue.get("key")

            try:
                result = _clone_issue(
                    client=client,
                    source_issue=issue,
                    target_project=target_project,
                    prefix=prefix,
                    include_subtasks=include_subtasks,
                    include_links=include_links,
                    created_mapping=created_mapping,
                )

                success += 1
                created_issues.append(result)

            except Exception as e:
                failed += 1
                errors[issue_key] = str(e)

            if i < total and delay > 0:
                time.sleep(delay)

        all_errors = {**retrieval_errors, **errors}
        return {
            "success": success,
            "failed": failed,
            "total": total,
            "errors": all_errors,
            "created_issues": created_issues,
            "retrieval_failed": len(retrieval_errors),
        }
    finally:
        client.close()


def _bulk_delete_impl(
    issue_keys: list[str] | None = None,
    jql: str | None = None,
    dry_run: bool = False,
    max_issues: int = 100,
    delete_subtasks: bool = True,
    delay: float = 0.1,
) -> dict[str, Any]:
    """Delete multiple issues permanently."""
    client = get_jira_client()
    try:
        issues = _get_issues_to_process(
            client,
            issue_keys=issue_keys,
            jql=jql,
            max_issues=max_issues,
            fields=["key", "summary", "issuetype", "status", "subtasks"],
        )

        total = len(issues)

        if total == 0:
            return {
                "success": 0,
                "failed": 0,
                "total": 0,
                "errors": {},
                "processed": [],
            }

        # Count subtasks
        total_subtasks = 0
        for issue in issues:
            subtasks = issue.get("fields", {}).get("subtasks", [])
            if subtasks:
                total_subtasks += len(subtasks)

        if dry_run:
            preview = []
            for issue in issues:
                key = issue.get("key")
                fields = issue.get("fields", {})
                summary = fields.get("summary", "")[:50]
                issue_type = fields.get("issuetype", {}).get("name", "")
                status = fields.get("status", {}).get("name", "")
                subtasks = fields.get("subtasks", [])
                preview.append(
                    {
                        "key": key,
                        "type": issue_type,
                        "status": status,
                        "summary": summary,
                        "subtasks": len(subtasks) if delete_subtasks else 0,
                    }
                )

            return {
                "dry_run": True,
                "success": 0,
                "failed": 0,
                "would_delete": total,
                "total": total,
                "total_subtasks": total_subtasks if delete_subtasks else 0,
                "issues": preview,
                "errors": {},
                "processed": [],
            }

        success = 0
        failed = 0
        errors = {}
        processed = []

        for i, issue in enumerate(issues, 1):
            issue_key = issue.get("key")

            try:
                client.delete_issue(issue_key, delete_subtasks=delete_subtasks)
                success += 1
                processed.append(issue_key)

            except Exception as e:
                failed += 1
                errors[issue_key] = str(e)

            if i < total and delay > 0:
                time.sleep(delay)

        return {
            "success": success,
            "failed": failed,
            "total": total,
            "errors": errors,
            "processed": processed,
        }
    finally:
        client.close()


# =============================================================================
# Formatting Functions
# =============================================================================


def _format_bulk_result(result: dict, operation: str) -> str:
    """Format bulk operation result for text output."""
    lines = []

    if result.get("dry_run"):
        count = result.get(
            "would_process", result.get("would_create", result.get("would_delete", 0))
        )
        lines.append(f"[DRY RUN] Would {operation} {count} issue(s)")

        issues = result.get("issues", [])
        if issues:
            lines.append("")
            for issue in issues[:20]:
                if isinstance(issue, dict):
                    key = issue.get("key", "")
                    if "from" in issue and "to" in issue:
                        lines.append(f"  - {key}: {issue['from']} -> {issue['to']}")
                    elif "current" in issue:
                        lines.append(
                            f"  - {key}: {issue['current']} -> {issue['action']}"
                        )
                    elif "summary" in issue:
                        lines.append(f"  - {key}: {issue['summary']}")
                    else:
                        lines.append(f"  - {key}")
                else:
                    lines.append(f"  - {issue}")

            if len(issues) > 20:
                lines.append(f"  ... and {len(issues) - 20} more")

        lines.append("")
        lines.append("Use --yes to apply changes")

    elif result.get("cancelled"):
        lines.append("Operation cancelled by user.")

    else:
        lines.append(f"{result['success']} succeeded, {result['failed']} failed")

        if result.get("retrieval_failed"):
            lines.append(f"  ({result['retrieval_failed']} could not be retrieved)")

        if result.get("created_issues"):
            lines.append("")
            lines.append("Created issues:")
            for item in result["created_issues"][:20]:
                lines.append(f"  {item['source']} -> {item['key']}")
            if len(result["created_issues"]) > 20:
                lines.append(f"  ... and {len(result['created_issues']) - 20} more")

        if result.get("errors"):
            lines.append("")
            lines.append("Errors:")
            for key, error in list(result["errors"].items())[:10]:
                error_short = error[:80] + "..." if len(error) > 80 else error
                lines.append(f"  {key}: {error_short}")
            if len(result["errors"]) > 10:
                lines.append(f"  ... and {len(result['errors']) - 10} more errors")

    return "\n".join(lines)


# =============================================================================
# Click Commands
# =============================================================================


@click.group()
def bulk():
    """Commands for bulk operations on multiple issues."""
    pass


@bulk.command(name="transition")
@click.option("--jql", "-q", help="JQL query to find issues")
@click.option("--issues", "-i", help="Comma-separated issue keys")
@click.option("--to", "-t", "target_status", required=True, help="Target status name")
@click.option("--comment", "-c", help="Add comment with transition")
@click.option("--resolution", "-r", help="Resolution for Done transitions")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without making changes")
@click.option(
    "--max-issues", "-m", type=int, default=100, help="Maximum issues to process"
)
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
def bulk_transition(
    ctx,
    jql,
    issues,
    target_status,
    comment,
    resolution,
    dry_run,
    max_issues,
    yes,
    output,
):
    """Transition multiple issues to a new status.

    Specify issues using either --jql or --issues (mutually exclusive).

    Examples:
        jira-as bulk transition --jql "project=PROJ AND status=Open" --to Done
        jira-as bulk transition --issues PROJ-1,PROJ-2 --to "In Progress"
    """
    if not jql and not issues:
        raise click.UsageError("Either --jql or --issues is required")
    if jql and issues:
        raise click.UsageError("--jql and --issues are mutually exclusive")

    issue_keys = parse_comma_list(issues)

    result = _bulk_transition_impl(
        issue_keys=issue_keys,
        jql=jql,
        target_status=target_status,
        resolution=resolution,
        comment=comment,
        dry_run=dry_run or not yes,
        max_issues=max_issues,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_bulk_result(result, f"transition to '{target_status}'"))

    if result.get("failed", 0) > 0 and not result.get("dry_run"):
        ctx.exit(1)


@bulk.command(name="assign")
@click.option("--jql", "-q", help="JQL query to find issues")
@click.option("--issues", "-i", help="Comma-separated issue keys")
@click.option("--assignee", "-a", help='User to assign (account ID, email, or "self")')
@click.option("--unassign", is_flag=True, help="Unassign all matching issues")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without making changes")
@click.option(
    "--max-issues", "-m", type=int, default=100, help="Maximum issues to process"
)
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
def bulk_assign(ctx, jql, issues, assignee, unassign, dry_run, max_issues, yes, output):
    """Assign or unassign multiple issues.

    Specify issues using either --jql or --issues (mutually exclusive).
    Specify target using either --assignee or --unassign.

    Examples:
        jira-as bulk assign --jql "project=PROJ AND status=Open" --assignee john.doe
        jira-as bulk assign --jql "assignee=leaving.user" --unassign
        jira-as bulk assign --issues PROJ-1,PROJ-2 --assignee self
    """
    if not jql and not issues:
        raise click.UsageError("Either --jql or --issues is required")
    if jql and issues:
        raise click.UsageError("--jql and --issues are mutually exclusive")
    if not assignee and not unassign:
        raise click.UsageError("Either --assignee or --unassign is required")
    if assignee and unassign:
        raise click.UsageError("--assignee and --unassign are mutually exclusive")

    issue_keys = parse_comma_list(issues)

    result = _bulk_assign_impl(
        issue_keys=issue_keys,
        jql=jql,
        assignee=assignee,
        unassign=unassign,
        dry_run=dry_run or not yes,
        max_issues=max_issues,
    )

    action = result.get("action", "unassign" if unassign else f"assign to {assignee}")

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_bulk_result(result, action))

    if result.get("failed", 0) > 0 and not result.get("dry_run"):
        ctx.exit(1)


@bulk.command(name="set-priority")
@click.option("--jql", "-q", help="JQL query to find issues")
@click.option("--issues", "-i", help="Comma-separated issue keys")
@click.option(
    "--priority",
    "-p",
    required=True,
    help="Priority name (Highest, High, Medium, Low, Lowest)",
)
@click.option("--dry-run", "-n", is_flag=True, help="Preview without making changes")
@click.option(
    "--max-issues", "-m", type=int, default=100, help="Maximum issues to process"
)
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
def bulk_set_priority(ctx, jql, issues, priority, dry_run, max_issues, yes, output):
    """Set priority for multiple issues.

    Specify issues using either --jql or --issues (mutually exclusive).

    Examples:
        jira-as bulk set-priority --jql "type=Bug AND labels=critical" --priority Highest
        jira-as bulk set-priority --issues PROJ-1,PROJ-2 --priority High
    """
    if not jql and not issues:
        raise click.UsageError("Either --jql or --issues is required")
    if jql and issues:
        raise click.UsageError("--jql and --issues are mutually exclusive")

    issue_keys = parse_comma_list(issues)

    result = _bulk_set_priority_impl(
        issue_keys=issue_keys,
        jql=jql,
        priority=priority,
        dry_run=dry_run or not yes,
        max_issues=max_issues,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_bulk_result(result, f"set priority to '{priority}'"))

    if result.get("failed", 0) > 0 and not result.get("dry_run"):
        ctx.exit(1)


@bulk.command(name="clone")
@click.option("--jql", "-q", help="JQL query to find issues")
@click.option("--issues", "-i", help="Comma-separated issue keys")
@click.option("--target-project", "-t", help="Target project key for clones")
@click.option("--prefix", "-P", help="Prefix for cloned issue summaries")
@click.option("--include-links", "-l", is_flag=True, help="Clone issue links")
@click.option("--include-subtasks", "-s", is_flag=True, help="Clone subtasks")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without making changes")
@click.option(
    "--max-issues", "-m", type=int, default=100, help="Maximum issues to process"
)
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
def bulk_clone(
    ctx,
    jql,
    issues,
    target_project,
    prefix,
    include_links,
    include_subtasks,
    dry_run,
    max_issues,
    yes,
    output,
):
    """Clone multiple issues.

    Specify issues using either --jql or --issues (mutually exclusive).

    Examples:
        jira-as bulk clone --jql "sprint='Sprint 42'" --include-subtasks --include-links
        jira-as bulk clone --issues PROJ-1,PROJ-2 --target-project NEWPROJ --prefix "[Clone]"
    """
    if not jql and not issues:
        raise click.UsageError("Either --jql or --issues is required")
    if jql and issues:
        raise click.UsageError("--jql and --issues are mutually exclusive")

    issue_keys = parse_comma_list(issues)

    result = _bulk_clone_impl(
        issue_keys=issue_keys,
        jql=jql,
        target_project=target_project,
        prefix=prefix,
        include_subtasks=include_subtasks,
        include_links=include_links,
        dry_run=dry_run or not yes,
        max_issues=max_issues,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_bulk_result(result, "clone"))

    if result.get("failed", 0) > 0 and not result.get("dry_run"):
        ctx.exit(1)


@bulk.command(name="delete")
@click.option("--jql", "-q", help="JQL query to find issues")
@click.option("--issues", "-i", help="Comma-separated issue keys")
@click.option("--no-subtasks", is_flag=True, help="Do NOT delete subtasks")
@click.option(
    "--dry-run", "-n", is_flag=True, help="Preview without deleting (RECOMMENDED)"
)
@click.option(
    "--max-issues", "-m", type=int, default=100, help="Maximum issues to process"
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation (use with caution)")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def bulk_delete(ctx, jql, issues, no_subtasks, dry_run, max_issues, yes, output):
    """Delete multiple issues permanently.

    WARNING: This is a destructive operation. Deleted issues cannot be recovered.

    Specify issues using either --jql or --issues (mutually exclusive).
    Always use --dry-run first to preview what would be deleted.

    Examples:
        jira-as bulk delete --jql "project=DEMO" --dry-run
        jira-as bulk delete --issues DEMO-1,DEMO-2 --yes
    """
    if not jql and not issues:
        raise click.UsageError("Either --jql or --issues is required")
    if jql and issues:
        raise click.UsageError("--jql and --issues are mutually exclusive")

    # Safety warning for non-dry-run
    if not dry_run and not yes:
        click.echo("WARNING: This will PERMANENTLY delete issues.")
        click.echo("Consider using --dry-run first to preview.\n")

    issue_keys = parse_comma_list(issues)

    result = _bulk_delete_impl(
        issue_keys=issue_keys,
        jql=jql,
        dry_run=dry_run or not yes,
        max_issues=max_issues,
        delete_subtasks=not no_subtasks,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_bulk_result(result, "delete"))

    if result.get("failed", 0) > 0 and not result.get("dry_run"):
        ctx.exit(1)
