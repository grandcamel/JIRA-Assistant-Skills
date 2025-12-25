#!/usr/bin/env python3
"""
Create a JSM service request.

Usage:
    python create_request.py --service-desk 1 --request-type 10 --summary "Email not working" --description "Cannot send emails"
    python create_request.py --service-desk "IT Support" --request-type "Incident" --summary "Server down"
    python create_request.py --service-desk 1 --request-type 10 --summary "Test" --field priority=High --dry-run
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError, NotFoundError
from formatters import print_success


def create_service_request(service_desk_id: str, request_type_id: str,
                           summary: str, description: str,
                           custom_fields: Optional[Dict[str, Any]] = None,
                           participants: Optional[List[str]] = None,
                           on_behalf_of: Optional[str] = None,
                           profile: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a service request.

    Args:
        service_desk_id: Service desk ID or key
        request_type_id: Request type ID
        summary: Request summary
        description: Request description
        custom_fields: Additional custom fields
        participants: List of participant email addresses
        on_behalf_of: Create on behalf of user email
        profile: JIRA profile to use

    Returns:
        Created request data

    Raises:
        ValueError: If required fields are missing
        NotFoundError: If service desk or request type not found
    """
    if not summary or not summary.strip():
        raise ValueError("summary is required")

    if not description or not description.strip():
        raise ValueError("description is required")

    # Build request field values
    fields = {
        'summary': summary,
        'description': description
    }

    # Add custom fields
    if custom_fields:
        fields.update(custom_fields)

    with get_jira_client(profile) as client:
        return client.create_request(
            service_desk_id=service_desk_id,
            request_type_id=request_type_id,
            fields=fields,
            participants=participants,
            on_behalf_of=on_behalf_of
        )


def parse_custom_fields(field_args: List[str]) -> Dict[str, Any]:
    """
    Parse custom field arguments from command line.

    Args:
        field_args: List of field=value strings

    Returns:
        Dictionary of field values
    """
    fields = {}
    for arg in field_args:
        if '=' not in arg:
            raise ValueError(f"Invalid field format: {arg}. Use field=value")

        key, value = arg.split('=', 1)
        fields[key.strip()] = value.strip()

    return fields


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create a JSM service request',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Basic usage:
    %(prog)s --service-desk 1 --request-type 10 --summary "Email not working" --description "Cannot send emails"

  With custom fields:
    %(prog)s --service-desk 1 --request-type 10 --summary "Server down" --description "Production server not responding" --field priority=High --field impact="Multiple Users"

  With participants:
    %(prog)s --service-desk 1 --request-type 10 --summary "Team access" --description "Need access for team" --participants "alice@example.com,bob@example.com"

  On behalf of customer:
    %(prog)s --service-desk 1 --request-type 10 --summary "Password reset" --description "User needs reset" --on-behalf-of "customer@example.com"

  Dry-run:
    %(prog)s --service-desk 1 --request-type 10 --summary "Test" --description "Test" --dry-run
        """
    )

    parser.add_argument('--service-desk', required=True,
                        help='Service desk ID or key')
    parser.add_argument('--request-type', required=True,
                        help='Request type ID')
    parser.add_argument('--summary', required=True,
                        help='Request summary')
    parser.add_argument('--description', required=True,
                        help='Request description')
    parser.add_argument('--field', action='append', default=[],
                        help='Custom field (format: field=value)')
    parser.add_argument('--participants',
                        help='Comma-separated list of participant emails')
    parser.add_argument('--on-behalf-of',
                        help='Create request on behalf of user email')
    parser.add_argument('--output', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be created without creating')
    parser.add_argument('--profile',
                        help='JIRA profile to use from config')

    args = parser.parse_args()

    try:
        # Parse custom fields
        custom_fields = parse_custom_fields(args.field) if args.field else None

        # Parse participants
        participants = None
        if args.participants:
            participants = [p.strip() for p in args.participants.split(',')]

        if args.dry_run:
            print("DRY RUN MODE - No changes will be made\n")
            print("Would create request:")
            print(f"  Service Desk: {args.service_desk}")
            print(f"  Request Type: {args.request_type}")
            print(f"  Summary: {args.summary}")
            print(f"  Description: {args.description}")
            if custom_fields:
                print(f"  Custom Fields: {json.dumps(custom_fields, indent=2)}")
            if participants:
                print(f"  Participants: {', '.join(participants)}")
            if args.on_behalf_of:
                print(f"  On Behalf Of: {args.on_behalf_of}")
            return 0

        request = create_service_request(
            service_desk_id=args.service_desk,
            request_type_id=args.request_type,
            summary=args.summary,
            description=args.description,
            custom_fields=custom_fields,
            participants=participants,
            on_behalf_of=args.on_behalf_of,
            profile=args.profile
        )

        if args.output == 'json':
            print(json.dumps(request, indent=2))
        else:
            print_success("Service request created successfully!\n")
            print(f"Request Key: {request.get('issueKey')}")

            req_type = request.get('requestType', {})
            print(f"Request Type: {req_type.get('name', 'N/A')}")

            status = request.get('currentStatus', {})
            print(f"Status: {status.get('status', 'N/A')}")

            print(f"\nSummary: {args.summary}")
            print(f"Description: {args.description}")

            reporter = request.get('reporter', {})
            print(f"\nReporter: {reporter.get('emailAddress', 'N/A')}")

            created = request.get('createdDate', {})
            print(f"Created: {created.get('friendly', 'N/A')}")

            links = request.get('_links', {})
            if 'web' in links:
                print(f"\nCustomer Portal: {links['web']}")
            if 'agent' in links:
                print(f"Agent View: {links['agent']}")

        return 0

    except ValueError as e:
        print_error(str(e))
        return 1
    except (JiraError, NotFoundError) as e:
        print_error(f"Failed to create request: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
