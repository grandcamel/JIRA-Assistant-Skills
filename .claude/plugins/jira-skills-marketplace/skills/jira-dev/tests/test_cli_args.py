"""
CLI Argument Parsing Tests for jira-dev skill.

Tests verify that argparse configurations are correct and handle
various input combinations properly.
"""

import pytest
import sys
import argparse
from pathlib import Path
from unittest.mock import patch, Mock

# Add scripts path
scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.mark.dev
@pytest.mark.unit
class TestCreateBranchNameCLI:
    """CLI argument tests for create_branch_name.py."""

    def test_required_issue_key(self):
        """Test that issue_key is required."""
        import create_branch_name

        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.argv', ['create_branch_name.py']):
                create_branch_name.main()

        assert exc_info.value.code == 2  # argparse error code

    def test_valid_prefix_choices(self):
        """Test valid prefix choices are accepted."""
        import create_branch_name

        valid_prefixes = ['feature', 'bugfix', 'hotfix', 'task', 'epic', 'spike', 'chore', 'docs']

        for prefix in valid_prefixes:
            with patch('sys.argv', ['create_branch_name.py', 'PROJ-123', '--prefix', prefix]):
                with patch.object(create_branch_name, 'get_jira_client') as mock_client:
                    mock_client.return_value.get_issue.return_value = {
                        'key': 'PROJ-123',
                        'fields': {'summary': 'Test', 'issuetype': {'name': 'Bug'}}
                    }
                    mock_client.return_value.close = Mock()
                    # Should not raise
                    try:
                        create_branch_name.main()
                    except SystemExit as e:
                        if e.code == 2:
                            pytest.fail(f"Prefix '{prefix}' should be valid")

    def test_invalid_prefix_rejected(self):
        """Test invalid prefix is rejected."""
        import create_branch_name

        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.argv', ['create_branch_name.py', 'PROJ-123', '--prefix', 'invalid']):
                create_branch_name.main()

        assert exc_info.value.code == 2

    def test_output_format_choices(self):
        """Test output format choices."""
        import create_branch_name

        valid_outputs = ['text', 'json', 'git']

        for output in valid_outputs:
            with patch('sys.argv', ['create_branch_name.py', 'PROJ-123', '--output', output]):
                with patch.object(create_branch_name, 'get_jira_client') as mock_client:
                    mock_client.return_value.get_issue.return_value = {
                        'key': 'PROJ-123',
                        'fields': {'summary': 'Test', 'issuetype': {'name': 'Bug'}}
                    }
                    mock_client.return_value.close = Mock()
                    try:
                        create_branch_name.main()
                    except SystemExit as e:
                        if e.code == 2:
                            pytest.fail(f"Output format '{output}' should be valid")

    def test_auto_prefix_flag(self):
        """Test auto-prefix flag is recognized."""
        import create_branch_name

        with patch('sys.argv', ['create_branch_name.py', 'PROJ-123', '--auto-prefix']):
            with patch.object(create_branch_name, 'get_jira_client') as mock_client:
                mock_client.return_value.get_issue.return_value = {
                    'key': 'PROJ-123',
                    'fields': {'summary': 'Test', 'issuetype': {'name': 'Bug'}}
                }
                mock_client.return_value.close = Mock()
                try:
                    create_branch_name.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("--auto-prefix should be valid")

    def test_short_options(self):
        """Test short option forms work."""
        import create_branch_name

        with patch('sys.argv', ['create_branch_name.py', 'PROJ-123', '-p', 'bugfix', '-o', 'json', '-a']):
            with patch.object(create_branch_name, 'get_jira_client') as mock_client:
                mock_client.return_value.get_issue.return_value = {
                    'key': 'PROJ-123',
                    'fields': {'summary': 'Test', 'issuetype': {'name': 'Bug'}}
                }
                mock_client.return_value.close = Mock()
                try:
                    create_branch_name.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("Short options should be valid")


@pytest.mark.dev
@pytest.mark.unit
class TestParseCommitIssuesCLI:
    """CLI argument tests for parse_commit_issues.py."""

    def test_required_message(self):
        """Test that message argument is required (or --from-stdin)."""
        import parse_commit_issues

        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.argv', ['parse_commit_issues.py']):
                parse_commit_issues.main()

        # Script prints help and exits with code 1 when no message or --from-stdin
        assert exc_info.value.code == 1

    def test_message_positional_arg(self):
        """Test message is accepted as positional argument."""
        import parse_commit_issues

        with patch('sys.argv', ['parse_commit_issues.py', 'PROJ-123: Fix bug']):
            # Should not raise argparse error
            try:
                parse_commit_issues.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("Message argument should be accepted")

    def test_project_filter_option(self):
        """Test project filter option."""
        import parse_commit_issues

        with patch('sys.argv', ['parse_commit_issues.py', 'PROJ-123: Fix bug', '--project', 'PROJ']):
            try:
                parse_commit_issues.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("--project option should be valid")

    def test_output_format_choices(self):
        """Test output format choices."""
        import parse_commit_issues

        for fmt in ['text', 'json']:
            with patch('sys.argv', ['parse_commit_issues.py', 'PROJ-123: Fix', '--output', fmt]):
                try:
                    parse_commit_issues.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail(f"Output format '{fmt}' should be valid")


