"""
Time tracking and worklog commands for jira-as CLI.

Commands:
- log: Add worklog to an issue
- worklogs: Get worklogs for an issue
- update-worklog: Update an existing worklog
- delete-worklog: Delete a worklog
- estimate: Set time estimates
- tracking: Get time tracking summary
- report: Generate time report
- export: Export timesheets to CSV/JSON
- bulk-log: Log time to multiple issues
"""

import csv
from collections import defaultdict
from datetime import datetime, timedelta
from io import StringIO
from typing import Any

import click

from jira_assistant_skills_lib import (
    AuthenticationError,
    JiraError,
    ValidationError,
    convert_to_jira_datetime_string,
    format_datetime_for_jira,
    format_seconds,
    get_jira_client,
    parse_relative_date,
    parse_time_string,
    text_to_adf,
    validate_issue_key,
    validate_time_format,
)

from ..cli_utils import format_json, handle_jira_errors, parse_comma_list

# =============================================================================
# Implementation Functions
# =============================================================================


def _add_worklog_impl(
    issue_key: str,
    time_spent: str,
    started: str | None = None,
    comment: str | None = None,
    adjust_estimate: str = "auto",
    new_estimate: str | None = None,
    reduce_by: str | None = None,
    visibility_type: str | None = None,
    visibility_value: str | None = None,
) -> dict[str, Any]:
    """
    Add a worklog to an issue.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
        time_spent: Time spent in JIRA format (e.g., '2h', '1d 4h')
        started: When work was started (ISO format, relative like 'yesterday')
        comment: Optional comment text
        adjust_estimate: How to adjust remaining estimate
        new_estimate: New remaining estimate (when adjust_estimate='new')
        reduce_by: Amount to reduce estimate (when adjust_estimate='manual')
        visibility_type: 'role' or 'group' to restrict visibility
        visibility_value: Role or group name for visibility restriction

    Returns:
        Created worklog object
    """
    validate_issue_key(issue_key)

    if not time_spent or not time_spent.strip():
        raise ValidationError("Time spent cannot be empty")

    if not validate_time_format(time_spent):
        raise ValidationError(
            f"Invalid time format: '{time_spent}'. Use format like '2h', '1d 4h', '30m'"
        )

    if visibility_type and not visibility_value:
        raise ValidationError(
            "--visibility-value is required when --visibility-type is specified"
        )
    if visibility_value and not visibility_type:
        raise ValidationError(
            "--visibility-type is required when --visibility-value is specified"
        )

    started_iso = None
    if started:
        try:
            dt = parse_relative_date(started)
            started_iso = format_datetime_for_jira(dt)
        except ValueError as e:
            raise ValidationError(str(e))

    comment_adf = None
    if comment:
        comment_adf = text_to_adf(comment)

    client = get_jira_client()
    try:
        return client.add_worklog(
            issue_key=issue_key,
            time_spent=time_spent,
            started=started_iso,
            comment=comment_adf,
            adjust_estimate=adjust_estimate,
            new_estimate=new_estimate,
            reduce_by=reduce_by,
            visibility_type=visibility_type,
            visibility_value=visibility_value,
        )
    finally:
        client.close()


def _get_worklogs_impl(
    issue_key: str,
    author_filter: str | None = None,
    since: str | None = None,
    until: str | None = None,
) -> dict[str, Any]:
    """
    Get worklogs for an issue with optional filtering.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
        author_filter: Filter by author email/accountId
        since: Only include worklogs started after this date
        until: Only include worklogs started before this date

    Returns:
        Dict with 'worklogs' list and 'total' count
    """
    validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        # Handle currentUser() filter
        if author_filter == "currentUser()":
            current_user = client.get(
                "/rest/api/3/myself", operation="get current user"
            )
            author_filter = current_user.get("emailAddress") or current_user.get(
                "accountId"
            )

        # Convert date strings to JIRA datetime format
        if since:
            try:
                since = convert_to_jira_datetime_string(since)
            except ValueError:
                pass

        if until:
            try:
                until = convert_to_jira_datetime_string(until)
            except ValueError:
                pass

        result = client.get_worklogs(issue_key)
        worklogs = result.get("worklogs", [])

        filtered = worklogs

        if author_filter:
            filtered = [
                w
                for w in filtered
                if w.get("author", {}).get("emailAddress") == author_filter
                or w.get("author", {}).get("displayName") == author_filter
                or w.get("author", {}).get("accountId") == author_filter
            ]

        if since:
            filtered = [w for w in filtered if w.get("started", "") >= since]

        if until:
            filtered = [w for w in filtered if w.get("started", "") <= until]

        return {
            "worklogs": filtered,
            "total": len(filtered),
            "startAt": result.get("startAt", 0),
            "maxResults": result.get("maxResults", len(filtered)),
        }
    finally:
        client.close()


