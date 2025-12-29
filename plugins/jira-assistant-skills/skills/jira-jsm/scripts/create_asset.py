#!/usr/bin/env python3
"""
Create a new asset/CMDB object.

Creates new asset with specified attributes.
Requires JSM Premium license or Assets license.

Usage:
    create_asset.py --type-id 5 --attr "IP Address=192.168.1.105" --attr "Status=Active"
    create_asset.py --type-id 5 --attr "IP Address=192.168.1.105" --attr "Status=Active" --dry-run
"""

import argparse
import sys
import json
from pathlib import Path

# Add shared lib to path
shared_lib_path = str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib')
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)

from jira_assistant_skills_lib import get_jira_client


def create_asset(object_type_id: int, attributes: dict, dry_run: bool = False):
    """
    Create a new asset.

    Args:
        object_type_id: Object type ID
        attributes: Dict mapping attribute names to values
        dry_run: If True, don't actually create

    Returns:
        Created asset object (or None if dry_run)
    """
    with get_jira_client() as client:
        # Check license first
        if not client.has_assets_license():
            print("ERROR: Assets/Insight not available. Requires JSM Premium license.", file=sys.stderr)
            sys.exit(1)

        if dry_run:
            print("DRY RUN: Would create asset with:")
            print(f"  Object Type ID: {object_type_id}")
            print(f"  Attributes: {json.dumps(attributes, indent=4)}")
            return None

        return client.create_asset(object_type_id, attributes)


def parse_attributes(attr_list: list) -> dict:
    """Parse attribute list into dict."""
    attributes = {}
    for attr_str in attr_list:
        if '=' not in attr_str:
            raise ValueError(f"Invalid attribute format: {attr_str}. Expected: name=value")
        name, value = attr_str.split('=', 1)
        attributes[name.strip()] = value.strip()
    return attributes


def main():
    parser = argparse.ArgumentParser(
        description="Create new asset/CMDB object",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--type-id', type=int, required=True,
                       help='Object type ID')
    parser.add_argument('--attr', action='append', required=True,
                       help='Attribute in format name=value (can be used multiple times)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without creating')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args()

    try:
        # Validate object_type_id is positive
        if args.type_id <= 0:
            print(f"Error: --type-id must be a positive integer, got {args.type_id}", file=sys.stderr)
            sys.exit(1)

        attributes = parse_attributes(args.attr)
        asset = create_asset(args.type_id, attributes, args.dry_run)

        if not args.dry_run:
            print(f"✓ Asset created successfully!")
            print(f"Asset ID: {asset.get('id')}")
            print(f"Asset Key: {asset.get('objectKey')}")

    except SystemExit:
        raise
    except Exception as e:
        print(f"Error creating asset: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
