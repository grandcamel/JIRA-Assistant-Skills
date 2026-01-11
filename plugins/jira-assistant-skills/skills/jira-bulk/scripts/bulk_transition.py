#!/usr/bin/env python3
"""
Bulk transition multiple JIRA issues.

Transitions multiple issues to a new status, with support for:
- Issue keys or JQL queries
- Resolution setting
- Comments during transition
- Dry-run preview
- Progress tracking
- Rate limiting
- Batching for large operations (>500 issues)
- Checkpoint/resume for interrupted operations

Usage:
    python bulk_transition.py --issues PROJ-1,PROJ-2 --to "Done"
    python bulk_transition.py --jql "project=PROJ AND status='In Progress'" --to "Done"
    python bulk_transition.py --jql "project=PROJ" --to "Done" --resolution "Fixed"
    python bulk_transition.py --issues PROJ-1 --to "In Review" --comment "Ready for review"
    python bulk_transition.py --jql "project=PROJ" --to "Done" --dry-run
    python bulk_transition.py --jql "project=PROJ" --to "Done" --batch-size 100 --enable-checkpoint
    python bulk_transition.py --resume transition-20231215-143022
    python bulk_transition.py --list-checkpoints
"""

import argparse
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from jira_assistant_skills_lib import (
    BatchConfig,
    BatchProcessor,
    BatchProgress,
    CheckpointManager,
    JiraError,
    ValidationError,
    generate_operation_id,
    get_jira_client,
    get_recommended_batch_size,
    list_pending_checkpoints,
    print_error,
    print_info,
    print_success,
    print_warning,
    text_to_adf,
    validate_issue_key,
    validate_jql,
)

# Default batch size threshold for automatic batching
BATCH_THRESHOLD = 500


def find_transition(transitions: list[dict], target_status: str) -> dict | None:
    """
    Find a transition that leads to the target status.

    Args:
        transitions: List of available transitions
        target_status: Target status name (case-insensitive)

    Returns:
        Matching transition dict or None
    """
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
    return response == "yes"


