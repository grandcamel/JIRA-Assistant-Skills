#!/usr/bin/env python3
"""
Manage JQL query history and cache.

Stores query history locally for quick access and reuse.

Usage:
    python jql_history.py --list
    python jql_history.py --add "project = PROJ" --name "My Query"
    python jql_history.py --run 1
    python jql_history.py --run my-query
    python jql_history.py --delete 3
    python jql_history.py --clear
"""

import sys
import argparse
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, ValidationError
from jira_assistant_skills_lib import format_table, print_success, print_info
from jira_assistant_skills_lib import validate_jql

# Default history file location
HISTORY_DIR = Path.home() / '.jira-skills'
HISTORY_FILE = HISTORY_DIR / 'jql_history.json'


def ensure_history_dir():
    """Ensure history directory exists."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def load_history() -> Dict[str, Any]:
    """
    Load query history from file.

    Returns:
        History dict with queries list and metadata
    """
    if not HISTORY_FILE.exists():
        return {'queries': [], 'version': 1}

    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {'queries': [], 'version': 1}


def save_history(history: Dict[str, Any]) -> None:
    """
    Save query history to file.

    Args:
        history: History dict to save
    """
    ensure_history_dir()
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


def add_query(jql: str, name: str = None, description: str = None) -> Dict[str, Any]:
    """
    Add a query to history.

    Args:
        jql: JQL query string
        name: Optional name/alias for the query
        description: Optional description

    Returns:
        The added query entry
    """
    history = load_history()

    # Check for duplicate names
    if name:
        for q in history['queries']:
            if q.get('name') == name:
                raise ValidationError(f"Query with name '{name}' already exists. Use --delete first or choose a different name.")

    entry = {
        'id': len(history['queries']) + 1,
        'jql': jql,
        'name': name,
        'description': description,
        'created': datetime.now().isoformat(),
        'last_used': None,
        'use_count': 0
    }

    history['queries'].append(entry)
    save_history(history)

    return entry


def get_query(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Get a query by ID or name.

    Args:
        identifier: Query ID (number) or name (string)

    Returns:
        Query entry or None if not found
    """
    history = load_history()

    # Try as ID first
    try:
        query_id = int(identifier)
        for q in history['queries']:
            if q.get('id') == query_id:
                return q
    except ValueError:
        pass

    # Try as name
    for q in history['queries']:
        if q.get('name') == identifier:
            return q

    return None


def update_query_usage(query_id: int) -> None:
    """
    Update query usage statistics.

    Args:
        query_id: ID of query to update
    """
    history = load_history()

    for q in history['queries']:
        if q.get('id') == query_id:
            q['last_used'] = datetime.now().isoformat()
            q['use_count'] = q.get('use_count', 0) + 1
            break

    save_history(history)


def delete_query(identifier: str) -> bool:
    """
    Delete a query from history.

    Args:
        identifier: Query ID or name

    Returns:
        True if deleted, False if not found
    """
    history = load_history()
    original_count = len(history['queries'])

    # Filter out the query
    try:
        query_id = int(identifier)
        history['queries'] = [q for q in history['queries'] if q.get('id') != query_id]
    except ValueError:
        history['queries'] = [q for q in history['queries'] if q.get('name') != identifier]

    if len(history['queries']) < original_count:
        save_history(history)
        return True

    return False


def clear_history() -> int:
    """
    Clear all query history.

    Returns:
        Number of queries cleared
    """
    history = load_history()
    count = len(history['queries'])
    history['queries'] = []
    save_history(history)
    return count


def list_queries(top: int = None, sort_by: str = 'id') -> List[Dict[str, Any]]:
    """
    List queries from history.

    Args:
        top: Limit to top N queries
        sort_by: Sort field ('id', 'use_count', 'last_used', 'created')

    Returns:
        List of query entries
    """
    history = load_history()
    queries = history['queries']

    # Sort
    if sort_by == 'use_count':
        queries.sort(key=lambda x: x.get('use_count', 0), reverse=True)
    elif sort_by == 'last_used':
        queries.sort(key=lambda x: x.get('last_used') or '', reverse=True)
    elif sort_by == 'created':
        queries.sort(key=lambda x: x.get('created') or '', reverse=True)
    else:
        queries.sort(key=lambda x: x.get('id', 0))

    if top:
        queries = queries[:top]

    return queries


def export_history(output_path: str) -> int:
    """
    Export history to a file.

    Args:
        output_path: Path to export file

    Returns:
        Number of queries exported
    """
    history = load_history()
    with open(output_path, 'w') as f:
        json.dump(history, f, indent=2)
    return len(history['queries'])


def import_history(input_path: str, merge: bool = True) -> int:
    """
    Import history from a file.

    Args:
        input_path: Path to import file
        merge: If True, merge with existing; if False, replace

    Returns:
        Number of queries imported
    """
    with open(input_path, 'r') as f:
        imported = json.load(f)

    if not merge:
        save_history(imported)
        return len(imported.get('queries', []))

    # Merge with existing
    history = load_history()
    existing_names = {q.get('name') for q in history['queries'] if q.get('name')}
    max_id = max([q.get('id', 0) for q in history['queries']] + [0])

    imported_count = 0
    for q in imported.get('queries', []):
        # Skip if name already exists
        if q.get('name') and q.get('name') in existing_names:
            continue

        max_id += 1
        q['id'] = max_id
        history['queries'].append(q)
        imported_count += 1

    save_history(history)
    return imported_count


