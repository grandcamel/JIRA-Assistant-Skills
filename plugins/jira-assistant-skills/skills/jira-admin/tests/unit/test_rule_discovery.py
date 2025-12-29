"""
Tests for automation rule discovery scripts - TDD approach.

Phase 1: Rule Discovery & Inspection
- list_automation_rules.py
- get_automation_rule.py
- search_automation_rules.py
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Add scripts and shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))


# =============================================================================
# Tests for list_automation_rules.py
# =============================================================================

class TestListAutomationRulesBasic:
    """Test basic rule listing functionality."""

    def test_list_automation_rules_basic(self, mock_automation_client, sample_automation_rules):
        """Test listing all automation rules."""
        from list_automation_rules import list_automation_rules

        # Setup mock
        mock_automation_client.get_rules.return_value = {
            'values': sample_automation_rules,
            'hasMore': False
        }

        # Execute
        result = list_automation_rules(client=mock_automation_client)

        # Verify
        assert len(result) == 3
        assert result[0]['name'] == 'Auto-assign to lead'
        mock_automation_client.get_rules.assert_called_once()

    def test_list_automation_rules_with_pagination(self, mock_automation_client, sample_automation_rules):
        """Test pagination through rules."""
        from list_automation_rules import list_automation_rules

        # Setup mock - first page
        first_page = {
            'values': sample_automation_rules[:2],
            'hasMore': True,
            'links': {'next': '?cursor=page2token'}
        }
        second_page = {
            'values': sample_automation_rules[2:],
            'hasMore': False
        }
        mock_automation_client.get_rules.side_effect = [first_page, second_page]

        # Execute with pagination
        result = list_automation_rules(client=mock_automation_client, fetch_all=True)

        # Verify all rules fetched
        assert len(result) == 3
        assert mock_automation_client.get_rules.call_count == 2

    def test_list_automation_rules_with_limit(self, mock_automation_client, sample_automation_rules):
        """Test limiting results."""
        from list_automation_rules import list_automation_rules

        # Setup mock
        mock_automation_client.get_rules.return_value = {
            'values': sample_automation_rules[:2],
            'hasMore': True
        }

        # Execute with limit
        result = list_automation_rules(client=mock_automation_client, limit=2)

        # Verify limit was respected
        assert len(result) == 2
        # Verify limit was passed to API
        call_kwargs = mock_automation_client.get_rules.call_args[1] if mock_automation_client.get_rules.call_args[1] else {}
        call_args = mock_automation_client.get_rules.call_args[0] if mock_automation_client.get_rules.call_args[0] else ()
        # Check limit was passed
        assert 2 in list(call_args) + list(call_kwargs.values()) or mock_automation_client.get_rules.call_args[1].get('limit') == 2


class TestListAutomationRulesFiltering:
    """Test filtering by project and state."""

    def test_list_automation_rules_project_scoped(self, mock_automation_client, sample_automation_rules):
        """Test filtering by project scope."""
        from list_automation_rules import list_automation_rules

        # Setup mock - only return project-scoped rules
        project_rules = [r for r in sample_automation_rules if r['ruleScope']['resources']]
        mock_automation_client.search_rules.return_value = {
            'values': project_rules,
            'hasMore': False
        }

        # Execute with project filter
        result = list_automation_rules(
            client=mock_automation_client,
            project='PROJ'
        )

        # Verify search was used with scope filter
        assert len(result) == 2
        mock_automation_client.search_rules.assert_called()

    def test_list_automation_rules_by_state_enabled(self, mock_automation_client, sample_automation_rules):
        """Test filtering by enabled state."""
        from list_automation_rules import list_automation_rules

        # Setup mock
        enabled_rules = [r for r in sample_automation_rules if r['state'] == 'ENABLED']
        mock_automation_client.search_rules.return_value = {
            'values': enabled_rules,
            'hasMore': False
        }

        # Execute with state filter
        result = list_automation_rules(
            client=mock_automation_client,
            state='enabled'
        )

        # Verify
        assert len(result) == 2
        assert all(r['state'] == 'ENABLED' for r in result)

    def test_list_automation_rules_by_state_disabled(self, mock_automation_client, sample_automation_rules):
        """Test filtering by disabled state."""
        from list_automation_rules import list_automation_rules

        # Setup mock
        disabled_rules = [r for r in sample_automation_rules if r['state'] == 'DISABLED']
        mock_automation_client.search_rules.return_value = {
            'values': disabled_rules,
            'hasMore': False
        }

        # Execute with state filter
        result = list_automation_rules(
            client=mock_automation_client,
            state='disabled'
        )

        # Verify
        assert len(result) == 1
        assert result[0]['state'] == 'DISABLED'


class TestListAutomationRulesEmpty:
    """Test handling when no rules exist."""

    def test_list_automation_rules_empty(self, mock_automation_client):
        """Test when no rules exist."""
        from list_automation_rules import list_automation_rules

        # Setup mock - empty results
        mock_automation_client.get_rules.return_value = {
            'values': [],
            'hasMore': False
        }

        # Execute
        result = list_automation_rules(client=mock_automation_client)

        # Verify empty list returned
        assert result == []


class TestListAutomationRulesErrors:
    """Test error handling."""

    def test_list_automation_rules_authentication_error(self, mock_automation_client):
        """Test authentication failure handling."""
        from list_automation_rules import list_automation_rules
        from error_handler import AuthenticationError

        # Setup mock to raise auth error
        mock_automation_client.get_rules.side_effect = AuthenticationError("Invalid credentials")

        # Execute and verify exception
        with pytest.raises(AuthenticationError):
            list_automation_rules(client=mock_automation_client)

    def test_list_automation_rules_permission_denied(self, mock_automation_client):
        """Test permission error handling."""
        from list_automation_rules import list_automation_rules
        from error_handler import AutomationPermissionError

        # Setup mock to raise permission error
        mock_automation_client.get_rules.side_effect = AutomationPermissionError("Admin access required")

        # Execute and verify exception
        with pytest.raises(AutomationPermissionError):
            list_automation_rules(client=mock_automation_client)


# =============================================================================
# Tests for get_automation_rule.py
# =============================================================================

class TestGetAutomationRuleBasic:
    """Test getting rule details."""

    def test_get_automation_rule_basic(self, mock_automation_client, sample_rule_detail):
        """Test getting rule details by ID."""
        from get_automation_rule import get_automation_rule

        # Setup mock
        mock_automation_client.get_rule.return_value = sample_rule_detail

        # Execute
        result = get_automation_rule(
            client=mock_automation_client,
            rule_id='ari:cloud:jira::site/12345-rule-001'
        )

        # Verify
        assert result['name'] == 'Auto-assign to lead'
        assert result['state'] == 'ENABLED'
        mock_automation_client.get_rule.assert_called_once_with('ari:cloud:jira::site/12345-rule-001')

    def test_get_automation_rule_with_components(self, mock_automation_client, sample_rule_detail):
        """Test rule with actions/conditions."""
        from get_automation_rule import get_automation_rule

        # Setup mock
        mock_automation_client.get_rule.return_value = sample_rule_detail

        # Execute
        result = get_automation_rule(
            client=mock_automation_client,
            rule_id='ari:cloud:jira::site/12345-rule-001'
        )

        # Verify components are included
        assert 'components' in result
        assert len(result['components']) == 1
        assert result['components'][0]['type'] == 'jira.issue.assign'

    def test_get_automation_rule_with_trigger_config(self, mock_automation_client, sample_rule_detail):
        """Test rule with trigger configuration."""
        from get_automation_rule import get_automation_rule

        # Setup mock
        mock_automation_client.get_rule.return_value = sample_rule_detail

        # Execute
        result = get_automation_rule(
            client=mock_automation_client,
            rule_id='ari:cloud:jira::site/12345-rule-001'
        )

        # Verify trigger config
        assert 'trigger' in result
        assert result['trigger']['type'] == 'jira.issue.event.trigger:created'
        assert 'configuration' in result['trigger']


class TestGetAutomationRuleByName:
    """Test getting rule by name."""

    def test_get_automation_rule_by_name(self, mock_automation_client, sample_automation_rules, sample_rule_detail):
        """Test finding rule by name then getting details."""
        from get_automation_rule import get_automation_rule

        # Setup mock - search returns rule, then get details
        mock_automation_client.search_rules.return_value = {
            'values': [sample_automation_rules[0]],
            'hasMore': False
        }
        mock_automation_client.get_rule.return_value = sample_rule_detail

        # Execute
        result = get_automation_rule(
            client=mock_automation_client,
            name='Auto-assign to lead'
        )

        # Verify
        assert result['name'] == 'Auto-assign to lead'
        mock_automation_client.get_rule.assert_called_once()


class TestGetAutomationRuleErrors:
    """Test error handling."""

    def test_get_automation_rule_not_found(self, mock_automation_client):
        """Test invalid rule ID error."""
        from get_automation_rule import get_automation_rule
        from error_handler import AutomationNotFoundError

        # Setup mock
        mock_automation_client.get_rule.side_effect = AutomationNotFoundError(
            "Rule", "ari:cloud:jira::site/invalid"
        )

        # Execute and verify exception
        with pytest.raises(AutomationNotFoundError):
            get_automation_rule(
                client=mock_automation_client,
                rule_id='ari:cloud:jira::site/invalid'
            )

    def test_get_automation_rule_permission_denied(self, mock_automation_client):
        """Test permission error."""
        from get_automation_rule import get_automation_rule
        from error_handler import AutomationPermissionError

        # Setup mock
        mock_automation_client.get_rule.side_effect = AutomationPermissionError(
            "Cannot view this rule"
        )

        # Execute and verify exception
        with pytest.raises(AutomationPermissionError):
            get_automation_rule(
                client=mock_automation_client,
                rule_id='ari:cloud:jira::site/12345-rule-001'
            )


# =============================================================================
# Tests for search_automation_rules.py
# =============================================================================

class TestSearchAutomationRulesByTrigger:
    """Test filtering by trigger type."""

    def test_search_by_trigger_type(self, mock_automation_client, sample_automation_rules):
        """Test filtering by trigger (e.g., issue_created)."""
        from search_automation_rules import search_automation_rules

        # Setup mock
        issue_created_rules = [
            r for r in sample_automation_rules
            if 'created' in r['trigger']['type']
        ]
        mock_automation_client.search_rules.return_value = {
            'values': issue_created_rules,
            'hasMore': False
        }

        # Execute
        result = search_automation_rules(
            client=mock_automation_client,
            trigger='jira.issue.event.trigger:created'
        )

        # Verify
        assert len(result) == 1
        assert 'created' in result[0]['trigger']['type']


class TestSearchAutomationRulesByState:
    """Test filtering by state."""

    def test_search_by_state(self, mock_automation_client, sample_automation_rules):
        """Test filtering by enabled/disabled."""
        from search_automation_rules import search_automation_rules

        # Setup mock
        enabled_rules = [r for r in sample_automation_rules if r['state'] == 'ENABLED']
        mock_automation_client.search_rules.return_value = {
            'values': enabled_rules,
            'hasMore': False
        }

        # Execute
        result = search_automation_rules(
            client=mock_automation_client,
            state='enabled'
        )

        # Verify
        assert len(result) == 2
        assert all(r['state'] == 'ENABLED' for r in result)


class TestSearchAutomationRulesByScope:
    """Test filtering by scope."""

    def test_search_by_scope(self, mock_automation_client, sample_automation_rules):
        """Test filtering by project ARI."""
        from search_automation_rules import search_automation_rules

        # Setup mock
        scoped_rules = [
            r for r in sample_automation_rules
            if 'ari:cloud:jira:12345:project/10000' in r['ruleScope']['resources']
        ]
        mock_automation_client.search_rules.return_value = {
            'values': scoped_rules,
            'hasMore': False
        }

        # Execute
        result = search_automation_rules(
            client=mock_automation_client,
            scope='ari:cloud:jira:12345:project/10000'
        )

        # Verify
        assert len(result) == 1


class TestSearchAutomationRulesCombined:
    """Test combined filters."""

    def test_search_combined_filters(self, mock_automation_client, sample_automation_rules):
        """Test multiple filters together."""
        from search_automation_rules import search_automation_rules

        # Setup mock - enabled + issue created trigger
        filtered_rules = [
            r for r in sample_automation_rules
            if r['state'] == 'ENABLED' and 'created' in r['trigger']['type']
        ]
        mock_automation_client.search_rules.return_value = {
            'values': filtered_rules,
            'hasMore': False
        }

        # Execute with combined filters
        result = search_automation_rules(
            client=mock_automation_client,
            trigger='jira.issue.event.trigger:created',
            state='enabled'
        )

        # Verify
        assert len(result) == 1
        assert result[0]['state'] == 'ENABLED'
        assert 'created' in result[0]['trigger']['type']


class TestSearchAutomationRulesEmpty:
    """Test when search returns no results."""

    def test_search_no_results(self, mock_automation_client):
        """Test when search returns empty."""
        from search_automation_rules import search_automation_rules

        # Setup mock
        mock_automation_client.search_rules.return_value = {
            'values': [],
            'hasMore': False
        }

        # Execute
        result = search_automation_rules(
            client=mock_automation_client,
            trigger='nonexistent.trigger'
        )

        # Verify
        assert result == []
