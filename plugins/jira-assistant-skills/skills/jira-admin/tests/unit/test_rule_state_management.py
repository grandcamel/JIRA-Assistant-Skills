"""
Tests for automation rule state management scripts - TDD approach.

Phase 2: Rule State Management
- enable_automation_rule.py
- disable_automation_rule.py
- toggle_automation_rule.py
"""

import sys
from pathlib import Path

import pytest

# Add scripts and shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


# =============================================================================
# Tests for enable_automation_rule.py
# =============================================================================


class TestEnableAutomationRule:
    """Test enabling automation rules."""

    def test_enable_automation_rule(self, mock_automation_client, sample_rule_detail):
        """Test enabling a disabled rule."""
        from enable_automation_rule import enable_automation_rule

        # Setup mock - rule was disabled, now enabled
        enabled_rule = sample_rule_detail.copy()
        enabled_rule["state"] = "ENABLED"
        mock_automation_client.enable_rule.return_value = enabled_rule

        # Execute
        result = enable_automation_rule(
            client=mock_automation_client, rule_id="ari:cloud:jira::site/12345-rule-001"
        )

        # Verify
        assert result["state"] == "ENABLED"
        mock_automation_client.enable_rule.assert_called_once_with(
            "ari:cloud:jira::site/12345-rule-001"
        )

    def test_enable_already_enabled_rule(
        self, mock_automation_client, sample_rule_detail
    ):
        """Test idempotency - enabling already enabled rule."""
        from enable_automation_rule import enable_automation_rule

        # Setup mock - rule already enabled
        mock_automation_client.enable_rule.return_value = sample_rule_detail

        # Execute
        result = enable_automation_rule(
            client=mock_automation_client, rule_id="ari:cloud:jira::site/12345-rule-001"
        )

        # Verify - should succeed without error
        assert result["state"] == "ENABLED"

    def test_enable_rule_by_name(
        self, mock_automation_client, sample_automation_rules, sample_rule_detail
    ):
        """Test enabling a rule by name."""
        from enable_automation_rule import enable_automation_rule

        # Setup mock
        mock_automation_client.search_rules.return_value = {
            "values": [sample_automation_rules[1]],  # The disabled rule
            "hasMore": False,
        }
        enabled_rule = sample_rule_detail.copy()
        enabled_rule["state"] = "ENABLED"
        mock_automation_client.enable_rule.return_value = enabled_rule

        # Execute
        result = enable_automation_rule(
            client=mock_automation_client, name="Comment on status change"
        )

        # Verify
        assert result["state"] == "ENABLED"
        mock_automation_client.search_rules.assert_called()


class TestEnableAutomationRuleErrors:
    """Test error handling for enable operations."""

    def test_enable_rule_invalid_id(self, mock_automation_client):
        """Test error for invalid rule ID."""
        from enable_automation_rule import enable_automation_rule

        from jira_assistant_skills_lib import AutomationNotFoundError

        # Setup mock
        mock_automation_client.enable_rule.side_effect = AutomationNotFoundError(
            "Rule", "invalid-rule-id"
        )

        # Execute and verify exception
        with pytest.raises(AutomationNotFoundError):
            enable_automation_rule(
                client=mock_automation_client, rule_id="invalid-rule-id"
            )

    def test_enable_rule_permission_denied(self, mock_automation_client):
        """Test permission error handling."""
        from enable_automation_rule import enable_automation_rule

        from jira_assistant_skills_lib import AutomationPermissionError

        # Setup mock
        mock_automation_client.enable_rule.side_effect = AutomationPermissionError(
            "Cannot manage this rule"
        )

        # Execute and verify exception
        with pytest.raises(AutomationPermissionError):
            enable_automation_rule(
                client=mock_automation_client,
                rule_id="ari:cloud:jira::site/12345-rule-001",
            )


class TestEnableAutomationRuleDryRun:
    """Test dry-run mode for enable operations."""

    def test_enable_rule_dry_run(self, mock_automation_client, sample_rule_detail):
        """Test dry-run mode shows preview without changes."""
        from enable_automation_rule import enable_automation_rule

        # Setup mock - get_rule for preview
        disabled_rule = sample_rule_detail.copy()
        disabled_rule["state"] = "DISABLED"
        mock_automation_client.get_rule.return_value = disabled_rule

        # Execute with dry_run
        result = enable_automation_rule(
            client=mock_automation_client,
            rule_id="ari:cloud:jira::site/12345-rule-001",
            dry_run=True,
        )

        # Verify no actual enable was called
        mock_automation_client.enable_rule.assert_not_called()
        # Result should indicate what would happen
        assert result.get("dry_run") is True or result.get("would_enable") is True


# =============================================================================
# Tests for disable_automation_rule.py
# =============================================================================


