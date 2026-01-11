#!/usr/bin/env python3
"""
Streaming export for large JIRA search results.

Efficiently exports large datasets (>10k issues) using:
- Paginated API calls with configurable page sizes
- Streaming writes to avoid memory buildup
- Progress tracking and resumable exports
- Multiple output formats (CSV, JSON Lines, JSON)

Usage:
    python streaming_export.py "project = PROJ" --output report.csv
    python streaming_export.py "project = PROJ" --output report.jsonl --format jsonl
    python streaming_export.py "project = PROJ" --output report.json --max-results 50000
    python streaming_export.py "project = PROJ" --output report.csv --page-size 200
    python streaming_export.py --resume export-20231215-143022
"""

import argparse
import csv
import json
import sys
import time
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from jira_assistant_skills_lib import (
    JiraError,
    get_jira_client,
    print_error,
    print_info,
    print_success,
    print_warning,
    validate_jql,
)

# Default configuration
DEFAULT_PAGE_SIZE = 100
DEFAULT_MAX_RESULTS = 100000
CHECKPOINT_INTERVAL = 1000  # Save checkpoint every N issues


@dataclass
class ExportProgress:
    """Tracks progress of a streaming export."""

    jql: str
    output_file: str
    format_type: str
    total_expected: int = 0
    total_exported: int = 0
    next_page_token: str | None = None
    started_at: str = ""
    updated_at: str = ""
    fields: list[str] = None
    is_complete: bool = False

    def __post_init__(self):
        if self.fields is None:
            self.fields = []


class ExportCheckpointManager:
    """Manages checkpoints for resumable exports."""

    def __init__(self, checkpoint_dir: str | None = None):
        if checkpoint_dir is None:
            checkpoint_dir = str(Path.home() / ".jira-skills" / "export-checkpoints")
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save(self, operation_id: str, progress: ExportProgress) -> None:
        """Save export progress to checkpoint."""
        progress.updated_at = datetime.now().isoformat()
        checkpoint_file = self.checkpoint_dir / f"{operation_id}.json"

        data = asdict(progress)
        temp_file = checkpoint_file.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=2)
        temp_file.rename(checkpoint_file)

    def load(self, operation_id: str) -> ExportProgress | None:
        """Load export progress from checkpoint."""
        checkpoint_file = self.checkpoint_dir / f"{operation_id}.json"
        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file) as f:
                data = json.load(f)
            return ExportProgress(**data)
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

    def clear(self, operation_id: str) -> None:
        """Remove checkpoint file."""
        checkpoint_file = self.checkpoint_dir / f"{operation_id}.json"
        if checkpoint_file.exists():
            checkpoint_file.unlink()

    def list_pending(self) -> list[dict[str, Any]]:
        """List all pending export checkpoints."""
        checkpoints = []
        for file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(file) as f:
                    data = json.load(f)
                progress = ExportProgress(**data)
                if not progress.is_complete:
                    checkpoints.append(
                        {
                            "operation_id": file.stem,
                            "jql": progress.jql[:50] + "..."
                            if len(progress.jql) > 50
                            else progress.jql,
                            "output_file": progress.output_file,
                            "progress": f"{progress.total_exported}/{progress.total_expected}",
                            "percent": (
                                progress.total_exported / progress.total_expected * 100
                            )
                            if progress.total_expected > 0
                            else 0,
                            "updated_at": progress.updated_at,
                        }
                    )
            except (json.JSONDecodeError, TypeError, KeyError):
                continue
        return sorted(checkpoints, key=lambda x: x.get("updated_at", ""), reverse=True)


