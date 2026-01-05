"""
Live Integration Tests: Link Lifecycle

Tests for complete link lifecycle (create, get, delete) against a real JIRA instance.
"""

import uuid

import pytest


@pytest.mark.integration
@pytest.mark.relationships
@pytest.mark.links
class TestLinkTypeDiscovery:
    """Tests for discovering available link types."""

    def test_get_all_link_types(self, jira_client):
        """Test fetching all available link types."""
        link_types = jira_client.get_link_types()

        assert isinstance(link_types, list)
        assert len(link_types) > 0

    def test_link_type_structure(self, jira_client):
        """Test that link types have required fields."""
        link_types = jira_client.get_link_types()

        for lt in link_types:
            assert "id" in lt
            assert "name" in lt
            assert "inward" in lt
            assert "outward" in lt

    def test_common_link_types_available(self, link_types):
        """Test that common link types exist."""
        type_names = [lt["name"].lower() for lt in link_types]

        # At least one of these should exist
        common_types = ["blocks", "duplicate", "relates", "cloners"]
        found = any(ct in " ".join(type_names) for ct in common_types)
        assert found, f"No common link types found. Available: {type_names}"


@pytest.mark.integration
@pytest.mark.relationships
@pytest.mark.links
class TestLinkCreation:
    """Tests for creating issue links."""

    def test_create_relates_link(self, jira_client, test_project):
        """Test creating a 'relates to' link between issues."""
        issue1 = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Relates Test 1 {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )
        issue2 = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Relates Test 2 {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )

        try:
            # Create relates link
            jira_client.create_link(
                link_type="Relates", inward_key=issue2["key"], outward_key=issue1["key"]
            )

            # Verify link exists on both sides
            links1 = jira_client.get_issue_links(issue1["key"])
            links2 = jira_client.get_issue_links(issue2["key"])

            assert len(links1) >= 1
            assert len(links2) >= 1

        finally:
            jira_client.delete_issue(issue1["key"])
            jira_client.delete_issue(issue2["key"])

    def test_create_blocks_link(self, jira_client, test_project):
        """Test creating a 'blocks' link between issues."""
        blocker = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Blocker Issue {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )
        blocked = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Blocked Issue {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )

        try:
            # Create blocks link: blocker blocks blocked
            jira_client.create_link(
                link_type="Blocks",
                inward_key=blocked["key"],  # is blocked by
                outward_key=blocker["key"],  # blocks
            )

            # Verify link exists
            links = jira_client.get_issue_links(blocker["key"])
            assert len(links) >= 1

            # Verify blocked issue is in links
            linked_keys = []
            for link in links:
                if "inwardIssue" in link:
                    linked_keys.append(link["inwardIssue"]["key"])
                if "outwardIssue" in link:
                    linked_keys.append(link["outwardIssue"]["key"])

            assert blocked["key"] in linked_keys

        finally:
            jira_client.delete_issue(blocker["key"])
            jira_client.delete_issue(blocked["key"])

    def test_create_duplicate_link(self, jira_client, test_project):
        """Test creating a 'duplicate' link between issues."""
        original = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Original Bug {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Bug"},
            }
        )
        duplicate = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Duplicate Bug {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Bug"},
            }
        )

        try:
            # Create duplicate link
            jira_client.create_link(
                link_type="Duplicate",
                inward_key=duplicate["key"],
                outward_key=original["key"],
            )

            # Verify link exists
            links = jira_client.get_issue_links(original["key"])
            assert len(links) >= 1

        finally:
            jira_client.delete_issue(original["key"])
            jira_client.delete_issue(duplicate["key"])

    def test_create_multiple_links(self, jira_client, test_project):
        """Test creating multiple links from one issue."""
        main_issue = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Main Issue {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )
        related_issues = []
        for i in range(3):
            issue = jira_client.create_issue(
                {
                    "project": {"key": test_project["key"]},
                    "summary": f"Related Issue {i + 1} {uuid.uuid4().hex[:8]}",
                    "issuetype": {"name": "Task"},
                }
            )
            related_issues.append(issue)
            jira_client.create_link("Relates", issue["key"], main_issue["key"])

        try:
            # Verify all links exist
            links = jira_client.get_issue_links(main_issue["key"])
            assert len(links) >= 3

        finally:
            jira_client.delete_issue(main_issue["key"])
            for issue in related_issues:
                jira_client.delete_issue(issue["key"])


@pytest.mark.integration
@pytest.mark.relationships
@pytest.mark.links
class TestLinkRetrieval:
    """Tests for retrieving issue links."""

    def test_get_issue_links(self, jira_client, linked_issues):
        """Test getting all links for an issue."""
        issue1, _issue2 = linked_issues

        links = jira_client.get_issue_links(issue1["key"])

        assert len(links) >= 1
        assert "type" in links[0]
        assert "id" in links[0]

    def test_get_link_by_id(self, jira_client, linked_issues):
        """Test getting a specific link by ID."""
        issue1, _issue2 = linked_issues

        # Get link ID from issue
        links = jira_client.get_issue_links(issue1["key"])
        link_id = links[0]["id"]

        # Get link by ID
        link = jira_client.get_link(link_id)

        assert link["id"] == link_id
        assert "type" in link

    def test_link_contains_issue_info(self, jira_client, linked_issues):
        """Test that links contain issue information."""
        issue1, _issue2 = linked_issues

        links = jira_client.get_issue_links(issue1["key"])

        # At least one direction should have issue info
        link = links[0]
        has_inward = "inwardIssue" in link
        has_outward = "outwardIssue" in link

        assert has_inward or has_outward

    def test_get_links_empty_issue(self, jira_client, test_issue):
        """Test getting links from issue with no links."""
        links = jira_client.get_issue_links(test_issue["key"])

        # New issue should have no links
        assert isinstance(links, list)
        assert len(links) == 0


