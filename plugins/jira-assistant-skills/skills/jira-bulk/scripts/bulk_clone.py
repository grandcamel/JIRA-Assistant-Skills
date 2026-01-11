#!/usr/bin/env python3
"""
Bulk clone multiple JIRA issues.

Clones multiple issues with options for:
- Including subtasks
- Including issue links
- Cloning to different project
- Adding prefix to summaries
- Dry-run preview
- Progress tracking

Usage:
    python bulk_clone.py --issues PROJ-1,PROJ-2 --include-subtasks
    python bulk_clone.py --issues PROJ-1,PROJ-2 --include-links
    python bulk_clone.py --issues PROJ-1,PROJ-2 --target-project NEWPROJ
    python bulk_clone.py --issues PROJ-1,PROJ-2 --prefix "[Clone]"
    python bulk_clone.py --jql "sprint=123" --include-subtasks --include-links
    python bulk_clone.py --jql "project=PROJ" --dry-run
"""

import argparse
import sys
import time
from collections.abc import Callable
from typing import Any

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from bulk_utils import confirm_bulk_operation

from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    print_error,
    print_info,
    print_success,
    print_warning,
    sanitize_error_message,
    validate_issue_key,
    validate_jql,
    validate_project_key,
)

# Fields to copy when cloning (excluding system fields)
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

# Custom fields to attempt copying
CUSTOM_FIELD_PREFIXES = ["customfield_"]


