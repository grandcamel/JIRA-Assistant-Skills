"""
Tests for manual automation rule scripts - TDD approach.

Phase 3: Manual Rule Invocation
- list_manual_rules.py
- invoke_manual_rule.py
"""

import sys
from pathlib import Path

import pytest

# Add scripts and shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


# =============================================================================
# Tests for list_manual_rules.py
# =============================================================================


class TestListManualRulesForIssues:
    """Test listing manual rules for issue context."""

    def test_list_manual_rules_for_issues(
        self, mock_automation_client, sample_manual_rules
    ):
        """Test listing manual rules for issue context."""
        from list_manual_rules import list_manual_rules

        # Setup mock
        mock_automation_client.get_manual_rules.return_value = {
            "values": sample_manual_rules,
            "hasMore": False,
        }

        # Execute
        result = list_manual_rules(client=mock_automation_client, context_type="issue")

        # Verify
        assert len(result) == 2
        assert result[0]["name"] == "Escalate to Manager"
        mock_automation_client.get_manual_rules.assert_called_once()


class TestListManualRulesForAlerts:
    """Test listing manual rules for alert context."""

    def test_list_manual_rules_for_alerts(self, mock_automation_client):
        """Test listing manual rules for alert context."""
        from list_manual_rules import list_manual_rules

        # Setup mock
        alert_rules = [
            {
                "id": "54321",
                "name": "Acknowledge Alert",
                "description": "Acknowledge this alert",
                "contextType": "alert",
            }
        ]
        mock_automation_client.get_manual_rules.return_value = {
            "values": alert_rules,
            "hasMore": False,
        }

        # Execute
        result = list_manual_rules(client=mock_automation_client, context_type="alert")

        # Verify
        assert len(result) == 1
        assert result[0]["contextType"] == "alert"


class TestListManualRulesEmpty:
    """Test when no manual rules exist."""

    def test_list_manual_rules_empty(self, mock_automation_client):
        """Test when no manual rules exist."""
        from list_manual_rules import list_manual_rules

        # Setup mock
        mock_automation_client.get_manual_rules.return_value = {
            "values": [],
            "hasMore": False,
        }

        # Execute
        result = list_manual_rules(client=mock_automation_client)

        # Verify
        assert result == []


class TestListManualRulesPagination:
    """Test pagination through manual rules."""

    def test_list_manual_rules_pagination(
        self, mock_automation_client, sample_manual_rules
    ):
        """Test pagination through manual rules."""
        from list_manual_rules import list_manual_rules

        # Setup mock - two pages
        first_page = {
            "values": sample_manual_rules[:1],
            "hasMore": True,
            "links": {"next": "?cursor=page2"},
        }
        second_page = {"values": sample_manual_rules[1:], "hasMore": False}
        mock_automation_client.get_manual_rules.side_effect = [first_page, second_page]

        # Execute with fetch_all
        result = list_manual_rules(client=mock_automation_client, fetch_all=True)

        # Verify all rules fetched
        assert len(result) == 2
        assert mock_automation_client.get_manual_rules.call_count == 2


# =============================================================================
# Tests for invoke_manual_rule.py
# =============================================================================


class TestInvokeManualRuleOnIssue:
    """Test invoking rule on an issue."""

    def test_invoke_manual_rule_on_issue(self, mock_automation_client):
        """Test invoking rule on an issue."""
        from invoke_manual_rule import invoke_manual_rule

        # Setup mock
        mock_automation_client.invoke_manual_rule.return_value = {
            "status": "success",
            "message": "Rule invoked successfully",
        }

        # Execute
        result = invoke_manual_rule(
            client=mock_automation_client, rule_id="12345", issue_key="PROJ-123"
        )

        # Verify
        assert result["status"] == "success"
        mock_automation_client.invoke_manual_rule.assert_called_once()

        # Verify context was passed correctly
        call_args = mock_automation_client.invoke_manual_rule.call_args
        assert "context" in call_args[1] or len(call_args[0]) > 1
        context = call_args[1].get("context") or call_args[0][1]
        assert context["issue"]["key"] == "PROJ-123"


