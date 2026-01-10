"""
Tests for permission diagnostics and project role management scripts.

Tests:
- check_my_permissions.py
- list_project_roles.py
- add_user_to_project_role.py
- remove_user_from_project_role.py
"""

import pytest

# ========== Fixtures ==========


@pytest.fixture
def sample_my_permissions_response():
    """Sample response from /rest/api/3/mypermissions."""
    return {
        "permissions": {
            "BROWSE_PROJECTS": {
                "key": "BROWSE_PROJECTS",
                "name": "Browse Projects",
                "description": "Ability to browse projects and issues.",
                "havePermission": True,
            },
            "CREATE_ISSUES": {
                "key": "CREATE_ISSUES",
                "name": "Create Issues",
                "description": "Ability to create issues.",
                "havePermission": True,
            },
            "DELETE_ISSUES": {
                "key": "DELETE_ISSUES",
                "name": "Delete Issues",
                "description": "Ability to delete issues.",
                "havePermission": False,
            },
            "EDIT_ISSUES": {
                "key": "EDIT_ISSUES",
                "name": "Edit Issues",
                "description": "Ability to edit issues.",
                "havePermission": True,
            },
        }
    }


@pytest.fixture
def sample_project_roles_response():
    """Sample response from /rest/api/3/project/{key}/role."""
    return {
        "Administrators": "https://test.atlassian.net/rest/api/3/project/10000/role/10002",
        "Developers": "https://test.atlassian.net/rest/api/3/project/10000/role/10003",
        "Users": "https://test.atlassian.net/rest/api/3/project/10000/role/10004",
    }


@pytest.fixture
def sample_role_actors_response():
    """Sample response from /rest/api/3/project/{key}/role/{id}."""
    return {
        "self": "https://test.atlassian.net/rest/api/3/project/DEMO/role/10002",
        "name": "Administrators",
        "id": 10002,
        "description": "Project administrators",
        "actors": [
            {
                "id": 10100,
                "displayName": "John Doe",
                "type": "atlassian-user-role-actor",
                "actorUser": {
                    "accountId": "5b10ac8d82e05b22cc7d4ef5",
                    "emailAddress": "john.doe@example.com",
                },
            },
            {
                "id": 10101,
                "displayName": "jira-developers",
                "type": "atlassian-group-role-actor",
                "actorGroup": {
                    "name": "jira-developers",
                    "groupId": "group-id-123",
                },
            },
        ],
    }


@pytest.fixture
def sample_empty_role_response():
    """Sample role with no actors."""
    return {
        "self": "https://test.atlassian.net/rest/api/3/project/DEMO/role/10002",
        "name": "Administrators",
        "id": 10002,
        "description": "Project administrators",
        "actors": [],
    }


# ========== check_my_permissions.py Tests ==========


