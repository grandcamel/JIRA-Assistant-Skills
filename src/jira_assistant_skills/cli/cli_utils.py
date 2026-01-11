"""
CLI utilities for jira-as commands.

Provides common patterns for Click commands:
- Parsing utilities (comma-separated lists, JSON)
- Error handling decorator
- Output formatting helpers
"""

import json
from collections.abc import Callable
from functools import wraps
from typing import Any

import click

from jira_assistant_skills_lib import JiraError, print_error


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
        click.BadParameter: If JSON is invalid
    """
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        raise click.BadParameter(f"Invalid JSON: {e}") from e


def handle_jira_errors(func: Callable) -> Callable:
    """
    Decorator for Click commands with standard JIRA error handling.

    Catches:
        - JiraError: Prints error message, exits with 1
        - KeyboardInterrupt: Prints cancellation message, exits with 130
        - click.BadParameter: Re-raises for Click to handle
        - Exception: Prints error with debug info, exits with 1

    Example:
        @issue.command(name="get")
        @click.argument("issue_key")
        @click.pass_context
        @handle_jira_errors
        def get_issue(ctx, issue_key):
            result = _get_issue_impl(issue_key)
            click.echo(format_issue(result))
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract ctx from args or kwargs
        ctx = kwargs.get("ctx") or (args[0] if args else None)
        try:
            return func(*args, **kwargs)
        except click.exceptions.Exit:
            # Normal exit, re-raise
            raise
        except click.BadParameter:
            # Let Click handle bad parameter errors
            raise
        except JiraError as e:
            print_error(e)
            if ctx and hasattr(ctx, "exit"):
                ctx.exit(1)
            else:
                raise SystemExit(1)
        except KeyboardInterrupt:
            click.echo("\nOperation cancelled", err=True)
            if ctx and hasattr(ctx, "exit"):
                ctx.exit(130)
            else:
                raise SystemExit(130)
        except Exception as e:
            print_error(e, debug=True)
            if ctx and hasattr(ctx, "exit"):
                ctx.exit(1)
            else:
                raise SystemExit(1)

    return wrapper


def format_json_output(data: Any) -> str:
    """
    Format data as pretty-printed JSON.

    Args:
        data: Data to format

    Returns:
        JSON string with 2-space indentation
    """
    return json.dumps(data, indent=2, default=str)


# Alias for convenience
format_json = format_json_output


def get_output_format(ctx: click.Context, explicit_output: str | None) -> str:
    """
    Get output format from explicit option or context.

    Args:
        ctx: Click context
        explicit_output: Explicitly specified output format

    Returns:
        Output format string ("text", "json", or "table")
    """
    if explicit_output:
        return explicit_output
    return ctx.obj.get("OUTPUT", "text") if ctx.obj else "text"


__all__ = [
    "format_json",
    "format_json_output",
    "get_output_format",
    "handle_jira_errors",
    "parse_comma_list",
    "parse_json_arg",
]