class TestInvokeManualRuleWithProperties:
    """Test passing custom properties to rule."""

    def test_invoke_manual_rule_with_properties(self, mock_automation_client):
        """Test passing custom properties to rule."""
        from invoke_manual_rule import invoke_manual_rule

        # Setup mock
        mock_automation_client.invoke_manual_rule.return_value = {
            "status": "success",
            "message": "Rule invoked with properties",
        }

        # Execute with properties
        properties = {"priority": "High", "assignee": "john@example.com"}
        result = invoke_manual_rule(
            client=mock_automation_client,
            rule_id="12345",
            issue_key="PROJ-123",
            properties=properties,
        )

        # Verify
        assert result["status"] == "success"

        # Verify properties were passed
        call_args = mock_automation_client.invoke_manual_rule.call_args
        passed_props = call_args[1].get("properties") or (
            call_args[0][2] if len(call_args[0]) > 2 else None
        )
        assert passed_props is not None


class TestInvokeManualRuleErrors:
    """Test error handling for rule invocation."""

    def test_invoke_manual_rule_invalid_context(self, mock_automation_client):
        """Test error for invalid context."""
        from invoke_manual_rule import invoke_manual_rule

        from jira_assistant_skills_lib import AutomationValidationError

        # Setup mock
        mock_automation_client.invoke_manual_rule.side_effect = (
            AutomationValidationError("Invalid context: issue not found")
        )

        # Execute and verify exception
        with pytest.raises(AutomationValidationError):
            invoke_manual_rule(
                client=mock_automation_client, rule_id="12345", issue_key="INVALID-999"
            )

    def test_invoke_manual_rule_not_found(self, mock_automation_client):
        """Test error for invalid rule ID."""
        from invoke_manual_rule import invoke_manual_rule

        from jira_assistant_skills_lib import AutomationNotFoundError

        # Setup mock
        mock_automation_client.invoke_manual_rule.side_effect = AutomationNotFoundError(
            "Manual rule", "invalid-rule"
        )

        # Execute and verify exception
        with pytest.raises(AutomationNotFoundError):
            invoke_manual_rule(
                client=mock_automation_client,
                rule_id="invalid-rule",
                issue_key="PROJ-123",
            )

    def test_invoke_manual_rule_permission_denied(self, mock_automation_client):
        """Test permission error."""
        from invoke_manual_rule import invoke_manual_rule

        from jira_assistant_skills_lib import AutomationPermissionError

        # Setup mock
        mock_automation_client.invoke_manual_rule.side_effect = (
            AutomationPermissionError("Cannot invoke this rule")
        )

        # Execute and verify exception
        with pytest.raises(AutomationPermissionError):
            invoke_manual_rule(
                client=mock_automation_client, rule_id="12345", issue_key="PROJ-123"
            )


class TestInvokeManualRuleDryRun:
    """Test dry-run mode for manual rule invocation."""

    def test_invoke_manual_rule_dry_run(self, mock_automation_client):
        """Test dry-run mode shows preview without invocation."""
        from invoke_manual_rule import invoke_manual_rule

        # Execute with dry_run
        result = invoke_manual_rule(
            client=mock_automation_client,
            rule_id="12345",
            issue_key="PROJ-123",
            dry_run=True,
        )

        # Verify no actual invocation was called
        mock_automation_client.invoke_manual_rule.assert_not_called()
        # Result should indicate dry run
        assert result.get("dry_run") is True
        assert result.get("would_invoke") is True
        assert result.get("rule_id") == "12345"
        assert result.get("context") == {"issue": {"key": "PROJ-123"}}

    def test_invoke_manual_rule_dry_run_with_properties(self, mock_automation_client):
        """Test dry-run includes properties in preview."""
        from invoke_manual_rule import invoke_manual_rule

        # Properties to pass
        properties = {"priority": "High", "assignee": "john@example.com"}

        # Execute with dry_run
        result = invoke_manual_rule(
            client=mock_automation_client,
            rule_id="12345",
            issue_key="PROJ-123",
            properties=properties,
            dry_run=True,
        )

        # Verify no actual invocation was called
        mock_automation_client.invoke_manual_rule.assert_not_called()
        # Result should include properties
        assert result.get("dry_run") is True
        assert result.get("properties") == properties

    def test_invoke_manual_rule_dry_run_with_context(self, mock_automation_client):
        """Test dry-run with custom context object."""
        from invoke_manual_rule import invoke_manual_rule

        # Custom context
        context = {"issue": {"key": "PROJ-456"}, "customData": {"field1": "value1"}}

        # Execute with dry_run
        result = invoke_manual_rule(
            client=mock_automation_client,
            rule_id="12345",
            context=context,
            dry_run=True,
        )

        # Verify no actual invocation was called
        mock_automation_client.invoke_manual_rule.assert_not_called()
        # Result should include the full context
        assert result.get("dry_run") is True
        assert result.get("context") == context
