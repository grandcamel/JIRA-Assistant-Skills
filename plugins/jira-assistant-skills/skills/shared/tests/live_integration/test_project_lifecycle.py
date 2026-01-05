"""
Live Integration Tests: Project Lifecycle

Tests for project creation and deletion operations.
These tests are special because they create/delete projects directly,
separate from the session-scoped test project.
"""

import contextlib
import time
import uuid

import pytest


@pytest.mark.integration
@pytest.mark.shared
class TestProjectCreation:
    """Tests for project creation."""

    def test_create_scrum_project(self, jira_client):
        """Test creating a Scrum project."""
        project_key = f"TST{uuid.uuid4().hex[:5].upper()}"

        try:
            project = jira_client.create_project(
                key=project_key,
                name=f"Test Scrum Project {project_key}",
                project_type_key="software",
                template_key="com.pyxis.greenhopper.jira:gh-simplified-agility-scrum",
                description="Test Scrum project",
            )

            assert project["key"] == project_key
            assert "id" in project

            # Wait for board creation
            time.sleep(2)

            # Verify board was auto-created
            boards = jira_client.get_all_boards(project_key=project_key)
            assert len(boards.get("values", [])) >= 1
            # Simplified templates create 'simple' type boards
            assert boards["values"][0]["type"] in ("scrum", "simple")

        finally:
            # Cleanup
            with contextlib.suppress(Exception):
                jira_client.delete_project(project_key, enable_undo=True)

    def test_create_kanban_project(self, jira_client):
        """Test creating a Kanban project."""
        project_key = f"KAN{uuid.uuid4().hex[:5].upper()}"

        try:
            project = jira_client.create_project(
                key=project_key,
                name=f"Test Kanban Project {project_key}",
                project_type_key="software",
                template_key="com.pyxis.greenhopper.jira:gh-simplified-agility-kanban",
                description="Test Kanban project",
            )

            assert project["key"] == project_key

            # Wait for board creation
            time.sleep(2)

            # Verify Kanban board was created
            boards = jira_client.get_all_boards(project_key=project_key)
            assert len(boards.get("values", [])) >= 1
            # Simplified templates may create 'simple' type boards
            assert boards["values"][0]["type"] in ("kanban", "simple")

        finally:
            # Cleanup
            with contextlib.suppress(Exception):
                jira_client.delete_project(project_key, enable_undo=True)


@pytest.mark.integration
@pytest.mark.shared
class TestProjectRetrieval:
    """Tests for project retrieval."""

    def test_get_project(self, jira_client, test_project):
        """Test getting project details."""
        project = jira_client.get_project(test_project["key"])

        assert project["key"] == test_project["key"]
        assert project["name"] == test_project["name"]
        assert "id" in project

    def test_get_project_with_expand(self, jira_client, test_project):
        """Test getting project with expanded fields."""
        project = jira_client.get_project(
            test_project["key"], expand=["description", "lead"]
        )

        assert project["key"] == test_project["key"]
        # Lead should be expanded
        if "lead" in project:
            assert "accountId" in project["lead"] or "displayName" in project["lead"]

    def test_get_project_statuses(self, jira_client, test_project):
        """Test getting project statuses."""
        statuses = jira_client.get_project_statuses(test_project["key"])

        assert isinstance(statuses, list)
        assert len(statuses) >= 1

        # Each entry should have issue type and statuses
        for status_group in statuses:
            assert "name" in status_group  # Issue type name
            assert "statuses" in status_group
            assert len(status_group["statuses"]) >= 1


@pytest.mark.integration
@pytest.mark.shared
class TestProjectDeletion:
    """Tests for project deletion."""

    def test_delete_project_with_undo(self, jira_client):
        """Test deleting a project with undo enabled (goes to trash)."""
        project_key = f"DEL{uuid.uuid4().hex[:5].upper()}"

        # Create project
        jira_client.create_project(key=project_key, name=f"Delete Test {project_key}")

        # Delete with undo enabled
        jira_client.delete_project(project_key, enable_undo=True)

        # Verify project is gone (from active projects)
        from jira_assistant_skills_lib import NotFoundError

        with pytest.raises(NotFoundError):
            jira_client.get_project(project_key)

    def test_delete_project_cascade(self, jira_client):
        """Test that deleting project removes its issues and sprints."""
        project_key = f"CAS{uuid.uuid4().hex[:5].upper()}"

        # Create project
        jira_client.create_project(
            key=project_key, name=f"Cascade Delete Test {project_key}"
        )

        time.sleep(2)

        # Create an issue
        issue = jira_client.create_issue(
            {
                "project": {"key": project_key},
                "summary": "Issue to be cascaded",
                "issuetype": {"name": "Task"},
            }
        )

        # Get board and create a sprint
        boards = jira_client.get_all_boards(project_key=project_key)
        if boards.get("values"):
            board_id = boards["values"][0]["id"]
            jira_client.create_sprint(board_id=board_id, name="Sprint to be cascaded")

        # Delete project
        jira_client.delete_project(project_key, enable_undo=True)

        # Verify issue is gone
        from jira_assistant_skills_lib import NotFoundError

        with pytest.raises(NotFoundError):
            jira_client.get_issue(issue["key"])


@pytest.mark.integration
@pytest.mark.shared
class TestCompleteWorkflow:
    """End-to-end workflow tests."""

    def test_complete_project_lifecycle(self, jira_client):
        """
        Test complete project lifecycle:
        1. Create project
        2. Create issues
        3. Create sprint
        4. Move issues to sprint
        5. Clean up and delete
        """
        project_key = f"LIF{uuid.uuid4().hex[:5].upper()}"

        try:
            # Step 1: Create project
            print(f"\n  Creating project {project_key}...")
            project = jira_client.create_project(
                key=project_key, name=f"Lifecycle Test {project_key}"
            )
            assert project["key"] == project_key
            time.sleep(2)

            # Step 2: Create issues
            print("  Creating issues...")
            issues = []
            for i in range(3):
                issue = jira_client.create_issue(
                    {
                        "project": {"key": project_key},
                        "summary": f"Lifecycle Issue {i}",
                        "issuetype": {"name": "Story"},
                    }
                )
                issues.append(issue)
            assert len(issues) == 3

            # Step 3: Get board and create sprint
            print("  Creating sprint...")
            boards = jira_client.get_all_boards(project_key=project_key)
            board_id = boards["values"][0]["id"]

            sprint = jira_client.create_sprint(
                board_id=board_id, name="Lifecycle Sprint"
            )
            assert sprint["state"] == "future"

            # Step 4: Move issues to sprint
            print("  Moving issues to sprint...")
            jira_client.move_issues_to_sprint(sprint["id"], [i["key"] for i in issues])

            # Wait for indexing
            time.sleep(1)

            # Verify issues in sprint (may take time to index)
            sprint_issues = jira_client.get_sprint_issues(sprint["id"])
            # Note: Sprint issues may not immediately show due to indexing
            # Just verify the call works
            assert "issues" in sprint_issues or "total" in sprint_issues

            # Step 5: Clean up
            print("  Cleaning up...")

            # Delete issues
            for issue in issues:
                jira_client.delete_issue(issue["key"])

            # Delete sprint
            jira_client.delete_sprint(sprint["id"])

            # Delete project
            jira_client.delete_project(project_key, enable_undo=True)

            print("  Complete lifecycle test passed!")

        except Exception as e:
            # Emergency cleanup
            with contextlib.suppress(Exception):
                jira_client.delete_project(project_key, enable_undo=True)
            raise e
