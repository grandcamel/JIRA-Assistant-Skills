#!/usr/bin/env python3
"""Claude CLI interaction for analyzing test failures and generating fixes."""

import json
import re
import subprocess
import logging
from dataclasses import dataclass
from pathlib import Path

from skill_editor import SkillEditor


logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """Information about a test case."""
    test_id: str
    input_text: str
    expected_skill: str
    actual_skill: str | None = None
    response_text: str | None = None
    category: str | None = None


@dataclass
class FixProposal:
    """A proposed fix from Claude."""
    analysis: str
    fix_target: str  # "expected", "actual", or "both"
    changes: list[dict]
    raw_response: str


class ClaudeAnalyzer:
    """Interacts with Claude CLI to analyze failures and propose fixes."""

    def __init__(
        self,
        skill_editor: SkillEditor | None = None,
        model: str = "haiku",
        timeout: int = 120,
    ):
        """Initialize Claude analyzer.

        Args:
            skill_editor: SkillEditor instance for reading SKILL.md files
            model: Claude model to use for analysis
            timeout: Timeout in seconds for Claude CLI calls
        """
        self.skill_editor = skill_editor or SkillEditor()
        self.model = model
        self.timeout = timeout

    def _run_claude(self, prompt: str) -> str:
        """Run Claude CLI with the given prompt.

        Args:
            prompt: The prompt to send to Claude

        Returns:
            Claude's response text
        """
        cmd = [
            "claude",
            "--print",
            "--model", self.model,
            "--permission-mode", "dontAsk",
            prompt,
        ]

        logger.debug(f"Running Claude CLI: {' '.join(cmd[:5])}...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )

        if result.returncode != 0:
            logger.error(f"Claude CLI error: {result.stderr}")
            raise RuntimeError(f"Claude CLI failed: {result.stderr}")

        return result.stdout

    def _extract_json(self, response: str) -> dict:
        """Extract JSON from Claude's response.

        Args:
            response: Claude's full response text

        Returns:
            Parsed JSON dictionary
        """
        # Try to find JSON block
        json_patterns = [
            r"```json\s*\n(.*?)\n```",
            r"```\s*\n(\{.*?\})\n```",
            r"(\{[^{}]*\"analysis\"[^{}]*\})",
        ]

        for pattern in json_patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue

        # Try to parse the entire response as JSON
        try:
            # Find the first { and last }
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass

        raise ValueError(f"Could not extract JSON from response: {response[:500]}...")

    def _get_skill_context(self, skill_name: str) -> str:
        """Get the SKILL.md content for a skill."""
        try:
            skill = self.skill_editor.parse_skill(skill_name)
            return f"""SKILL.md for {skill_name}:
---
{skill.raw_frontmatter}
---
{skill.body[:2000]}...
"""
        except FileNotFoundError:
            return f"(SKILL.md not found for {skill_name})"

    def analyze_failure(self, test_case: TestCase) -> FixProposal:
        """Analyze a test failure and propose a fix.

        Args:
            test_case: The failing test case

        Returns:
            A fix proposal from Claude
        """
        expected_context = self._get_skill_context(test_case.expected_skill)

        actual_context = ""
        if test_case.actual_skill and test_case.actual_skill != test_case.expected_skill:
            actual_context = self._get_skill_context(test_case.actual_skill)

        prompt = f'''You are a skills routing test engineer. Analyze this failing routing test and propose a fix.

TEST CASE:
- Test ID: {test_case.test_id}
- Category: {test_case.category or "unknown"}
- Input text: "{test_case.input_text}"
- Expected skill: {test_case.expected_skill}
- Actual skill routed to: {test_case.actual_skill or "none"}
- Response excerpt: {(test_case.response_text or "")[:500]}

CURRENT SKILL DEFINITIONS:

{expected_context}

{actual_context}

TASK:
Analyze why routing failed and propose minimal changes to fix it. The goal is to make the expected skill ({test_case.expected_skill}) be selected for this input.

Consider:
1. Is the description in frontmatter specific enough?
2. Does "When to use this skill" section cover this use case?
3. If actual skill was incorrectly matched, should its description be narrowed?

Output ONLY valid JSON (no other text):
{{
  "analysis": "Brief explanation of why routing failed",
  "fix_target": "expected|actual|both",
  "changes": [
    {{
      "skill": "jira-skillname",
      "section": "frontmatter|when_to_use",
      "action": "replace|append|prepend",
      "old_text": "text to find (only for replace action, can be empty)",
      "new_text": "new text to add or replace with"
    }}
  ]
}}'''

        response = self._run_claude(prompt)
        logger.debug(f"Claude response for {test_case.test_id}: {response[:500]}...")

        try:
            data = self._extract_json(response)
        except ValueError as e:
            logger.error(f"Failed to parse Claude response: {e}")
            # Return a default proposal to retry
            return FixProposal(
                analysis=f"Failed to parse response: {str(e)}",
                fix_target="expected",
                changes=[],
                raw_response=response,
            )

        return FixProposal(
            analysis=data.get("analysis", ""),
            fix_target=data.get("fix_target", "expected"),
            changes=data.get("changes", []),
            raw_response=response,
        )

    def resolve_conflict(
        self,
        test_a: TestCase,
        test_a_fix: FixProposal,
        test_b: TestCase,
    ) -> FixProposal:
        """Propose a fix that resolves a conflict between two tests.

        When fixing test A causes test B to fail, this generates a fix
        that should satisfy both tests.

        Args:
            test_a: The test that was fixed
            test_a_fix: The fix that was applied to test A
            test_b: The test that regressed

        Returns:
            A fix proposal that should work for both tests
        """
        # Get all relevant skill contexts
        skills = {test_a.expected_skill, test_b.expected_skill}
        if test_a.actual_skill:
            skills.add(test_a.actual_skill)
        if test_b.actual_skill:
            skills.add(test_b.actual_skill)

        skill_contexts = "\n\n".join(
            self._get_skill_context(skill) for skill in skills if skill
        )

        prompt = f'''You are a skills routing test engineer resolving a conflict between two tests.

SITUATION:
Fixing Test A caused Test B to regress. We need a solution that works for BOTH tests.

TEST A (was failing, fix was applied):
- Test ID: {test_a.test_id}
- Input text: "{test_a.input_text}"
- Expected skill: {test_a.expected_skill}
- Previous analysis: {test_a_fix.analysis}
- Fix that was applied: {json.dumps(test_a_fix.changes, indent=2)}

TEST B (now failing due to Test A's fix):
- Test ID: {test_b.test_id}
- Input text: "{test_b.input_text}"
- Expected skill: {test_b.expected_skill}
- Actual skill (wrong): {test_b.actual_skill or "none"}

CURRENT SKILL DEFINITIONS:

{skill_contexts}

TASK:
Propose changes that will make BOTH tests pass. You may need to:
1. Make skill descriptions more specific to avoid overlap
2. Add distinguishing keywords or patterns
3. Narrow one skill's scope while expanding another's

Output ONLY valid JSON (no other text):
{{
  "analysis": "Explanation of the conflict and resolution strategy",
  "fix_target": "both",
  "changes": [
    {{
      "skill": "jira-skillname",
      "section": "frontmatter|when_to_use",
      "action": "replace|append|prepend",
      "old_text": "text to find (only for replace action)",
      "new_text": "new text"
    }}
  ]
}}'''

        response = self._run_claude(prompt)
        logger.debug(f"Claude conflict resolution response: {response[:500]}...")

        try:
            data = self._extract_json(response)
        except ValueError as e:
            logger.error(f"Failed to parse conflict resolution response: {e}")
            return FixProposal(
                analysis=f"Failed to parse response: {str(e)}",
                fix_target="both",
                changes=[],
                raw_response=response,
            )

        return FixProposal(
            analysis=data.get("analysis", ""),
            fix_target=data.get("fix_target", "both"),
            changes=data.get("changes", []),
            raw_response=response,
        )

    def generate_alternative_fix(
        self,
        test_case: TestCase,
        previous_attempts: list[FixProposal],
    ) -> FixProposal:
        """Generate an alternative fix after previous attempts failed.

        Args:
            test_case: The failing test case
            previous_attempts: List of previous fix attempts that didn't work

        Returns:
            A new fix proposal
        """
        expected_context = self._get_skill_context(test_case.expected_skill)

        actual_context = ""
        if test_case.actual_skill and test_case.actual_skill != test_case.expected_skill:
            actual_context = self._get_skill_context(test_case.actual_skill)

        # Summarize previous attempts
        attempts_summary = "\n".join(
            f"- Attempt {i+1}: {p.analysis} - Changes: {json.dumps(p.changes)}"
            for i, p in enumerate(previous_attempts)
        )

        prompt = f'''You are a skills routing test engineer. Previous fix attempts have failed. Try a DIFFERENT approach.

TEST CASE:
- Test ID: {test_case.test_id}
- Category: {test_case.category or "unknown"}
- Input text: "{test_case.input_text}"
- Expected skill: {test_case.expected_skill}
- Actual skill routed to: {test_case.actual_skill or "none"}

PREVIOUS FAILED ATTEMPTS:
{attempts_summary}

CURRENT SKILL DEFINITIONS:

{expected_context}

{actual_context}

TASK:
The previous approaches didn't work. Try something DIFFERENT:
1. If you modified frontmatter before, try "When to use" section instead
2. If you added text, try replacing existing text
3. If you only touched the expected skill, try also modifying the actual skill
4. Consider adding negative patterns ("do NOT use for...")
5. Consider more specific trigger words or patterns

Output ONLY valid JSON (no other text):
{{
  "analysis": "Explanation of the new approach",
  "fix_target": "expected|actual|both",
  "changes": [
    {{
      "skill": "jira-skillname",
      "section": "frontmatter|when_to_use",
      "action": "replace|append|prepend",
      "old_text": "text to find (only for replace action)",
      "new_text": "new text"
    }}
  ]
}}'''

        response = self._run_claude(prompt)
        logger.debug(f"Claude alternative fix response: {response[:500]}...")

        try:
            data = self._extract_json(response)
        except ValueError as e:
            logger.error(f"Failed to parse alternative fix response: {e}")
            return FixProposal(
                analysis=f"Failed to parse response: {str(e)}",
                fix_target="expected",
                changes=[],
                raw_response=response,
            )

        return FixProposal(
            analysis=data.get("analysis", ""),
            fix_target=data.get("fix_target", "expected"),
            changes=data.get("changes", []),
            raw_response=response,
        )
