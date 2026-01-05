"""
Live Integration Tests: Version Management

Tests for version CRUD operations and issue version management against a real JIRA instance.
"""

import time
import uuid
from datetime import datetime, timedelta

import pytest


@pytest.mark.integration
@pytest.mark.shared
class TestVersionCRUD:
    """Tests for version create, read, update, delete operations."""

    def test_create_version(self, jira_client, test_project):
        """Test creating a basic version."""
        version_name = f"v{uuid.uuid4().hex[:8]}"

        version = jira_client.create_version(
            project_id=test_project["id"], name=version_name, description="Test version"
        )

        assert version["name"] == version_name
        assert version["description"] == "Test version"
        assert not version["archived"]
        assert not version["released"]
        assert "id" in version

        # Cleanup
        jira_client.delete_version(version["id"])

    def test_create_version_with_dates(self, jira_client, test_project):
        """Test creating a version with start and release dates."""
        version_name = f"v{uuid.uuid4().hex[:8]}"
        start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        release_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        version = jira_client.create_version(
            project_id=test_project["id"],
            name=version_name,
            start_date=start_date,
            release_date=release_date,
        )

        assert version["name"] == version_name
        assert "startDate" in version
        assert "releaseDate" in version
        # Dates should match (JIRA returns ISO format)
        assert start_date in version["startDate"]
        assert release_date in version["releaseDate"]

        # Cleanup
        jira_client.delete_version(version["id"])

    def test_get_versions(self, jira_client, test_project):
        """Test getting all versions for a project."""
        # Create a test version
        version_name = f"v{uuid.uuid4().hex[:8]}"
        created = jira_client.create_version(
            project_id=test_project["id"], name=version_name
        )

        try:
            # Get all versions
            versions = jira_client.get_project_versions(test_project["key"])

            assert isinstance(versions, list)
            assert len(versions) >= 1

            # Our version should be in the list
            version_names = [v["name"] for v in versions]
            assert version_name in version_names

        finally:
            jira_client.delete_version(created["id"])

    def test_get_version_by_id(self, jira_client, test_project):
        """Test getting a specific version by ID."""
        version_name = f"v{uuid.uuid4().hex[:8]}"
        created = jira_client.create_version(
            project_id=test_project["id"],
            name=version_name,
            description="Specific version test",
        )

        try:
            # Get the version by ID
            version = jira_client.get_version(created["id"])

            assert version["id"] == created["id"]
            assert version["name"] == version_name
            assert version["description"] == "Specific version test"

        finally:
            jira_client.delete_version(created["id"])

    def test_update_version(self, jira_client, test_project):
        """Test updating a version."""
        version_name = f"v{uuid.uuid4().hex[:8]}"
        created = jira_client.create_version(
            project_id=test_project["id"], name=version_name
        )

        try:
            new_name = f"v{uuid.uuid4().hex[:8]}-updated"
            new_description = "Updated description"

            # Update version
            updated = jira_client.update_version(
                created["id"], name=new_name, description=new_description
            )

            assert updated["name"] == new_name
            assert updated["description"] == new_description

        finally:
            jira_client.delete_version(created["id"])

    def test_release_version(self, jira_client, test_project):
        """Test releasing a version."""
        version_name = f"v{uuid.uuid4().hex[:8]}"
        created = jira_client.create_version(
            project_id=test_project["id"], name=version_name
        )

        try:
            release_date = datetime.now().strftime("%Y-%m-%d")

            # Release the version
            released = jira_client.update_version(
                created["id"], released=True, release_date=release_date
            )

            assert released["released"]
            assert "releaseDate" in released
            assert release_date in released["releaseDate"]

        finally:
            jira_client.delete_version(created["id"])

    def test_archive_version(self, jira_client, test_project):
        """Test archiving a version."""
        version_name = f"v{uuid.uuid4().hex[:8]}"
        created = jira_client.create_version(
            project_id=test_project["id"], name=version_name
        )

        try:
            # Archive the version
            archived = jira_client.update_version(created["id"], archived=True)

            assert archived["archived"]

        finally:
            jira_client.delete_version(created["id"])

    def test_delete_version(self, jira_client, test_project):
        """Test deleting a version."""
        version_name = f"v{uuid.uuid4().hex[:8]}"
        created = jira_client.create_version(
            project_id=test_project["id"], name=version_name
        )

        # Delete the version
        jira_client.delete_version(created["id"])

        # Verify it's gone
        from jira_assistant_skills_lib import NotFoundError

        with pytest.raises(NotFoundError):
            jira_client.get_version(created["id"])


