"""
Live Integration Tests: Version Lifecycle

Tests for version CRUD operations against a real JIRA instance.
"""

import uuid
from datetime import datetime, timedelta

import pytest


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.version
class TestVersionCreation:
    """Tests for creating versions."""

    def test_create_simple_version(self, jira_client, test_project):
        """Test creating a basic version."""
        version_name = f"Test Version {uuid.uuid4().hex[:8]}"

        version = jira_client.create_version(
            project=test_project["key"], name=version_name
        )

        try:
            assert "id" in version
            assert version["name"] == version_name
        finally:
            jira_client.delete_version(version["id"])

    def test_create_version_with_description(self, jira_client, test_project):
        """Test creating a version with description."""
        version_name = f"Test Version Desc {uuid.uuid4().hex[:8]}"
        description = "This is a test version with description"

        version = jira_client.create_version(
            project=test_project["key"], name=version_name, description=description
        )

        try:
            assert version["description"] == description
        finally:
            jira_client.delete_version(version["id"])

    def test_create_version_with_dates(self, jira_client, test_project):
        """Test creating a version with start and release dates."""
        version_name = f"Test Version Dates {uuid.uuid4().hex[:8]}"
        start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        release_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        version = jira_client.create_version(
            project=test_project["key"],
            name=version_name,
            start_date=start_date,
            release_date=release_date,
        )

        try:
            assert version.get("startDate") == start_date
            assert version.get("releaseDate") == release_date
        finally:
            jira_client.delete_version(version["id"])

    def test_create_released_version(self, jira_client, test_project):
        """Test creating a version marked as released."""
        version_name = f"Test Released Version {uuid.uuid4().hex[:8]}"

        version = jira_client.create_version(
            project=test_project["key"], name=version_name, released=True
        )

        try:
            assert version.get("released") is True
        finally:
            jira_client.delete_version(version["id"])


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.version
class TestVersionRetrieval:
    """Tests for retrieving versions."""

    def test_get_project_versions(self, jira_client, test_project, test_version):
        """Test getting all versions for a project."""
        versions = jira_client.get_project_versions(test_project["key"])

        assert isinstance(versions, list)
        assert len(versions) >= 1

        version_names = [v["name"] for v in versions]
        assert test_version["name"] in version_names

    def test_get_version_by_id(self, jira_client, test_version):
        """Test getting a specific version by ID."""
        version = jira_client.get_version(test_version["id"])

        assert version["id"] == test_version["id"]
        assert version["name"] == test_version["name"]


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.version
class TestVersionUpdate:
    """Tests for updating versions."""

    def test_update_version_name(self, jira_client, test_version):
        """Test updating a version's name."""
        new_name = f"Updated Version {uuid.uuid4().hex[:8]}"

        updated = jira_client.update_version(test_version["id"], name=new_name)

        assert updated["name"] == new_name

    def test_update_version_description(self, jira_client, test_version):
        """Test updating a version's description."""
        new_description = "Updated description"

        updated = jira_client.update_version(
            test_version["id"], description=new_description
        )

        assert updated["description"] == new_description

    def test_update_version_dates(self, jira_client, test_version):
        """Test updating a version's dates."""
        new_start = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        new_release = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")

        updated = jira_client.update_version(
            test_version["id"], start_date=new_start, release_date=new_release
        )

        assert updated.get("startDate") == new_start
        assert updated.get("releaseDate") == new_release


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.version
class TestVersionRelease:
    """Tests for releasing and archiving versions."""

    def test_release_version(self, jira_client, test_project):
        """Test releasing a version."""
        version_name = f"Test Release Version {uuid.uuid4().hex[:8]}"
        version = jira_client.create_version(
            project=test_project["key"], name=version_name
        )

        try:
            # Release the version
            released = jira_client.update_version(version["id"], released=True)

            assert released.get("released") is True
        finally:
            jira_client.delete_version(version["id"])

    def test_archive_version(self, jira_client, test_project):
        """Test archiving a version."""
        version_name = f"Test Archive Version {uuid.uuid4().hex[:8]}"
        version = jira_client.create_version(
            project=test_project["key"], name=version_name
        )

        try:
            # Archive the version
            archived = jira_client.update_version(version["id"], archived=True)

            assert archived.get("archived") is True
        finally:
            jira_client.delete_version(version["id"])

    def test_unrelease_version(self, jira_client, test_project):
        """Test unreleasing a version."""
        version_name = f"Test Unrelease {uuid.uuid4().hex[:8]}"
        version = jira_client.create_version(
            project=test_project["key"], name=version_name, released=True
        )

        try:
            # Unrelease the version
            unreleased = jira_client.update_version(version["id"], released=False)

            assert unreleased.get("released") is False
        finally:
            jira_client.delete_version(version["id"])


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.version
class TestVersionDeletion:
    """Tests for deleting versions."""

    def test_delete_version(self, jira_client, test_project):
        """Test deleting a version."""
        version_name = f"Test Delete Version {uuid.uuid4().hex[:8]}"
        version = jira_client.create_version(
            project=test_project["key"], name=version_name
        )

        # Delete the version
        jira_client.delete_version(version["id"])

        # Verify it's gone
        from jira_assistant_skills_lib import NotFoundError

        with pytest.raises(NotFoundError):
            jira_client.get_version(version["id"])


@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.version
class TestVersionWithIssues:
    """Tests for versions with associated issues."""

    def test_assign_issue_to_version(self, jira_client, test_issue, test_version):
        """Test assigning an issue to a version."""
        jira_client.update_issue(
            test_issue["key"], fields={"fixVersions": [{"id": test_version["id"]}]}
        )

        issue = jira_client.get_issue(test_issue["key"])
        fix_versions = issue["fields"].get("fixVersions", [])
        version_ids = [v["id"] for v in fix_versions]

        assert test_version["id"] in version_ids

    def test_remove_issue_from_version(self, jira_client, test_issue, test_version):
        """Test removing an issue from a version."""
        # First assign
        jira_client.update_issue(
            test_issue["key"], fields={"fixVersions": [{"id": test_version["id"]}]}
        )

        # Then remove
        jira_client.update_issue(test_issue["key"], fields={"fixVersions": []})

        issue = jira_client.get_issue(test_issue["key"])
        fix_versions = issue["fields"].get("fixVersions", [])

        assert len(fix_versions) == 0

    def test_assign_multiple_versions(self, jira_client, test_issue, test_project):
        """Test assigning multiple versions to an issue."""
        # Create two versions
        v1 = jira_client.create_version(
            project=test_project["key"], name=f"Test V1 {uuid.uuid4().hex[:8]}"
        )
        v2 = jira_client.create_version(
            project=test_project["key"], name=f"Test V2 {uuid.uuid4().hex[:8]}"
        )

        try:
            jira_client.update_issue(
                test_issue["key"],
                fields={"fixVersions": [{"id": v1["id"]}, {"id": v2["id"]}]},
            )

            issue = jira_client.get_issue(test_issue["key"])
            fix_versions = issue["fields"].get("fixVersions", [])

            assert len(fix_versions) == 2
        finally:
            jira_client.delete_version(v1["id"])
            jira_client.delete_version(v2["id"])
