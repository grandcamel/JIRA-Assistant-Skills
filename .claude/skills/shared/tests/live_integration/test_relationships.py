"""
Live Integration Tests: Issue Relationships

Tests for issue linking operations against a real JIRA instance.
"""

import pytest
import uuid


@pytest.mark.integration
@pytest.mark.shared
class TestLinkTypes:
    """Tests for link type operations."""

    def test_get_link_types(self, jira_client):
        """Test fetching available link types."""
        link_types = jira_client.get_link_types()

        assert isinstance(link_types, list)
        assert len(link_types) > 0

        # Verify structure
        for lt in link_types:
            assert 'id' in lt
            assert 'name' in lt
            assert 'inward' in lt
            assert 'outward' in lt

    def test_common_link_types_exist(self, jira_client):
        """Test that common link types are available."""
        link_types = jira_client.get_link_types()
        type_names = [lt['name'].lower() for lt in link_types]

        # At least one of these should exist
        common_types = ['blocks', 'duplicate', 'relates', 'cloners']
        found = any(ct in ' '.join(type_names) for ct in common_types)
        assert found, f"No common link types found. Available: {type_names}"


@pytest.mark.integration
@pytest.mark.shared
class TestLinkCreation:
    """Tests for creating issue links."""

    def test_create_blocks_link(self, jira_client, test_project):
        """Test creating a 'blocks' link between issues."""
        # Create two issues
        blocker = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Blocker Issue {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })
        blocked = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Blocked Issue {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })

        try:
            # Create link: blocker blocks blocked
            jira_client.create_link(
                link_type='Blocks',
                inward_key=blocked['key'],   # is blocked by
                outward_key=blocker['key']   # blocks
            )

            # Verify link exists
            links = jira_client.get_issue_links(blocker['key'])
            assert len(links) >= 1

            linked_keys = []
            for link in links:
                if 'inwardIssue' in link:
                    linked_keys.append(link['inwardIssue']['key'])
                if 'outwardIssue' in link:
                    linked_keys.append(link['outwardIssue']['key'])

            assert blocked['key'] in linked_keys
        finally:
            for issue in [blocker, blocked]:
                try:
                    jira_client.delete_issue(issue['key'])
                except Exception:
                    pass

    def test_create_relates_link(self, jira_client, test_project):
        """Test creating a 'relates to' link."""
        issue1 = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Related Issue 1 {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })
        issue2 = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Related Issue 2 {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })

        try:
            # Create relates link
            jira_client.create_link(
                link_type='Relates',
                inward_key=issue2['key'],
                outward_key=issue1['key']
            )

            # Verify from both sides
            links1 = jira_client.get_issue_links(issue1['key'])
            links2 = jira_client.get_issue_links(issue2['key'])

            assert len(links1) >= 1
            assert len(links2) >= 1
        finally:
            for issue in [issue1, issue2]:
                try:
                    jira_client.delete_issue(issue['key'])
                except Exception:
                    pass

    def test_create_duplicate_link(self, jira_client, test_project):
        """Test creating a 'duplicate' link."""
        original = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Original Issue {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Bug'}
        })
        duplicate = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Duplicate Issue {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Bug'}
        })

        try:
            # Create duplicate link
            jira_client.create_link(
                link_type='Duplicate',
                inward_key=duplicate['key'],   # is duplicated by
                outward_key=original['key']    # duplicates
            )

            # Verify link
            links = jira_client.get_issue_links(original['key'])
            assert len(links) >= 1
        finally:
            for issue in [original, duplicate]:
                try:
                    jira_client.delete_issue(issue['key'])
                except Exception:
                    pass


@pytest.mark.integration
@pytest.mark.shared
class TestLinkRetrieval:
    """Tests for retrieving issue links."""

    def test_get_issue_links(self, jira_client, test_project):
        """Test getting all links for an issue."""
        # Create linked issues
        issue1 = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Link Test 1 {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })
        issue2 = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Link Test 2 {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })
        issue3 = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Link Test 3 {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })

        try:
            # Create multiple links
            jira_client.create_link('Blocks', issue2['key'], issue1['key'])
            jira_client.create_link('Relates', issue3['key'], issue1['key'])

            # Get links for issue1
            links = jira_client.get_issue_links(issue1['key'])

            assert len(links) >= 2
        finally:
            for issue in [issue1, issue2, issue3]:
                try:
                    jira_client.delete_issue(issue['key'])
                except Exception:
                    pass

    def test_get_link_by_id(self, jira_client, test_project):
        """Test getting a specific link by ID."""
        # Create linked issues
        issue1 = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Link ID Test 1 {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })
        issue2 = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Link ID Test 2 {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })

        try:
            # Create link
            jira_client.create_link('Relates', issue2['key'], issue1['key'])

            # Get link ID from issue
            links = jira_client.get_issue_links(issue1['key'])
            link_id = links[0]['id']

            # Get link by ID
            link = jira_client.get_link(link_id)

            assert link['id'] == link_id
            assert 'type' in link
        finally:
            for issue in [issue1, issue2]:
                try:
                    jira_client.delete_issue(issue['key'])
                except Exception:
                    pass