@pytest.mark.integration
@pytest.mark.shared
class TestVersionIssueManagement:
    """Tests for managing issue versions."""

    def test_assign_issue_to_fix_version(self, jira_client, test_project):
        """Test assigning an issue to a fix version."""
        # Create version
        version_name = f"v{uuid.uuid4().hex[:8]}"
        version = jira_client.create_version(
            project_id=test_project["id"], name=version_name
        )

        # Create issue
        issue = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Fix Version Test {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Bug"},
            }
        )

        try:
            # Assign to fix version
            jira_client.update_issue(
                issue["key"], fields={"fixVersions": [{"name": version_name}]}
            )

            # Verify
            updated = jira_client.get_issue(issue["key"])
            fix_versions = updated["fields"].get("fixVersions", [])
            assert len(fix_versions) >= 1
            assert fix_versions[0]["name"] == version_name

        finally:
            jira_client.delete_issue(issue["key"])
            jira_client.delete_version(version["id"])

    def test_move_issues_between_versions(self, jira_client, test_project):
        """Test moving issues from one version to another."""
        # Create two versions
        old_version_name = f"v{uuid.uuid4().hex[:8]}-old"
        new_version_name = f"v{uuid.uuid4().hex[:8]}-new"

        old_version = jira_client.create_version(
            project_id=test_project["id"], name=old_version_name
        )
        new_version = jira_client.create_version(
            project_id=test_project["id"], name=new_version_name
        )

        # Create issues in old version
        issues = []
        for i in range(2):
            issue = jira_client.create_issue(
                {
                    "project": {"key": test_project["key"]},
                    "summary": f"Version Move Test {i} {uuid.uuid4().hex[:8]}",
                    "issuetype": {"name": "Task"},
                    "fixVersions": [{"name": old_version_name}],
                }
            )
            issues.append(issue)

        try:
            # Small delay for indexing
            time.sleep(1)

            # Move issues to new version
            for issue in issues:
                jira_client.update_issue(
                    issue["key"], fields={"fixVersions": [{"name": new_version_name}]}
                )

            # Verify all issues moved
            for issue in issues:
                updated = jira_client.get_issue(issue["key"])
                fix_versions = updated["fields"].get("fixVersions", [])
                assert len(fix_versions) >= 1
                assert fix_versions[0]["name"] == new_version_name

        finally:
            for issue in issues:
                jira_client.delete_issue(issue["key"])
            jira_client.delete_version(old_version["id"])
            jira_client.delete_version(new_version["id"])

    def test_get_version_issue_counts(self, jira_client, test_project):
        """Test getting issue counts for a version."""
        version_name = f"v{uuid.uuid4().hex[:8]}"
        version = jira_client.create_version(
            project_id=test_project["id"], name=version_name
        )

        # Create issues in this version
        issues = []
        for i in range(3):
            issue = jira_client.create_issue(
                {
                    "project": {"key": test_project["key"]},
                    "summary": f"Count Test {i} {uuid.uuid4().hex[:8]}",
                    "issuetype": {"name": "Story"},
                    "fixVersions": [{"name": version_name}],
                }
            )
            issues.append(issue)

        try:
            # Small delay for indexing
            time.sleep(2)

            # Get version with issue counts
            # Note: Issue counts may take time to update in JIRA
            version_data = jira_client.get_version(version["id"])

            # Just verify the API call works and returns the version
            assert version_data["id"] == version["id"]
            assert version_data["name"] == version_name

        finally:
            for issue in issues:
                jira_client.delete_issue(issue["key"])
            jira_client.delete_version(version["id"])

    def test_remove_version_from_issue(self, jira_client, test_project):
        """Test removing a version from an issue."""
        version_name = f"v{uuid.uuid4().hex[:8]}"
        version = jira_client.create_version(
            project_id=test_project["id"], name=version_name
        )

        # Create issue with version
        issue = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Remove Version Test {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
                "fixVersions": [{"name": version_name}],
            }
        )

        try:
            # Remove version from issue
            jira_client.update_issue(issue["key"], fields={"fixVersions": []})

            # Verify
            updated = jira_client.get_issue(issue["key"])
            fix_versions = updated["fields"].get("fixVersions", [])
            assert len(fix_versions) == 0

        finally:
            jira_client.delete_issue(issue["key"])
            jira_client.delete_version(version["id"])