@pytest.mark.admin
@pytest.mark.unit
class TestCheckMyPermissions:
    """Test permission checking functionality."""

    def test_check_permissions_all_have(self, mock_jira_client):
        """Test checking permissions when user has all of them."""
        from check_my_permissions import check_permissions

        # Setup mock
        mock_jira_client.get.return_value = {
            "permissions": {
                "BROWSE_PROJECTS": {
                    "key": "BROWSE_PROJECTS",
                    "name": "Browse Projects",
                    "description": "Browse projects",
                    "havePermission": True,
                },
                "CREATE_ISSUES": {
                    "key": "CREATE_ISSUES",
                    "name": "Create Issues",
                    "description": "Create issues",
                    "havePermission": True,
                },
            }
        }

        # Execute
        result = check_permissions(
            mock_jira_client,
            project_key="DEMO",
            permissions=["BROWSE_PROJECTS", "CREATE_ISSUES"],
        )

        # Verify
        assert len(result) == 2
        assert all(p["havePermission"] for p in result)

    def test_check_permissions_some_missing(
        self, mock_jira_client, sample_my_permissions_response
    ):
        """Test checking permissions when user lacks some."""
        from check_my_permissions import check_permissions

        # Setup mock - API returns all permissions regardless of request
        mock_jira_client.get.return_value = sample_my_permissions_response

        # Execute - request specific permissions
        result = check_permissions(
            mock_jira_client,
            project_key="DEMO",
            permissions=["BROWSE_PROJECTS", "DELETE_ISSUES", "CREATE_ISSUES", "EDIT_ISSUES"],
        )

        # Verify - API returns what it has, we check what was returned
        assert len(result) == 4
        have = [p for p in result if p["havePermission"]]
        missing = [p for p in result if not p["havePermission"]]
        assert len(have) == 3  # BROWSE, CREATE, EDIT
        assert len(missing) == 1  # DELETE
        assert missing[0]["key"] == "DELETE_ISSUES"

    def test_check_permissions_only_have_filter(
        self, mock_jira_client, sample_my_permissions_response
    ):
        """Test filtering to only show permissions user has."""
        from check_my_permissions import check_permissions

        # Setup mock
        mock_jira_client.get.return_value = sample_my_permissions_response

        # Execute
        result = check_permissions(
            mock_jira_client,
            project_key="DEMO",
            permissions=["BROWSE_PROJECTS", "DELETE_ISSUES", "CREATE_ISSUES"],
            only_have=True,
        )

        # Verify
        assert all(p["havePermission"] for p in result)

    def test_check_permissions_only_missing_filter(
        self, mock_jira_client, sample_my_permissions_response
    ):
        """Test filtering to only show permissions user lacks."""
        from check_my_permissions import check_permissions

        # Setup mock
        mock_jira_client.get.return_value = sample_my_permissions_response

        # Execute
        result = check_permissions(
            mock_jira_client,
            project_key="DEMO",
            permissions=["BROWSE_PROJECTS", "DELETE_ISSUES", "CREATE_ISSUES"],
            only_missing=True,
        )

        # Verify
        assert all(not p["havePermission"] for p in result)


# ========== list_project_roles.py Tests ==========


@pytest.mark.admin
@pytest.mark.unit
class TestListProjectRoles:
    """Test project role listing functionality."""

    def test_list_all_roles(
        self,
        mock_jira_client,
        sample_project_roles_response,
        sample_role_actors_response,
    ):
        """Test listing all roles for a project."""
        from list_project_roles import list_project_roles

        # Setup mocks
        mock_jira_client.get.side_effect = [
            sample_project_roles_response,  # First call: get all roles
            sample_role_actors_response,  # Second call: get Administrators role
            {  # Third call: get Developers role
                "name": "Developers",
                "id": 10003,
                "actors": [],
            },
            {  # Fourth call: get Users role
                "name": "Users",
                "id": 10004,
                "actors": [],
            },
        ]

        # Execute
        result = list_project_roles(mock_jira_client, project_key="DEMO")

        # Verify
        assert len(result) == 3
        role_names = [r["name"] for r in result]
        assert "Administrators" in role_names
        assert "Developers" in role_names
        assert "Users" in role_names

    def test_list_specific_role(
        self,
        mock_jira_client,
        sample_project_roles_response,
        sample_role_actors_response,
    ):
        """Test listing a specific role."""
        from list_project_roles import list_project_roles

        # Setup mocks
        mock_jira_client.get.side_effect = [
            sample_project_roles_response,
            sample_role_actors_response,
        ]

        # Execute
        result = list_project_roles(
            mock_jira_client,
            project_key="DEMO",
            role_name="Administrators",
        )

        # Verify
        assert len(result) == 1
        assert result[0]["name"] == "Administrators"
        assert len(result[0]["users"]) == 1
        assert len(result[0]["groups"]) == 1

    def test_list_role_with_users_and_groups(
        self,
        mock_jira_client,
        sample_project_roles_response,
        sample_role_actors_response,
    ):
        """Test that role listing correctly parses users and groups."""
        from list_project_roles import list_project_roles

        # Setup mocks
        mock_jira_client.get.side_effect = [
            sample_project_roles_response,
            sample_role_actors_response,
        ]

        # Execute
        result = list_project_roles(
            mock_jira_client,
            project_key="DEMO",
            role_name="Administrators",
        )

        # Verify users
        users = result[0]["users"]
        assert len(users) == 1
        assert users[0]["displayName"] == "John Doe"
        assert users[0]["accountId"] == "5b10ac8d82e05b22cc7d4ef5"

        # Verify groups
        groups = result[0]["groups"]
        assert len(groups) == 1
        assert groups[0]["name"] == "jira-developers"

    def test_list_role_not_found(self, mock_jira_client, sample_project_roles_response):
        """Test error when role not found."""
        from list_project_roles import list_project_roles

        from jira_assistant_skills_lib import NotFoundError

        # Setup mock
        mock_jira_client.get.return_value = sample_project_roles_response

        # Execute and verify
        with pytest.raises(NotFoundError):
            list_project_roles(
                mock_jira_client,
                project_key="DEMO",
                role_name="NonexistentRole",
            )


