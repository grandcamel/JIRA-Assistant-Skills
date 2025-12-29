#!/usr/bin/env python3
"""
Build JQL queries from components.

Helps construct JQL queries from clauses, templates, and options
with optional validation.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add shared library to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, print_error


# Predefined templates for common queries
TEMPLATES = {
    'my-open': 'assignee = currentUser() AND status != Done',
    'my-bugs': 'assignee = currentUser() AND type = Bug AND status != Done',
    'my-recent': 'assignee = currentUser() AND updated >= -7d ORDER BY updated DESC',
    'unassigned': 'assignee IS EMPTY AND status != Done',
    'sprint-incomplete': 'sprint in openSprints() AND status != Done',
    'sprint-complete': 'sprint in openSprints() AND status = Done',
    'blockers': 'priority = Highest AND status != Done',
    'overdue': 'duedate < now() AND status != Done',
    'created-today': 'created >= startOfDay()',
    'updated-today': 'updated >= startOfDay()',
    'no-estimate': 'timeoriginalestimate IS EMPTY AND type != Epic',
}


def build_jql(clauses: List[str],
              operator: str = 'AND',
              order_by: str = None,
              order_desc: bool = False) -> str:
    """
    Build JQL query from clauses.

    Args:
        clauses: List of JQL clauses (e.g., ['project = PROJ', 'status = Open'])
        operator: Join operator (AND or OR)
        order_by: Field to order by
        order_desc: Use descending order

    Returns:
        Complete JQL query string
    """
    if not clauses:
        return ''

    # Join clauses with operator
    jql = f' {operator} '.join(clauses)

    # Add ORDER BY if specified
    if order_by:
        direction = 'DESC' if order_desc else 'ASC'
        jql = f'{jql} ORDER BY {order_by} {direction}'

    return jql


def build_from_template(template_name: str,
                        substitutions: Dict[str, str] = None) -> str:
    """
    Build JQL from a predefined template.

    Args:
        template_name: Name of the template
        substitutions: Optional substitutions (e.g., {'PROJ': 'MYPROJ'})

    Returns:
        JQL query string
    """
    if template_name not in TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}. "
                        f"Available: {', '.join(TEMPLATES.keys())}")

    jql = TEMPLATES[template_name]

    # Apply substitutions if provided
    if substitutions:
        for key, value in substitutions.items():
            jql = jql.replace(key, value)

    return jql


def build_and_validate(client, clauses: List[str] = None,
                       template: str = None,
                       operator: str = 'AND',
                       order_by: str = None,
                       order_desc: bool = False) -> Dict[str, Any]:
    """
    Build and validate a JQL query.

    Args:
        client: JIRA client
        clauses: List of JQL clauses
        template: Template name to use instead of clauses
        operator: Join operator
        order_by: Field to order by
        order_desc: Use descending order

    Returns:
        dict with jql, valid, and errors
    """
    if template:
        jql = build_from_template(template)
    else:
        jql = build_jql(clauses or [], operator, order_by, order_desc)

    if not jql:
        return {'jql': '', 'valid': False, 'errors': ['No query built']}

    # Validate
    result = client.parse_jql([jql])
    parsed = result.get('queries', [{}])[0]
    errors = parsed.get('errors', [])

    return {
        'jql': jql,
        'valid': len(errors) == 0,
        'errors': errors
    }


def format_for_copy(jql: str) -> str:
    """
    Format JQL for easy copy/paste.

    Args:
        jql: JQL query string

    Returns:
        Clean JQL string
    """
    return jql.strip()


def list_templates() -> str:
    """
    List available templates.

    Returns:
        Formatted template list
    """
    lines = ["Available Templates:", ""]
    for name, jql in sorted(TEMPLATES.items()):
        lines.append(f"  {name}")
        lines.append(f"    {jql}")
        lines.append("")
    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Build JQL queries from components.',
        epilog='''
Examples:
  %(prog)s --clause "project = PROJ" --clause "status != Done"
  %(prog)s --clause "project = PROJ" --order-by created --desc
  %(prog)s --template my-bugs
  %(prog)s --template my-open --validate
  %(prog)s --list-templates
        '''
    )

    parser.add_argument('--clause', '-c', action='append', dest='clauses',
                        help='JQL clause (can be repeated)')
    parser.add_argument('--template', '-t',
                        help='Use predefined template')
    parser.add_argument('--operator', '-op', choices=['AND', 'OR'],
                        default='AND', help='Clause join operator')
    parser.add_argument('--order-by', '-o',
                        help='Field to order by')
    parser.add_argument('--desc', action='store_true',
                        help='Use descending order')
    parser.add_argument('--validate', '-v', action='store_true',
                        help='Validate the built query')
    parser.add_argument('--list-templates', '-l', action='store_true',
                        help='List available templates')
    parser.add_argument('--output', choices=['text', 'json'],
                        default='text', help='Output format')
    parser.add_argument('--profile', '-p',
                        help='JIRA profile to use')

    args = parser.parse_args()

    # List templates
    if args.list_templates:
        print(list_templates())
        return

    # Build query
    if args.template:
        try:
            jql = build_from_template(args.template)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.clauses:
        jql = build_jql(
            args.clauses,
            args.operator,
            args.order_by,
            args.desc
        )
    else:
        parser.error("Provide --clause or --template to build a query")

    # Validate if requested
    if args.validate:
        try:
            client = get_jira_client(args.profile)
            result = client.parse_jql([jql])
            parsed = result.get('queries', [{}])[0]
            errors = parsed.get('errors', [])

            if args.output == 'json':
                print(json.dumps({
                    'jql': jql,
                    'valid': len(errors) == 0,
                    'errors': errors
                }, indent=2))
            else:
                print(f"Built JQL Query:")
                print(f"{jql}")
                print()
                if errors:
                    print("Validation FAILED:")
                    for error in errors:
                        print(f"  - {error}")
                    sys.exit(1)
                else:
                    print("Query validated successfully")

        except JiraError as e:
            print_error(e)
            sys.exit(1)
    else:
        # Just output the query
        if args.output == 'json':
            print(json.dumps({'jql': jql}, indent=2))
        else:
            print(f"Built JQL Query:")
            print(f"{jql}")
            print()
            print("Use --validate to check syntax against JIRA")


if __name__ == '__main__':
    main()