def bulk_transition_batched(
    client=None,
    issue_keys: list[str] | None = None,
    jql: str | None = None,
    target_status: str | None = None,
    resolution: str | None = None,
    comment: str | None = None,
    dry_run: bool = False,
    max_issues: int = 10000,
    batch_size: int | None = None,
    delay_between_batches: float = 1.0,
    delay_between_items: float = 0.1,
    enable_checkpoint: bool = False,
    operation_id: str | None = None,
    progress_callback: Callable | None = None,
    show_progress: bool = True,
    skip_confirmation: bool = False,
) -> dict[str, Any]:
    """
    Transition multiple issues with batching and checkpoint support.

    For operations on >500 issues, automatically uses batching with
    configurable batch sizes and checkpoint/resume capability.

    Args:
        client: JiraClient instance (optional, created if not provided)
        issue_keys: List of issue keys to transition
        jql: JQL query to find issues (alternative to issue_keys)
        target_status: Target status name
        resolution: Optional resolution to set
        comment: Optional comment to add during transition
        dry_run: If True, preview without making changes
        max_issues: Maximum number of issues to process (default: 10000)
        batch_size: Issues per batch (auto-calculated if None)
        delay_between_batches: Seconds between batches (default: 1.0)
        delay_between_items: Seconds between items (default: 0.1)
        enable_checkpoint: Enable checkpoint/resume (default: False)
        operation_id: Unique ID for checkpoint (auto-generated if None)
        progress_callback: Optional callback for progress updates
        show_progress: Show progress bar (default: True)
        skip_confirmation: Skip confirmation prompt (default: False)

    Returns:
        Dict with success, failed, errors, batch_info, etc.
    """
    close_client = False
    if client is None:
        client = get_jira_client()
        close_client = True

    try:
        # Get issues to process
        if issue_keys:
            issues = [{"key": validate_issue_key(k)} for k in issue_keys[:max_issues]]
        elif jql:
            jql = validate_jql(jql)
            # For large queries, paginate
            all_issues = []
            start_at = 0
            page_size = 100

            while len(all_issues) < max_issues:
                result = client.search_issues(
                    jql,
                    fields=["key", "summary", "status"],
                    max_results=min(page_size, max_issues - len(all_issues)),
                    start_at=start_at,
                )
                page_issues = result.get("issues", [])
                if not page_issues:
                    break
                all_issues.extend(page_issues)
                if len(page_issues) < page_size:
                    break
                start_at += page_size

            issues = all_issues[:max_issues]
        else:
            raise ValidationError("Either --issues or --jql must be provided")

        total = len(issues)

        if total == 0:
            return {
                "success": 0,
                "failed": 0,
                "total": 0,
                "errors": {},
                "processed": [],
                "batched": False,
            }

        # Calculate batch size if not specified
        if batch_size is None:
            batch_size = get_recommended_batch_size(total, "transition")

        # Determine if we need batching
        use_batching = total > BATCH_THRESHOLD or enable_checkpoint

        if dry_run:
            print_info(
                f"[DRY RUN] Would transition {total} issue(s) to '{target_status}'"
            )
            if use_batching:
                num_batches = (total + batch_size - 1) // batch_size
                print_info(f"  Batching: {num_batches} batches of ~{batch_size} issues")
            for issue in issues[:20]:  # Only show first 20
                key = issue.get("key")
                current_status = (
                    issue.get("fields", {}).get("status", {}).get("name", "Unknown")
                )
                print(f"  - {key} ({current_status} -> {target_status})")
            if total > 20:
                print(f"  ... and {total - 20} more issues")
            return {
                "dry_run": True,
                "success": 0,
                "failed": 0,
                "would_process": total,
                "total": total,
                "errors": {},
                "processed": [],
                "batched": use_batching,
                "batch_count": (total + batch_size - 1) // batch_size
                if use_batching
                else 1,
            }

        # Confirmation for large operations
        if not skip_confirmation and total > 50:
            if not confirm_bulk_operation(total, f"transition to '{target_status}'"):
                return {
                    "cancelled": True,
                    "success": 0,
                    "failed": 0,
                    "total": total,
                    "errors": {},
                    "processed": [],
                }

        # Generate operation ID for checkpointing
        if enable_checkpoint and operation_id is None:
            operation_id = generate_operation_id("transition")

        # Configure batch processor
        config = BatchConfig(
            batch_size=batch_size,
            delay_between_batches=delay_between_batches,
            delay_between_items=delay_between_items,
            max_items=max_issues,
            enable_checkpoints=enable_checkpoint,
            operation_id=operation_id,
        )

        # Track results
        success = 0
        failed = 0
        errors = {}
        processed = []

        # Process function for each issue
        def process_issue(issue: dict) -> bool:
            nonlocal success, failed, errors, processed
            issue_key = issue.get("key")

            try:
                # Get available transitions
                transitions = client.get_transitions(issue_key)

                # Find matching transition
                transition = find_transition(transitions, target_status)

                if not transition:
                    available = [t["name"] for t in transitions]
                    raise ValidationError(
                        f"Transition to '{target_status}' not available. "
                        f"Available: {', '.join(available)}"
                    )

                # Build fields for transition
                fields = {}
                if resolution:
                    fields["resolution"] = {"name": resolution}

                # Execute transition
                client.transition_issue(
                    issue_key, transition["id"], fields=fields if fields else None
                )

                # Add comment if provided
                if comment:
                    client.add_comment(issue_key, text_to_adf(comment))

                success += 1
                processed.append(issue_key)
                return True

            except Exception as e:
                failed += 1
                errors[issue_key] = str(e)
                return False

        # Progress callback wrapper
        def on_progress(progress: BatchProgress):
            if progress_callback:
                progress_callback(
                    progress.processed_items,
                    progress.total_items,
                    progress.processed_keys[-1] if progress.processed_keys else "",
                    "batch_complete",
                )
            elif show_progress and not TQDM_AVAILABLE:
                pct = progress.percent_complete
                print_info(
                    f"Batch {progress.current_batch}/{progress.total_batches} complete "
                    f"({pct:.1f}% - {progress.successful_items} success, {progress.failed_items} failed)"
                )

        # Use tqdm for progress if available
        if TQDM_AVAILABLE and show_progress and not progress_callback:
            with tqdm(
                total=total, desc=f"Transitioning to '{target_status}'", unit="issue"
            ) as pbar:
                batch_processor = BatchProcessor(
                    config=config,
                    process_item=lambda issue: (process_issue(issue), pbar.update(1))[
                        0
                    ],
                    progress_callback=None,
                )
                batch_result = batch_processor.process(
                    issues,
                    get_key=lambda x: x.get("key"),
                    resume=enable_checkpoint,
                    dry_run=False,
                )
        else:
            batch_processor = BatchProcessor(
                config=config,
                process_item=process_issue,
                progress_callback=on_progress if use_batching else None,
            )
            batch_result = batch_processor.process(
                issues,
                get_key=lambda x: x.get("key"),
                resume=enable_checkpoint,
                dry_run=False,
            )

        return {
            "success": success,
            "failed": failed,
            "total": total,
            "errors": errors,
            "processed": processed,
            "batched": use_batching,
            "batch_count": batch_result.total_batches,
            "operation_id": operation_id if enable_checkpoint else None,
        }

    finally:
        if close_client:
            client.close()


