#!/usr/bin/env python3
"""
Shared utilities for JIRA Assistant skill scripts.

Provides common patterns for:
- Argument parsing (comma-separated lists, JSON fields)
- Error handling and exit codes
- Output formatting (text vs JSON)
- Profile handling

Usage:
    from shared.scripts.script_utils import (
        run_script,
        parse_comma_list,
        parse_json_arg,
        add_common_args,
        format_output,
    )

    def main(argv=None):
        parser = argparse.ArgumentParser(...)
        add_common_args(parser)  # Adds --profile, --output
        args = parser.parse_args(argv)

        result = my_operation(...)
        format_output(result, args.output, success_message=f"Done: {result['key']}")

    if __name__ == "__main__":
        run_script(main)  # Handles errors and exit codes
"""

import argparse
import json
import sys
from collections.abc import Callable
from functools import wraps
from typing import Any

from jira_assistant_skills_lib import JiraError, print_error, print_success


def parse_comma_list(value: str | None) -> list[str] | None:
    """
    Parse a comma-separated string into a list.

    Args:
        value: Comma-separated string or None

    Returns:
        List of stripped strings, or None if input is None/empty/whitespace

    Example:
        parse_comma_list("a, b, c") -> ["a", "b", "c"]
        parse_comma_list(None) -> None
    """
    if not value or not value.strip():
        return None
    result = [item.strip() for item in value.split(",") if item.strip()]
    return result if result else None


def parse_json_arg(value: str | None) -> dict | None:
    """
    Parse a JSON string argument into a dict.

    Args:
        value: JSON string or None

    Returns:
        Parsed dict, or None if input is None/empty

    Raises:
        ValueError: If JSON is invalid
    """
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """
    Add common arguments to an argument parser.

    Adds:
        --output: Output format (text/json)

    Args:
        parser: ArgumentParser instance to modify
    """
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def add_bulk_args(parser: argparse.ArgumentParser) -> None:
    """
    Add common bulk operation arguments.

    Adds:
        --dry-run: Preview without making changes
        --max-issues: Maximum issues to process
        --yes: Skip confirmation prompt
        --no-progress: Disable progress bar
    """
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without making them",
    )
    parser.add_argument(
        "--max-issues",
        type=int,
        default=100,
        help="Maximum issues to process (default: 100)",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt for large operations",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar",
    )


def format_output(
    result: Any,
    output_format: str = "text",
    success_message: str | None = None,
    text_formatter: Callable[[Any], str] | None = None,
) -> None:
    """
    Format and print output based on format preference.

    Args:
        result: Result data to output
        output_format: "text" or "json"
        success_message: Message to print for text format (uses print_success)
        text_formatter: Optional custom formatter for text output

    Example:
        format_output(
            {"key": "PROJ-123", "summary": "Test"},
            args.output,
            success_message=f"Created: {result['key']}"
        )
    """
    if output_format == "json":
        print(json.dumps(result, indent=2, default=str))
    else:
        if text_formatter:
            print(text_formatter(result))
        elif success_message:
            print_success(success_message)
        else:
            # Default: pretty print dict
            for key, value in result.items() if isinstance(result, dict) else []:
                print(f"{key}: {value}")


def run_script(main_func: Callable, argv: list[str] | None = None) -> None:
    """
    Run a script's main function with standard error handling.

    Catches:
        - JiraError: Prints error message, exits with 1
        - KeyboardInterrupt: Prints cancellation message, exits with 130
        - Exception: Prints error with debug info, exits with 1

    Args:
        main_func: Main function to run (should accept argv parameter)
        argv: Command line arguments (default: sys.argv[1:])

    Example:
        def main(argv=None):
            parser = argparse.ArgumentParser(...)
            args = parser.parse_args(argv)
            # ... do work ...

        if __name__ == "__main__":
            run_script(main)
    """
    try:
        main_func(argv)
    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(130)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


def script_main(func: Callable) -> Callable:
    """
    Decorator for script main functions with error handling.

    Wraps the function with run_script error handling.

    Example:
        @script_main
        def main(argv=None):
            parser = argparse.ArgumentParser(...)
            args = parser.parse_args(argv)
            # ... do work ...

        if __name__ == "__main__":
            main()
    """

    @wraps(func)
    def wrapper(argv: list[str] | None = None):
        run_script(func, argv)

    return wrapper


class ScriptResult:
    """
    Helper class for building script results with consistent structure.

    Example:
        result = ScriptResult()
        result.set("key", "PROJ-123")
        result.set("summary", "Test issue")
        result.add_info("Created successfully")
        result.add_warning("No assignee specified")
        return result.to_dict()
    """

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._info: list[str] = []
        self._warnings: list[str] = []

    def set(self, key: str, value: Any) -> "ScriptResult":
        """Set a result field."""
        self._data[key] = value
        return self

    def add_info(self, message: str) -> "ScriptResult":
        """Add an informational message."""
        self._info.append(message)
        return self

    def add_warning(self, message: str) -> "ScriptResult":
        """Add a warning message."""
        self._warnings.append(message)
        return self

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = dict(self._data)
        if self._info:
            result["_info"] = self._info
        if self._warnings:
            result["_warnings"] = self._warnings
        return result


# Convenience re-exports
__all__ = [
    "ScriptResult",
    "add_bulk_args",
    "add_common_args",
    "format_output",
    "parse_comma_list",
    "parse_json_arg",
    "run_script",
    "script_main",
]