def generate_export_id() -> str:
    """Generate unique export operation ID."""
    return f"export-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def flatten_issue(issue: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    """
    Flatten an issue for export, extracting nested field values.

    Args:
        issue: Raw issue from JIRA API
        fields: List of fields to extract

    Returns:
        Flattened dictionary with simple values
    """
    row = {"key": issue.get("key", "")}
    issue_fields = issue.get("fields", {})

    for field in fields:
        if field == "key":
            continue

        value = issue_fields.get(field, "")

        if value is None:
            value = ""
        elif isinstance(value, dict):
            # Extract display value from nested objects
            if "displayName" in value:
                value = value["displayName"]
            elif "name" in value:
                value = value["name"]
            elif "value" in value:
                value = value["value"]
            elif "emailAddress" in value:
                value = value["emailAddress"]
            else:
                value = json.dumps(value)
        elif isinstance(value, list):
            # Join list items
            items = []
            for item in value:
                if isinstance(item, dict):
                    items.append(
                        item.get("name")
                        or item.get("displayName")
                        or item.get("value")
                        or str(item)
                    )
                else:
                    items.append(str(item))
            value = ", ".join(items)
        elif not isinstance(value, str):
            value = str(value)

        row[field] = value

    return row


def stream_issues(
    client,
    jql: str,
    fields: list[str],
    max_results: int = DEFAULT_MAX_RESULTS,
    page_size: int = DEFAULT_PAGE_SIZE,
    next_page_token: str | None = None,
    progress_callback: Callable[[int, int, str | None], None] | None = None,
) -> Iterator[dict[str, Any]]:
    """
    Stream issues from JIRA API using token-based pagination.

    Uses nextPageToken per CHANGE-2046 migration requirements.

    Args:
        client: JIRA client instance
        jql: JQL query string
        fields: List of fields to fetch
        max_results: Maximum total results
        page_size: Results per API call
        next_page_token: Token to resume from (for checkpoint recovery)
        progress_callback: Optional callback(fetched, total, next_token)

    Yields:
        Issue dictionaries one at a time
    """
    total = None
    fetched = 0
    current_token = next_page_token

    while fetched < max_results:
        try:
            result = client.search_issues(
                jql,
                fields=fields,
                max_results=min(page_size, max_results - fetched),
                next_page_token=current_token,
            )

            if total is None:
                total = min(result.get("total", 0), max_results)
                if progress_callback:
                    progress_callback(fetched, total, current_token)

            issues = result.get("issues", [])
            if not issues:
                break

            # Get next page token for subsequent requests
            current_token = result.get("nextPageToken")

            for issue in issues:
                yield issue
                fetched += 1

                if fetched >= max_results:
                    break

            if progress_callback:
                progress_callback(fetched, total, current_token)

            # No more pages if no nextPageToken
            if not current_token:
                break

            # Small delay between pages to avoid rate limiting
            if fetched < total:
                time.sleep(0.1)

        except JiraError as e:
            print_warning(f"Error after fetching {fetched} issues: {e}")
            raise


class StreamingExporter:
    """
    Handles streaming export of large JIRA datasets.
    """

    def __init__(
        self,
        client,
        jql: str,
        output_file: str,
        format_type: str = "csv",
        fields: list[str] | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        page_size: int = DEFAULT_PAGE_SIZE,
        enable_checkpoint: bool = False,
    ):
        self.client = client
        self.jql = validate_jql(jql)
        self.output_file = output_file
        self.format_type = format_type.lower()
        self.max_results = max_results
        self.page_size = page_size
        self.enable_checkpoint = enable_checkpoint

        # Default fields if not specified
        if fields is None:
            self.fields = [
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
        else:
            self.fields = fields if "key" in fields else ["key", *fields]

        self.checkpoint_mgr = ExportCheckpointManager() if enable_checkpoint else None
        self.operation_id = generate_export_id() if enable_checkpoint else None

    def _write_csv_header(self, writer, columns: list[str]) -> None:
        """Write CSV header row."""
        writer.writerow(columns)

    def _write_csv_row(self, writer, row: dict[str, Any], columns: list[str]) -> None:
        """Write a single CSV row."""
        writer.writerow([row.get(col, "") for col in columns])

    def _write_jsonl_row(self, f, row: dict[str, Any]) -> None:
        """Write a single JSON Lines row."""
        f.write(json.dumps(row) + "\n")

    def export(
        self, resume_from: ExportProgress | None = None, show_progress: bool = True
    ) -> dict[str, Any]:
        """
        Execute streaming export.

        Uses token-based pagination per CHANGE-2046.

        Args:
            resume_from: Optional checkpoint to resume from
            show_progress: Show progress bar

        Returns:
            Export statistics
        """
        resume_token = None
        resume_count = 0
        mode = "w"

        # Handle resume
        if resume_from:
            resume_token = resume_from.next_page_token
            resume_count = resume_from.total_exported
            mode = "a"
            print_info(f"Resuming from checkpoint (exported: {resume_count})")

        # Get total count first
        initial_result = self.client.search_issues(
            self.jql, fields=["key"], max_results=1
        )
        total_available = initial_result.get("total", 0)
        total_to_export = min(total_available, self.max_results)

        if total_to_export == 0:
            return {
                "success": True,
                "exported": 0,
                "total": 0,
                "output_file": self.output_file,
            }

        print_info(f"Exporting {total_to_export} issues to {self.output_file}")
        print_info(f"  Format: {self.format_type}, Page size: {self.page_size}")

        # Initialize progress
        progress = ExportProgress(
            jql=self.jql,
            output_file=self.output_file,
            format_type=self.format_type,
            total_expected=total_to_export,
            total_exported=resume_count,
            next_page_token=resume_token,
            started_at=resume_from.started_at
            if resume_from
            else datetime.now().isoformat(),
            fields=self.fields,
        )

        exported = resume_count
        current_token = resume_token
        columns = ["key"] + [f for f in self.fields if f != "key"]

        # Setup progress tracking
        pbar = None
        if TQDM_AVAILABLE and show_progress:
            pbar = tqdm(
                total=total_to_export,
                initial=resume_count,
                desc="Exporting",
                unit="issue",
            )

        try:
            if self.format_type == "csv":
                with open(self.output_file, mode, newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)

                    # Write header if starting fresh
                    if mode == "w":
                        self._write_csv_header(writer, columns)

                    def update_token(fetched, total, token):
                        nonlocal current_token
                        current_token = token

                    for issue in stream_issues(
                        self.client,
                        self.jql,
                        self.fields,
                        max_results=self.max_results,
                        page_size=self.page_size,
                        next_page_token=current_token,
                        progress_callback=update_token,
                    ):
                        row = flatten_issue(issue, self.fields)
                        self._write_csv_row(writer, row, columns)
                        exported += 1

                        if pbar:
                            pbar.update(1)

                        # Save checkpoint periodically
                        if (
                            self.enable_checkpoint
                            and exported % CHECKPOINT_INTERVAL == 0
                        ):
                            progress.total_exported = exported
                            progress.next_page_token = current_token
                            self.checkpoint_mgr.save(self.operation_id, progress)

            elif self.format_type == "jsonl":
                with open(self.output_file, mode, encoding="utf-8") as f:

                    def update_token_jsonl(fetched, total, token):
                        nonlocal current_token
                        current_token = token

                    for issue in stream_issues(
                        self.client,
                        self.jql,
                        self.fields,
                        max_results=self.max_results,
                        page_size=self.page_size,
                        next_page_token=current_token,
                        progress_callback=update_token_jsonl,
                    ):
                        row = flatten_issue(issue, self.fields)
                        self._write_jsonl_row(f, row)
                        exported += 1

                        if pbar:
                            pbar.update(1)

                        # Save checkpoint periodically
                        if (
                            self.enable_checkpoint
                            and exported % CHECKPOINT_INTERVAL == 0
                        ):
                            progress.total_exported = exported
                            progress.next_page_token = current_token
                            self.checkpoint_mgr.save(self.operation_id, progress)

            elif self.format_type == "json":
                # JSON format requires collecting all results
                # For very large exports, recommend jsonl instead
                if total_to_export > 50000:
                    print_warning(
                        "JSON format may use significant memory for large exports. "
                        "Consider using --format jsonl instead."
                    )

                all_rows = []
                for issue in stream_issues(
                    self.client,
                    self.jql,
                    self.fields,
                    max_results=self.max_results,
                    page_size=self.page_size,
                    next_page_token=current_token,
                ):
                    row = flatten_issue(issue, self.fields)
                    all_rows.append(row)
                    exported += 1

                    if pbar:
                        pbar.update(1)

                with open(self.output_file, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "issues": all_rows,
                            "total": len(all_rows),
                            "jql": self.jql,
                            "exported_at": datetime.now().isoformat(),
                        },
                        f,
                        indent=2,
                    )

        finally:
            if pbar:
                pbar.close()

        # Mark complete and clean up checkpoint
        if self.enable_checkpoint:
            progress.total_exported = exported
            progress.is_complete = True
            self.checkpoint_mgr.clear(self.operation_id)

        return {
            "success": True,
            "exported": exported,
            "total": total_to_export,
            "output_file": self.output_file,
            "format": self.format_type,
            "operation_id": self.operation_id,
        }


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Streaming export for large JIRA search results",
        epilog="""