def clone_issue(
    client,
    source_issue: dict[str, Any],
    target_project: str | None = None,
    prefix: str | None = None,
    include_subtasks: bool = False,
    include_links: bool = False,
    created_mapping: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Clone a single issue.

    Args:
        client: JiraClient instance
        source_issue: Source issue data
        target_project: Target project key (optional)
        prefix: Prefix to add to summary (optional)
        include_subtasks: Whether to clone subtasks
        include_links: Whether to recreate links
        created_mapping: Mapping of source to cloned keys

    Returns:
        Created issue data
    """
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

    # Copy custom fields that are safe to copy
    for key, value in source_fields.items():
        if key.startswith("customfield_") and value is not None:
            # Skip complex fields that might cause issues
            if not isinstance(value, (dict, list)) or key in fields:
                continue
            # Try to copy simple custom fields
            try:
                fields[key] = value
            except Exception:
                pass  # Skip fields that can't be copied

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
            # Get full subtask data
            subtask_data = client.get_issue(subtask_key)
            subtask_fields = subtask_data.get("fields", {})

            # Create subtask clone
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
                    # Create link from new issue to existing issue
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
            except Exception as e:
                # Sanitize error message for logging to prevent sensitive data exposure
                sanitized_msg = sanitize_error_message(str(e))
                print_warning(f"Could not recreate link: {sanitized_msg}")

    return {
        "key": new_key,
        "id": created.get("id"),
        "source": source_key,
        "subtasks": cloned_subtasks,
        "links": cloned_links,
    }


def bulk_clone(
    client=None,
    issue_keys: list[str] | None = None,
    jql: str | None = None,
    target_project: str | None = None,
    prefix: str | None = None,
    include_subtasks: bool = False,
    include_links: bool = False,
    dry_run: bool = False,
    max_issues: int = 100,
    delay_between_ops: float = 0.2,
    progress_callback: Callable | None = None,
    show_progress: bool = True,
    confirm_threshold: int = 50,
    skip_confirmation: bool = False,
) -> dict[str, Any]:
    """
    Clone multiple issues.

    Args:
        client: JiraClient instance (optional, created if not provided)
        issue_keys: List of issue keys to clone
        jql: JQL query to find issues (alternative to issue_keys)
        target_project: Target project key (optional)
        prefix: Prefix to add to summary (optional)
        include_subtasks: Whether to clone subtasks
        include_links: Whether to recreate links
        dry_run: If True, preview without making changes
        max_issues: Maximum number of issues to process
        delay_between_ops: Delay between operations (seconds)
        progress_callback: Optional callback(current, total, issue_key, status)
        show_progress: If True, show tqdm progress bar (default: True)
        confirm_threshold: Prompt for confirmation above this count (default: 50)
        skip_confirmation: If True, skip confirmation prompt (default: False)

    Returns:
        Dict with success, failed, errors, created_issues, etc.
    """
    close_client = False
    if client is None:
        client = get_jira_client()
        close_client = True

    try:
        # Validate target project if provided
        if target_project:
            target_project = validate_project_key(target_project)

        # Get issues to process - clone requires full issue data
        retrieval_errors = {}
        if issue_keys:
            issue_keys = [validate_issue_key(k) for k in issue_keys[:max_issues]]
            issues = []
            for key in issue_keys:
                try:
                    issue = client.get_issue(key)
                    issues.append(issue)
                except JiraError as e:
                    # Sanitize error message for logging to prevent sensitive data exposure
                    sanitized_msg = sanitize_error_message(str(e))
                    retrieval_errors[key] = sanitized_msg
                    print_warning(f"Could not retrieve {key}: {sanitized_msg}")
        elif jql:
            jql = validate_jql(jql)
            result = client.search_issues(jql, fields=["*all"], max_results=max_issues)
            issues = result.get("issues", [])
            retrieval_errors = {}  # JQL search handles its own errors
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
            print_info(f"[DRY RUN] Would clone {total} issue(s):")
            for issue in issues:
                key = issue.get("key")
                summary = issue.get("fields", {}).get("summary", "")[:50]
                subtask_count = len(issue.get("fields", {}).get("subtasks", []))
                link_count = len(issue.get("fields", {}).get("issuelinks", []))
                details = []
                if include_subtasks and subtask_count:
                    details.append(f"{subtask_count} subtasks")
                if include_links and link_count:
                    details.append(f"{link_count} links")
                detail_str = f" ({', '.join(details)})" if details else ""
                print(f"  - {key}: {summary}...{detail_str}")
            return {
                "dry_run": True,
                "success": 0,
                "failed": 0,
                "would_create": total,
                "total": total,
                "errors": retrieval_errors,
                "created_issues": [],
                "retrieval_failed": len(retrieval_errors),
            }

        # Confirmation for large operations using shared utility
        if not skip_confirmation and not confirm_bulk_operation(
            total, "clone", confirm_threshold
        ):
            return {
                "cancelled": True,
                "success": 0,
                "failed": 0,
                "total": total,
                "errors": retrieval_errors,
                "created_issues": [],
                "retrieval_failed": len(retrieval_errors),
            }

        success = 0
        failed = 0
        errors = {}
        created_issues = []
        created_mapping = {}

        # Use tqdm progress bar if available and enabled
        use_tqdm = TQDM_AVAILABLE and show_progress and not progress_callback
        if use_tqdm:
            issue_iterator = tqdm(
                enumerate(issues, 1), total=total, desc="Cloning issues", unit="issue"
            )
        else:
            issue_iterator = enumerate(issues, 1)

        for i, issue in issue_iterator:
            issue_key = issue.get("key")

            try:
                result = clone_issue(
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

                if use_tqdm:
                    issue_iterator.set_postfix(success=success, failed=failed)
                elif progress_callback:
                    progress_callback(i, total, issue_key, "success")
                else:
                    print_success(
                        f"[{i}/{total}] Cloned {issue_key} -> {result['key']}"
                    )

            except Exception as e:
                failed += 1
                # Sanitize error message for logging to prevent sensitive data exposure
                sanitized_msg = sanitize_error_message(str(e))
                errors[issue_key] = sanitized_msg

                if use_tqdm:
                    issue_iterator.set_postfix(success=success, failed=failed)
                elif progress_callback:
                    progress_callback(i, total, issue_key, "failed")
                else:
                    print_warning(f"[{i}/{total}] Failed {issue_key}: {sanitized_msg}")

            # Rate limiting delay
            if i < total and delay_between_ops > 0:
                time.sleep(delay_between_ops)

        # Merge retrieval errors with cloning errors
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
        if close_client:
            client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Bulk clone JIRA issues",
        epilog="Example: python bulk_clone.py --issues PROJ-1,PROJ-2 --include-subtasks",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--issues", "-i", help="Comma-separated issue keys (e.g., PROJ-1,PROJ-2)"
    )
    group.add_argument("--jql", "-q", help="JQL query to find issues")

    parser.add_argument("--target-project", "-t", help="Target project key for clones")
    parser.add_argument("--prefix", "-x", help="Prefix to add to cloned summaries")
    parser.add_argument(
        "--include-subtasks", "-s", action="store_true", help="Clone subtasks"
    )
    parser.add_argument(
        "--include-links", "-l", action="store_true", help="Recreate issue links"
    )
    parser.add_argument(
        "--max-issues",
        type=int,
        default=100,
        help="Maximum issues to process (default: 100)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without making them"
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt for large operations",
    )
    parser.add_argument(
        "--no-progress", action="store_true", help="Disable progress bar"
    )

    args = parser.parse_args(argv)

    try:
        issue_keys = None
        if args.issues:
            issue_keys = [k.strip() for k in args.issues.split(",")]

        result = bulk_clone(
            issue_keys=issue_keys,
            jql=args.jql,
            target_project=args.target_project,
            prefix=args.prefix,
            include_subtasks=args.include_subtasks,
            include_links=args.include_links,
            dry_run=args.dry_run,
            max_issues=args.max_issues,
            show_progress=not args.no_progress,
            skip_confirmation=args.yes,
        )

        if result.get("cancelled"):
            print("\nOperation cancelled by user.")
            sys.exit(0)

        retrieval_failed = result.get("retrieval_failed", 0)
        if retrieval_failed > 0:
            print(
                f"\nSummary: {result['success']} cloned, {result['failed']} failed, {retrieval_failed} could not be retrieved"
            )
        else:
            print(f"\nSummary: {result['success']} cloned, {result['failed']} failed")

        if result["created_issues"]:
            print("\nCreated issues:")
            for item in result["created_issues"]:
                print(f"  {item['source']} -> {item['key']}")

        if result["failed"] > 0 or retrieval_failed > 0:
            sys.exit(1)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(130)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