def _update_worklog_impl(
    issue_key: str,
    worklog_id: str,
    time_spent: str | None = None,
    started: str | None = None,
    comment: str | None = None,
    adjust_estimate: str = "auto",
    new_estimate: str | None = None,
) -> dict[str, Any]:
    """
    Update an existing worklog.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
        worklog_id: Worklog ID to update
        time_spent: New time spent (optional)
        started: New start time (optional)
        comment: New comment text (optional)
        adjust_estimate: How to adjust remaining estimate
        new_estimate: New remaining estimate

    Returns:
        Updated worklog object
    """
    validate_issue_key(issue_key)

    if not any([time_spent, started, comment]):
        raise ValidationError(
            "At least one of --time, --started, or --comment must be specified"
        )

    if time_spent and not validate_time_format(time_spent):
        raise ValidationError(
            f"Invalid time format: '{time_spent}'. Use format like '2h', '1d 4h', '30m'"
        )

    started_iso = None
    if started:
        try:
            dt = parse_relative_date(started)
            started_iso = format_datetime_for_jira(dt)
        except ValueError as e:
            raise ValidationError(str(e))

    comment_adf = None
    if comment:
        comment_adf = text_to_adf(comment)

    client = get_jira_client()
    try:
        return client.update_worklog(
            issue_key=issue_key,
            worklog_id=worklog_id,
            time_spent=time_spent,
            started=started_iso if started_iso else started,
            comment=comment_adf,
            adjust_estimate=adjust_estimate,
            new_estimate=new_estimate,
        )
    finally:
        client.close()