Examples:
  %(prog)s "project = PROJ" --output report.csv
  %(prog)s "project = PROJ" --output report.jsonl --format jsonl
  %(prog)s "project = PROJ" --output report.csv --max-results 50000
  %(prog)s "project = PROJ" --output report.csv --enable-checkpoint
  %(prog)s --list-checkpoints
  %(prog)s --resume export-20231215-143022
        """,
    )

    parser.add_argument("jql", nargs="?", help="JQL query string")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument(
        "--format",
        "-f",
        choices=["csv", "json", "jsonl"],
        default="csv",
        help="Export format (default: csv)",
    )
    parser.add_argument("--fields", help="Comma-separated list of fields to export")
    parser.add_argument(
        "--max-results",
        "-m",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help=f"Maximum results to export (default: {DEFAULT_MAX_RESULTS})",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help=f"Results per API call (default: {DEFAULT_PAGE_SIZE})",
    )
    parser.add_argument(
        "--enable-checkpoint",
        action="store_true",
        help="Enable checkpoint/resume for large exports",
    )
    parser.add_argument("--resume", help="Resume from checkpoint (operation ID)")
    parser.add_argument(
        "--list-checkpoints",
        action="store_true",
        help="List pending export checkpoints",
    )
    parser.add_argument(
        "--no-progress", action="store_true", help="Disable progress bar"
    )

    args = parser.parse_args(argv)

    try:
        # Handle list checkpoints
        if args.list_checkpoints:
            mgr = ExportCheckpointManager()
            checkpoints = mgr.list_pending()
            if not checkpoints:
                print("No pending export checkpoints found.")
            else:
                print(f"Found {len(checkpoints)} pending export(s):\n")
                for cp in checkpoints:
                    print(f"  ID: {cp['operation_id']}")
                    print(f"    Query: {cp['jql']}")
                    print(f"    Output: {cp['output_file']}")
                    print(f"    Progress: {cp['progress']} ({cp['percent']:.1f}%)")
                    print(f"    Updated: {cp['updated_at']}")
                    print()
            sys.exit(0)

        # Handle resume
        if args.resume:
            mgr = ExportCheckpointManager()
            progress = mgr.load(args.resume)
            if not progress:
                print(f"Error: Checkpoint '{args.resume}' not found.")
                sys.exit(1)

            print_info(f"Resuming export: {args.resume}")
            client = get_jira_client()

            exporter = StreamingExporter(
                client=client,
                jql=progress.jql,
                output_file=progress.output_file,
                format_type=progress.format_type,
                fields=progress.fields,
                max_results=progress.total_expected,
                enable_checkpoint=True,
            )
            exporter.operation_id = args.resume

            result = exporter.export(
                resume_from=progress, show_progress=not args.no_progress
            )

            client.close()
            print_success(
                f"Export complete: {result['exported']} issues to {result['output_file']}"
            )
            sys.exit(0)

        # Normal export
        if not args.jql:
            parser.error("JQL query is required (or use --resume/--list-checkpoints)")
        if not args.output:
            parser.error("--output is required")

        fields = [f.strip() for f in args.fields.split(",")] if args.fields else None

        client = get_jira_client()

        exporter = StreamingExporter(
            client=client,
            jql=args.jql,
            output_file=args.output,
            format_type=args.format,
            fields=fields,
            max_results=args.max_results,
            page_size=args.page_size,
            enable_checkpoint=args.enable_checkpoint,
        )

        result = exporter.export(show_progress=not args.no_progress)

        client.close()

        print_success(
            f"Export complete: {result['exported']} issues to {result['output_file']}"
        )
        if result.get("operation_id"):
            print_info(f"  Operation ID: {result['operation_id']}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nExport cancelled")
        if args.enable_checkpoint:
            print("Use --resume to continue from last checkpoint")
        sys.exit(130)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
