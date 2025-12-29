#!/usr/bin/env python3
"""
Update a project component in JIRA.

Usage:
    python update_component.py --id 10000 --name "New Name"
    python update_component.py --id 10000 --description "Updated description"
    python update_component.py --id 10000 --lead 5b10a2844c20165700ede22h
    python update_component.py --id 10000 --assignee-type PROJECT_LEAD
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import print_success


def update_component(component_id: str, name: str = None, description: str = None,
                    lead_account_id: str = None, assignee_type: str = None,
                    profile: str = None) -> Dict[str, Any]:
    """
    Update a component.

    Args:
        component_id: Component ID
        name: Optional new name
        description: Optional new description
        lead_account_id: Optional new lead account ID
        assignee_type: Optional new assignee type
        profile: JIRA profile to use

    Returns:
        Updated component data
    """
    update_data = {}

    if name:
        update_data['name'] = name
    if description:
        update_data['description'] = description
    if lead_account_id:
        update_data['leadAccountId'] = lead_account_id
    if assignee_type:
        update_data['assigneeType'] = assignee_type

    client = get_jira_client(profile)
    result = client.update_component(component_id, **update_data)
    client.close()

    return result


def update_component_dry_run(component_id: str, name: str = None, description: str = None,
                             lead_account_id: str = None, assignee_type: str = None) -> Dict[str, Any]:
    """
    Show what would be updated without updating.

    Args:
        component_id: Component ID
        name: Optional new name
        description: Optional new description
        lead_account_id: Optional new lead account ID
        assignee_type: Optional new assignee type

    Returns:
        Update data that would be applied
    """
    update_data = {
        'component_id': component_id
    }

    if name:
        update_data['name'] = name
    if description:
        update_data['description'] = description
    if lead_account_id:
        update_data['leadAccountId'] = lead_account_id
    if assignee_type:
        update_data['assigneeType'] = assignee_type

    return update_data


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Update a project component in JIRA',
        epilog='''
Examples:
  %(prog)s --id 10000 --name "New Name"
  %(prog)s --id 10000 --description "Updated description"
  %(prog)s --id 10000 --lead 5b10a2844c20165700ede22h
  %(prog)s --id 10000 --assignee-type PROJECT_LEAD --dry-run
        '''
    )

    parser.add_argument('--id',
                       required=True,
                       help='Component ID to update')
    parser.add_argument('--name', '-n',
                       help='New component name')
    parser.add_argument('--description', '-d',
                       help='New component description')
    parser.add_argument('--lead', '-l',
                       help='New component lead account ID')
    parser.add_argument('--assignee-type', '-a',
                       choices=['COMPONENT_LEAD', 'PROJECT_LEAD', 'PROJECT_DEFAULT', 'UNASSIGNED'],
                       help='New default assignee type')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be updated without updating')
    parser.add_argument('--profile', '-p',
                       help='JIRA profile to use')

    args = parser.parse_args()

    # Check that at least one field to update is specified
    if not any([args.name, args.description, args.lead, args.assignee_type]):
        print_error("Error: Must specify at least one field to update (--name, --description, --lead, --assignee-type)")
        sys.exit(1)

    try:
        if args.dry_run:
            # Dry run mode
            update_data = update_component_dry_run(
                component_id=args.id,
                name=args.name,
                description=args.description,
                lead_account_id=args.lead,
                assignee_type=args.assignee_type
            )

            print(f"[DRY RUN] Would update component {args.id}:\n")
            if update_data.get('name'):
                print(f"  Name: {update_data['name']}")
            if update_data.get('description'):
                print(f"  Description: {update_data['description']}")
            if update_data.get('leadAccountId'):
                print(f"  Lead Account ID: {update_data['leadAccountId']}")
            if update_data.get('assigneeType'):
                print(f"  Assignee Type: {update_data['assigneeType']}")
            print("\nNo component updated (dry-run mode).")

        else:
            # Update component
            component = update_component(
                component_id=args.id,
                name=args.name,
                description=args.description,
                lead_account_id=args.lead,
                assignee_type=args.assignee_type,
                profile=args.profile
            )

            component_name = component.get('name', args.id)
            print_success(f"Updated component '{component_name}' (ID: {component['id']})")

            # Show updated fields
            print("\nUpdated fields:")
            if args.name:
                print(f"  Name: {component['name']}")
            if args.description:
                print(f"  Description: {component.get('description', '')}")
            if args.lead:
                lead_name = component.get('lead', {}).get('displayName', '')
                print(f"  Lead: {lead_name}")
            if args.assignee_type:
                print(f"  Assignee Type: {component['assigneeType']}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
