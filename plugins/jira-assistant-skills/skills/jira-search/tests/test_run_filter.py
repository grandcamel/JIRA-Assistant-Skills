"""
Tests for run_filter.py - Run saved JIRA filters.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.fixture
def sample_search_results():
    """Sample search results from running a filter."""
    return {
        "issues": [
            {
                "key": "PROJ-123",
                "fields": {
                    "summary": "Test issue 1",
                    "status": {"name": "Open"},
                    "priority": {"name": "High"},
                },
            },
            {
                "key": "PROJ-124",
                "fields": {
                    "summary": "Test issue 2",
                    "status": {"name": "In Progress"},
                    "priority": {"name": "Medium"},
                },
            },
        ],
        "total": 2,
    }


@pytest.mark.search
@pytest.mark.unit
class TestRunFilterById:
    """Tests for running filters by ID."""

    def test_run_filter_by_id_success(
        self, mock_jira_client, sample_filter, sample_search_results
    ):
        """Test running a filter by ID."""
        mock_jira_client.get.return_value = sample_filter
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch("run_filter.get_jira_client", return_value=mock_jira_client):
            from run_filter import run_filter

            result = run_filter(filter_id="10042")

            assert result["total"] == 2
            assert len(result["issues"]) == 2
            mock_jira_client.get.assert_called_once()
            mock_jira_client.search_issues.assert_called_once()

    def test_run_filter_by_id_with_max_results(
        self, mock_jira_client, sample_filter, sample_search_results
    ):
        """Test running a filter with custom max results."""
        mock_jira_client.get.return_value = sample_filter
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch("run_filter.get_jira_client", return_value=mock_jira_client):
            from run_filter import run_filter

            run_filter(filter_id="10042", max_results=100)

            mock_jira_client.search_issues.assert_called_with(
                sample_filter["jql"], max_results=100
            )

    def test_run_filter_empty_jql_raises_error(self, mock_jira_client):
        """Test that a filter with no JQL raises an error."""
        mock_jira_client.get.return_value = {
            "id": "10042",
            "name": "Empty Filter",
            "jql": "",
        }

        with patch("run_filter.get_jira_client", return_value=mock_jira_client):
            from run_filter import run_filter

            from jira_assistant_skills_lib import ValidationError

            with pytest.raises(ValidationError) as exc_info:
                run_filter(filter_id="10042")
            assert "no JQL" in str(exc_info.value)


@pytest.mark.search
@pytest.mark.unit
class TestRunFilterByName:
    """Tests for running filters by name."""

    def test_run_filter_by_name_success(
        self, mock_jira_client, sample_filter_list, sample_filter, sample_search_results
    ):
        """Test running a filter by name."""
        mock_jira_client.get.side_effect = [
            sample_filter_list,  # First call: get list of filters
            sample_filter,  # Second call: get specific filter
        ]
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch("run_filter.get_jira_client", return_value=mock_jira_client):
            from run_filter import run_filter

            result = run_filter(filter_name="My Bugs")

            assert result["total"] == 2

    def test_run_filter_by_name_case_insensitive(
        self, mock_jira_client, sample_filter_list, sample_filter, sample_search_results
    ):
        """Test that filter name matching is case insensitive."""
        mock_jira_client.get.side_effect = [sample_filter_list, sample_filter]
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch("run_filter.get_jira_client", return_value=mock_jira_client):
            from run_filter import run_filter

            result = run_filter(filter_name="MY BUGS")

            assert result["total"] == 2

    def test_run_filter_by_name_not_found(self, mock_jira_client, sample_filter_list):
        """Test error when filter name not found."""
        mock_jira_client.get.return_value = sample_filter_list

        with patch("run_filter.get_jira_client", return_value=mock_jira_client):
            from run_filter import run_filter

            from jira_assistant_skills_lib import ValidationError

            with pytest.raises(ValidationError) as exc_info:
                run_filter(filter_name="Nonexistent Filter")
            assert "not found" in str(exc_info.value)


@pytest.mark.search
@pytest.mark.unit
class TestRunFilterValidation:
    """Tests for input validation."""

    def test_no_id_or_name_raises_error(self):
        """Test that either ID or name must be specified."""
        from run_filter import run_filter

        from jira_assistant_skills_lib import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            run_filter()
        assert "--id" in str(exc_info.value) or "--name" in str(exc_info.value)


@pytest.mark.search
@pytest.mark.unit
class TestRunFilterMain:
    """Tests for main() function and CLI."""

    def test_main_with_id(
        self, mock_jira_client, sample_filter, sample_search_results, capsys
    ):
        """Test main function with filter ID."""
        mock_jira_client.get.return_value = sample_filter
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch("run_filter.get_jira_client", return_value=mock_jira_client):
            from run_filter import main

            result = main(["--id", "10042"])

            assert result is None  # Success returns None
            captured = capsys.readouterr()
            assert "Found 2 issue" in captured.out

    def test_main_with_name(
        self,
        mock_jira_client,
        sample_filter_list,
        sample_filter,
        sample_search_results,
        capsys,
    ):
        """Test main function with filter name."""
        mock_jira_client.get.side_effect = [sample_filter_list, sample_filter]
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch("run_filter.get_jira_client", return_value=mock_jira_client):
            from run_filter import main

            result = main(["--name", "My Bugs"])

            assert result is None
            captured = capsys.readouterr()
            assert "Found 2 issue" in captured.out

    def test_main_json_output(
        self, mock_jira_client, sample_filter, sample_search_results, capsys
    ):
        """Test main function with JSON output."""
        mock_jira_client.get.return_value = sample_filter
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch("run_filter.get_jira_client", return_value=mock_jira_client):
            import json

            from run_filter import main

            main(["--id", "10042", "--output", "json"])

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output["total"] == 2

    def test_main_with_max_results(
        self, mock_jira_client, sample_filter, sample_search_results
    ):
        """Test main function with max results parameter."""
        mock_jira_client.get.return_value = sample_filter
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch("run_filter.get_jira_client", return_value=mock_jira_client):
            from run_filter import main

            main(["--id", "10042", "--max-results", "25"])

            mock_jira_client.search_issues.assert_called_with(
                sample_filter["jql"], max_results=25
            )

    def test_main_with_profile(
        self, mock_jira_client, sample_filter, sample_search_results
    ):
        """Test main function with profile parameter."""
        mock_jira_client.get.return_value = sample_filter
        mock_jira_client.search_issues.return_value = sample_search_results

        with patch(
            "run_filter.get_jira_client", return_value=mock_jira_client
        ) as mock_get_client:
            from run_filter import main

            main(["--id", "10042", "--profile", "development"])

            mock_get_client.assert_called_with("development")


@pytest.mark.search
@pytest.mark.unit
class TestRunFilterErrors:
    """Tests for error handling."""

    def test_jira_error_handling(self, mock_jira_client):
        """Test handling of JIRA API errors."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get.side_effect = JiraError("API Error", status_code=500)

        with patch("run_filter.get_jira_client", return_value=mock_jira_client):
            from run_filter import main

            with pytest.raises(SystemExit) as exc_info:
                main(["--id", "10042"])
            assert exc_info.value.code == 1

    def test_filter_not_found_error(self, mock_jira_client):
        """Test handling of filter not found error."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get.side_effect = NotFoundError("Filter 99999 not found")

        with patch("run_filter.get_jira_client", return_value=mock_jira_client):
            from run_filter import main

            with pytest.raises(SystemExit) as exc_info:
                main(["--id", "99999"])
            assert exc_info.value.code == 1

    def test_invalid_filter_list_response(self, mock_jira_client):
        """Test handling when filter list is not a list."""
        mock_jira_client.get.return_value = {"error": "unexpected format"}

        with patch("run_filter.get_jira_client", return_value=mock_jira_client):
            from run_filter import run_filter

            from jira_assistant_skills_lib import ValidationError

            with pytest.raises(ValidationError) as exc_info:
                run_filter(filter_name="My Filter")
            assert "Could not retrieve" in str(exc_info.value)