@pytest.mark.dev
@pytest.mark.unit
class TestLinkCommitCLI:
    """CLI argument tests for link_commit.py."""

    def test_required_args(self):
        """Test required arguments."""
        import link_commit

        # Missing all required args
        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.argv', ['link_commit.py']):
                link_commit.main()
        assert exc_info.value.code == 2

        # Missing commit_sha
        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.argv', ['link_commit.py', 'PROJ-123']):
                link_commit.main()
        assert exc_info.value.code == 2

    def test_all_required_args_present(self):
        """Test all required arguments are accepted."""
        import link_commit

        with patch('sys.argv', ['link_commit.py', 'PROJ-123', '--commit', 'abc123def']):
            with patch.object(link_commit, 'get_jira_client') as mock_client:
                mock_client.return_value.post.return_value = {'id': '10001'}
                mock_client.return_value.close = Mock()
                try:
                    link_commit.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("Required args should be accepted")

    def test_optional_message_and_repo(self):
        """Test optional --message and --repo options."""
        import link_commit

        with patch('sys.argv', [
            'link_commit.py', 'PROJ-123', '--commit', 'abc123def',
            '--message', 'Fix login bug',
            '--repo', 'https://github.com/org/repo'
        ]):
            with patch.object(link_commit, 'get_jira_client') as mock_client:
                mock_client.return_value.post.return_value = {'id': '10001'}
                mock_client.return_value.close = Mock()
                try:
                    link_commit.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("Optional args should be accepted")


@pytest.mark.dev
@pytest.mark.unit
class TestLinkPRCLI:
    """CLI argument tests for link_pr.py."""

    def test_required_args(self):
        """Test required arguments."""
        import link_pr

        # Missing required args
        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.argv', ['link_pr.py']):
                link_pr.main()
        assert exc_info.value.code == 2

    def test_issue_key_and_pr_url_required(self):
        """Test issue_key and pr_url are required."""
        import link_pr

        with patch('sys.argv', ['link_pr.py', 'PROJ-123', '--pr', 'https://github.com/org/repo/pull/456']):
            with patch.object(link_pr, 'get_jira_client') as mock_client:
                mock_client.return_value.post.return_value = {'id': '10001'}
                mock_client.return_value.close = Mock()
                try:
                    link_pr.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("Required args should be accepted")

    def test_status_choices(self):
        """Test status choices."""
        import link_pr

        for status in ['open', 'merged', 'closed']:
            with patch('sys.argv', [
                'link_pr.py', 'PROJ-123',
                '--pr', 'https://github.com/org/repo/pull/456',
                '--status', status
            ]):
                with patch.object(link_pr, 'get_jira_client') as mock_client:
                    mock_client.return_value.post.return_value = {'id': '10001'}
                    mock_client.return_value.close = Mock()
                    try:
                        link_pr.main()
                    except SystemExit as e:
                        if e.code == 2:
                            pytest.fail(f"Status '{status}' should be valid")


@pytest.mark.dev
@pytest.mark.unit
class TestCreatePRDescriptionCLI:
    """CLI argument tests for create_pr_description.py."""

    def test_required_issue_key(self):
        """Test issue_key is required."""
        import create_pr_description

        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.argv', ['create_pr_description.py']):
                create_pr_description.main()
        assert exc_info.value.code == 2

    def test_optional_flags(self):
        """Test optional flags are recognized."""
        import create_pr_description

        with patch('sys.argv', [
            'create_pr_description.py', 'PROJ-123',
            '--include-checklist', '--include-labels'
        ]):
            with patch.object(create_pr_description, 'get_jira_client') as mock_client:
                mock_client.return_value.get_issue.return_value = {
                    'key': 'PROJ-123',
                    'fields': {
                        'summary': 'Test',
                        'description': None,
                        'labels': ['label1']
                    }
                }
                mock_client.return_value.close = Mock()
                try:
                    create_pr_description.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("Optional flags should be accepted")

    def test_output_format_choices(self):
        """Test output format choices."""
        import create_pr_description

        # Implementation only supports 'text' and 'json' (not 'markdown')
        for fmt in ['text', 'json']:
            with patch('sys.argv', ['create_pr_description.py', 'PROJ-123', '--output', fmt]):
                with patch.object(create_pr_description, 'get_jira_client') as mock_client:
                    mock_client.return_value.get_issue.return_value = {
                        'key': 'PROJ-123',
                        'fields': {
                            'summary': 'Test',
                            'description': None,
                            'labels': []
                        }
                    }
                    mock_client.return_value.close = Mock()
                    try:
                        create_pr_description.main()
                    except SystemExit as e:
                        if e.code == 2:
                            pytest.fail(f"Output format '{fmt}' should be valid")
