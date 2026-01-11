#!/usr/bin/env python3
"""
Interactive JQL query builder.

Provides a guided interface for building JQL queries with
field suggestions, validation, and testing.

Usage:
    python jql_interactive.py
    python jql_interactive.py --start-with "project = PROJ"
    python jql_interactive.py --quick
"""

import argparse
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    print_error,
    print_info,
    print_success,
)

# Common JQL fields with their operators
COMMON_FIELDS = {
    "project": {
        "operators": ["=", "!=", "in", "not in"],
        "example": "project = PROJ",
        "description": "Project key or name",
    },
    "status": {
        "operators": [
            "=",
            "!=",
            "in",
            "not in",
            "was",
            "was in",
            "was not",
            "was not in",
            "changed",
        ],
        "example": 'status = "In Progress"',
        "description": "Issue status",
    },
    "assignee": {
        "operators": [
            "=",
            "!=",
            "in",
            "not in",
            "was",
            "was in",
            "was not",
            "was not in",
            "changed",
            "is",
            "is not",
        ],
        "example": "assignee = currentUser()",
        "description": "Assigned user",
    },
    "reporter": {
        "operators": [
            "=",
            "!=",
            "in",
            "not in",
            "was",
            "was in",
            "was not",
            "was not in",
            "changed",
            "is",
            "is not",
        ],
        "example": "reporter = currentUser()",
        "description": "Issue reporter",
    },
    "priority": {
        "operators": ["=", "!=", ">", ">=", "<", "<=", "in", "not in"],
        "example": "priority = High",
        "description": "Issue priority",
    },
    "type": {
        "operators": ["=", "!=", "in", "not in"],
        "example": "type = Bug",
        "description": "Issue type (Bug, Story, Task, etc.)",
    },
    "created": {
        "operators": ["=", "!=", ">", ">=", "<", "<="],
        "example": "created >= -7d",
        "description": "Creation date/time",
    },
    "updated": {
        "operators": ["=", "!=", ">", ">=", "<", "<="],
        "example": "updated >= startOfDay()",
        "description": "Last update date/time",
    },
    "resolved": {
        "operators": ["=", "!=", ">", ">=", "<", "<=", "is", "is not"],
        "example": "resolved >= -30d",
        "description": "Resolution date/time",
    },
    "duedate": {
        "operators": ["=", "!=", ">", ">=", "<", "<=", "is", "is not"],
        "example": "duedate < now()",
        "description": "Due date",
    },
    "labels": {
        "operators": ["=", "!=", "in", "not in", "is", "is not"],
        "example": "labels = urgent",
        "description": "Issue labels",
    },
    "sprint": {
        "operators": ["=", "!=", "in", "not in", "is", "is not"],
        "example": "sprint in openSprints()",
        "description": "Agile sprint",
    },
    "text": {
        "operators": ["~", "!~"],
        "example": 'text ~ "search term"',
        "description": "Full text search",
    },
    "summary": {
        "operators": ["~", "!~", "is", "is not"],
        "example": 'summary ~ "bug"',
        "description": "Issue summary text search",
    },
    "description": {
        "operators": ["~", "!~", "is", "is not"],
        "example": 'description ~ "error"',
        "description": "Issue description text search",
    },
}


# Common JQL functions
JQL_FUNCTIONS = {
    "currentUser()": "The currently logged-in user",
    "startOfDay()": "Start of today",
    "startOfDay(-1d)": "Start of yesterday",
    "startOfDay(-7d)": "Start of 7 days ago",
    "startOfWeek()": "Start of current week",
    "startOfMonth()": "Start of current month",
    "endOfDay()": "End of today",
    "endOfWeek()": "End of current week",
    "endOfMonth()": "End of current month",
    "now()": "Current date/time",
    "openSprints()": "All open/active sprints",
    "closedSprints()": "All closed sprints",
    "futureSprints()": "All future sprints",
    'membersOf("group")': "Members of a JIRA group",
    "EMPTY": "Field has no value",
    "NULL": "Field has no value (same as EMPTY)",
}