def bulk_transition(
    client=None,
    issue_keys: list[str] | None = None,
    jql: str | None = None,
    target_status: str | None = None,
    resolution: str | None = None,
    comment: str | None = None,
    dry_run: bool = False,
    max_issues: int = 100,
    delay_between_ops: float = 0.1,
    progress_callback: Callable | None = None,
    show_progress: bool = True,
    confirm_threshold: int = 50,
    skip_confirmation: bool = False,
) -> dict[str, Any]:
    """
    Transition multiple issues to a new status.

    Args:
        client: JiraClient instance (optional, created if not provided)
        issue_keys: List of issue keys to transition
        jql: JQL query to find issues (alternative to issue_keys)
        target_status: Target status name
        resolution: Optional resolution to set
        comment: Optional comment to add during transition
        dry_run: If True, preview without making changes
        max_issues: Maximum number of issues to process
        delay_between_ops: Delay between operations (seconds)
        progress_callback: Optional callback(current, total, issue_key, status)
        show_progress: If True, show tqdm progress bar (default: True)
        confirm_threshold: Prompt for confirmation above this count (default: 50)
        skip_confirmation: If True, skip confirmation prompt (default: False)

    Returns:
        Dict with success, failed, errors, etc.
    """
    close_client = False
    if client is None:
        client = get_jira_client()
        close_client = True

    try:
        # Get issues to process
        if issue_keys:
            issues = [{"key": validate_issue_key(k)} for k in issue_keys[:max_issues]]
        elif jql:
            jql = validate_jql(jql)
            result = client.search_issues(
                jql, fields=["key", "summary", "status"], max_results=max_issues
            )
            issues = result.get("issues", [])
        else:
            raise ValidationError("Either --issues or --jql must be provided")

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
            print_info(
                f"[DRY RUN] Would transition {total} issue(s) to '{target_status}':"
            )
            for issue in issues:
                key = issue.get("key", issue.get("key"))
                current_status = (
                    issue.get("fields", {}).get("status", {}).get("name", "Unknown")
                )
                print(f"  - {key} ({current_status} -> {target_status})")
            return {
                "dry_run": True,
                "success": 0,
                "failed": 0,
                "would_process": total,
                "total": total,
                "errors": {},
                "processed": [],
            }

        # Confirmation for large operations
        if not skip_confirmation and not confirm_bulk_operation(
            total, f"transition to '{target_status}'", confirm_threshold
        ):
            return {
                "cancelled": True,
                "success": 0,
                "failed": 0,
                "total": total,
                "errors": {},
                "processed": [],
            }

        success = 0
        failed = 0
        errors = {}
        processed = []

        # Use tqdm progress bar if available and enabled
        use_tqdm = TQDM_AVAILABLE and show_progress and not progress_callback
        if use_tqdm:
            issue_iterator = tqdm(
                enumerate(issues, 1),
                total=total,
                desc=f"Transitioning to '{target_status}'",
                unit="issue",
            )
        else:
            issue_iterator = enumerate(issues, 1)

        for i, issue in issue_iterator:
            issue_key = issue.get("key")

            try:
                # Get available transitions
                transitions = client.get_transitions(issue_key)

                # Find matching transition
                transition = find_transition(transitions, target_status)

                if not transition:
                    available = [t["name"] for t in transitions]
                    raise ValidationError(
                        f"Transition to '{target_status}' not available. "
                        f"Available: {', '.join(available)}"
                    )

                # Build fields for transition
                fields = {}
                if resolution:
                    fields["resolution"] = {"name": resolution}

                # Execute transition
                client.transition_issue(
                    issue_key, transition["id"], fields=fields if fields else None
                )

                # Add comment if provided
                if comment:
                    client.add_comment(issue_key, text_to_adf(comment))

                success += 1
                processed.append(issue_key)

                if use_tqdm:
                    issue_iterator.set_postfix(success=success, failed=failed)
                elif progress_callback:
                    progress_callback(i, total, issue_key, "success")
                else:
                    print_success(
                        f"[{i}/{total}] Transitioned {issue_key} to '{target_status}'"
                    )

            except Exception as e:
                failed += 1
                errors[issue_key] = str(e)

                if use_tqdm:
                    issue_iterator.set_postfix(success=success, failed=failed)
                elif progress_callback:
                    progress_callback(i, total, issue_key, "failed")
                else:
                    print_warning(f"[{i}/{total}] Failed {issue_key}: {e}")

            # Rate limiting delay
            if i < total and delay_between_ops > 0:
                time.sleep(delay_between_ops)

        return {
            "success": success,
            "failed": failed,
            "total": total,
            "errors": errors,
            "processed": processed,
        }

    finally:
        if close_client:
            client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Bulk transition JIRA issues to new status",
        epilog="""
Examples:
  %(prog)s --issues PROJ-1,PROJ-2 --to "Done"
  %(prog)s --jql "project=PROJ" --to "Done" --batch-size 100
  %(prog)s --jql "project=PROJ" --to "Done" --enable-checkpoint
  %(prog)s --resume transition-20231215-143022 --to "Done"
  %(prog)s --list-checkpoints
        """,
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--issues", "-i", help="Comma-separated issue keys (e.g., PROJ-1,PROJ-2)"
    )
    group.add_argument("--jql", "-q", help="JQL query to find issues")
    group.add_argument("--resume", help="Resume from checkpoint (operation ID)")
    group.add_argument(
        "--list-checkpoints",
        action="store_true",
        help="List pending checkpoints that can be resumed",
    )

    parser.add_argument(
        "--to",
        "-t",
        dest="target_status",
        help='Target status name (e.g., "Done", "In Progress")',
    )
    parser.add_argument(
        "--resolution", "-r", help="Resolution to set (e.g., Fixed, Won't Fix)"
    )
    parser.add_argument("--comment", "-c", help="Comment to add during transition")
    parser.add_argument(
        "--max-issues",
        type=int,
        default=10000,
        help="Maximum issues to process (default: 10000)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Issues per batch (auto-calculated if not specified)",
    )
    parser.add_argument(
        "--enable-checkpoint",
        action="store_true",
        help="Enable checkpoint/resume for large operations",
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
        # Handle list checkpoints
        if args.list_checkpoints:
            checkpoints = list_pending_checkpoints()
            if not checkpoints:
                print("No pending checkpoints found.")
            else:
                print(f"Found {len(checkpoints)} pending checkpoint(s):\n")
                for cp in checkpoints:
                    print(f"  ID: {cp['operation_id']}")
                    print(
                        f"    Progress: {cp['progress']:.1f}% ({cp['processed']}/{cp['total']})"
                    )
                    print(f"    Started: {cp['started_at']}")
                    print(f"    Updated: {cp['updated_at']}")
                    print()
            sys.exit(0)

        # Handle resume
        if args.resume:
            if not args.target_status:
                parser.error("--to is required when resuming")
            # Load checkpoint and continue
            checkpoint_mgr = CheckpointManager(
                str(Path.home() / ".jira-skills" / "checkpoints"), args.resume
            )
            if not checkpoint_mgr.exists():
                print(f"Error: Checkpoint '{args.resume}' not found.")
                sys.exit(1)
            progress = checkpoint_mgr.load()
            print_info(f"Resuming from checkpoint: {args.resume}")
            print_info(
                f"  Progress: {progress.processed_items}/{progress.total_items} ({progress.percent_complete:.1f}%)"
            )
            # Continue processing - the batch processor will skip already processed items
            # For now, we need the original JQL or issue list which we don't have
            print(
                "Note: Resume functionality requires storing the original query in checkpoint."
            )
            print("This feature is partially implemented.")
            sys.exit(0)

        # Require issues or JQL
        if not args.issues and not args.jql:
            parser.error(
                "Either --issues, --jql, --resume, or --list-checkpoints is required"
            )

        if not args.target_status:
            parser.error("--to is required")

        issue_keys = None
        if args.issues:
            issue_keys = [k.strip() for k in args.issues.split(",")]

        # Use batched version for large operations or when checkpoint is enabled
        use_batched = (
            args.batch_size
            or args.enable_checkpoint
            or args.max_issues > BATCH_THRESHOLD
        )

        if use_batched:
            result = bulk_transition_batched(
                issue_keys=issue_keys,
                jql=args.jql,
                target_status=args.target_status,
                resolution=args.resolution,
                comment=args.comment,
                dry_run=args.dry_run,
                max_issues=args.max_issues,
                batch_size=args.batch_size,
                enable_checkpoint=args.enable_checkpoint,
                show_progress=not args.no_progress,
                skip_confirmation=args.yes,
            )
        else:
            result = bulk_transition(
                issue_keys=issue_keys,
                jql=args.jql,
                target_status=args.target_status,
                resolution=args.resolution,
                comment=args.comment,
                dry_run=args.dry_run,
                max_issues=args.max_issues,
                show_progress=not args.no_progress,
                skip_confirmation=args.yes,
            )

        if result.get("cancelled"):
            print("\nOperation cancelled by user.")
            sys.exit(0)

        print(f"\nSummary: {result['success']} succeeded, {result['failed']} failed")
        if result.get("batched"):
            print(f"  Processed in {result.get('batch_count', 0)} batches")
        if result.get("operation_id"):
            print(f"  Checkpoint ID: {result['operation_id']}")

        if result["failed"] > 0:
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
