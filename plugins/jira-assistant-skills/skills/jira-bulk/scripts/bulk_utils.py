#!/usr/bin/env python3
"""
Shared utility functions for bulk operations.

Provides common patterns for:
- Issue retrieval (by keys or JQL)
- Dry-run preview logic
- Progress tracking loops with tqdm support
- Result dictionary construction
- Confirmation prompts for large operations

Usage:
    from bulk_utils import get_issues_to_process, execute_bulk_operation, BulkResult
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, TypedDict


# Optional tqdm support
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from jira_assistant_skills_lib import ValidationError
from jira_assistant_skills_lib import validate_issue_key, validate_jql
from jira_assistant_skills_lib import print_success, print_warning, print_info


class BulkResult(TypedDict, total=False):
    """Result dictionary returned by bulk operations."""
    success: int
    failed: int
    total: int
    errors: Dict[str, str]
    processed: List[str]
    dry_run: bool
    would_process: int
    cancelled: bool


def confirm_bulk_operation(count: int, operation: str, threshold: int = 50) -> bool:
    """
    Prompt for confirmation if operation affects many issues.

    Args:
        count: Number of issues to be affected
        operation: Description of the operation
        threshold: Number of issues above which to prompt (default: 50)

    Returns:
        True if confirmed or count below threshold, False otherwise
    """
    if count <= threshold:
        return True

    print(f"\nWARNING: This operation will {operation} {count} issue(s).")
    response = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
    return response == 'yes'


def get_issues_to_process(
    client,
    issue_keys: Optional[List[str]] = None,
    jql: Optional[str] = None,
    max_issues: int = 100,
    fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve issues to process from either issue keys or JQL query.

    Args:
        client: JiraClient instance
        issue_keys: List of issue keys to process
        jql: JQL query to find issues (alternative to issue_keys)
        max_issues: Maximum number of issues to retrieve
        fields: List of fields to retrieve (default: ['key', 'summary'])

    Returns:
        List of issue dictionaries

    Raises:
        ValidationError: If neither issue_keys nor jql provided
    """
    if fields is None:
        fields = ['key', 'summary']

    if issue_keys:
        # Validate and return as minimal issue dicts
        validated_keys = [validate_issue_key(k) for k in issue_keys[:max_issues]]
        return [{'key': key} for key in validated_keys]
    elif jql:
        # Validate JQL and search
        validated_jql = validate_jql(jql)
        result = client.search_issues(validated_jql, fields=fields, max_results=max_issues)
        return result.get('issues', [])
    else:
        raise ValidationError("Either --issues or --jql must be provided")


def execute_bulk_operation(
    issues: List[Dict[str, Any]],
    operation_func: Callable[[Dict[str, Any], int, int], Any],
    dry_run: bool = False,
    dry_run_message: Optional[str] = None,
    dry_run_item_formatter: Optional[Callable[[Dict[str, Any]], str]] = None,
    delay: float = 0.1,
    progress_callback: Optional[Callable[[int, int, str, str], None]] = None,
    success_message_formatter: Optional[Callable[[str, Any], str]] = None,
    failure_message_formatter: Optional[Callable[[str, Exception], str]] = None,
    show_progress: bool = True,
    progress_desc: Optional[str] = None,
    confirm_threshold: int = 50,
    skip_confirmation: bool = False,
    operation_name: Optional[str] = None
) -> BulkResult:
    """
    Execute a bulk operation on a list of issues.

    Args:
        issues: List of issue dictionaries to process
        operation_func: Function to execute for each issue.
                       Signature: (issue: Dict, index: int, total: int) -> Any
                       Returns any result value for the operation.
        dry_run: If True, preview without making changes
        dry_run_message: Message to display in dry-run mode
        dry_run_item_formatter: Function to format each issue in dry-run preview.
                               Signature: (issue: Dict) -> str
        delay: Delay between operations in seconds (default: 0.1)
        progress_callback: Optional callback for progress updates.
                          Signature: (current: int, total: int, issue_key: str, status: str)
        success_message_formatter: Optional formatter for success messages.
                                  Signature: (issue_key: str, result: Any) -> str
        failure_message_formatter: Optional formatter for failure messages.
                                  Signature: (issue_key: str, error: Exception) -> str
        show_progress: If True, show tqdm progress bar when available (default: True)
        progress_desc: Description for progress bar (default: "Processing")
        confirm_threshold: Prompt for confirmation above this count (default: 50)
        skip_confirmation: If True, skip confirmation prompt (default: False)
        operation_name: Name of operation for confirmation (e.g., "transition to 'Done'")

    Returns:
        BulkResult dictionary with success/failed counts, errors, and processed keys
    """
    total = len(issues)

    # Handle empty issues list
    if total == 0:
        return BulkResult(
            success=0,
            failed=0,
            total=0,
            errors={},
            processed=[]
        )

    # Handle dry-run mode
    if dry_run:
        message = dry_run_message or f"[DRY RUN] Would process {total} issue(s):"
        print_info(message)

        for issue in issues:
            if dry_run_item_formatter:
                print(f"  - {dry_run_item_formatter(issue)}")
            else:
                print(f"  - {issue.get('key')}")

        return BulkResult(
            dry_run=True,
            success=0,
            failed=0,
            would_process=total,
            total=total,
            errors={},
            processed=[]
        )

    # Confirmation for large operations
    if not skip_confirmation and operation_name:
        if not confirm_bulk_operation(total, operation_name, confirm_threshold):
            return BulkResult(
                cancelled=True,
                success=0,
                failed=0,
                total=total,
                errors={},
                processed=[]
            )

    # Execute the bulk operation
    success = 0
    failed = 0
    errors: Dict[str, str] = {}
    processed: List[str] = []

    # Use tqdm progress bar if available and enabled
    use_tqdm = TQDM_AVAILABLE and show_progress and not progress_callback
    if use_tqdm:
        issue_iterator = tqdm(
            enumerate(issues, 1),
            total=total,
            desc=progress_desc or "Processing",
            unit="issue"
        )
    else:
        issue_iterator = enumerate(issues, 1)

    for i, issue in issue_iterator:
        issue_key = issue.get('key')

        try:
            result = operation_func(issue, i, total)
            success += 1
            processed.append(issue_key)

            if use_tqdm:
                issue_iterator.set_postfix(success=success, failed=failed)
            elif progress_callback:
                progress_callback(i, total, issue_key, 'success')
            else:
                if success_message_formatter:
                    print_success(f"[{i}/{total}] {success_message_formatter(issue_key, result)}")
                else:
                    print_success(f"[{i}/{total}] Processed {issue_key}")

        except Exception as e:
            failed += 1
            errors[issue_key] = str(e)

            if use_tqdm:
                issue_iterator.set_postfix(success=success, failed=failed)
            elif progress_callback:
                progress_callback(i, total, issue_key, 'failed')
            else:
                if failure_message_formatter:
                    print_warning(f"[{i}/{total}] {failure_message_formatter(issue_key, e)}")
                else:
                    print_warning(f"[{i}/{total}] Failed {issue_key}: {e}")

        # Rate limiting delay (skip after last item)
        if i < total and delay > 0:
            time.sleep(delay)

    return BulkResult(
        success=success,
        failed=failed,
        total=total,
        errors=errors,
        processed=processed
    )


def create_empty_result() -> BulkResult:
    """Create an empty result dictionary for zero-issue cases."""
    return BulkResult(
        success=0,
        failed=0,
        total=0,
        errors={},
        processed=[]
    )