class InteractiveBuilder:
    """Interactive JQL query builder."""

    def __init__(self):
        self.clauses = []
        self.order_by = None
        self.order_desc = False
        self.client = None

    def get_client(self):
        """Get or create JIRA client."""
        if not self.client:
            self.client = get_jira_client()
        return self.client

    def close_client(self):
        """Close JIRA client if open."""
        if self.client:
            self.client.close()
            self.client = None

    def build_jql(self) -> str:
        """Build the current JQL query string."""
        if not self.clauses:
            return ""

        jql = " AND ".join(self.clauses)

        if self.order_by:
            direction = "DESC" if self.order_desc else "ASC"
            jql = f"{jql} ORDER BY {self.order_by} {direction}"

        return jql

    def add_clause(self, clause: str):
        """Add a clause to the query."""
        self.clauses.append(clause)

    def remove_clause(self, index: int) -> bool:
        """Remove a clause by index."""
        if 0 <= index < len(self.clauses):
            del self.clauses[index]
            return True
        return False

    def clear_clauses(self):
        """Clear all clauses."""
        self.clauses = []
        self.order_by = None
        self.order_desc = False

    def set_order(self, field: str, desc: bool = False):
        """Set ORDER BY clause."""
        self.order_by = field
        self.order_desc = desc

    def validate(self) -> dict[str, Any]:
        """Validate the current query."""
        jql = self.build_jql()
        if not jql:
            return {"valid": False, "errors": ["No query to validate"]}

        client = self.get_client()
        result = client.parse_jql([jql])
        parsed = result.get("queries", [{}])[0]
        errors = parsed.get("errors", [])

        return {"valid": len(errors) == 0, "errors": errors, "jql": jql}

    def run_query(self, max_results: int = 20) -> dict[str, Any]:
        """Run the current query."""
        jql = self.build_jql()
        if not jql:
            raise ValidationError("No query to run")

        client = self.get_client()
        return client.search_issues(
            jql,
            fields=["key", "summary", "status", "priority", "issuetype"],
            max_results=max_results,
        )

    def get_projects(self) -> list[str]:
        """Get available projects."""
        client = self.get_client()
        projects = client.get_projects()
        return [p.get("key", "") for p in projects]

    def get_statuses(self) -> list[str]:
        """Get available statuses."""
        client = self.get_client()
        statuses = client.get("/rest/api/3/status")
        return list({s.get("name", "") for s in statuses})

    def get_priorities(self) -> list[str]:
        """Get available priorities."""
        client = self.get_client()
        priorities = client.get("/rest/api/3/priority")
        return [p.get("name", "") for p in priorities]


def prompt(message: str, default: str | None = None) -> str:
    """Prompt user for input."""
    if default:
        result = input(f"{message} [{default}]: ").strip()
        return result if result else default
    return input(f"{message}: ").strip()


def prompt_choice(message: str, choices: list[str], allow_custom: bool = False) -> str:
    """Prompt user to select from choices."""
    print(f"\n{message}")
    for i, choice in enumerate(choices, 1):
        print(f"  [{i}] {choice}")
    if allow_custom:
        print("  [c] Enter custom value")

    while True:
        selection = input("Select: ").strip().lower()

        if allow_custom and selection == "c":
            return input("Enter value: ").strip()

        try:
            idx = int(selection) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass

        print("Invalid selection, try again.")


def display_menu(builder: InteractiveBuilder):
    """Display main menu."""
    print("\n" + "=" * 50)
    print("JQL Interactive Builder")
    print("=" * 50)

    jql = builder.build_jql()
    if jql:
        print(f"\nCurrent query:\n  {jql}")
    else:
        print("\nCurrent query: (empty)")

    print("\nClauses:")
    if builder.clauses:
        for i, clause in enumerate(builder.clauses):
            print(f"  [{i}] {clause}")
    else:
        print("  (none)")

    print("\nActions:")
    print("  [1] Add field clause")
    print("  [2] Add custom clause")
    print("  [3] Set ORDER BY")
    print("  [4] Remove clause")
    print("  [5] Clear all")
    print("  [6] Validate query")
    print("  [7] Run query")
    print("  [8] Copy to clipboard")
    print("  [9] Show help")
    print("  [0] Exit")