def _delete_worklog_impl(
    issue_key: str,
    worklog_id: str,
    adjust_estimate: str = "auto",
    new_estimate: str | None = None,
    increase_by: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Delete a worklog from an issue.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
        worklog_id: Worklog ID to delete
        adjust_estimate: How to adjust remaining estimate
        new_estimate: New remaining estimate
        increase_by: Amount to increase estimate
        dry_run: If True, show what would be deleted without deleting

    Returns:
        Dict with worklog info and deletion status
    """
    validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        worklog = client.get_worklog(issue_key, worklog_id)

        if dry_run:
            return {
                "dry_run": True,
                "worklog": worklog,
                "deleted": False,
            }

        client.delete_worklog(
            issue_key=issue_key,
            worklog_id=worklog_id,
            adjust_estimate=adjust_estimate,
            new_estimate=new_estimate,
            increase_by=increase_by,
        )

        return {
            "dry_run": False,
            "worklog": worklog,
            "deleted": True,
        }
    finally:
        client.close()


def _set_estimate_impl(
    issue_key: str,
    original_estimate: str | None = None,
    remaining_estimate: str | None = None,
) -> dict[str, Any]:
    """
    Set time estimates on an issue.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
        original_estimate: Original estimate (e.g., '2d')
        remaining_estimate: Remaining estimate (e.g., '1d 4h')

    Returns:
        Dict with old and new time tracking info
    """
    validate_issue_key(issue_key)

    if not original_estimate and not remaining_estimate:
        raise ValidationError(
            "At least one of original_estimate or remaining_estimate must be provided"
        )

    if original_estimate and not validate_time_format(original_estimate):
        raise ValidationError(
            f"Invalid time format: '{original_estimate}'. Use format like '2h', '1d 4h', '30m'"
        )

    if remaining_estimate and not validate_time_format(remaining_estimate):
        raise ValidationError(
            f"Invalid time format: '{remaining_estimate}'. Use format like '2h', '1d 4h', '30m'"
        )

    client = get_jira_client()
    try:
        current = client.get_time_tracking(issue_key)

        client.set_time_tracking(
            issue_key=issue_key,
            original_estimate=original_estimate,
            remaining_estimate=remaining_estimate,
        )

        updated = client.get_time_tracking(issue_key)

        return {
            "previous": current,
            "current": updated,
        }
    finally:
        client.close()


def _get_time_tracking_impl(issue_key: str) -> dict[str, Any]:
    """
    Get time tracking info for an issue.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')

    Returns:
        Time tracking info dict with progress
    """
    validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        result = client.get_time_tracking(issue_key)
        result["progress"] = _calculate_progress(result)
        return result
    finally:
        client.close()


def _generate_report_impl(
    project: str | None = None,
    author: str | None = None,
    since: str | None = None,
    until: str | None = None,
    group_by: str | None = None,
) -> dict[str, Any]:
    """
    Generate a time report.

    Args:
        project: Project key to filter by
        author: Author email/accountId to filter by
        since: Start date for filtering
        until: End date for filtering
        group_by: Grouping option (issue, day, user)

    Returns:
        Report data dict with entries, totals, and grouping
    """
    client = get_jira_client()
    try:
        jql_parts = []
        if project:
            jql_parts.append(f"project = {project}")
        jql_parts.append("timespent > 0")
        jql = " AND ".join(jql_parts)

        since_dt = None
        until_dt = None
        if since:
            since_dt = parse_relative_date(since)
        if until:
            until_dt = parse_relative_date(until)
            until_dt = until_dt.replace(hour=23, minute=59, second=59)

        search_result = client.search_issues(jql, fields=["summary"], max_results=100)
        issues = search_result.get("issues", [])

        entries = []
        for issue in issues:
            issue_key = issue["key"]
            issue_summary = issue["fields"].get("summary", "")

            worklogs_result = client.get_worklogs(issue_key)
            worklogs = worklogs_result.get("worklogs", [])

            for worklog in worklogs:
                started_str = worklog.get("started", "")
                try:
                    started_dt = datetime.fromisoformat(
                        started_str.replace("+0000", "+00:00").replace("Z", "+00:00")
                    )
                    started_dt = started_dt.replace(tzinfo=None)
                except (ValueError, AttributeError):
                    continue

                if since_dt and started_dt.date() < since_dt.date():
                    continue
                if until_dt and started_dt.date() > until_dt.date():
                    continue

                worklog_author = worklog.get("author", {})
                author_email = worklog_author.get("emailAddress", "")
                author_id = worklog_author.get("accountId", "")

                if author and author not in (author_email, author_id):
                    continue

                entries.append(
                    {
                        "issue_key": issue_key,
                        "issue_summary": issue_summary,
                        "worklog_id": worklog.get("id"),
                        "author": worklog_author.get("displayName", author_email),
                        "author_email": author_email,
                        "started": started_str,
                        "started_date": started_dt.strftime("%Y-%m-%d"),
                        "time_spent": worklog.get("timeSpent", ""),
                        "time_seconds": worklog.get("timeSpentSeconds", 0),
                    }
                )

        total_seconds = sum(e["time_seconds"] for e in entries)

        result = {
            "entries": entries,
            "entry_count": len(entries),
            "total_seconds": total_seconds,
            "total_formatted": format_seconds(total_seconds) if total_seconds else "0m",
            "filters": {
                "project": project,
                "author": author,
                "since": since,
                "until": until,
            },
        }

        if group_by:
            result["group_by"] = group_by
            result["grouped"] = _group_entries(entries, group_by)

        return result
    finally:
        client.close()


def _export_timesheets_impl(
    project: str | None = None,
    author: str | None = None,
    since: str | None = None,
    until: str | None = None,
) -> dict[str, Any]:
    """
    Fetch timesheet data from JIRA.

    Args:
        project: Project key to filter by
        author: Author email/accountId to filter by
        since: Start date
        until: End date

    Returns:
        Timesheet data dict with entries
    """
    client = get_jira_client()
    try:
        jql_parts = []
        if project:
            jql_parts.append(f"project = {project}")
        jql_parts.append("timespent > 0")
        jql = " AND ".join(jql_parts)

        since_dt = None
        until_dt = None
        if since:
            since_dt = parse_relative_date(since)
        if until:
            until_dt = parse_relative_date(until)
            until_dt = until_dt.replace(hour=23, minute=59, second=59)

        search_result = client.search_issues(jql, fields=["summary"], max_results=100)
        issues = search_result.get("issues", [])

        entries = []
        for issue in issues:
            issue_key = issue["key"]
            issue_summary = issue["fields"].get("summary", "")

            worklogs_result = client.get_worklogs(issue_key)
            worklogs = worklogs_result.get("worklogs", [])

            for worklog in worklogs:
                started_str = worklog.get("started", "")
                try:
                    started_dt = datetime.fromisoformat(
                        started_str.replace("+0000", "+00:00").replace("Z", "+00:00")
                    )
                    started_dt = started_dt.replace(tzinfo=None)
                except (ValueError, AttributeError):
                    continue

                if since_dt and started_dt.date() < since_dt.date():
                    continue
                if until_dt and started_dt.date() > until_dt.date():
                    continue

                worklog_author = worklog.get("author", {})
                author_email = worklog_author.get("emailAddress", "")
                author_id = worklog_author.get("accountId", "")

                if author and author not in (author_email, author_id):
                    continue

                comment_text = ""
                comment = worklog.get("comment")
                if comment and isinstance(comment, dict):
                    for content in comment.get("content", []):
                        for child in content.get("content", []):
                            if child.get("type") == "text":
                                comment_text += child.get("text", "")

                entries.append(
                    {
                        "issue_key": issue_key,
                        "issue_summary": issue_summary,
                        "worklog_id": worklog.get("id"),
                        "author": worklog_author.get("displayName", author_email),
                        "author_email": author_email,
                        "started": started_str,
                        "started_date": started_dt.strftime("%Y-%m-%d"),
                        "time_spent": worklog.get("timeSpent", ""),
                        "time_seconds": worklog.get("timeSpentSeconds", 0),
                        "comment": comment_text,
                    }
                )

        total_seconds = sum(e["time_seconds"] for e in entries)

        return {
            "entries": entries,
            "entry_count": len(entries),
            "total_seconds": total_seconds,
            "total_formatted": format_seconds(total_seconds) if total_seconds else "0m",
            "generated_at": datetime.now().isoformat(),
            "filters": {
                "project": project,
                "author": author,
                "since": since,
                "until": until,
            },
        }
    finally:
        client.close()


def _bulk_log_time_impl(
    issues: list[str] | None = None,
    jql: str | None = None,
    time_spent: str | None = None,
    comment: str | None = None,
    started: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Log time to multiple issues.

    Args:
        issues: List of issue keys
        jql: JQL query to find issues
        time_spent: Time to log per issue
        comment: Optional comment for all worklogs
        started: Optional start time
        dry_run: If True, preview without logging

    Returns:
        Result dict with success/failure counts
    """
    if not validate_time_format(time_spent):
        raise ValidationError(
            f"Invalid time format: '{time_spent}'. Use format like '2h', '1d 4h', '30m'"
        )

    time_seconds = parse_time_string(time_spent)

    client = get_jira_client()
    try:
        if jql:
            search_result = client.search_issues(
                jql, fields=["summary"], max_results=100
            )
            issues = [issue["key"] for issue in search_result.get("issues", [])]

        if not issues:
            return {
                "success_count": 0,
                "failure_count": 0,
                "total_seconds": 0,
                "entries": [],
                "failures": [],
                "dry_run": dry_run,
                "would_log_count": 0,
            }

        comment_adf = None
        if comment:
            comment_adf = text_to_adf(comment)

        if dry_run:
            preview = []
            for issue_key in issues:
                try:
                    issue = client.get_issue(issue_key)
                    preview.append(
                        {
                            "issue": issue_key,
                            "summary": issue.get("fields", {}).get("summary", ""),
                            "time_to_log": time_spent,
                        }
                    )
                except JiraError:
                    preview.append(
                        {
                            "issue": issue_key,
                            "summary": "(unable to fetch)",
                            "time_to_log": time_spent,
                        }
                    )

            return {
                "dry_run": True,
                "would_log_count": len(issues),
                "would_log_seconds": time_seconds * len(issues),
                "would_log_formatted": format_seconds(time_seconds * len(issues)),
                "preview": preview,
            }

        successes = []
        failures = []

        for issue_key in issues:
            try:
                worklog = client.add_worklog(
                    issue_key=issue_key,
                    time_spent=time_spent,
                    started=started,
                    comment=comment_adf,
                )
                successes.append(
                    {
                        "issue": issue_key,
                        "worklog_id": worklog.get("id"),
                        "time_spent": time_spent,
                    }
                )
            except (JiraError, AuthenticationError) as e:
                failures.append({"issue": issue_key, "error": str(e)})

        total_seconds = time_seconds * len(successes)

        return {
            "success_count": len(successes),
            "failure_count": len(failures),
            "total_seconds": total_seconds,
            "total_formatted": format_seconds(total_seconds),
            "entries": successes,
            "failures": failures,
            "dry_run": False,
        }
    finally:
        client.close()


# =============================================================================
# Helper Functions
# =============================================================================


def _calculate_progress(time_tracking: dict[str, Any]) -> int | None:
    """Calculate completion percentage."""
    original_seconds = time_tracking.get("originalEstimateSeconds")
    spent_seconds = time_tracking.get("timeSpentSeconds", 0)

    if not original_seconds:
        return None

    if not spent_seconds:
        return 0

    return min(100, int((spent_seconds / original_seconds) * 100))


def _generate_progress_bar(progress: int, width: int = 20) -> str:
    """Generate a visual progress bar."""
    filled = int(width * progress / 100)
    empty = width - filled
    return "█" * filled + "░" * empty


def _group_entries(entries: list[dict], group_by: str) -> dict[str, Any]:
    """Group entries by the specified field."""
    grouped = defaultdict(lambda: {"entries": [], "total_seconds": 0})

    for entry in entries:
        if group_by == "issue":
            key = entry["issue_key"]
        elif group_by == "day":
            key = entry["started_date"]
        elif group_by == "user":
            key = entry["author"]
        else:
            key = "all"

        grouped[key]["entries"].append(entry)
        grouped[key]["total_seconds"] += entry["time_seconds"]

    for key in grouped:
        grouped[key]["total_formatted"] = format_seconds(grouped[key]["total_seconds"])
        grouped[key]["entry_count"] = len(grouped[key]["entries"])

    return dict(grouped)


def _extract_comment_text(comment: dict | None) -> str:
    """Extract text from ADF comment."""
    if not comment:
        return ""
    text_parts = []
    for block in comment.get("content", []):
        for content in block.get("content", []):
            if content.get("type") == "text":
                text_parts.append(content.get("text", ""))
    return " ".join(text_parts)


def _resolve_period_dates(period: str) -> tuple[str, str]:
    """Resolve named period to since/until dates."""
    today = datetime.now().date()

    if period == "today":
        return str(today), str(today)
    elif period == "yesterday":
        yesterday = today - timedelta(days=1)
        return str(yesterday), str(yesterday)
    elif period == "this-week":
        start = today - timedelta(days=today.weekday())
        return str(start), str(today)
    elif period == "last-week":
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        return str(start), str(end)
    elif period == "this-month":
        return str(today.replace(day=1)), str(today)
    elif period == "last-month":
        first_of_month = today.replace(day=1)
        last_month_end = first_of_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        return str(last_month_start), str(last_month_end)
    elif "-" in period and len(period) == 7:
        year, month = period.split("-")
        year = int(year)
        month = int(month)
        start = datetime(year, month, 1).date()
        if month == 12:
            end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end = datetime(year, month + 1, 1).date() - timedelta(days=1)
        return str(start), str(end)
    else:
        return period, period


# =============================================================================
# Formatting Functions
# =============================================================================


def _format_worklog_added(result: dict[str, Any], issue_key: str) -> str:
    """Format worklog added result for text output."""
    lines = [f"Worklog added to {issue_key}:"]
    lines.append(f"  Worklog ID: {result.get('id')}")
    lines.append(
        f"  Time logged: {result.get('timeSpent')} ({result.get('timeSpentSeconds')} seconds)"
    )

    if result.get("started"):
        lines.append(f"  Started: {result.get('started')}")

    comment_text = _extract_comment_text(result.get("comment"))
    if comment_text:
        lines.append(f"  Comment: {comment_text}")

    if result.get("visibility"):
        vis = result.get("visibility", {})
        lines.append(f"  Visibility: {vis.get('type', '')} = {vis.get('value', '')}")

    return "\n".join(lines)


def _format_worklogs(result: dict[str, Any], issue_key: str) -> str:
    """Format worklogs for text output."""
    worklogs = result.get("worklogs", [])
    lines = [f"Worklogs for {issue_key}:", ""]

    if not worklogs:
        lines.append("No worklogs found.")
        return "\n".join(lines)

    lines.append(f"{'ID':<10} {'Author':<20} {'Started':<20} {'Time':<10} Comment")
    lines.append("-" * 80)

    total_seconds = 0
    for worklog in worklogs:
        worklog_id = worklog.get("id", "")
        author = worklog.get("author", {}).get("displayName", "Unknown")
        started = worklog.get("started", "")[:19].replace("T", " ")
        time_spent = worklog.get("timeSpent", "")
        time_seconds = worklog.get("timeSpentSeconds", 0)
        total_seconds += time_seconds

        comment_text = ""
        comment = worklog.get("comment", {})
        if comment:
            for block in comment.get("content", []):
                for content in block.get("content", []):
                    if content.get("type") == "text":
                        comment_text = content.get("text", "")[:30]
                        break

        lines.append(
            f"{worklog_id:<10} {author:<20} {started:<20} {time_spent:<10} {comment_text}"
        )

    lines.append("-" * 80)
    lines.append(f"Total: {format_seconds(total_seconds)} ({len(worklogs)} entries)")

    return "\n".join(lines)


def _format_worklog_updated(
    result: dict[str, Any], worklog_id: str, issue_key: str
) -> str:
    """Format worklog updated result for text output."""
    lines = [f"Worklog {worklog_id} updated on {issue_key}:"]
    lines.append(
        f"  Time logged: {result.get('timeSpent')} ({result.get('timeSpentSeconds')} seconds)"
    )
    if result.get("started"):
        lines.append(f"  Started: {result.get('started')}")
    lines.append(f"  Updated: {result.get('updated')}")
    return "\n".join(lines)


def _format_worklog_deleted(
    result: dict[str, Any], worklog_id: str, issue_key: str
) -> str:
    """Format worklog deleted result for text output."""
    worklog = result.get("worklog", {})
    time_spent = worklog.get("timeSpent", "Unknown")
    time_seconds = worklog.get("timeSpentSeconds", 0)
    author = worklog.get("author", {}).get("displayName", "Unknown")
    started = worklog.get("started", "")[:19].replace("T", " ")

    if result.get("dry_run"):
        lines = ["Dry-run mode - worklog would be deleted:"]
        lines.append(f"  Worklog ID: {worklog_id}")
        lines.append(f"  Issue: {issue_key}")
        lines.append(f"  Time: {time_spent} ({time_seconds} seconds)")
        lines.append(f"  Author: {author}")
        lines.append(f"  Started: {started}")
        lines.append("")
        lines.append("Run without --dry-run to delete.")
    else:
        lines = [f"Deleted worklog {worklog_id} from {issue_key}"]
        lines.append(f"  Time removed: {time_spent}")

    return "\n".join(lines)


def _format_estimate_updated(
    result: dict[str, Any],
    issue_key: str,
    updated_original: bool,
    updated_remaining: bool,
) -> str:
    """Format estimate updated result for text output."""
    lines = [f"Time estimates updated for {issue_key}:"]

    previous = result.get("previous", {})
    current = result.get("current", {})

    if updated_original:
        old_orig = previous.get("originalEstimate", "unset")
        new_orig = current.get("originalEstimate", "unset")
        lines.append(f"  Original estimate: {new_orig} (was {old_orig})")

    if updated_remaining:
        old_rem = previous.get("remainingEstimate", "unset")
        new_rem = current.get("remainingEstimate", "unset")
        lines.append(f"  Remaining estimate: {new_rem} (was {old_rem})")

    if current.get("timeSpent"):
        lines.append(f"  Time spent: {current.get('timeSpent')}")

    return "\n".join(lines)


def _format_time_tracking(result: dict[str, Any], issue_key: str) -> str:
    """Format time tracking info for text output."""
    lines = [f"Time Tracking for {issue_key}:", ""]

    original = result.get("originalEstimate", "Not set")
    original_sec = result.get("originalEstimateSeconds")
    if original_sec:
        lines.append(
            f"Original Estimate:    {original} ({format_seconds(original_sec)})"
        )
    else:
        lines.append(f"Original Estimate:    {original}")

    remaining = result.get("remainingEstimate", "Not set")
    remaining_sec = result.get("remainingEstimateSeconds")
    if remaining_sec:
        lines.append(
            f"Remaining Estimate:   {remaining} ({format_seconds(remaining_sec)})"
        )
    else:
        lines.append(f"Remaining Estimate:   {remaining}")

    spent = result.get("timeSpent", "None")
    spent_sec = result.get("timeSpentSeconds")
    if spent_sec:
        lines.append(f"Time Spent:           {spent} ({format_seconds(spent_sec)})")
    else:
        lines.append(f"Time Spent:           {spent}")

    progress = result.get("progress")
    if progress is not None:
        lines.append("")
        bar = _generate_progress_bar(progress)
        lines.append(f"Progress: {bar} {progress}% complete")
        if spent_sec and original_sec:
            lines.append(
                f"          {format_seconds(spent_sec)} logged of {format_seconds(original_sec)} estimated"
            )

    return "\n".join(lines)


def _format_report_text(report: dict[str, Any]) -> str:
    """Format report as text output."""
    lines = []

    filters = report.get("filters", {})
    if filters.get("author"):
        lines.append(f"Time Report: {filters['author']}")
    elif filters.get("project"):
        lines.append(f"Time Report: Project {filters['project']}")
    else:
        lines.append("Time Report")

    if filters.get("since") or filters.get("until"):
        period = f"{filters.get('since', '...')} to {filters.get('until', '...')}"
        lines.append(f"Period: {period}")

    lines.append("")

    if "grouped" in report:
        for key, data in sorted(report["grouped"].items()):
            lines.append(
                f"{key}: {data['total_formatted']} ({data['entry_count']} entries)"
            )
    elif report["entries"]:
        lines.append(f"{'Issue':<12} {'Author':<15} {'Date':<12} {'Time':<8}")
        lines.append("-" * 50)
        for entry in report["entries"]:
            lines.append(
                f"{entry['issue_key']:<12} "
                f"{entry['author'][:15]:<15} "
                f"{entry['started_date']:<12} "
                f"{entry['time_spent']:<8}"
            )

    lines.append("")
    lines.append(
        f"Total: {report['total_formatted']} ({report['entry_count']} entries)"
    )

    return "\n".join(lines)


def _format_report_csv(report: dict[str, Any]) -> str:
    """Format report as CSV output."""
    lines = ["Issue Key,Issue Summary,Author,Date,Time Spent,Seconds"]
    for entry in report["entries"]:
        summary = entry["issue_summary"].replace('"', '""')
        lines.append(
            f'{entry["issue_key"]},"{summary}",{entry["author"]},{entry["started_date"]},{entry["time_spent"]},{entry["time_seconds"]}'
        )
    return "\n".join(lines)


def _format_export_csv(data: dict[str, Any]) -> str:
    """Format timesheet data as CSV."""
    output = StringIO()
    fieldnames = [
        "Issue Key",
        "Issue Summary",
        "Author",
        "Email",
        "Date",
        "Time Spent",
        "Seconds",
        "Comment",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for entry in data.get("entries", []):
        writer.writerow(
            {
                "Issue Key": entry.get("issue_key", ""),
                "Issue Summary": entry.get("issue_summary", ""),
                "Author": entry.get("author", ""),
                "Email": entry.get("author_email", ""),
                "Date": entry.get("started_date", ""),
                "Time Spent": entry.get("time_spent", ""),
                "Seconds": entry.get("time_seconds", 0),
                "Comment": entry.get("comment", ""),
            }
        )

    return output.getvalue()


def _format_bulk_log_result(result: dict[str, Any]) -> str:
    """Format bulk log result for text output."""
    lines = []

    if result.get("dry_run"):
        lines.append("Bulk Time Logging Preview (dry-run):")
        for item in result.get("preview", []):
            lines.append(
                f"  {item['issue']}: +{item['time_to_log']} ({item['summary'][:40]})"
            )
        lines.append("")
        lines.append(
            f"Would log {result['would_log_formatted']} total to {result['would_log_count']} issues."
        )
        lines.append("Run without --dry-run to apply.")
    else:
        lines.append("Bulk Time Logging Complete:")
        lines.append(f"  Successful: {result['success_count']} issues")
        if result["failure_count"] > 0:
            lines.append(f"  Failed: {result['failure_count']} issues")
            for failure in result["failures"]:
                lines.append(f"    - {failure['issue']}: {failure['error']}")
        lines.append(f"  Total logged: {result['total_formatted']}")

    return "\n".join(lines)


# =============================================================================
# Click Commands
# =============================================================================


@click.group()
def time():
    """Commands for time tracking and worklogs."""
    pass


@time.command(name="log")
@click.argument("issue_key")
@click.option(
    "--time",
    "-t",
    "time_spent",
    required=True,
    help="Time spent (e.g., 2h, 1d 4h, 30m)",
)
@click.option("--comment", "-c", help="Worklog comment")
@click.option("--started", "-s", help="Start time (YYYY-MM-DD or ISO datetime)")
@click.option(
    "--adjust-estimate",
    "-a",
    type=click.Choice(["auto", "leave", "new", "manual"]),
    default="auto",
    help="How to adjust remaining estimate",
)
@click.option(
    "--new-estimate", help="New remaining estimate (when adjust=new or manual)"
)
@click.option("--reduce-by", help="Amount to reduce estimate (when adjust=manual)")
@click.option(
    "--visibility-type",
    type=click.Choice(["role", "group"]),
    help="Restrict visibility to role or group",
)
@click.option(
    "--visibility-value", help="Role or group name for visibility restriction"
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
def time_log(
    ctx,
    issue_key: str,
    time_spent: str,
    comment: str,
    started: str,
    adjust_estimate: str,
    new_estimate: str,
    reduce_by: str,
    visibility_type: str,
    visibility_value: str,
    output: str,
):
    """Log time worked on an issue.

    Examples:
        jira-as time log PROJ-123 --time 2h
        jira-as time log PROJ-123 --time "1d 4h" --comment "Code review"
    """
    result = _add_worklog_impl(
        issue_key,
        time_spent,
        started=started,
        comment=comment,
        adjust_estimate=adjust_estimate,
        new_estimate=new_estimate,
        reduce_by=reduce_by,
        visibility_type=visibility_type,
        visibility_value=visibility_value,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_worklog_added(result, issue_key))


@time.command(name="worklogs")
@click.argument("issue_key")
@click.option("--since", "-s", help="Show worklogs since date (YYYY-MM-DD)")
@click.option("--until", "-u", help="Show worklogs until date (YYYY-MM-DD)")
@click.option("--author", "-a", help="Filter by author")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def time_worklogs(
    ctx, issue_key: str, since: str, until: str, author: str, output: str
):
    """Get worklogs for an issue."""
    result = _get_worklogs_impl(
        issue_key, author_filter=author, since=since, until=until
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_worklogs(result, issue_key))


@time.command(name="update-worklog")
@click.argument("issue_key")
@click.option("--worklog-id", "-w", required=True, help="Worklog ID to update")
@click.option("--time", "-t", "time_spent", help="New time spent")
@click.option("--comment", "-c", help="New comment")
@click.option("--started", "-s", help="New start time")
@click.option(
    "--adjust-estimate",
    type=click.Choice(["auto", "leave", "new"]),
    default="auto",
    help="How to adjust remaining estimate",
)
@click.option("--new-estimate", help="New remaining estimate (when adjust=new)")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def time_update_worklog(
    ctx,
    issue_key: str,
    worklog_id: str,
    time_spent: str,
    comment: str,
    started: str,
    adjust_estimate: str,
    new_estimate: str,
    output: str,
):
    """Update an existing worklog."""
    result = _update_worklog_impl(
        issue_key,
        worklog_id,
        time_spent=time_spent,
        started=started,
        comment=comment,
        adjust_estimate=adjust_estimate,
        new_estimate=new_estimate,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_worklog_updated(result, worklog_id, issue_key))


@time.command(name="delete-worklog")
@click.argument("issue_key")
@click.option("--worklog-id", "-w", required=True, help="Worklog ID to delete")
@click.option(
    "--adjust-estimate",
    "-a",
    type=click.Choice(["auto", "leave", "new", "manual"]),
    default="auto",
    help="How to adjust remaining estimate",
)
@click.option("--new-estimate", help="New remaining estimate (when adjust=new)")
@click.option("--increase-by", help="Amount to increase estimate (when adjust=manual)")
@click.option("--dry-run", "-n", is_flag=True, help="Preview deletion without deleting")
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
def time_delete_worklog(
    ctx,
    issue_key: str,
    worklog_id: str,
    adjust_estimate: str,
    new_estimate: str,
    increase_by: str,
    dry_run: bool,
    yes: bool,
    output: str,
):
    """Delete a worklog.

    Examples:
        jira-as time delete-worklog PROJ-123 --worklog-id 12345
        jira-as time delete-worklog PROJ-123 --worklog-id 12345 --adjust-estimate leave
        jira-as time delete-worklog PROJ-123 --worklog-id 12345 --dry-run
    """
    # For non-dry-run, we need to confirm unless --yes
    if not dry_run and not yes:
        # First do a dry-run to show what will be deleted
        preview = _delete_worklog_impl(issue_key, worklog_id, dry_run=True)
        worklog = preview.get("worklog", {})
        time_spent = worklog.get("timeSpent", "Unknown")
        author = worklog.get("author", {}).get("displayName", "Unknown")
        started = worklog.get("started", "")[:19].replace("T", " ")

        click.echo(f"About to delete worklog from {issue_key}:")
        click.echo(f"  Worklog ID: {worklog_id}")
        click.echo(f"  Time: {time_spent}")
        click.echo(f"  Author: {author}")
        click.echo(f"  Started: {started}")

        if not click.confirm("\nAre you sure?"):
            click.echo("Cancelled.")
            return

    result = _delete_worklog_impl(
        issue_key,
        worklog_id,
        adjust_estimate=adjust_estimate,
        new_estimate=new_estimate,
        increase_by=increase_by,
        dry_run=dry_run,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_worklog_deleted(result, worklog_id, issue_key))


@time.command(name="estimate")
@click.argument("issue_key")
@click.option("--original", "-o", help="Original estimate (e.g., 2d, 4h)")
@click.option("--remaining", "-r", help="Remaining estimate (e.g., 1d 4h)")
@click.option(
    "--output",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def time_estimate(ctx, issue_key: str, original: str, remaining: str, output: str):
    """Set time estimate for an issue.

    At least one of --original or --remaining is required.

    Examples:
        jira-as time estimate PROJ-123 --original 2d
        jira-as time estimate PROJ-123 --remaining "1d 4h"
        jira-as time estimate PROJ-123 --original 2d --remaining "1d 4h"
    """
    if not original and not remaining:
        raise click.UsageError("At least one of --original or --remaining is required")

    result = _set_estimate_impl(
        issue_key, original_estimate=original, remaining_estimate=remaining
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(
            _format_estimate_updated(result, issue_key, bool(original), bool(remaining))
        )


@time.command(name="tracking")
@click.argument("issue_key")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def time_tracking(ctx, issue_key: str, output: str):
    """Get time tracking information for an issue."""
    result = _get_time_tracking_impl(issue_key)

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_time_tracking(result, issue_key))


@time.command(name="report")
@click.option("--project", "-p", help="Project key")
@click.option("--user", "-u", help="User (account ID or email)")
@click.option("--since", "-s", help="Start date (YYYY-MM-DD)")
@click.option("--until", help="End date (YYYY-MM-DD)")
@click.option(
    "--period",
    type=click.Choice(
        ["today", "yesterday", "this-week", "last-week", "this-month", "last-month"]
    ),
    help="Predefined time period",
)
@click.option(
    "--group-by",
    "-g",
    type=click.Choice(["issue", "day", "user"]),
    help="Group results by field",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "csv", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def time_report(
    ctx,
    project: str,
    user: str,
    since: str,
    until: str,
    period: str,
    group_by: str,
    output_format: str,
):
    """Generate a time report."""
    if period:
        since, until = _resolve_period_dates(period)

    result = _generate_report_impl(
        project=project,
        author=user,
        since=since,
        until=until,
        group_by=group_by,
    )

    if output_format == "json":
        click.echo(format_json(result))
    elif output_format == "csv":
        click.echo(_format_report_csv(result))
    else:
        click.echo(_format_report_text(result))


@time.command(name="export")
@click.option("--project", "-p", help="Project key")
@click.option("--user", "-u", help="User (account ID or email)")
@click.option("--since", "-s", help="Start date (YYYY-MM-DD)")
@click.option("--until", help="End date (YYYY-MM-DD)")
@click.option(
    "--period",
    help="Predefined time period (or YYYY-MM format)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["csv", "json"]),
    default="csv",
    help="Export format",
)
@click.option("--output", "-o", "output_file", help="Output file path")
@click.pass_context
@handle_jira_errors
def time_export(
    ctx,
    project: str,
    user: str,
    since: str,
    until: str,
    period: str,
    output_format: str,
    output_file: str,
):
    """Export timesheets to CSV or JSON."""
    if period:
        since, until = _resolve_period_dates(period)

    data = _export_timesheets_impl(
        project=project,
        author=user,
        since=since,
        until=until,
    )

    if output_file:
        if output_format == "csv":
            content = _format_export_csv(data)
        else:
            content = format_json(data)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        click.echo(f"Exported {data['entry_count']} entries to {output_file}")
        click.echo(f"Total time: {data['total_formatted']}")
    else:
        if output_format == "csv":
            click.echo(_format_export_csv(data))
        else:
            click.echo(format_json(data))


@time.command(name="bulk-log")
@click.option("--jql", "-j", help="JQL query to find issues")
@click.option("--issues", "-i", help="Comma-separated issue keys (e.g., PROJ-1,PROJ-2)")
@click.option(
    "--time",
    "-t",
    "time_spent",
    required=True,
    help="Time to log (e.g., 2h, 30m)",
)
@click.option("--comment", "-c", help="Worklog comment")
@click.option("--started", "-s", help="Start time for all worklogs")
@click.option("--dry-run", "-n", is_flag=True, help="Show what would be logged")
@click.option("--force", "-f", "yes", is_flag=True, help="Skip confirmation")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def time_bulk_log(
    ctx,
    jql: str,
    issues: str,
    time_spent: str,
    comment: str,
    started: str,
    dry_run: bool,
    yes: bool,
    output: str,
):
    """Log time on multiple issues.

    Specify issues using either --jql or --issues (mutually exclusive).

    Examples:
        jira-as time bulk-log --jql "sprint = 456" --time 15m --comment "Standup"
        jira-as time bulk-log --issues PROJ-1,PROJ-2 --time 30m --dry-run
    """
    if not jql and not issues:
        raise click.UsageError("Either --jql or --issues is required")
    if jql and issues:
        raise click.UsageError("--jql and --issues are mutually exclusive")

    issue_list = None
    if issues:
        issue_list = parse_comma_list(issues)
        if issue_list:
            for key in issue_list:
                validate_issue_key(key)

    result = _bulk_log_time_impl(
        issues=issue_list,
        jql=jql,
        time_spent=time_spent,
        comment=comment,
        started=started,
        dry_run=dry_run,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_bulk_log_result(result))