# ========== add_user_to_project_role.py Tests ==========


@pytest.mark.admin
@pytest.mark.unit
class TestAddUserToProjectRole:
    """Test adding users to project roles."""

    def test_add_user_by_account_id(
        self,
        mock_jira_client,
        sample_project_roles_response,
        sample_role_actors_response,
    ):
        """Test adding user by account ID."""
        from add_user_to_project_role import add_user_to_project_role

        # Setup mocks
        mock_jira_client.get.side_effect = [
            sample_role_actors_response,  # resolve_role_id tries ID first
        ]
        mock_jira_client.post.return_value = sample_role_actors_response

        # Execute
        add_user_to_project_role(
            mock_jira_client,
            project_key="DEMO",
            role_id=10002,
            account_id="new-user-id",
        )

        # Verify
        mock_jira_client.post.assert_called_once()
        call_args = mock_jira_client.post.call_args
        assert "DEMO" in call_args[0][0]
        assert "10002" in call_args[0][0]

    def test_resolve_role_by_name(
        self,
        mock_jira_client,
        sample_project_roles_response,
        sample_role_actors_response,
    ):
        """Test resolving role by name."""
        from add_user_to_project_role import resolve_role_id

        # Setup mocks - first call fails (not an ID), second gets roles
        mock_jira_client.get.side_effect = [
            sample_project_roles_response,
        ]

        # Execute
        role_id, role_name = resolve_role_id(
            mock_jira_client,
            project_key="DEMO",
            role_identifier="Administrators",
        )

        # Verify
        assert role_id == 10002
        assert role_name == "Administrators"

    def test_resolve_user_by_email(self, mock_jira_client, sample_users):
        """Test resolving user by email."""
        from add_user_to_project_role import resolve_user_account_id

        # Setup mock
        mock_jira_client.search_users.return_value = sample_users

        # Execute
        account_id, display_info = resolve_user_account_id(
            mock_jira_client,
            user_identifier="john.doe@example.com",
        )

        # Verify
        assert account_id == "5b10ac8d82e05b22cc7d4ef5"
        assert display_info == "John Doe"

    def test_resolve_user_not_found(self, mock_jira_client):
        """Test error when user not found by email."""
        from add_user_to_project_role import resolve_user_account_id

        from jira_assistant_skills_lib import NotFoundError

        # Setup mock - return empty list
        mock_jira_client.search_users.return_value = []

        # Execute and verify
        with pytest.raises(NotFoundError):
            resolve_user_account_id(
                mock_jira_client,
                user_identifier="nonexistent@example.com",
            )


# ========== remove_user_from_project_role.py Tests ==========