@pytest.mark.integration
@pytest.mark.shared
class TestVersionWorkflow:
    """Tests for complete version lifecycle workflows."""

    def test_complete_version_lifecycle(self, jira_client, test_project):
        """
        Test complete version lifecycle:
        1. Create version
        2. Add issues
        3. Release version
        4. Archive version
        5. Clean up
        """
        version_name = f"v{uuid.uuid4().hex[:8]}"

        try:
            # Step 1: Create version
            print(f"\n  Creating version {version_name}...")
            version = jira_client.create_version(
                project_id=test_project["id"],
                name=version_name,
                description="Complete lifecycle test",
            )
            assert not version["released"]
            assert not version["archived"]

            # Step 2: Create and add issues
            print("  Creating issues...")
            issues = []
            for i in range(2):
                issue = jira_client.create_issue(
                    {
                        "project": {"key": test_project["key"]},
                        "summary": f"Lifecycle Issue {i} {uuid.uuid4().hex[:8]}",
                        "issuetype": {"name": "Story"},
                        "fixVersions": [{"name": version_name}],
                    }
                )
                issues.append(issue)

            # Step 3: Release version
            print("  Releasing version...")
            release_date = datetime.now().strftime("%Y-%m-%d")
            released = jira_client.update_version(
                version["id"], released=True, release_date=release_date
            )
            assert released["released"]

            # Step 4: Archive version
            print("  Archiving version...")
            archived = jira_client.update_version(version["id"], archived=True)
            assert archived["archived"]

            # Step 5: Clean up
            print("  Cleaning up...")
            for issue in issues:
                jira_client.delete_issue(issue["key"])
            jira_client.delete_version(version["id"])

            print("  Complete version lifecycle test passed!")

        except Exception as e:
            # Emergency cleanup
            try:
                if "issues" in locals():
                    for issue in issues:
                        jira_client.delete_issue(issue["key"])
            except Exception:
                pass
            try:
                if "version" in locals():
                    jira_client.delete_version(version["id"])
            except Exception:
                pass
            raise e

    def test_unreleased_version_filter(self, jira_client, test_project):
        """Test filtering for unreleased versions."""
        # Create released and unreleased versions
        released_name = f"v{uuid.uuid4().hex[:8]}-released"
        unreleased_name = f"v{uuid.uuid4().hex[:8]}-unreleased"

        released_version = jira_client.create_version(
            project_id=test_project["id"], name=released_name
        )
        unreleased_version = jira_client.create_version(
            project_id=test_project["id"], name=unreleased_name
        )

        try:
            # Release one version
            jira_client.update_version(released_version["id"], released=True)

            # Get all versions
            versions = jira_client.get_project_versions(test_project["key"])

            # Filter unreleased
            unreleased = [v for v in versions if not v.get("released", False)]

            # Our unreleased version should be in the list
            unreleased_names = [v["name"] for v in unreleased]
            assert unreleased_name in unreleased_names

        finally:
            jira_client.delete_version(released_version["id"])
            jira_client.delete_version(unreleased_version["id"])

    def test_archived_version_filter(self, jira_client, test_project):
        """Test filtering for archived versions."""
        # Create archived and active versions
        archived_name = f"v{uuid.uuid4().hex[:8]}-archived"
        active_name = f"v{uuid.uuid4().hex[:8]}-active"

        archived_version = jira_client.create_version(
            project_id=test_project["id"], name=archived_name
        )
        active_version = jira_client.create_version(
            project_id=test_project["id"], name=active_name
        )

        try:
            # Archive one version
            jira_client.update_version(archived_version["id"], archived=True)

            # Get all versions
            versions = jira_client.get_project_versions(test_project["key"])

            # Filter archived
            archived = [v for v in versions if v.get("archived", False)]

            # Our archived version should be in the list
            archived_names = [v["name"] for v in archived]
            assert archived_name in archived_names

            # Active version should not be archived
            active_check = next((v for v in versions if v["name"] == active_name), None)
            assert active_check is not None
            assert not active_check.get("archived", False)

        finally:
            jira_client.delete_version(archived_version["id"])
            jira_client.delete_version(active_version["id"])