def add_field_clause(builder: InteractiveBuilder):
    """Interactively add a field clause."""
    fields = list(COMMON_FIELDS.keys())
    field = prompt_choice("Select field", fields, allow_custom=True)

    if field in COMMON_FIELDS:
        operators = COMMON_FIELDS[field]["operators"]
        print(f"\nExample: {COMMON_FIELDS[field]['example']}")
    else:
        operators = [
            "=",
            "!=",
            "~",
            "in",
            "not in",
            "is",
            "is not",
            ">",
            ">=",
            "<",
            "<=",
        ]

    operator = prompt_choice("Select operator", operators)

    # Get value with suggestions for certain fields
    if field == "project":
        try:
            projects = builder.get_projects()
            if projects:
                print(f"\nAvailable projects: {', '.join(projects[:10])}")
        except Exception:
            pass

    if field == "status":
        try:
            statuses = builder.get_statuses()
            if statuses:
                print(f"\nAvailable statuses: {', '.join(statuses[:10])}")
        except Exception:
            pass

    if field == "priority":
        try:
            priorities = builder.get_priorities()
            if priorities:
                print(f"\nAvailable priorities: {', '.join(priorities)}")
        except Exception:
            pass

    if field in ["assignee", "reporter"]:
        print("\nCommon values: currentUser(), EMPTY")

    if field in ["created", "updated", "resolved", "duedate"]:
        print("\nCommon values: -7d, startOfDay(), now(), startOfWeek()")

    value = prompt("Enter value")

    # Format the clause
    if operator in ["in", "not in"]:
        # Check if value looks like a list
        if "," in value and not value.startswith("("):
            value = f"({value})"
    elif operator in ["~", "!~"]:
        # Text search - quote if needed
        if '"' not in value and "'" not in value:
            value = f'"{value}"'
    elif operator in ["=", "!="] and field in ["status", "type", "priority"]:
        # Quote values with spaces
        if " " in value and '"' not in value:
            value = f'"{value}"'

    clause = f"{field} {operator} {value}"
    builder.add_clause(clause)
    print_success(f"Added: {clause}")


def show_help():
    """Show help information."""
    print("\n" + "=" * 50)
    print("JQL Help")
    print("=" * 50)

    print("\nCommon Fields:")
    for field, info in list(COMMON_FIELDS.items())[:8]:
        print(f"  {field}: {info['description']}")
        print(f"    Example: {info['example']}")

    print("\nCommon Functions:")
    for func, desc in list(JQL_FUNCTIONS.items())[:8]:
        print(f"  {func}: {desc}")

    print("\nTime Expressions:")
    print("  -7d       : 7 days ago")
    print("  -1w       : 1 week ago")
    print("  -30d      : 30 days ago")
    print("  startOfDay(-1d) : Start of yesterday")

    print("\nOperators:")
    print("  =, !=     : Equals / Not equals")
    print("  ~, !~     : Contains / Does not contain")
    print("  in, not in: In list / Not in list")
    print("  is, is not: Is empty / Is not empty")
    print("  >, >=, <, <=: Comparison")

    input("\nPress Enter to continue...")