class TestDisableAutomationRule:
    """Test disabling automation rules."""

    def test_disable_automation_rule(self, mock_automation_client, sample_rule_detail):
        """Test disabling an enabled rule."""
        from disable_automation_rule import disable_automation_rule

        # Setup mock
        disabled_rule = sample_rule_detail.copy()
        disabled_rule["state"] = "DISABLED"
        mock_automation_client.disable_rule.return_value = disabled_rule

        # Execute
        result = disable_automation_rule(
            client=mock_automation_client, rule_id="ari:cloud:jira::site/12345-rule-001"
        )

        # Verify
        assert result["state"] == "DISABLED"
        mock_automation_client.disable_rule.assert_called_once_with(
            "ari:cloud:jira::site/12345-rule-001"
        )

    def test_disable_already_disabled_rule(
        self, mock_automation_client, sample_rule_detail
    ):
        """Test idempotency - disabling already disabled rule."""
        from disable_automation_rule import disable_automation_rule

        # Setup mock - rule already disabled
        disabled_rule = sample_rule_detail.copy()
        disabled_rule["state"] = "DISABLED"
        mock_automation_client.disable_rule.return_value = disabled_rule

        # Execute
        result = disable_automation_rule(
            client=mock_automation_client, rule_id="ari:cloud:jira::site/12345-rule-001"
        )

        # Verify - should succeed without error
        assert result["state"] == "DISABLED"

    def test_disable_rule_by_name(
        self, mock_automation_client, sample_automation_rules, sample_rule_detail
    ):
        """Test disabling a rule by name."""
        from disable_automation_rule import disable_automation_rule

        # Setup mock
        mock_automation_client.search_rules.return_value = {
            "values": [sample_automation_rules[0]],  # The enabled rule
            "hasMore": False,
        }
        disabled_rule = sample_rule_detail.copy()
        disabled_rule["state"] = "DISABLED"
        mock_automation_client.disable_rule.return_value = disabled_rule

        # Execute
        result = disable_automation_rule(
            client=mock_automation_client, name="Auto-assign to lead"
        )

        # Verify
        assert result["state"] == "DISABLED"


class TestDisableAutomationRuleErrors:
    """Test error handling for disable operations."""

    def test_disable_rule_invalid_id(self, mock_automation_client):
        """Test error for invalid rule ID."""
        from disable_automation_rule import disable_automation_rule

        from jira_assistant_skills_lib import AutomationNotFoundError

        # Setup mock
        mock_automation_client.disable_rule.side_effect = AutomationNotFoundError(
            "Rule", "invalid-rule-id"
        )

        # Execute and verify exception
        with pytest.raises(AutomationNotFoundError):
            disable_automation_rule(
                client=mock_automation_client, rule_id="invalid-rule-id"
            )

    def test_disable_rule_permission_denied(self, mock_automation_client):
        """Test permission error handling."""
        from disable_automation_rule import disable_automation_rule

        from jira_assistant_skills_lib import AutomationPermissionError

        # Setup mock
        mock_automation_client.disable_rule.side_effect = AutomationPermissionError(
            "Cannot manage this rule"
        )

        # Execute and verify exception
        with pytest.raises(AutomationPermissionError):
            disable_automation_rule(
                client=mock_automation_client,
                rule_id="ari:cloud:jira::site/12345-rule-001",
            )


class TestDisableAutomationRuleDryRun:
    """Test dry-run mode for disable operations."""

    def test_disable_rule_dry_run(self, mock_automation_client, sample_rule_detail):
        """Test dry-run mode shows preview without changes."""
        from disable_automation_rule import disable_automation_rule

        # Setup mock - get_rule returns the current state for preview
        mock_automation_client.get_rule.return_value = sample_rule_detail

        # Execute with dry_run
        result = disable_automation_rule(
            client=mock_automation_client,
            rule_id="ari:cloud:jira::site/12345-rule-001",
            dry_run=True,
        )

        # Verify no actual disable was called
        mock_automation_client.disable_rule.assert_not_called()
        # Result should indicate dry run
        assert result.get("dry_run") is True
        assert result.get("would_disable") is True
        assert result.get("rule_id") == "ari:cloud:jira::site/12345-rule-001"
        assert result.get("current_state") == sample_rule_detail.get("state")
        assert result.get("new_state") == "DISABLED"

    def test_disable_rule_dry_run_shows_rule_name(
        self, mock_automation_client, sample_rule_detail
    ):
        """Test dry-run includes rule name in preview."""
        from disable_automation_rule import disable_automation_rule

        # Setup mock
        mock_automation_client.get_rule.return_value = sample_rule_detail

        # Execute with dry_run
        result = disable_automation_rule(
            client=mock_automation_client,
            rule_id="ari:cloud:jira::site/12345-rule-001",
            dry_run=True,
        )

        # Verify name is included
        assert result.get("name") == sample_rule_detail.get("name")


# =============================================================================
# Tests for toggle_automation_rule.py
# =============================================================================


