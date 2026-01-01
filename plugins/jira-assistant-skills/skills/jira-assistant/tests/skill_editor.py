#!/usr/bin/env python3
"""SKILL.md parsing and modification utilities."""

import re
import shutil
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass


@dataclass
class SkillContent:
    """Parsed content of a SKILL.md file."""
    frontmatter: dict[str, str]
    body: str
    raw_frontmatter: str
    file_path: Path

    @property
    def description(self) -> str:
        """Get the description from frontmatter."""
        return self.frontmatter.get("description", "")

    @property
    def when_to_use_section(self) -> str | None:
        """Extract the 'When to use this skill' section."""
        # Look for section header variations
        patterns = [
            r"##\s*When to use this skill\s*\n(.*?)(?=\n##|\Z)",
            r"##\s*When to Use This Skill\s*\n(.*?)(?=\n##|\Z)",
            r"##\s*When to use\s*\n(.*?)(?=\n##|\Z)",
        ]

        for pattern in patterns:
            match = re.search(pattern, self.body, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None


class SkillEditor:
    """Editor for SKILL.md files with backup/restore support."""

    SKILLS_BASE_PATH = Path(__file__).parent.parent.parent  # skills/ directory
    BACKUP_DIR = Path(__file__).parent / ".skill_backups"

    def __init__(self, skills_base_path: Path | None = None):
        """Initialize skill editor.

        Args:
            skills_base_path: Base path to skills directory. If None, uses default.
        """
        self.skills_base_path = skills_base_path or self.SKILLS_BASE_PATH
        self.backup_stack: list[tuple[str, Path]] = []  # (skill_name, backup_path)

    def get_skill_path(self, skill_name: str) -> Path:
        """Get the path to a skill's SKILL.md file."""
        # Handle skill names with or without 'jira-' prefix
        if not skill_name.startswith("jira-"):
            skill_name = f"jira-{skill_name}"

        skill_dir = self.skills_base_path / skill_name
        skill_md = skill_dir / "SKILL.md"

        if not skill_md.exists():
            raise FileNotFoundError(f"SKILL.md not found for {skill_name} at {skill_md}")

        return skill_md

    def parse_skill(self, skill_name: str) -> SkillContent:
        """Parse a SKILL.md file.

        Args:
            skill_name: Name of the skill (e.g., 'jira-issue' or 'issue')

        Returns:
            Parsed skill content
        """
        skill_path = self.get_skill_path(skill_name)
        content = skill_path.read_text()

        # Parse YAML frontmatter
        frontmatter = {}
        raw_frontmatter = ""
        body = content

        if content.startswith("---"):
            # Find the closing ---
            end_match = re.search(r"\n---\s*\n", content[3:])
            if end_match:
                end_pos = end_match.end() + 3
                raw_frontmatter = content[3:end_match.start() + 3].strip()
                body = content[end_pos:]

                # Parse frontmatter (simple key: value parsing)
                for line in raw_frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip()
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        frontmatter[key] = value

        return SkillContent(
            frontmatter=frontmatter,
            body=body,
            raw_frontmatter=raw_frontmatter,
            file_path=skill_path,
        )

    def backup_skill(self, skill_name: str) -> Path:
        """Create a backup of a skill's SKILL.md file.

        Args:
            skill_name: Name of the skill

        Returns:
            Path to the backup file
        """
        skill_path = self.get_skill_path(skill_name)

        # Ensure backup directory exists
        self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_name = f"{skill_name}_{timestamp}.md"
        backup_path = self.BACKUP_DIR / backup_name

        shutil.copy2(skill_path, backup_path)
        self.backup_stack.append((skill_name, backup_path))

        return backup_path

    def restore_skill(self, skill_name: str | None = None) -> bool:
        """Restore a skill from the most recent backup.

        Args:
            skill_name: Specific skill to restore. If None, restores the most recent backup.

        Returns:
            True if restored successfully, False if no backup found
        """
        if not self.backup_stack:
            return False

        if skill_name is None:
            # Pop the most recent backup
            name, backup_path = self.backup_stack.pop()
        else:
            # Find the most recent backup for this skill
            for i in range(len(self.backup_stack) - 1, -1, -1):
                name, backup_path = self.backup_stack[i]
                if name == skill_name:
                    self.backup_stack.pop(i)
                    break
            else:
                return False

        skill_path = self.get_skill_path(name)
        shutil.copy2(backup_path, skill_path)

        return True

    def restore_all(self) -> int:
        """Restore all skills from backups.

        Returns:
            Number of skills restored
        """
        count = 0
        while self.backup_stack:
            if self.restore_skill():
                count += 1
        return count

    def update_frontmatter(
        self,
        skill_name: str,
        updates: dict[str, str],
        backup: bool = True,
    ) -> SkillContent:
        """Update frontmatter fields in a SKILL.md file.

        Args:
            skill_name: Name of the skill
            updates: Dictionary of field updates
            backup: Whether to create a backup first

        Returns:
            Updated skill content
        """
        if backup:
            self.backup_skill(skill_name)

        skill = self.parse_skill(skill_name)
        content = skill.file_path.read_text()

        for key, value in updates.items():
            # Escape special characters in the value for YAML
            escaped_value = value.replace('"', '\\"')

            # Check if key exists in frontmatter
            if key in skill.frontmatter:
                old_value = skill.frontmatter[key]
                # Replace the existing value
                # Handle both quoted and unquoted values
                patterns = [
                    (f'{key}: "{re.escape(old_value)}"', f'{key}: "{escaped_value}"'),
                    (f"{key}: '{re.escape(old_value)}'", f'{key}: "{escaped_value}"'),
                    (f"{key}: {re.escape(old_value)}", f'{key}: "{escaped_value}"'),
                ]
                for old_pattern, new_pattern in patterns:
                    if old_pattern in content:
                        content = content.replace(old_pattern, new_pattern, 1)
                        break
            else:
                # Add new field after the opening ---
                content = content.replace(
                    "---\n",
                    f'---\n{key}: "{escaped_value}"\n',
                    1,
                )

        skill.file_path.write_text(content)
        return self.parse_skill(skill_name)

    def update_section(
        self,
        skill_name: str,
        section_header: str,
        new_content: str,
        action: str = "replace",
        backup: bool = True,
    ) -> SkillContent:
        """Update a section in the SKILL.md body.

        Args:
            skill_name: Name of the skill
            section_header: Header of the section (e.g., "When to use this skill")
            new_content: New content for the section
            action: "replace", "append", or "prepend"
            backup: Whether to create a backup first

        Returns:
            Updated skill content
        """
        if backup:
            self.backup_skill(skill_name)

        skill = self.parse_skill(skill_name)
        content = skill.file_path.read_text()

        # Find the section
        pattern = rf"(##\s*{re.escape(section_header)}\s*\n)(.*?)(\n##|\Z)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

        if match:
            header = match.group(1)
            old_content = match.group(2)
            next_section = match.group(3)

            if action == "replace":
                new_section_content = new_content
            elif action == "append":
                new_section_content = old_content.rstrip() + "\n" + new_content
            elif action == "prepend":
                new_section_content = new_content + "\n" + old_content.lstrip()
            else:
                raise ValueError(f"Unknown action: {action}")

            # Ensure proper spacing
            if not new_section_content.startswith("\n"):
                new_section_content = "\n" + new_section_content
            if not new_section_content.endswith("\n"):
                new_section_content = new_section_content + "\n"

            new_full_section = header + new_section_content + next_section
            content = content[:match.start()] + new_full_section + content[match.end():]
        else:
            raise ValueError(f"Section '{section_header}' not found in {skill_name}")

        skill.file_path.write_text(content)
        return self.parse_skill(skill_name)

    def apply_change(
        self,
        skill_name: str,
        section: str,
        action: str,
        old_text: str | None,
        new_text: str,
        backup: bool = True,
    ) -> SkillContent:
        """Apply a change from Claude's fix proposal.

        Args:
            skill_name: Name of the skill
            section: "frontmatter" or "when_to_use" or section header
            action: "replace", "append", or "prepend"
            old_text: Text to find (for replace action)
            new_text: New text
            backup: Whether to create a backup first

        Returns:
            Updated skill content
        """
        if section == "frontmatter":
            # For frontmatter, treat new_text as the new description
            return self.update_frontmatter(
                skill_name,
                {"description": new_text},
                backup=backup,
            )
        elif section in ("when_to_use", "When to use this skill"):
            section_header = "When to use this skill"
            return self.update_section(
                skill_name,
                section_header,
                new_text,
                action=action,
                backup=backup,
            )
        else:
            # Treat section as a section header
            return self.update_section(
                skill_name,
                section,
                new_text,
                action=action,
                backup=backup,
            )

    def apply_changes(
        self,
        changes: list[dict],
        backup: bool = True,
    ) -> list[SkillContent]:
        """Apply multiple changes from Claude's fix proposal.

        Args:
            changes: List of change dictionaries with keys:
                - skill: skill name
                - section: "frontmatter" or section header
                - action: "replace", "append", "prepend"
                - old_text: text to find (for replace)
                - new_text: new text

        Returns:
            List of updated skill contents
        """
        results = []
        backed_up_skills = set()

        for change in changes:
            skill_name = change["skill"]
            should_backup = backup and skill_name not in backed_up_skills

            result = self.apply_change(
                skill_name=skill_name,
                section=change["section"],
                action=change.get("action", "replace"),
                old_text=change.get("old_text"),
                new_text=change["new_text"],
                backup=should_backup,
            )
            results.append(result)

            if should_backup:
                backed_up_skills.add(skill_name)

        return results

    def get_all_skill_names(self) -> list[str]:
        """Get list of all available skill names."""
        skills = []
        for skill_dir in self.skills_base_path.iterdir():
            if skill_dir.is_dir() and skill_dir.name.startswith("jira-"):
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    skills.append(skill_dir.name)
        return sorted(skills)

    def cleanup_backups(self, keep_latest: int = 0) -> int:
        """Clean up old backups.

        Args:
            keep_latest: Number of latest backups to keep per skill. 0 = delete all.

        Returns:
            Number of backups deleted
        """
        if not self.BACKUP_DIR.exists():
            return 0

        deleted = 0
        if keep_latest == 0:
            # Delete all
            for backup_file in self.BACKUP_DIR.glob("*.md"):
                backup_file.unlink()
                deleted += 1
            self.backup_stack.clear()
        else:
            # Group by skill and keep latest N
            skill_backups: dict[str, list[Path]] = {}
            for backup_file in self.BACKUP_DIR.glob("*.md"):
                # Extract skill name from filename
                skill_name = "_".join(backup_file.stem.split("_")[:-3])  # Remove timestamp
                if skill_name not in skill_backups:
                    skill_backups[skill_name] = []
                skill_backups[skill_name].append(backup_file)

            for skill_name, backups in skill_backups.items():
                # Sort by modification time, newest first
                backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                for backup in backups[keep_latest:]:
                    backup.unlink()
                    deleted += 1
                    # Remove from stack if present
                    self.backup_stack = [
                        (n, p) for n, p in self.backup_stack if p != backup
                    ]

        return deleted