@pytest.mark.integration
@pytest.mark.relationships
@pytest.mark.links
class TestLinkDeletion:
    """Tests for deleting issue links."""

    def test_delete_link(self, jira_client, test_project):
        """Test deleting an issue link."""
        # Create linked issues
        issue1 = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Delete Link Test 1 {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )
        issue2 = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Delete Link Test 2 {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )

        try:
            # Create link
            jira_client.create_link("Relates", issue2["key"], issue1["key"])

            # Get link ID
            links = jira_client.get_issue_links(issue1["key"])
            assert len(links) >= 1
            link_id = links[0]["id"]

            # Delete link
            jira_client.delete_link(link_id)

            # Verify link is gone
            links_after = jira_client.get_issue_links(issue1["key"])
            link_ids_after = [l["id"] for l in links_after]
            assert link_id not in link_ids_after

        finally:
            jira_client.delete_issue(issue1["key"])
            jira_client.delete_issue(issue2["key"])

    def test_delete_all_links_from_issue(self, jira_client, test_project):
        """Test deleting all links from an issue."""
        # Create main issue with multiple links
        main_issue = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Multi-link Issue {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )
        related = []
        for i in range(3):
            issue = jira_client.create_issue(
                {
                    "project": {"key": test_project["key"]},
                    "summary": f"Related {i + 1} {uuid.uuid4().hex[:8]}",
                    "issuetype": {"name": "Task"},
                }
            )
            related.append(issue)
            jira_client.create_link("Relates", issue["key"], main_issue["key"])

        try:
            # Verify links exist
            links = jira_client.get_issue_links(main_issue["key"])
            assert len(links) >= 3

            # Delete all links
            for link in links:
                jira_client.delete_link(link["id"])

            # Verify all gone
            links_after = jira_client.get_issue_links(main_issue["key"])
            assert len(links_after) == 0

        finally:
            jira_client.delete_issue(main_issue["key"])
            for issue in related:
                jira_client.delete_issue(issue["key"])

    def test_delete_link_affects_both_issues(self, jira_client, test_project):
        """Test that deleting a link removes it from both issues."""
        issue1 = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Bidirectional Test 1 {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )
        issue2 = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Bidirectional Test 2 {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )

        try:
            # Create link
            jira_client.create_link("Relates", issue2["key"], issue1["key"])

            # Verify link on both sides
            links1 = jira_client.get_issue_links(issue1["key"])
            links2 = jira_client.get_issue_links(issue2["key"])
            assert len(links1) >= 1
            assert len(links2) >= 1

            # Delete link from one side
            jira_client.delete_link(links1[0]["id"])

            # Verify gone from both sides
            links1_after = jira_client.get_issue_links(issue1["key"])
            links2_after = jira_client.get_issue_links(issue2["key"])
            assert len(links1_after) == 0
            assert len(links2_after) == 0

        finally:
            jira_client.delete_issue(issue1["key"])
            jira_client.delete_issue(issue2["key"])


@pytest.mark.integration
@pytest.mark.relationships
@pytest.mark.links
class TestLinkDirectionality:
    """Tests for link direction handling."""

    def test_blocks_link_direction(self, jira_client, test_project):
        """Test that blocks link shows correct direction."""
        blocker = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Blocker {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )
        blocked = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Blocked {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )

        try:
            # Create blocks link
            jira_client.create_link("Blocks", blocked["key"], blocker["key"])

            # Check from blocker's perspective
            blocker_links = jira_client.get_issue_links(blocker["key"])
            assert len(blocker_links) >= 1

            # Should have inward link (blocked issue)
            blocker_link = blocker_links[0]
            assert blocker_link["type"]["name"] == "Blocks"

            # Check from blocked's perspective
            blocked_links = jira_client.get_issue_links(blocked["key"])
            assert len(blocked_links) >= 1

        finally:
            jira_client.delete_issue(blocker["key"])
            jira_client.delete_issue(blocked["key"])

    def test_relates_link_is_symmetric(self, jira_client, linked_issues):
        """Test that relates link appears symmetrically on both issues."""
        issue1, issue2 = linked_issues

        links1 = jira_client.get_issue_links(issue1["key"])
        links2 = jira_client.get_issue_links(issue2["key"])

        # Both should have exactly one link
        assert len(links1) == 1
        assert len(links2) == 1

        # Both should be the same link type
        assert links1[0]["type"]["name"] == links2[0]["type"]["name"]
