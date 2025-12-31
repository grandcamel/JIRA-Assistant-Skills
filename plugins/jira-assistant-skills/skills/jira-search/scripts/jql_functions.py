#!/usr/bin/env python3
"""
List JQL functions with usage examples.

Shows all functions available for JQL queries, including their
return types and example usage patterns.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add shared library to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, print_error
from jira_assistant_skills_lib import format_table


# Example usages for common functions
FUNCTION_EXAMPLES = {
    'currentUser()': 'assignee = currentUser()',
    'membersOf(group)': 'assignee in membersOf("developers")',
    'startOfDay()': 'created >= startOfDay(-7)',
    'startOfWeek()': 'created >= startOfWeek()',
    'startOfMonth()': 'created >= startOfMonth()',
    'endOfDay()': 'duedate <= endOfDay()',
    'endOfWeek()': 'duedate <= endOfWeek()',
    'endOfMonth()': 'duedate <= endOfMonth()',
    'now()': 'updated >= now("-1h")',
    'currentLogin()': 'lastViewed > currentLogin()',
    'openSprints()': 'sprint in openSprints()',
    'closedSprints()': 'sprint in closedSprints()',
    'futureSprints()': 'sprint in futureSprints()',
    'componentsLeadByUser()': 'component in componentsLeadByUser()',
    'projectsLeadByUser()': 'project in projectsLeadByUser()',
    'projectsWhereUserHasPermission()': 'project in projectsWhereUserHasPermission("Browse Projects")',
    'projectsWhereUserHasRole()': 'project in projectsWhereUserHasRole("Administrators")',
    'issueHistory()': 'issue in issueHistory()',
    'linkedIssues()': 'issue in linkedIssues("PROJ-123")',
    'votedIssues()': 'issue in votedIssues()',
    'watchedIssues()': 'issue in watchedIssues()',
}


def get_functions(client, name_filter: Optional[str] = None,
                  list_only: bool = False,
                  type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get JQL functions.

    Args:
        client: JIRA client
        name_filter: Filter functions by name (case-insensitive substring match)
        list_only: Only return functions that return lists (for IN operator)
        type_filter: Filter by return type (case-insensitive)

    Returns:
        List of function objects
    """
    data = client.get_jql_autocomplete()
    functions = data.get('visibleFunctionNames', [])

    # Apply filters
    if name_filter:
        name_lower = name_filter.lower()
        functions = [f for f in functions
                     if name_lower in f.get('value', '').lower()
                     or name_lower in f.get('displayName', '').lower()]

    if list_only:
        functions = [f for f in functions if f.get('isList') == 'true']

    if type_filter:
        type_lower = type_filter.lower()
        functions = [f for f in functions
                     if any(type_lower in str(t).lower()
                            for t in f.get('types', []))]

    return functions


def get_return_type(func: Dict[str, Any]) -> str:
    """
    Extract human-readable return type from function.

    Args:
        func: Function object

    Returns:
        Human-readable type string
    """
    types = func.get('types', [])
    if not types:
        return 'Unknown'

    # Simplify type names
    simplified = []
    for t in types:
        if 'Date' in str(t):
            simplified.append('Date')
        elif 'User' in str(t) or 'ApplicationUser' in str(t):
            simplified.append('User')
        elif 'Issue' in str(t):
            simplified.append('Issue')
        elif 'Project' in str(t):
            simplified.append('Project')
        elif 'Component' in str(t):
            simplified.append('Component')
        elif 'Sprint' in str(t):
            simplified.append('Sprint')
        else:
            # Use the simple name after last dot
            simple = str(t).split('.')[-1]
            simplified.append(simple)

    return ', '.join(set(simplified))


def format_functions_text(functions: List[Dict[str, Any]],
                          show_examples: bool = False) -> str:
    """
    Format functions as human-readable table.

    Args:
        functions: List of function objects
        show_examples: Include usage examples

    Returns:
        Formatted string
    """
    if not functions:
        return "No functions found"

    # Prepare data for table
    data = []
    for func in functions:
        is_list = func.get('isList') == 'true'
        return_type = get_return_type(func)

        row = {
            'Function': func.get('value', ''),
            'Returns List': 'Yes' if is_list else 'No',
            'Type': return_type
        }
        data.append(row)

    # Sort by function name
    data.sort(key=lambda x: x['Function'].lower())

    table = format_table(data, columns=['Function', 'Returns List', 'Type'])

    # Add examples if requested
    if show_examples:
        examples = []
        for func in functions:
            func_name = func.get('value', '')
            # Find a matching example
            for key, example in FUNCTION_EXAMPLES.items():
                if key in func_name or func_name in key:
                    examples.append(f"  {example}")
                    break

        if examples:
            # Limit to 5 examples
            examples = examples[:5]
            examples_str = "\n\nExamples:\n" + "\n".join(examples)
            table += examples_str

    return f"JQL Functions:\n\n{table}\n\nTotal: {len(functions)} functions"


def format_functions_json(functions: List[Dict[str, Any]]) -> str:
    """
    Format functions as JSON.

    Args:
        functions: List of function objects

    Returns:
        JSON string
    """
    return json.dumps(functions, indent=2)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='List JQL functions with usage examples.',
        epilog='''
Examples:
  %(prog)s                       # List all functions
  %(prog)s --filter date         # Filter functions containing "date"
  %(prog)s --list-only           # Show only functions returning lists
  %(prog)s --type Date           # Show only date functions
  %(prog)s --with-examples       # Include usage examples
  %(prog)s --output json         # Output as JSON
        '''
    )

    parser.add_argument('--filter', '-f', dest='name_filter',
                        help='Filter functions by name (case-insensitive)')
    parser.add_argument('--list-only', action='store_true',
                        help='Show only functions that return lists')
    parser.add_argument('--type', '-t', dest='type_filter',
                        help='Filter by return type (e.g., Date, User)')
    parser.add_argument('--with-examples', action='store_true',
                        help='Include usage examples')
    parser.add_argument('--output', '-o', choices=['text', 'json'],
                        default='text', help='Output format (default: text)')
    parser.add_argument('--profile', '-p',
                        help='JIRA profile to use')

    args = parser.parse_args(argv)

    try:
        client = get_jira_client(args.profile)

        functions = get_functions(
            client,
            name_filter=args.name_filter,
            list_only=args.list_only,
            type_filter=args.type_filter
        )

        if args.output == 'json':
            print(format_functions_json(functions))
        else:
            print(format_functions_text(functions, show_examples=args.with_examples))

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
