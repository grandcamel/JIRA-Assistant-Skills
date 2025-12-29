"""
Unit tests for create_group.py script.

Tests cover:
- Creating a new group
- Dry-run mode
- Duplicate group handling
- Group name validation
- Permission error handling
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add scripts path
scripts_path = str(Path(__file__).parent.parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


class TestCreateGroupBasic:
    """Tests for basic group creation."""

    def test_create_group_success(self, mock_jira_client, sample_group):
        """Test creating a new group successfully."""
        mock_jira_client.create_group.return_value = sample_group

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from create_group import create_group
            result = create_group(mock_jira_client, name="jira-developers")

        mock_jira_client.create_group.assert_called_once_with(name="jira-developers")
        assert result['name'] == "jira-developers"
        assert 'groupId' in result

    def test_create_group_returns_group_id(self, mock_jira_client, sample_group):
        """Test that created group includes groupId."""
        mock_jira_client.create_group.return_value = sample_group

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from create_group import create_group
            result = create_group(mock_jira_client, name="jira-developers")

        assert result['groupId'] == "276f955c-63d7-42c8-9520-92d01dca0625"


class TestCreateGroupDryRun:
    """Tests for dry-run mode."""

    def test_create_group_dry_run_no_api_call(self, mock_jira_client):
        """Test that dry-run mode does not make API call."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from create_group import create_group
            result = create_group(mock_jira_client, name="new-group", dry_run=True)

        mock_jira_client.create_group.assert_not_called()
        assert result is None

    def test_create_group_dry_run_returns_preview(self, mock_jira_client):
        """Test that dry-run mode returns preview info."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from create_group import format_dry_run_preview
            preview = format_dry_run_preview("new-group")

        assert "new-group" in preview
        assert "dry run" in preview.lower() or "preview" in preview.lower()


class TestCreateGroupDuplicate:
    """Tests for duplicate group handling."""

    def test_create_group_duplicate_raises_conflict(self, mock_jira_client):
        """Test that creating duplicate group raises ConflictError."""
        from jira_assistant_skills_lib import ConflictError
        mock_jira_client.create_group.side_effect = ConflictError(
            "Group name 'jira-developers' is already used"
        )

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from create_group import create_group

            with pytest.raises(ConflictError) as exc_info:
                create_group(mock_jira_client, name="jira-developers")

        assert "already" in str(exc_info.value).lower()


class TestCreateGroupValidation:
    """Tests for group name validation."""

    def test_create_group_empty_name_fails(self, mock_jira_client):
        """Test that empty group name raises validation error."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from create_group import validate_group_name, create_group
            from jira_assistant_skills_lib import ValidationError

            with pytest.raises(ValidationError):
                validate_group_name("")

    def test_create_group_valid_name_passes(self, mock_jira_client):
        """Test that valid group name passes validation."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from create_group import validate_group_name

            # Should not raise
            validate_group_name("valid-group-name")
            validate_group_name("Group With Spaces")
            validate_group_name("group_123")


class TestCreateGroupPermissionError:
    """Tests for permission error handling."""

    def test_create_group_permission_denied(self, mock_jira_client):
        """Test handling insufficient permissions error."""
        from jira_assistant_skills_lib import PermissionError
        mock_jira_client.create_group.side_effect = PermissionError(
            "Site administration permission required"
        )

        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from create_group import create_group

            with pytest.raises(PermissionError) as exc_info:
                create_group(mock_jira_client, name="new-group")

        assert "permission" in str(exc_info.value).lower()


class TestCreateGroupOutputFormats:
    """Tests for output formatting."""

    def test_format_created_group_text(self, mock_jira_client, sample_group):
        """Test text output format for created group."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from create_group import format_created_group
            output = format_created_group(sample_group)

        assert "jira-developers" in output
        assert "276f955c-63d7-42c8-9520-92d01dca0625" in output

    def test_format_created_group_json(self, mock_jira_client, sample_group):
        """Test JSON output format for created group."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from create_group import format_created_group_json
            output = format_created_group_json(sample_group)

        parsed = json.loads(output)
        assert parsed['name'] == "jira-developers"


class TestCreateGroupSystemGroupWarning:
    """Tests for system group name warning."""

    def test_create_group_system_name_warning(self, mock_jira_client, system_groups):
        """Test warning when using system group-like name."""
        with patch('config_manager.get_jira_client', return_value=mock_jira_client):
            from create_group import check_system_group_name

            # Should not warn for names that are similar but not exact matches
            warning = check_system_group_name("jira-administrators-new")
            assert warning is None  # Not an exact system group name

            # Should not warn for regular names
            warning = check_system_group_name("my-custom-group")
            assert warning is None
