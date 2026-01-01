"""
Unit tests for automation rule discovery scripts.

Tests list_automation_rules.py, get_automation_rule.py, and search_automation_rules.py
using mock automation client.

Usage:
    pytest plugins/jira-assistant-skills/skills/jira-admin/tests/unit/test_automation_rules.py -v
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add scripts to path
_this_dir = Path(__file__).parent.parent
_scripts_path = _this_dir.parent / 'scripts'
sys.path.insert(0, str(_scripts_path))


@pytest.mark.unit
@pytest.mark.admin
class TestListAutomationRules:
    """Tests for list_automation_rules.py functionality."""

    def test_list_all_rules(self, mock_automation_client, sample_automation_rules, sample_rules_response):
        """Test listing all automation rules."""
        from list_automation_rules import list_automation_rules

        mock_automation_client.get_rules.return_value = sample_rules_response

        result = list_automation_rules(client=mock_automation_client)

        assert len(result) == 3
        mock_automation_client.get_rules.assert_called_once()

    def test_list_rules_with_project_filter(self, mock_automation_client, sample_automation_rules):
        """Test listing rules filtered by project."""
        from list_automation_rules import list_automation_rules

        # Filter to project-scoped rules only
        filtered_rules = [r for r in sample_automation_rules if r['ruleScope']['resources']]
        mock_automation_client.search_rules.return_value = {
            'values': filtered_rules,
            'hasMore': False
        }

        result = list_automation_rules(
            client=mock_automation_client,
            project='PROJ'
        )

        assert len(result) == 2
        mock_automation_client.search_rules.assert_called_once()

    def test_list_rules_with_state_filter(self, mock_automation_client, sample_automation_rules):
        """Test listing rules filtered by state."""
        from list_automation_rules import list_automation_rules

        # Filter to enabled rules only
        enabled_rules = [r for r in sample_automation_rules if r['state'] == 'ENABLED']
        mock_automation_client.search_rules.return_value = {
            'values': enabled_rules,
            'hasMore': False
        }

        result = list_automation_rules(
            client=mock_automation_client,
            state='enabled'
        )

        assert len(result) == 2
        for rule in result:
            assert rule['state'] == 'ENABLED'

    def test_list_rules_disabled_filter(self, mock_automation_client, sample_automation_rules):
        """Test listing disabled rules only."""
        from list_automation_rules import list_automation_rules

        disabled_rules = [r for r in sample_automation_rules if r['state'] == 'DISABLED']
        mock_automation_client.search_rules.return_value = {
            'values': disabled_rules,
            'hasMore': False
        }

        result = list_automation_rules(
            client=mock_automation_client,
            state='disabled'
        )

        assert len(result) == 1
        assert result[0]['state'] == 'DISABLED'

    def test_list_rules_with_pagination(self, mock_automation_client, sample_automation_rules):
        """Test listing rules with pagination."""
        from list_automation_rules import list_automation_rules

        # First page
        page1 = {
            'values': sample_automation_rules[:2],
            'hasMore': True,
            'links': {'next': '?cursor=page2'}
        }
        # Second page
        page2 = {
            'values': sample_automation_rules[2:],
            'hasMore': False
        }

        mock_automation_client.get_rules.side_effect = [page1, page2]

        result = list_automation_rules(
            client=mock_automation_client,
            fetch_all=True
        )

        assert len(result) == 3
        assert mock_automation_client.get_rules.call_count == 2

    def test_list_rules_with_limit(self, mock_automation_client, sample_automation_rules):
        """Test listing rules with result limit."""
        from list_automation_rules import list_automation_rules

        mock_automation_client.get_rules.return_value = {
            'values': sample_automation_rules[:1],
            'hasMore': True
        }

        result = list_automation_rules(
            client=mock_automation_client,
            limit=1
        )

        assert len(result) == 1
        mock_automation_client.get_rules.assert_called_once_with(limit=1, cursor=None)

    def test_list_rules_empty_result(self, mock_automation_client):
        """Test listing rules when none exist."""
        from list_automation_rules import list_automation_rules

        mock_automation_client.get_rules.return_value = {
            'values': [],
            'hasMore': False
        }

        result = list_automation_rules(client=mock_automation_client)

        assert result == []

    def test_format_rule_summary(self, sample_automation_rules):
        """Test formatting rule for display."""
        from list_automation_rules import format_rule_summary

        rule = sample_automation_rules[0]
        formatted = format_rule_summary(rule)

        assert 'ID' in formatted
        assert 'Name' in formatted
        assert formatted['Name'] == 'Auto-assign to lead'
        assert formatted['State'] == 'ENABLED'
        assert formatted['Scope'] == 'Project'

    def test_format_rule_summary_global_scope(self, sample_automation_rules):
        """Test formatting rule with global scope."""
        from list_automation_rules import format_rule_summary

        # Second rule has global scope (empty resources)
        rule = sample_automation_rules[1]
        formatted = format_rule_summary(rule)

        assert formatted['Scope'] == 'Global'


@pytest.mark.unit
@pytest.mark.admin
class TestGetAutomationRule:
    """Tests for get_automation_rule.py functionality."""

    def test_get_rule_by_id(self, mock_automation_client, sample_rule_detail):
        """Test getting rule by ID."""
        from get_automation_rule import get_automation_rule

        mock_automation_client.get_rule.return_value = sample_rule_detail

        result = get_automation_rule(
            client=mock_automation_client,
            rule_id='ari:cloud:jira::site/12345-rule-001'
        )

        assert result['id'] == 'ari:cloud:jira::site/12345-rule-001'
        assert result['name'] == 'Auto-assign to lead'
        mock_automation_client.get_rule.assert_called_once_with('ari:cloud:jira::site/12345-rule-001')

    def test_get_rule_by_name(self, mock_automation_client, sample_automation_rules, sample_rule_detail):
        """Test getting rule by name."""
        from get_automation_rule import get_automation_rule

        mock_automation_client.search_rules.return_value = {
            'values': sample_automation_rules,
            'hasMore': False
        }
        mock_automation_client.get_rule.return_value = sample_rule_detail

        result = get_automation_rule(
            client=mock_automation_client,
            name='Auto-assign to lead'
        )

        assert result['name'] == 'Auto-assign to lead'

    def test_get_rule_by_name_partial_match(self, mock_automation_client, sample_automation_rules, sample_rule_detail):
        """Test getting rule by partial name match."""
        from get_automation_rule import get_automation_rule

        mock_automation_client.search_rules.return_value = {
            'values': sample_automation_rules,
            'hasMore': False
        }
        mock_automation_client.get_rule.return_value = sample_rule_detail

        result = get_automation_rule(
            client=mock_automation_client,
            name='Auto-assign'
        )

        assert result['name'] == 'Auto-assign to lead'

    def test_get_rule_not_found(self, mock_automation_client):
        """Test getting non-existent rule by name."""
        from get_automation_rule import get_automation_rule
        from jira_assistant_skills_lib import AutomationNotFoundError

        mock_automation_client.search_rules.return_value = {
            'values': [],
            'hasMore': False
        }

        with pytest.raises(AutomationNotFoundError):
            get_automation_rule(
                client=mock_automation_client,
                name='Non-existent Rule'
            )

    def test_get_rule_multiple_matches(self, mock_automation_client, sample_automation_rules):
        """Test getting rule when multiple match the name."""
        from get_automation_rule import get_automation_rule

        # Both rules contain "on" in name
        rules_with_on = [r for r in sample_automation_rules if 'on' in r['name'].lower()]
        mock_automation_client.search_rules.return_value = {
            'values': rules_with_on,
            'hasMore': False
        }

        with pytest.raises(ValueError, match="Multiple rules match"):
            get_automation_rule(
                client=mock_automation_client,
                name='on'
            )

    def test_get_rule_missing_parameters(self, mock_automation_client):
        """Test that either rule_id or name must be provided."""
        from get_automation_rule import get_automation_rule

        with pytest.raises(ValueError, match="Either rule_id or name must be provided"):
            get_automation_rule(client=mock_automation_client)

    def test_format_rule_output(self, sample_rule_detail):
        """Test formatting rule output for display."""
        from get_automation_rule import format_rule_output

        output = format_rule_output(sample_rule_detail)

        assert 'Auto-assign to lead' in output
        assert 'ENABLED' in output
        assert 'Trigger' in output
        assert 'Components' in output

    def test_format_rule_output_trigger_only(self, sample_rule_detail):
        """Test formatting rule with trigger only."""
        from get_automation_rule import format_rule_output

        output = format_rule_output(sample_rule_detail, show_trigger=True, show_all=False)

        assert 'Trigger' in output
        assert 'jira.issue.event.trigger:created' in output

    def test_format_rule_output_components_only(self, sample_rule_detail):
        """Test formatting rule with components only."""
        from get_automation_rule import format_rule_output

        output = format_rule_output(sample_rule_detail, show_components=True, show_all=False)

        assert 'Components' in output


@pytest.mark.unit
@pytest.mark.admin
class TestSearchAutomationRules:
    """Tests for search_automation_rules.py functionality."""

    def test_search_rules_by_query(self, mock_automation_client, sample_automation_rules):
        """Test searching rules by query."""
        from search_automation_rules import search_automation_rules

        mock_automation_client.search_rules.return_value = {
            'values': sample_automation_rules,
            'hasMore': False
        }

        result = search_automation_rules(
            client=mock_automation_client,
            query='assign'
        )

        # Should filter locally by query
        assert len(result) >= 1

    def test_search_rules_by_state(self, mock_automation_client, sample_automation_rules):
        """Test searching rules by state."""
        from search_automation_rules import search_automation_rules

        enabled_rules = [r for r in sample_automation_rules if r['state'] == 'ENABLED']
        mock_automation_client.search_rules.return_value = {
            'values': enabled_rules,
            'hasMore': False
        }

        result = search_automation_rules(
            client=mock_automation_client,
            state='enabled'
        )

        assert all(r['state'] == 'ENABLED' for r in result)

    def test_search_rules_empty_result(self, mock_automation_client):
        """Test searching with no matching results."""
        from search_automation_rules import search_automation_rules

        mock_automation_client.search_rules.return_value = {
            'values': [],
            'hasMore': False
        }

        result = search_automation_rules(
            client=mock_automation_client,
            query='nonexistent'
        )

        assert result == []


@pytest.mark.unit
@pytest.mark.admin
class TestAutomationRuleStateManagement:
    """Tests for rule state management - enable, disable, toggle."""

    def test_enable_rule(self, mock_automation_client, sample_rule_detail):
        """Test enabling a rule."""
        from enable_automation_rule import enable_automation_rule

        mock_automation_client.enable_rule.return_value = {**sample_rule_detail, 'state': 'ENABLED'}

        result = enable_automation_rule(
            client=mock_automation_client,
            rule_id='ari:cloud:jira::site/12345-rule-001'
        )

        assert result['state'] == 'ENABLED'
        mock_automation_client.enable_rule.assert_called_once()

    def test_disable_rule(self, mock_automation_client, sample_rule_detail):
        """Test disabling a rule."""
        from disable_automation_rule import disable_automation_rule

        mock_automation_client.disable_rule.return_value = {**sample_rule_detail, 'state': 'DISABLED'}

        result = disable_automation_rule(
            client=mock_automation_client,
            rule_id='ari:cloud:jira::site/12345-rule-001'
        )

        assert result['state'] == 'DISABLED'
        mock_automation_client.disable_rule.assert_called_once()

    def test_toggle_rule_enable(self, mock_automation_client, sample_rule_detail):
        """Test toggling a disabled rule to enabled."""
        from toggle_automation_rule import toggle_automation_rule

        disabled_rule = {**sample_rule_detail, 'state': 'DISABLED'}
        mock_automation_client.get_rule.return_value = disabled_rule
        mock_automation_client.enable_rule.return_value = {**sample_rule_detail, 'state': 'ENABLED'}

        result = toggle_automation_rule(
            client=mock_automation_client,
            rule_id='ari:cloud:jira::site/12345-rule-001'
        )

        assert result['state'] == 'ENABLED'
        mock_automation_client.enable_rule.assert_called_once()

    def test_toggle_rule_disable(self, mock_automation_client, sample_rule_detail):
        """Test toggling an enabled rule to disabled."""
        from toggle_automation_rule import toggle_automation_rule

        mock_automation_client.get_rule.return_value = sample_rule_detail  # Already enabled
        mock_automation_client.disable_rule.return_value = {**sample_rule_detail, 'state': 'DISABLED'}

        result = toggle_automation_rule(
            client=mock_automation_client,
            rule_id='ari:cloud:jira::site/12345-rule-001'
        )

        assert result['state'] == 'DISABLED'
        mock_automation_client.disable_rule.assert_called_once()
