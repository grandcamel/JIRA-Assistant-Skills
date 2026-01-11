#!/usr/bin/env python3
"""
Run a saved JIRA filter.

Usage:
    python run_filter.py --id 12345
    python run_filter.py --name "My Open Issues"
"""

import argparse
import sys

from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    format_json,
    format_search_results,
    get_jira_client,
    print_error,
    print_info,
)


def run_filter(
    filter_id: str | None = None,
    filter_name: str | None = None,
    max_results: int = 50,
) -> dict:
    """
    Execute a saved filter.

    Args:
        filter_id: Filter ID
        filter_name: Filter name (alternative to ID)
        max_results: Maximum results

    Returns:
        Search results
    """
    if not filter_id and not filter_name:
        raise ValidationError("Either --id or --name must be specified")

    client = get_jira_client()

    if filter_name:
        filters = client.get("/rest/api/3/filter/my", operation="get filters")
        if isinstance(filters, list):
            matching = [
                f for f in filters if f.get("name", "").lower() == filter_name.lower()
            ]
            if not matching:
                raise ValidationError(f"Filter '{filter_name}' not found")
            filter_id = matching[0]["id"]
        else:
            raise ValidationError("Could not retrieve filters")

    filter_data = client.get(
        f"/rest/api/3/filter/{filter_id}", operation=f"get filter {filter_id}"
    )
    jql = filter_data.get("jql", "")

    if not jql:
        raise ValidationError(f"Filter {filter_id} has no JQL query")

    results = client.search_issues(jql, max_results=max_results)
    client.close()

    return results


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Run a saved JIRA filter",
        epilog='Example: python run_filter.py --name "My Open Issues"',
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", help="Filter ID")
    group.add_argument("--name", "-n", help="Filter name")

    parser.add_argument(
        "--max-results",
        "-m",
        type=int,
        default=50,
        help="Maximum number of results (default: 50)",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        results = run_filter(
            filter_id=args.id,
            filter_name=args.name,
            max_results=args.max_results,
        )

        issues = results.get("issues", [])
        total = results.get("total", 0)

        if args.output == "json":
            print(format_json(results))
        else:
            print_info(f"Found {total} issue(s)")
            if issues:
                print()
                print(format_search_results(issues))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