@pytest.mark.integration
@pytest.mark.shared
class TestLinkDeletion:
    """Tests for deleting issue links."""

    def test_delete_link(self, jira_client, test_project):
        """Test deleting an issue link."""
        # Create linked issues
        issue1 = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Delete Link Test 1 {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })
        issue2 = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Delete Link Test 2 {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })

        try:
            # Create link
            jira_client.create_link('Relates', issue2['key'], issue1['key'])

            # Get link ID
            links = jira_client.get_issue_links(issue1['key'])
            assert len(links) >= 1
            link_id = links[0]['id']

            # Delete link
            jira_client.delete_link(link_id)

            # Verify link is gone
            links_after = jira_client.get_issue_links(issue1['key'])
            link_ids_after = [l['id'] for l in links_after]
            assert link_id not in link_ids_after
        finally:
            for issue in [issue1, issue2]:
                try:
                    jira_client.delete_issue(issue['key'])
                except Exception:
                    pass

    def test_delete_all_links(self, jira_client, test_project):
        """Test deleting all links from an issue."""
        # Create issues
        main_issue = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Main Issue {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })
        related = []
        for i in range(3):
            issue = jira_client.create_issue({
                'project': {'key': test_project['key']},
                'summary': f'Related {i} {uuid.uuid4().hex[:8]}',
                'issuetype': {'name': 'Task'}
            })
            related.append(issue)
            jira_client.create_link('Relates', issue['key'], main_issue['key'])

        try:
            # Verify links exist
            links = jira_client.get_issue_links(main_issue['key'])
            assert len(links) >= 3

            # Delete all links
            for link in links:
                jira_client.delete_link(link['id'])

            # Verify all gone
            links_after = jira_client.get_issue_links(main_issue['key'])
            assert len(links_after) == 0
        finally:
            try:
                jira_client.delete_issue(main_issue['key'])
            except Exception:
                pass
            for issue in related:
                try:
                    jira_client.delete_issue(issue['key'])
                except Exception:
                    pass


@pytest.mark.integration
@pytest.mark.shared
class TestIssueCloning:
    """Tests for issue cloning operations."""

    def test_clone_issue(self, jira_client, test_project):
        """Test cloning a basic issue."""
        # Create original issue
        original = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Original Issue {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'},
            'description': {
                'type': 'doc',
                'version': 1,
                'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Original description'}]}]
            },
            'priority': {'name': 'High'}
        })

        try:
            # Clone the issue
            clone = jira_client.clone_issue(
                original['key'],
                summary=f'Clone of {original["key"]} {uuid.uuid4().hex[:8]}'
            )

            # Verify clone was created
            assert clone['key'] != original['key']
            assert clone['key'].startswith(test_project['key'])

            # Verify clone has cloner link to original
            clone_links = jira_client.get_issue_links(clone['key'])
            linked_keys = []
            for link in clone_links:
                if link['type']['name'] == 'Cloners':
                    if 'inwardIssue' in link:
                        linked_keys.append(link['inwardIssue']['key'])
                    if 'outwardIssue' in link:
                        linked_keys.append(link['outwardIssue']['key'])

            assert original['key'] in linked_keys, "Clone should have Cloners link to original"

            # Cleanup
            jira_client.delete_issue(clone['key'])

        finally:
            jira_client.delete_issue(original['key'])

    def test_clone_issue_with_subtasks(self, jira_client, test_project):
        """Test cloning an issue including its subtasks."""
        # Create parent issue
        parent = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Parent Issue {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })

        # Create subtasks
        subtask1 = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Subtask 1 {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Subtask'},
            'parent': {'key': parent['key']}
        })
        subtask2 = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Subtask 2 {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Subtask'},
            'parent': {'key': parent['key']}
        })

        try:
            # Clone with subtasks
            clone = jira_client.clone_issue(
                parent['key'],
                summary=f'Clone with Subtasks {uuid.uuid4().hex[:8]}',
                clone_subtasks=True
            )

            # Verify clone exists
            assert clone['key'] != parent['key']

            # Get clone details to check for subtasks
            clone_data = jira_client.get_issue(clone['key'])
            cloned_subtasks = clone_data['fields'].get('subtasks', [])

            # Should have 2 cloned subtasks
            assert len(cloned_subtasks) == 2, f"Expected 2 cloned subtasks, found {len(cloned_subtasks)}"

            # Cleanup cloned subtasks
            for subtask in cloned_subtasks:
                jira_client.delete_issue(subtask['key'])

            # Cleanup clone
            jira_client.delete_issue(clone['key'])

        finally:
            # Cleanup original (parent deletes cascade to subtasks)
            jira_client.delete_issue(parent['key'])

    def test_clone_preserves_links(self, jira_client, test_project):
        """Test that cloning preserves issue links.

        Note: JIRA's clone behavior for links varies by configuration.
        Some instances preserve all links, others only certain types.
        This test verifies that at minimum the clone has a Cloners link.
        """
        # Create original issue
        original = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Original with Links {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Story'}
        })

        # Create related issue
        related = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Related Issue {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Story'}
        })

        try:
            # Link original to related issue
            jira_client.create_link('Relates', related['key'], original['key'])

            # Verify original has link
            original_links = jira_client.get_issue_links(original['key'])
            assert len(original_links) >= 1

            # Clone the original
            clone = jira_client.clone_issue(
                original['key'],
                summary=f'Clone Preserves Links {uuid.uuid4().hex[:8]}',
                clone_links=True
            )

            # Get clone's links
            clone_links = jira_client.get_issue_links(clone['key'])

            # At minimum, clone should have Cloners link to original
            assert len(clone_links) >= 1

            # Verify Cloners link exists
            has_cloners_link = False
            for link in clone_links:
                if link['type']['name'] == 'Cloners':
                    has_cloners_link = True
                    break

            assert has_cloners_link, "Clone should have Cloners link to original"

            # Optionally verify other links were preserved (behavior varies by instance)
            # Some JIRA instances preserve 'Relates' links, others don't
            # We just verify the Cloners link is always created

            # Cleanup
            jira_client.delete_issue(clone['key'])

        finally:
            jira_client.delete_issue(original['key'])
            jira_client.delete_issue(related['key'])
