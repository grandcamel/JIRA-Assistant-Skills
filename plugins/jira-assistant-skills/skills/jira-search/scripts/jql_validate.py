#!/usr/bin/env python3
"""
Validate JQL query syntax.

Parses and validates JQL queries, showing specific errors
and suggesting corrections for common mistakes.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from difflib import get_close_matches

# Add shared library to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, print_error


# Common field names for suggestions
COMMON_FIELDS = [
    'project', 'status', 'type', 'issuetype', 'priority', 'assignee',
    'reporter', 'creator', 'created', 'updated', 'resolved', 'duedate',
    'summary', 'description', 'labels', 'component', 'components',
    'fixVersion', 'affectedVersion', 'sprint', 'epic', 'parent',
    'resolution', 'watchers', 'voter', 'comment', 'key', 'id'
]


def suggest_correction(invalid_field: str, known_fields: List[str] = None) -> Optional[str]:
    """
    Suggest a correction for an invalid field name.

    Args:
        invalid_field: The invalid field name
        known_fields: List of valid field names

    Returns:
        Suggested correction or None
    """
    if known_fields is None:
        known_fields = COMMON_FIELDS

    matches = get_close_matches(invalid_field.lower(),
                                [f.lower() for f in known_fields],
                                n=1, cutoff=0.6)
    if matches:
        # Find original case version
        for field in known_fields:
            if field.lower() == matches[0]:
                return field
    return None


def validate_jql(client, query: str) -> Dict[str, Any]:
    """
    Validate a single JQL query.

    Args:
        client: JIRA client
        query: JQL query string

    Returns:
        Validation result with valid, errors, and structure
    """
    result = client.parse_jql([query])
    parsed = result.get('queries', [{}])[0]

    errors = parsed.get('errors', [])
    structure = parsed.get('structure')

    return {
        'valid': len(errors) == 0,
        'query': query,
        'errors': errors,
        'structure': structure
    }


def validate_multiple(client, queries: List[str]) -> List[Dict[str, Any]]:
    """
    Validate multiple JQL queries at once.

    Args:
        client: JIRA client
        queries: List of JQL query strings

    Returns:
        List of validation results
    """
    result = client.parse_jql(queries)

    results = []
    for i, parsed in enumerate(result.get('queries', [])):
        query = queries[i] if i < len(queries) else parsed.get('query', '')
        errors = parsed.get('errors', [])
        structure = parsed.get('structure')

        results.append({
            'valid': len(errors) == 0,
            'query': query,
            'errors': errors,
            'structure': structure
        })

    return results


def format_structure(structure: Dict[str, Any], indent: int = 2) -> str:
    """
    Format parsed query structure for display.

    Args:
        structure: Parsed structure from API
        indent: Indentation level

    Returns:
        Formatted structure string
    """
    if not structure:
        return "  (no structure available)"

    lines = []
    prefix = " " * indent

    # Handle WHERE clause
    where = structure.get('where', {})
    if where:
        clauses = where.get('clauses', [])
        for clause in clauses:
            field = clause.get('field', {}).get('name', '?')
            operator = clause.get('operator', '?')
            operand = clause.get('operand', {})

            if isinstance(operand, dict):
                value = operand.get('value', operand.get('values', '?'))
            else:
                value = operand

            lines.append(f"{prefix}{field} {operator} {value}")

    # Handle ORDER BY
    order_by = structure.get('orderBy', {})
    if order_by:
        fields = order_by.get('fields', [])
        for field in fields:
            name = field.get('field', {}).get('name', '?')
            direction = field.get('direction', 'asc')
            lines.append(f"{prefix}ORDER BY {name} {direction}")

    return "\n".join(lines) if lines else "  (empty structure)"


def format_validation_result(result: Dict[str, Any],
                             show_structure: bool = False) -> str:
    """
    Format a validation result for display.

    Args:
        result: Validation result
        show_structure: Show parsed structure

    Returns:
        Formatted string
    """
    lines = []
    query = result.get('query', '')
    lines.append(f"JQL Query: {query}")
    lines.append("")

    if result['valid']:
        lines.append("Valid JQL")

        if show_structure and result.get('structure'):
            lines.append("")
            lines.append("Structure:")
            lines.append(format_structure(result['structure']))

            # Extract field names
            where = result.get('structure', {}).get('where', {})
            clauses = where.get('clauses', [])
            fields = [c.get('field', {}).get('name', '') for c in clauses]
            fields = [f for f in fields if f]
            if fields:
                lines.append("")
                lines.append(f"Fields used: {', '.join(fields)}")
    else:
        lines.append("Invalid JQL")
        lines.append("")
        lines.append("Errors:")
        for i, error in enumerate(result['errors'], 1):
            lines.append(f"  {i}. {error}")

            # Try to suggest corrections for field errors
            if "does not exist" in error.lower() and "'" in error:
                # Extract field name from error
                import re
                match = re.search(r"'(\w+)'", error)
                if match:
                    invalid_field = match.group(1)
                    suggestion = suggest_correction(invalid_field)
                    if suggestion:
                        lines.append(f"     -> Did you mean '{suggestion}'?")

    return "\n".join(lines)


def format_results_json(results: List[Dict[str, Any]]) -> str:
    """
    Format results as JSON.

    Args:
        results: List of validation results

    Returns:
        JSON string
    """
    return json.dumps(results, indent=2)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate JQL query syntax.',
        epilog='''
Examples:
  %(prog)s "project = PROJ AND status = Open"
  %(prog)s "project = PROJ" "type = Bug" --batch
  %(prog)s "project = PROJ" --show-structure
  %(prog)s --file queries.txt
  %(prog)s "project = PROJ" --output json
        '''
    )

    parser.add_argument('queries', nargs='*',
                        help='JQL query or queries to validate')
    parser.add_argument('--batch', action='store_true',
                        help='Validate multiple queries')
    parser.add_argument('--file', '-f',
                        help='Read queries from file (one per line)')
    parser.add_argument('--show-structure', '-s', action='store_true',
                        help='Show parsed query structure')
    parser.add_argument('--output', '-o', choices=['text', 'json'],
                        default='text', help='Output format (default: text)')
    parser.add_argument('--profile', '-p',
                        help='JIRA profile to use')

    args = parser.parse_args()

    # Collect queries
    queries = list(args.queries) if args.queries else []

    if args.file:
        with open(args.file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    queries.append(line)

    if not queries:
        parser.error("No queries provided. Provide queries as arguments or use --file")

    try:
        client = get_jira_client(args.profile)

        if len(queries) == 1 and not args.batch:
            # Single query
            result = validate_jql(client, queries[0])

            if args.output == 'json':
                print(format_results_json([result]))
            else:
                print(format_validation_result(result,
                                               show_structure=args.show_structure))

            # Exit with error code if invalid
            sys.exit(0 if result['valid'] else 1)
        else:
            # Multiple queries
            results = validate_multiple(client, queries)

            if args.output == 'json':
                print(format_results_json(results))
            else:
                for i, result in enumerate(results):
                    if i > 0:
                        print("\n" + "-" * 50 + "\n")
                    print(format_validation_result(result,
                                                   show_structure=args.show_structure))

            # Exit with error code if any invalid
            all_valid = all(r['valid'] for r in results)
            sys.exit(0 if all_valid else 1)

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