def format_query_list(queries: List[Dict[str, Any]]) -> str:
    """Format query list as a table."""
    if not queries:
        return "No queries in history."

    table_data = []
    for q in queries:
        table_data.append({
            'id': q.get('id', ''),
            'name': q.get('name') or '-',
            'jql': (q.get('jql', '')[:50] + '...') if len(q.get('jql', '')) > 50 else q.get('jql', ''),
            'uses': q.get('use_count', 0),
            'last_used': (q.get('last_used') or '')[:10]
        })

    return format_table(
        table_data,
        columns=['id', 'name', 'jql', 'uses', 'last_used'],
        headers=['ID', 'Name', 'JQL', 'Uses', 'Last Used']
    )


def main():
    parser = argparse.ArgumentParser(
        description='Manage JQL query history and cache',
        epilog='''
Examples:
  %(prog)s --list
  %(prog)s --add "project = PROJ" --name my-issues
  %(prog)s --run my-issues
  %(prog)s --run 5
  %(prog)s --top 10
  %(prog)s --delete 3
  %(prog)s --clear
  %(prog)s --export history.json
  %(prog)s --import history.json
        '''
    )

    # Action group
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--list', '-l',
                             action='store_true',
                             help='List saved queries')
    action_group.add_argument('--add', '-a',
                             metavar='JQL',
                             help='Add a new query to history')
    action_group.add_argument('--run', '-r',
                             metavar='ID_OR_NAME',
                             help='Run a query from history')
    action_group.add_argument('--delete', '-d',
                             metavar='ID_OR_NAME',
                             help='Delete a query from history')
    action_group.add_argument('--clear',
                             action='store_true',
                             help='Clear all query history')
    action_group.add_argument('--export',
                             metavar='FILE',
                             help='Export history to JSON file')
    action_group.add_argument('--import',
                             dest='import_file',
                             metavar='FILE',
                             help='Import history from JSON file')

    # Options for --add
    parser.add_argument('--name', '-n',
                       help='Name/alias for the query (with --add)')
    parser.add_argument('--description',
                       help='Description for the query (with --add)')

    # Options for --list
    parser.add_argument('--top', '-t',
                       type=int,
                       help='Show top N most used queries')
    parser.add_argument('--sort',
                       choices=['id', 'use_count', 'last_used', 'created'],
                       default='id',
                       help='Sort queries by field (default: id)')

    # Options for --run
    parser.add_argument('--max-results', '-m',
                       type=int,
                       default=50,
                       help='Maximum results when running query (default: 50)')

    # Options for --import
    parser.add_argument('--replace',
                       action='store_true',
                       help='Replace history instead of merging (with --import)')

    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format (default: text)')
    parser.add_argument('--profile',
                       help='JIRA profile to use (with --run)')

    args = parser.parse_args()

    try:
        if args.list:
            queries = list_queries(top=args.top, sort_by=args.sort)

            if args.output == 'json':
                print(json.dumps(queries, indent=2))
            else:
                print("JQL Query History")
                print("=" * 60)
                print()
                print(format_query_list(queries))
                print()
                print(f"History file: {HISTORY_FILE}")

        elif args.add:
            jql = validate_jql(args.add)
            entry = add_query(jql, name=args.name, description=args.description)

            if args.output == 'json':
                print(json.dumps(entry, indent=2))
            else:
                name_info = f" (name: {entry['name']})" if entry['name'] else ""
                print_success(f"Added query #{entry['id']}{name_info}")
                print(f"  JQL: {entry['jql']}")

        elif args.run:
            query = get_query(args.run)
            if not query:
                raise ValidationError(f"Query '{args.run}' not found in history")

            jql = query['jql']
            update_query_usage(query['id'])

            # Execute the query
            client = get_jira_client(args.profile)
            results = client.search_issues(
                jql,
                fields=['key', 'summary', 'status', 'priority', 'issuetype', 'assignee', 'reporter'],
                max_results=args.max_results
            )
            client.close()

            if args.output == 'json':
                print(json.dumps(results, indent=2))
            else:
                name_info = f" ({query['name']})" if query.get('name') else ""
                print_info(f"Running query #{query['id']}{name_info}")
                print(f"JQL: {jql}")
                print()

                issues = results.get('issues', [])
                total = results.get('total', 0)

                if issues:
                    table_data = []
                    for issue in issues:
                        fields = issue.get('fields', {})
                        table_data.append({
                            'key': issue.get('key', ''),
                            'type': fields.get('issuetype', {}).get('name', ''),
                            'status': fields.get('status', {}).get('name', ''),
                            'priority': fields.get('priority', {}).get('name', ''),
                            'summary': fields.get('summary', '')[:50]
                        })

                    print(format_table(
                        table_data,
                        columns=['key', 'type', 'status', 'priority', 'summary'],
                        headers=['Key', 'Type', 'Status', 'Priority', 'Summary']
                    ))
                    print()

                print(f"Found {total} issue(s)")

        elif args.delete:
            if delete_query(args.delete):
                print_success(f"Deleted query '{args.delete}'")
            else:
                raise ValidationError(f"Query '{args.delete}' not found")

        elif args.clear:
            count = clear_history()
            print_success(f"Cleared {count} query(ies) from history")

        elif args.export:
            count = export_history(args.export)
            print_success(f"Exported {count} query(ies) to {args.export}")

        elif args.import_file:
            count = import_history(args.import_file, merge=not args.replace)
            action = "Replaced with" if args.replace else "Imported"
            print_success(f"{action} {count} query(ies) from {args.import_file}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