def run_interactive(builder: InteractiveBuilder, start_with: str | None = None):
    """Run the interactive builder loop."""
    if start_with:
        builder.add_clause(start_with)
        print_info(f"Starting with: {start_with}")

    while True:
        try:
            display_menu(builder)
            choice = input("\nSelect action: ").strip()

            if choice == "1":
                add_field_clause(builder)

            elif choice == "2":
                clause = prompt("Enter custom clause (e.g., 'project = PROJ')")
                if clause:
                    builder.add_clause(clause)
                    print_success(f"Added: {clause}")

            elif choice == "3":
                field = prompt("ORDER BY field", "created")
                desc = prompt("Descending? (y/n)", "y").lower() == "y"
                builder.set_order(field, desc)
                print_success(f"Set ORDER BY {field} {'DESC' if desc else 'ASC'}")

            elif choice == "4":
                if builder.clauses:
                    idx = prompt("Clause index to remove")
                    try:
                        if builder.remove_clause(int(idx)):
                            print_success("Clause removed")
                        else:
                            print("Invalid index")
                    except ValueError:
                        print("Invalid index")
                else:
                    print("No clauses to remove")

            elif choice == "5":
                builder.clear_clauses()
                print_success("Cleared all clauses")

            elif choice == "6":
                result = builder.validate()
                if result["valid"]:
                    print_success("Query is valid!")
                else:
                    print("Validation errors:")
                    for error in result["errors"]:
                        print(f"  - {error}")

            elif choice == "7":
                try:
                    results = builder.run_query()
                    issues = results.get("issues", [])
                    total = results.get("total", 0)

                    if issues:
                        print(
                            f"\nFound {total} issue(s), showing first {len(issues)}:\n"
                        )
                        for issue in issues:
                            fields = issue.get("fields", {})
                            key = issue.get("key", "")
                            summary = fields.get("summary", "")[:50]
                            status = fields.get("status", {}).get("name", "")
                            print(f"  {key} [{status}] {summary}")
                    else:
                        print("\nNo issues found.")

                except Exception as e:
                    print(f"Error running query: {e}")

            elif choice == "8":
                jql = builder.build_jql()
                if jql:
                    print(f"\nCopy this JQL:\n{jql}")
                else:
                    print("No query to copy")

            elif choice == "9":
                show_help()

            elif choice == "0":
                jql = builder.build_jql()
                if jql:
                    print(f"\nFinal query:\n{jql}")
                break

            else:
                print("Invalid choice")

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break

    builder.close_client()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Interactive JQL query builder",
        epilog="""
Examples:
  %(prog)s
  %(prog)s --start-with "project = PROJ"
  %(prog)s --quick
        """,
    )

    parser.add_argument("--start-with", "-s", help="Start with an existing JQL clause")
    parser.add_argument(
        "--quick",
        "-q",
        action="store_true",
        help="Quick mode with common field prompts",
    )
    args = parser.parse_args(argv)

    try:
        builder = InteractiveBuilder()

        if args.quick:
            # Quick mode - prompt for common fields
            print("Quick Query Builder")
            print("=" * 40)
            print("Enter values or press Enter to skip\n")

            project = prompt("Project key")
            if project:
                builder.add_clause(f"project = {project}")

            status = prompt("Status (e.g., Open, 'In Progress')")
            if status:
                if " " in status and '"' not in status:
                    status = f'"{status}"'
                builder.add_clause(f"status = {status}")

            assignee = prompt("Assignee (e.g., currentUser())")
            if assignee:
                builder.add_clause(f"assignee = {assignee}")

            issue_type = prompt("Type (e.g., Bug, Story)")
            if issue_type:
                builder.add_clause(f"type = {issue_type}")

            # Show result
            jql = builder.build_jql()
            if jql:
                print(f"\nBuilt query:\n{jql}")

                validate = prompt("\nValidate and run? (y/n)", "y")
                if validate.lower() == "y":
                    result = builder.validate()
                    if result["valid"]:
                        print_success("Query is valid!")
                        results = builder.run_query()
                        total = results.get("total", 0)
                        print(f"Found {total} issue(s)")
                    else:
                        print("Validation errors:")
                        for error in result["errors"]:
                            print(f"  - {error}")
            else:
                print("\nNo query built (all fields skipped)")

            builder.close_client()

        else:
            run_interactive(builder, start_with=args.start_with)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
