#!/usr/bin/env python3
"""
Update an existing asset/CMDB object.

Updates asset attributes.
Requires JSM Premium license or Assets license.

Usage:
    update_asset.py --id 10001 --attr "Status=Inactive"
    update_asset.py --id 10001 --attr "Status=Inactive" --attr "Location=DC-2" --dry-run
"""

import argparse
import json
import sys
from pathlib import Path

# Add shared lib to path
shared_lib_path = str(
    Path(__file__).parent.parent.parent.parent / "shared" / "scripts" / "lib"
)
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)

from jira_assistant_skills_lib import get_jira_client


def update_asset(asset_id: int, attributes: dict, dry_run: bool = False):
    """
    Update an existing asset.

    Args:
        asset_id: Asset object ID
        attributes: Dict mapping attribute names to new values
        dry_run: If True, don't actually update

    Returns:
        Updated asset object (or None if dry_run)
    """
    with get_jira_client() as client:
        # Check license first
        if not client.has_assets_license():
            print(
                "ERROR: Assets/Insight not available. Requires JSM Premium license.",
                file=sys.stderr,
            )
            sys.exit(1)

        if dry_run:
            print("DRY RUN: Would update asset with:")
            print(f"  Asset ID: {asset_id}")
            print(f"  Attributes: {json.dumps(attributes, indent=4)}")
            return None

        return client.update_asset(asset_id, attributes)


def parse_attributes(attr_list: list) -> dict:
    """Parse attribute list into dict."""
    attributes = {}
    for attr_str in attr_list:
        if "=" not in attr_str:
            raise ValueError(
                f"Invalid attribute format: {attr_str}. Expected: name=value"
            )
        name, value = attr_str.split("=", 1)
        attributes[name.strip()] = value.strip()
    return attributes


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Update existing asset/CMDB object",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--id", type=int, required=True, help="Asset object ID")
    parser.add_argument(
        "--attr",
        action="append",
        required=True,
        help="Attribute in format name=value (can be used multiple times)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without updating"
    )

    args = parser.parse_args(argv)

    try:
        attributes = parse_attributes(args.attr)
        asset = update_asset(args.id, attributes, args.dry_run)

        if not args.dry_run:
            print("✓ Asset updated successfully!")
            print(f"Asset ID: {asset.get('id')}")
            print(f"Asset Key: {asset.get('objectKey')}")

    except SystemExit:
        raise
    except Exception as e:
        print(f"Error updating asset: {e!s}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
