#!/usr/bin/env python3
"""
Migration script to update imports from vendored library to jira-assistant-skills-lib package.

This script performs in-place modifications:
1. Removes sys.path.insert lines for the shared library
2. Changes 'from module import X' to 'from jira_assistant_skills_lib import X'
"""

import re
import os
from pathlib import Path

# Modules that are part of jira-assistant-skills-lib
SHARED_MODULES = {
    'config_manager',
    'error_handler',
    'validators',
    'formatters',
    'adf_helper',
    'jira_client',
    'time_utils',
    'cache',
    'jsm_utils',
    'credential_manager',
    'project_context',
    'automation_client',
    'transition_helpers',
    'user_helpers',
    'batch_processor',
    'request_batcher',
    'permission_helpers',
    'autocomplete_cache',
}


def migrate_file(filepath: Path) -> bool:
    """
    Migrate a single file's imports.
    Returns True if file was modified.
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()

    modified = False
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Pattern 1: Remove sys.path.insert for shared lib
        if re.search(r"sys\.path\.insert\(0, str\(.*'shared'.*'scripts'.*'lib'\)\)", line):
            # Skip this line
            modified = True
            i += 1
            continue

        # Pattern 2: Remove variable assignment + sys.path.insert block
        # e.g., skills_dir = Path(...)\n sys.path.insert(0, str(skills_dir / 'shared'...))
        if re.search(r"^\w+_dir = Path\(__file__\)", line):
            # Check if next line is sys.path.insert using this variable
            if i + 1 < len(lines) and re.search(r"sys\.path\.insert\(0, str\(\w+_dir\s*/\s*'shared'", lines[i + 1]):
                # Also check for comment line before the variable
                if new_lines and re.search(r"#.*shared.*lib|#.*Add.*path", new_lines[-1], re.IGNORECASE):
                    new_lines.pop()  # Remove the comment
                # Skip both lines
                modified = True
                i += 2
                continue

        # Pattern 3: Change 'from module import X' to 'from jira_assistant_skills_lib import X'
        match = re.match(r'^from (' + '|'.join(SHARED_MODULES) + r') import (.+)$', line)
        if match:
            module = match.group(1)
            imports = match.group(2)
            new_lines.append(f'from jira_assistant_skills_lib import {imports}\n')
            modified = True
            i += 1
            continue

        new_lines.append(line)
        i += 1

    # Clean up extra blank lines
    if modified:
        # Remove consecutive empty lines (keep at most 2)
        cleaned_lines = []
        blank_count = 0
        for line in new_lines:
            if line.strip() == '':
                blank_count += 1
                if blank_count <= 2:
                    cleaned_lines.append(line)
            else:
                blank_count = 0
                cleaned_lines.append(line)

        with open(filepath, 'w') as f:
            f.writelines(cleaned_lines)

    return modified


def main():
    """Main migration function."""
    plugins_dir = Path(__file__).parent / 'plugins' / 'jira-assistant-skills' / 'skills'

    if not plugins_dir.exists():
        print(f"Error: {plugins_dir} does not exist")
        return

    migrated_count = 0
    error_count = 0

    # Find all Python files
    for py_file in plugins_dir.rglob('*.py'):
        # Skip __pycache__
        if '__pycache__' in str(py_file):
            continue
        # Skip the shared lib directory itself
        if 'shared/scripts/lib' in str(py_file):
            continue

        try:
            if migrate_file(py_file):
                print(f"Migrated: {py_file.relative_to(Path(__file__).parent)}")
                migrated_count += 1
        except Exception as e:
            print(f"Error migrating {py_file}: {e}")
            error_count += 1

    print(f"\nMigration complete: {migrated_count} files migrated, {error_count} errors")


if __name__ == '__main__':
    main()
