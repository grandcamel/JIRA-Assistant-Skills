"""
Tests for automation template and rule creation scripts - TDD approach.

Phase 4: Rule Creation & Updates
- list_automation_templates.py
- get_automation_template.py
- create_rule_from_template.py
- update_automation_rule.py
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Add scripts and shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared' / 'scripts' / 'lib'))


# =============================================================================
# Tests for list_automation_templates.py
# =============================================================================

class TestListAutomationTemplatesAll:
    """Test listing all templates."""

    def test_list_templates_all(self, mock_automation_client, sample_automation_templates):
        """Test listing all templates."""
        from list_automation_templates import list_automation_templates

        # Setup mock
        mock_automation_client.get_templates.return_value = {
            'values': sample_automation_templates,
            'hasMore': False
        }

        # Execute
        result = list_automation_templates(client=mock_automation_client)

        # Verify
        assert len(result) == 2
        assert result[0]['name'] == 'Assign issues to project lead'
        mock_automation_client.get_templates.assert_called_once()


class TestListAutomationTemplatesByCategory:
    """Test filtering by category."""

    def test_list_templates_by_category(self, mock_automation_client, sample_automation_templates):
        """Test filtering by category."""
        from list_automation_templates import list_automation_templates

        # Setup mock
        mock_automation_client.get_templates.return_value = {
            'values': sample_automation_templates,
            'hasMore': False
        }

        # Execute with category filter
        result = list_automation_templates(
            client=mock_automation_client,
            category='Issue Management'
        )

        # Verify
        assert len(result) == 2
        assert all(t['category'] == 'Issue Management' for t in result)


class TestListAutomationTemplatesPagination:
    """Test pagination."""

    def test_list_templates_pagination(self, mock_automation_client, sample_automation_templates):
        """Test pagination."""
        from list_automation_templates import list_automation_templates

        # Setup mock - two pages
        first_page = {
            'values': sample_automation_templates[:1],
            'hasMore': True,
            'links': {'next': '?cursor=page2'}
        }
        second_page = {
            'values': sample_automation_templates[1:],
            'hasMore': False
        }
        mock_automation_client.get_templates.side_effect = [first_page, second_page]

        # Execute with fetch_all
        result = list_automation_templates(
            client=mock_automation_client,
            fetch_all=True
        )

        # Verify all templates fetched
        assert len(result) == 2
        assert mock_automation_client.get_templates.call_count == 2


# =============================================================================
# Tests for get_automation_template.py
# =============================================================================

class TestGetAutomationTemplate:
    """Test getting template details."""

    def test_get_automation_template(self, mock_automation_client, sample_automation_templates):
        """Test getting template details."""
        from get_automation_template import get_automation_template

        # Setup mock
        mock_automation_client.get_template.return_value = sample_automation_templates[0]

        # Execute
        result = get_automation_template(
            client=mock_automation_client,
            template_id='template-001'
        )

        # Verify
        assert result['name'] == 'Assign issues to project lead'
        assert 'parameters' in result
        mock_automation_client.get_template.assert_called_once_with('template-001')


class TestGetAutomationTemplateErrors:
    """Test error handling."""

    def test_get_template_not_found(self, mock_automation_client):
        """Test invalid template ID error."""
        from get_automation_template import get_automation_template
        from error_handler import AutomationNotFoundError

        # Setup mock
        mock_automation_client.get_template.side_effect = AutomationNotFoundError(
            "Template", "invalid-template"
        )

        # Execute and verify exception
        with pytest.raises(AutomationNotFoundError):
            get_automation_template(
                client=mock_automation_client,
                template_id='invalid-template'
            )


# =============================================================================
# Tests for create_rule_from_template.py
# =============================================================================

class TestCreateRuleFromTemplateBasic:
    """Test creating rule from template."""

    def test_create_rule_from_template_basic(self, mock_automation_client, sample_rule_detail):
        """Test creating rule from template."""
        from create_rule_from_template import create_rule_from_template

        # Setup mock
        mock_automation_client.create_rule_from_template.return_value = sample_rule_detail

        # Execute
        result = create_rule_from_template(
            client=mock_automation_client,
            template_id='template-001',
            project='PROJ'
        )

        # Verify
        assert result['name'] == 'Auto-assign to lead'
        mock_automation_client.create_rule_from_template.assert_called_once()


class TestCreateRuleFromTemplateWithParams:
    """Test providing template parameters."""

    def test_create_rule_from_template_with_params(self, mock_automation_client, sample_rule_detail):
        """Test providing template parameters."""
        from create_rule_from_template import create_rule_from_template

        # Setup mock
        mock_automation_client.create_rule_from_template.return_value = sample_rule_detail

        # Execute with parameters
        result = create_rule_from_template(
            client=mock_automation_client,
            template_id='template-001',
            project='PROJ',
            parameters={'projectKey': 'PROJ', 'assignee': 'john@example.com'}
        )

        # Verify
        assert result is not None
        # Check parameters were passed
        call_args = mock_automation_client.create_rule_from_template.call_args
        passed_params = call_args[1].get('parameters') or call_args[0][1]
        assert 'projectKey' in passed_params


class TestCreateRuleFromTemplateWithName:
    """Test creating with custom name."""

    def test_create_rule_from_template_with_name(self, mock_automation_client, sample_rule_detail):
        """Test creating with custom name."""
        from create_rule_from_template import create_rule_from_template

        # Setup mock
        custom_rule = sample_rule_detail.copy()
        custom_rule['name'] = 'My Custom Rule'
        mock_automation_client.create_rule_from_template.return_value = custom_rule

        # Execute with custom name
        result = create_rule_from_template(
            client=mock_automation_client,
            template_id='template-001',
            project='PROJ',
            name='My Custom Rule'
        )

        # Verify
        assert result['name'] == 'My Custom Rule'


class TestCreateRuleFromTemplateErrors:
    """Test error handling."""

    def test_create_rule_from_template_invalid_template(self, mock_automation_client):
        """Test error for invalid template ID."""
        from create_rule_from_template import create_rule_from_template
        from error_handler import AutomationNotFoundError

        # Setup mock
        mock_automation_client.create_rule_from_template.side_effect = AutomationNotFoundError(
            "Template", "invalid-template"
        )

        # Execute and verify exception
        with pytest.raises(AutomationNotFoundError):
            create_rule_from_template(
                client=mock_automation_client,
                template_id='invalid-template',
                project='PROJ'
            )

    def test_create_rule_from_template_missing_params(self, mock_automation_client):
        """Test validation of required parameters."""
        from create_rule_from_template import create_rule_from_template
        from error_handler import AutomationValidationError

        # Setup mock
        mock_automation_client.create_rule_from_template.side_effect = AutomationValidationError(
            "Missing required parameter: projectKey"
        )

        # Execute and verify exception
        with pytest.raises(AutomationValidationError):
            create_rule_from_template(
                client=mock_automation_client,
                template_id='template-001',
                project='PROJ',
                parameters={}  # Missing required params
            )


class TestCreateRuleFromTemplateDryRun:
    """Test dry-run mode."""

    def test_create_rule_from_template_dry_run(self, mock_automation_client, sample_automation_templates):
        """Test dry-run mode."""
        from create_rule_from_template import create_rule_from_template

        # Setup mock for template lookup
        mock_automation_client.get_template.return_value = sample_automation_templates[0]

        # Execute with dry_run
        result = create_rule_from_template(
            client=mock_automation_client,
            template_id='template-001',
            project='PROJ',
            dry_run=True
        )

        # Verify no actual creation
        mock_automation_client.create_rule_from_template.assert_not_called()
        assert result.get('dry_run') is True


# =============================================================================
# Tests for update_automation_rule.py
# =============================================================================

class TestUpdateAutomationRuleName:
    """Test updating rule name."""

    def test_update_rule_name(self, mock_automation_client, sample_rule_detail):
        """Test updating rule name."""
        from update_automation_rule import update_automation_rule

        # Setup mock
        updated_rule = sample_rule_detail.copy()
        updated_rule['name'] = 'New Rule Name'
        mock_automation_client.update_rule.return_value = updated_rule

        # Execute
        result = update_automation_rule(
            client=mock_automation_client,
            rule_id='ari:cloud:jira::site/12345-rule-001',
            name='New Rule Name'
        )

        # Verify
        assert result['name'] == 'New Rule Name'
        mock_automation_client.update_rule.assert_called_once()


class TestUpdateAutomationRuleDescription:
    """Test updating rule description."""

    def test_update_rule_description(self, mock_automation_client, sample_rule_detail):
        """Test updating rule description."""
        from update_automation_rule import update_automation_rule

        # Setup mock
        updated_rule = sample_rule_detail.copy()
        updated_rule['description'] = 'Updated description'
        mock_automation_client.update_rule.return_value = updated_rule

        # Execute
        result = update_automation_rule(
            client=mock_automation_client,
            rule_id='ari:cloud:jira::site/12345-rule-001',
            description='Updated description'
        )

        # Verify
        assert result['description'] == 'Updated description'


class TestUpdateAutomationRuleConfig:
    """Test updating rule with config file."""

    def test_update_rule_with_config(self, mock_automation_client, sample_rule_detail):
        """Test updating rule with full config."""
        from update_automation_rule import update_automation_rule

        # Setup mock
        mock_automation_client.update_rule.return_value = sample_rule_detail

        # Config to update
        config = {
            'name': 'Updated Name',
            'description': 'Updated description'
        }

        # Execute
        result = update_automation_rule(
            client=mock_automation_client,
            rule_id='ari:cloud:jira::site/12345-rule-001',
            config=config
        )

        # Verify
        assert result is not None
        # Check config was passed
        call_args = mock_automation_client.update_rule.call_args
        passed_config = call_args[1].get('rule_config') or call_args[0][1]
        assert 'name' in passed_config


class TestUpdateAutomationRuleErrors:
    """Test error handling."""

    def test_update_rule_not_found(self, mock_automation_client):
        """Test error for invalid rule ID."""
        from update_automation_rule import update_automation_rule
        from error_handler import AutomationNotFoundError

        # Setup mock
        mock_automation_client.update_rule.side_effect = AutomationNotFoundError(
            "Rule", "invalid-rule"
        )

        # Execute and verify exception
        with pytest.raises(AutomationNotFoundError):
            update_automation_rule(
                client=mock_automation_client,
                rule_id='invalid-rule',
                name='New Name'
            )

    def test_update_rule_permission_denied(self, mock_automation_client):
        """Test permission error."""
        from update_automation_rule import update_automation_rule
        from error_handler import AutomationPermissionError

        # Setup mock
        mock_automation_client.update_rule.side_effect = AutomationPermissionError(
            "Cannot update this rule"
        )

        # Execute and verify exception
        with pytest.raises(AutomationPermissionError):
            update_automation_rule(
                client=mock_automation_client,
                rule_id='ari:cloud:jira::site/12345-rule-001',
                name='New Name'
            )


class TestUpdateAutomationRuleDryRun:
    """Test dry-run mode for update operations."""

    def test_update_rule_dry_run(self, mock_automation_client, sample_rule_detail):
        """Test dry-run mode shows preview without changes."""
        from update_automation_rule import update_automation_rule

        # Setup mock - get_rule returns the current state for preview
        mock_automation_client.get_rule.return_value = sample_rule_detail

        # Execute with dry_run
        result = update_automation_rule(
            client=mock_automation_client,
            rule_id='ari:cloud:jira::site/12345-rule-001',
            name='New Rule Name',
            dry_run=True
        )

        # Verify no actual update was called
        mock_automation_client.update_rule.assert_not_called()
        # Result should indicate dry run
        assert result.get('dry_run') is True
        assert result.get('would_update') is True
        assert result.get('rule_id') == 'ari:cloud:jira::site/12345-rule-001'
        assert result.get('current_name') == sample_rule_detail.get('name')
        assert 'name' in result.get('updates', {})
        assert result['updates']['name'] == 'New Rule Name'

    def test_update_rule_dry_run_with_description(self, mock_automation_client, sample_rule_detail):
        """Test dry-run includes description updates."""
        from update_automation_rule import update_automation_rule

        # Setup mock
        mock_automation_client.get_rule.return_value = sample_rule_detail

        # Execute with dry_run
        result = update_automation_rule(
            client=mock_automation_client,
            rule_id='ari:cloud:jira::site/12345-rule-001',
            description='Updated description',
            dry_run=True
        )

        # Verify updates include description
        assert result.get('dry_run') is True
        assert 'description' in result.get('updates', {})
        assert result['updates']['description'] == 'Updated description'
        assert result.get('current_description') == sample_rule_detail.get('description')

    def test_update_rule_dry_run_with_config(self, mock_automation_client, sample_rule_detail):
        """Test dry-run with full config object."""
        from update_automation_rule import update_automation_rule

        # Setup mock
        mock_automation_client.get_rule.return_value = sample_rule_detail

        # Config to update
        config = {
            'name': 'Config Updated Name',
            'description': 'Config Updated Description'
        }

        # Execute with dry_run
        result = update_automation_rule(
            client=mock_automation_client,
            rule_id='ari:cloud:jira::site/12345-rule-001',
            config=config,
            dry_run=True
        )

        # Verify no actual update was called
        mock_automation_client.update_rule.assert_not_called()
        # Result should show the config updates
        assert result.get('dry_run') is True
        assert result.get('updates') == config
