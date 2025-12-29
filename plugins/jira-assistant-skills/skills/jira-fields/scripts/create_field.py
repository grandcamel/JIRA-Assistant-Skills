#!/usr/bin/env python3
"""
Create a custom field in JIRA.

Requires JIRA Administrator permissions.

Usage:
    python create_field.py --name "Story Points" --type number
    python create_field.py --name "Epic Link" --type select
    python create_field.py --name "Effort" --type number --description "Effort in hours"
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, ValidationError
from jira_assistant_skills_lib import format_json, print_success

# Field type mappings sourced from assets/field-types-reference.json
# See that file for complete documentation, examples, and use cases
def _load_field_types() -> Dict[str, Dict[str, str]]:
    """Load field types from JSON reference file with fallback to hardcoded values."""
    ref_file = Path(__file__).parent.parent / 'assets' / 'field-types-reference.json'
    try:
        with open(ref_file) as f:
            data = json.load(f)
            # Extract only type and searcher for API calls
            return {
                key: {'type': val['type'], 'searcher': val['searcher']}
                for key, val in data['field_types'].items()
            }
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        # Fallback to hardcoded values if reference file unavailable
        return {
            'text': {
                'type': 'com.atlassian.jira.plugin.system.customfieldtypes:textfield',
                'searcher': 'com.atlassian.jira.plugin.system.customfieldtypes:textsearcher'
            },
            'textarea': {
                'type': 'com.atlassian.jira.plugin.system.customfieldtypes:textarea',
                'searcher': 'com.atlassian.jira.plugin.system.customfieldtypes:textsearcher'
            },
            'number': {
                'type': 'com.atlassian.jira.plugin.system.customfieldtypes:float',
                'searcher': 'com.atlassian.jira.plugin.system.customfieldtypes:exactnumber'
            },
            'date': {
                'type': 'com.atlassian.jira.plugin.system.customfieldtypes:datepicker',
                'searcher': 'com.atlassian.jira.plugin.system.customfieldtypes:daterange'
            },
            'datetime': {
                'type': 'com.atlassian.jira.plugin.system.customfieldtypes:datetime',
                'searcher': 'com.atlassian.jira.plugin.system.customfieldtypes:datetimerange'
            },
            'select': {
                'type': 'com.atlassian.jira.plugin.system.customfieldtypes:select',
                'searcher': 'com.atlassian.jira.plugin.system.customfieldtypes:multiselectsearcher'
            },
            'multiselect': {
                'type': 'com.atlassian.jira.plugin.system.customfieldtypes:multiselect',
                'searcher': 'com.atlassian.jira.plugin.system.customfieldtypes:multiselectsearcher'
            },
            'checkbox': {
                'type': 'com.atlassian.jira.plugin.system.customfieldtypes:multicheckboxes',
                'searcher': 'com.atlassian.jira.plugin.system.customfieldtypes:multiselectsearcher'
            },
            'radio': {
                'type': 'com.atlassian.jira.plugin.system.customfieldtypes:radiobuttons',
                'searcher': 'com.atlassian.jira.plugin.system.customfieldtypes:multiselectsearcher'
            },
            'url': {
                'type': 'com.atlassian.jira.plugin.system.customfieldtypes:url',
                'searcher': 'com.atlassian.jira.plugin.system.customfieldtypes:exacttextsearcher'
            },
            'user': {
                'type': 'com.atlassian.jira.plugin.system.customfieldtypes:userpicker',
                'searcher': 'com.atlassian.jira.plugin.system.customfieldtypes:userpickergroupsearcher'
            },
            'labels': {
                'type': 'com.atlassian.jira.plugin.system.customfieldtypes:labels',
                'searcher': 'com.atlassian.jira.plugin.system.customfieldtypes:labelsearcher'
            }
        }

FIELD_TYPES = _load_field_types()


def create_field(name: str,
                 field_type: str,
                 description: str = None,
                 profile: str = None,
                 client=None) -> Dict[str, Any]:
    """
    Create a custom field.

    Args:
        name: Field name
        field_type: Field type (text, number, select, etc.)
        description: Optional field description
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Created field data

    Raises:
        ValidationError: If field type is invalid
        JiraError: If API call fails
    """
    if field_type not in FIELD_TYPES:
        raise ValidationError(
            f"Invalid field type: {field_type}. "
            f"Valid types: {', '.join(FIELD_TYPES.keys())}"
        )

    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        type_config = FIELD_TYPES[field_type]

        data = {
            'name': name,
            'type': type_config['type'],
            'searcherKey': type_config['searcher']
        }

        if description:
            data['description'] = description

        result = client.post('/rest/api/3/field', data=data)
        return result

    finally:
        if should_close:
            client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Create a custom field in JIRA',
        epilog='Example: python create_field.py --name "Story Points" --type number'
    )

    parser.add_argument('--name', '-n', required=True,
                        help='Field name')
    parser.add_argument('--type', '-t', required=True,
                        choices=list(FIELD_TYPES.keys()),
                        help='Field type')
    parser.add_argument('--description', '-d',
                        help='Field description')
    parser.add_argument('--profile',
                        help='JIRA profile to use')
    parser.add_argument('--output', '-o',
                        choices=['text', 'json'],
                        default='text',
                        help='Output format')

    args = parser.parse_args()

    try:
        result = create_field(
            name=args.name,
            field_type=args.type,
            description=args.description,
            profile=args.profile
        )

        if args.output == 'json':
            print(format_json(result))
        else:
            print_success(f"Created field: {result.get('name')}")
            print(f"Field ID: {result.get('id')}")
            print(f"Type: {result.get('schema', {}).get('type', 'unknown')}")

    except ValidationError as e:
        print_error(e)
        sys.exit(1)
    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