class TestToggleAutomationRule:
    """Test toggling automation rule state."""

    def test_toggle_enabled_to_disabled(
        self, mock_automation_client, sample_rule_detail
    ):
        """Test toggling from enabled to disabled."""
        from toggle_automation_rule import toggle_automation_rule

        # Setup mock - rule is enabled
        mock_automation_client.get_rule.return_value = sample_rule_detail

        disabled_rule = sample_rule_detail.copy()
        disabled_rule["state"] = "DISABLED"
        mock_automation_client.disable_rule.return_value = disabled_rule

        # Execute
        result = toggle_automation_rule(
            client=mock_automation_client, rule_id="ari:cloud:jira::site/12345-rule-001"
        )

        # Verify - enabled rule was disabled
        assert result["state"] == "DISABLED"
        mock_automation_client.disable_rule.assert_called_once()
        mock_automation_client.enable_rule.assert_not_called()

    def test_toggle_disabled_to_enabled(
        self, mock_automation_client, sample_rule_detail
    ):
        """Test toggling from disabled to enabled."""
        from toggle_automation_rule import toggle_automation_rule

        # Setup mock - rule is disabled
        disabled_rule = sample_rule_detail.copy()
        disabled_rule["state"] = "DISABLED"
        mock_automation_client.get_rule.return_value = disabled_rule

        enabled_rule = sample_rule_detail.copy()
        enabled_rule["state"] = "ENABLED"
        mock_automation_client.enable_rule.return_value = enabled_rule

        # Execute
        result = toggle_automation_rule(
            client=mock_automation_client, rule_id="ari:cloud:jira::site/12345-rule-001"
        )

        # Verify - disabled rule was enabled
        assert result["state"] == "ENABLED"
        mock_automation_client.enable_rule.assert_called_once()
        mock_automation_client.disable_rule.assert_not_called()

    def test_toggle_rule_by_name(
        self, mock_automation_client, sample_automation_rules, sample_rule_detail
    ):
        """Test toggling a rule by name."""
        from toggle_automation_rule import toggle_automation_rule

        # Setup mock
        mock_automation_client.search_rules.return_value = {
            "values": [sample_automation_rules[0]],
            "hasMore": False,
        }
        mock_automation_client.get_rule.return_value = sample_rule_detail

        disabled_rule = sample_rule_detail.copy()
        disabled_rule["state"] = "DISABLED"
        mock_automation_client.disable_rule.return_value = disabled_rule

        # Execute
        result = toggle_automation_rule(
            client=mock_automation_client, name="Auto-assign to lead"
        )

        # Verify toggle happened
        assert result["state"] == "DISABLED"


class TestToggleAutomationRuleDryRun:
    """Test dry-run mode for toggle operations."""

    def test_toggle_rule_dry_run_enabled_to_disabled(
        self, mock_automation_client, sample_rule_detail
    ):
        """Test dry-run mode shows preview for toggling enabled rule."""
        from toggle_automation_rule import toggle_automation_rule

        # Setup mock - rule is enabled
        mock_automation_client.get_rule.return_value = sample_rule_detail

        # Execute with dry_run
        result = toggle_automation_rule(
            client=mock_automation_client,
            rule_id="ari:cloud:jira::site/12345-rule-001",
            dry_run=True,
        )

        # Verify no actual toggle was called
        mock_automation_client.enable_rule.assert_not_called()
        mock_automation_client.disable_rule.assert_not_called()
        # Result should indicate dry run
        assert result.get("dry_run") is True
        assert result.get("would_toggle") is True
        assert result.get("rule_id") == "ari:cloud:jira::site/12345-rule-001"
        assert result.get("current_state") == "ENABLED"
        assert result.get("new_state") == "DISABLED"

    def test_toggle_rule_dry_run_disabled_to_enabled(
        self, mock_automation_client, sample_rule_detail
    ):
        """Test dry-run mode shows preview for toggling disabled rule."""
        from toggle_automation_rule import toggle_automation_rule

        # Setup mock - rule is disabled
        disabled_rule = sample_rule_detail.copy()
        disabled_rule["state"] = "DISABLED"
        mock_automation_client.get_rule.return_value = disabled_rule

        # Execute with dry_run
        result = toggle_automation_rule(
            client=mock_automation_client,
            rule_id="ari:cloud:jira::site/12345-rule-001",
            dry_run=True,
        )

        # Verify no actual toggle was called
        mock_automation_client.enable_rule.assert_not_called()
        mock_automation_client.disable_rule.assert_not_called()
        # Result should indicate dry run
        assert result.get("dry_run") is True
        assert result.get("would_toggle") is True
        assert result.get("current_state") == "DISABLED"
        assert result.get("new_state") == "ENABLED"

    def test_toggle_rule_dry_run_shows_rule_name(
        self, mock_automation_client, sample_rule_detail
    ):
        """Test dry-run includes rule name in preview."""
        from toggle_automation_rule import toggle_automation_rule

        # Setup mock
        mock_automation_client.get_rule.return_value = sample_rule_detail

        # Execute with dry_run
        result = toggle_automation_rule(
            client=mock_automation_client,
            rule_id="ari:cloud:jira::site/12345-rule-001",
            dry_run=True,
        )

        # Verify name is included
        assert result.get("name") == sample_rule_detail.get("name")
