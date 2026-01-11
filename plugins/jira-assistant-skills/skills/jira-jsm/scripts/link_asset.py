#!/usr/bin/env python3
"""
Link an asset to a service request.

Creates a link between an asset/CMDB object and a service request.
Requires JSM Premium license or Assets license.

Usage:
    link_asset.py --request REQ-123 --asset-id 10001
    link_asset.py --request REQ-123 --asset-id 10001 --comment "Primary server affected"
"""

import argparse
import sys
from pathlib import Path

# Add shared lib to path
shared_lib_path = str(
    Path(__file__).parent.parent.parent.parent / "shared" / "scripts" / "lib"
)
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)


from jira_assistant_skills_lib import get_jira_client


def link_asset(asset_id: int, issue_key: str, comment: str | None = None):
    """
    Link an asset to a service request.

    Args:
        asset_id: Asset object ID
        issue_key: Request issue key
        comment: Optional comment about the link

    Returns:
        None
    """
    with get_jira_client() as client:
        # Check license first
        if not client.has_assets_license():
            print(
                "ERROR: Assets/Insight not available. Requires JSM Premium license.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Link asset to request (adds internal comment)
        client.link_asset_to_request(asset_id, issue_key)

        # Add additional comment if provided
        if comment:
            client.add_request_comment(issue_key, comment, public=False)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Link asset to service request",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--request", required=True, help="Request issue key (e.g., REQ-123)"
    )
    parser.add_argument("--asset-id", type=int, required=True, help="Asset object ID")
    parser.add_argument("--comment", help="Optional comment about the link")

    args = parser.parse_args(argv)

    try:
        link_asset(args.asset_id, args.request, args.comment)

        print(f"✓ Asset {args.asset_id} linked to {args.request} successfully!")

    except SystemExit:
        raise
    except Exception as e:
        print(f"Error linking asset: {e!s}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