@pytest.mark.admin
@pytest.mark.unit
class TestRemoveUserFromProjectRole:
    """Test removing users from project roles."""

    def test_remove_user_success(
        self,
        mock_jira_client,
        sample_role_actors_response,
    ):
        """Test successfully removing a user from a role."""
        from remove_user_from_project_role import remove_user_from_project_role

        # Setup mock
        mock_jira_client.delete.return_value = None

        # Execute
        remove_user_from_project_role(
            mock_jira_client,
            project_key="DEMO",
            role_id=10002,
            account_id="5b10ac8d82e05b22cc7d4ef5",
        )

        # Verify
        mock_jira_client.delete.assert_called_once()
        call_args = mock_jira_client.delete.call_args
        assert "DEMO" in call_args[0][0]
        assert "10002" in call_args[0][0]
        assert call_args[1]["params"]["user"] == "5b10ac8d82e05b22cc7d4ef5"

    def test_check_user_in_role_true(
        self, mock_jira_client, sample_role_actors_response
    ):
        """Test checking if user is in role - returns True."""
        from remove_user_from_project_role import check_user_in_role

        # Setup mock
        mock_jira_client.get.return_value = sample_role_actors_response

        # Execute
        result = check_user_in_role(
            mock_jira_client,
            project_key="DEMO",
            role_id=10002,
            account_id="5b10ac8d82e05b22cc7d4ef5",
        )

        # Verify
        assert result is True

    def test_check_user_in_role_false(
        self, mock_jira_client, sample_role_actors_response
    ):
        """Test checking if user is in role - returns False."""
        from remove_user_from_project_role import check_user_in_role

        # Setup mock
        mock_jira_client.get.return_value = sample_role_actors_response

        # Execute
        result = check_user_in_role(
            mock_jira_client,
            project_key="DEMO",
            role_id=10002,
            account_id="different-user-id",
        )

        # Verify
        assert result is False

    def test_check_user_in_empty_role(
        self, mock_jira_client, sample_empty_role_response
    ):
        """Test checking if user is in an empty role."""
        from remove_user_from_project_role import check_user_in_role

        # Setup mock
        mock_jira_client.get.return_value = sample_empty_role_response

        # Execute
        result = check_user_in_role(
            mock_jira_client,
            project_key="DEMO",
            role_id=10002,
            account_id="any-user-id",
        )

        # Verify
        assert result is False


# ========== Format Output Tests ==========


@pytest.mark.admin
@pytest.mark.unit
class TestOutputFormatting:
    """Test output formatting functions."""

    def test_format_permissions_output_table(self):
        """Test formatting permissions as table."""
        from check_my_permissions import format_permissions_output

        permissions = [
            {
                "key": "BROWSE_PROJECTS",
                "name": "Browse Projects",
                "description": "Browse projects",
                "havePermission": True,
            },
            {
                "key": "DELETE_ISSUES",
                "name": "Delete Issues",
                "description": "Delete issues",
                "havePermission": False,
            },
        ]

        result = format_permissions_output(
            permissions, output_format="table", project_key="DEMO"
        )

        assert "BROWSE_PROJECTS" in result
        assert "DELETE_ISSUES" in result
        assert "DEMO" in result

    def test_format_permissions_output_json(self):
        """Test formatting permissions as JSON."""
        import json

        from check_my_permissions import format_permissions_output

        permissions = [
            {
                "key": "BROWSE_PROJECTS",
                "name": "Browse Projects",
                "description": "Browse projects",
                "havePermission": True,
            },
        ]

        result = format_permissions_output(permissions, output_format="json")

        # Should be valid JSON
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["key"] == "BROWSE_PROJECTS"

    def test_format_roles_output_table(self):
        """Test formatting roles as table."""
        from list_project_roles import format_roles_output

        roles = [
            {
                "id": 10002,
                "name": "Administrators",
                "description": "Project admins",
                "users": [
                    {"displayName": "John Doe", "emailAddress": "john@example.com"}
                ],
                "groups": [],
                "totalActors": 1,
            },
        ]

        result = format_roles_output(roles, output_format="table", project_key="DEMO")

        assert "Administrators" in result
        assert "John Doe" in result
        assert "DEMO" in result
