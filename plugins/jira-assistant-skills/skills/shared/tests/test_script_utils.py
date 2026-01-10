"""Tests for shared script utilities."""

import argparse
import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest

# Add scripts path to allow imports
sys.path.insert(0, str(__file__).replace("/tests/test_script_utils.py", "/scripts"))

from script_utils import (
    ScriptResult,
    add_bulk_args,
    add_common_args,
    format_output,
    parse_comma_list,
    parse_json_arg,
    run_script,
    script_main,
)


class TestParseCommaList:
    """Tests for parse_comma_list function."""

    def test_basic_list(self):
        result = parse_comma_list("a,b,c")
        assert result == ["a", "b", "c"]

    def test_with_spaces(self):
        result = parse_comma_list("a, b, c")
        assert result == ["a", "b", "c"]

    def test_extra_spaces(self):
        result = parse_comma_list("  a  ,  b  ,  c  ")
        assert result == ["a", "b", "c"]

    def test_single_item(self):
        result = parse_comma_list("single")
        assert result == ["single"]

    def test_none_input(self):
        result = parse_comma_list(None)
        assert result is None

    def test_empty_string(self):
        result = parse_comma_list("")
        assert result is None

    def test_whitespace_only(self):
        result = parse_comma_list("   ")
        assert result is None

    def test_empty_items_filtered(self):
        result = parse_comma_list("a,,b,  ,c")
        assert result == ["a", "b", "c"]


class TestParseJsonArg:
    """Tests for parse_json_arg function."""

    def test_valid_object(self):
        result = parse_json_arg('{"key": "value"}')
        assert result == {"key": "value"}

    def test_nested_object(self):
        result = parse_json_arg('{"outer": {"inner": 123}}')
        assert result == {"outer": {"inner": 123}}

    def test_none_input(self):
        result = parse_json_arg(None)
        assert result is None

    def test_empty_string(self):
        result = parse_json_arg("")
        assert result is None

    def test_invalid_json(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_json_arg("{invalid}")


class TestAddCommonArgs:
    """Tests for add_common_args function."""

    def test_adds_profile_arg(self):
        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args(["--profile", "test-profile"])
        assert args.profile == "test-profile"

    def test_adds_output_arg(self):
        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args(["--output", "json"])
        assert args.output == "json"

    def test_output_default(self):
        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args([])
        assert args.output == "text"

    def test_output_short_flag(self):
        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args(["-o", "json"])
        assert args.output == "json"


class TestAddBulkArgs:
    """Tests for add_bulk_args function."""

    def test_adds_dry_run(self):
        parser = argparse.ArgumentParser()
        add_bulk_args(parser)
        args = parser.parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_adds_max_issues(self):
        parser = argparse.ArgumentParser()
        add_bulk_args(parser)
        args = parser.parse_args(["--max-issues", "50"])
        assert args.max_issues == 50

    def test_max_issues_default(self):
        parser = argparse.ArgumentParser()
        add_bulk_args(parser)
        args = parser.parse_args([])
        assert args.max_issues == 100

    def test_adds_yes_flag(self):
        parser = argparse.ArgumentParser()
        add_bulk_args(parser)
        args = parser.parse_args(["--yes"])
        assert args.yes is True

    def test_yes_short_flag(self):
        parser = argparse.ArgumentParser()
        add_bulk_args(parser)
        args = parser.parse_args(["-y"])
        assert args.yes is True


class TestFormatOutput:
    """Tests for format_output function."""

    def test_json_output(self, capsys):
        data = {"key": "PROJ-123", "summary": "Test"}
        format_output(data, "json")
        captured = capsys.readouterr()
        assert json.loads(captured.out) == data

    def test_text_with_success_message(self, capsys):
        with patch("script_utils.print_success") as mock_success:
            format_output({"key": "PROJ-123"}, "text", success_message="Created!")
            mock_success.assert_called_once_with("Created!")

    def test_text_with_formatter(self, capsys):
        formatter = lambda x: f"Key: {x['key']}"
        format_output({"key": "PROJ-123"}, "text", text_formatter=formatter)
        captured = capsys.readouterr()
        assert "Key: PROJ-123" in captured.out


class TestRunScript:
    """Tests for run_script function."""

    def test_successful_run(self):
        def main_func(argv=None):
            pass

        # Should not raise
        run_script(main_func)

    def test_jira_error_handling(self):
        from jira_assistant_skills_lib import JiraError

        def main_func(argv=None):
            raise JiraError("Test error", 400)

        with pytest.raises(SystemExit) as exc_info:
            run_script(main_func)
        assert exc_info.value.code == 1

    def test_keyboard_interrupt_handling(self):
        def main_func(argv=None):
            raise KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            run_script(main_func)
        assert exc_info.value.code == 130

    def test_generic_exception_handling(self):
        def main_func(argv=None):
            raise ValueError("Test error")

        with pytest.raises(SystemExit) as exc_info:
            run_script(main_func)
        assert exc_info.value.code == 1


class TestScriptMainDecorator:
    """Tests for script_main decorator."""

    def test_decorator_wraps_function(self):
        @script_main
        def my_main(argv=None):
            pass

        # Should not raise
        my_main()

    def test_decorator_handles_errors(self):
        from jira_assistant_skills_lib import JiraError

        @script_main
        def my_main(argv=None):
            raise JiraError("Test", 400)

        with pytest.raises(SystemExit) as exc_info:
            my_main()
        assert exc_info.value.code == 1


class TestScriptResult:
    """Tests for ScriptResult helper class."""

    def test_set_values(self):
        result = ScriptResult()
        result.set("key", "PROJ-123")
        result.set("summary", "Test")
        assert result.to_dict() == {"key": "PROJ-123", "summary": "Test"}

    def test_method_chaining(self):
        result = ScriptResult().set("a", 1).set("b", 2)
        assert result.to_dict() == {"a": 1, "b": 2}

    def test_add_info(self):
        result = ScriptResult()
        result.set("key", "PROJ-123")
        result.add_info("Info message")
        data = result.to_dict()
        assert data["_info"] == ["Info message"]

    def test_add_warning(self):
        result = ScriptResult()
        result.set("key", "PROJ-123")
        result.add_warning("Warning message")
        data = result.to_dict()
        assert data["_warnings"] == ["Warning message"]

    def test_no_info_or_warnings_when_empty(self):
        result = ScriptResult()
        result.set("key", "PROJ-123")
        data = result.to_dict()
        assert "_info" not in data
        assert "_warnings" not in data
