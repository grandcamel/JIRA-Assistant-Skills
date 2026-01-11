#!/usr/bin/env python3
"""
Export JQL search results to file.

Usage:
    python export_results.py "project = PROJ" --output report.csv
    python export_results.py "assignee = currentUser()" --output my-issues.json --format json
"""

import argparse
import json
import sys

from jira_assistant_skills_lib import (
    JiraError,
    export_csv,
    get_jira_client,
    print_error,
    print_success,
    validate_jql,
)


def export_results(
    jql: str,
    output_file: str,
    format_type: str = "csv",
    fields: list | None = None,
    max_results: int = 1000,
) -> None:
    """
    Export search results to file.

    Args:
        jql: JQL query
        output_file: Output file path
        format_type: Export format ('csv' or 'json')
        fields: Fields to include
        max_results: Maximum results to export
    """
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
    results = client.search_issues(
        jql, fields=fields, max_results=max_results, start_at=0
    )
    client.close()

    issues = results.get("issues", [])

    if not issues:
        print("No issues found to export")
        return

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
                    item.get("name", str(item)) if isinstance(item, dict) else str(item)
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
            json.dump({"issues": export_data, "total": len(export_data)}, f, indent=2)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Export JQL search results to file",
        epilog='Example: python export_results.py "project = PROJ" --output report.csv',
    )

    parser.add_argument("jql", help="JQL query string")
    parser.add_argument("--output", "-o", required=True, help="Output file path")
    parser.add_argument(
        "--format",
        "-f",
        choices=["csv", "json"],
        default="csv",
        help="Export format (default: csv)",
    )
    parser.add_argument("--fields", help="Comma-separated list of fields to include")
    parser.add_argument(
        "--max-results",
        "-m",
        type=int,
        default=1000,
        help="Maximum results to export (default: 1000)",
    )

    args = parser.parse_args(argv)

    try:
        fields = [f.strip() for f in args.fields.split(",")] if args.fields else None

        export_results(
            jql=args.jql,
            output_file=args.output,
            format_type=args.format,
            fields=fields,
            max_results=args.max_results,
        )

        print_success(f"Exported results to {args.output}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
