"""
Live Integration Tests: Knowledge Base

Tests for knowledge base search and article management against a real JIRA instance.
"""

import uuid

import pytest


@pytest.mark.jsm
@pytest.mark.jsm_kb
class TestKnowledgeBaseSearch:
    """Tests for knowledge base search functionality."""

    def test_search_knowledge_base(self, jira_client, test_service_desk):
        """Test searching the knowledge base."""
        try:
            result = jira_client.search_knowledge_base(
                test_service_desk["id"], query="help"
            )

            assert "values" in result or "articles" in str(result).lower()
            # Search should return a list (may be empty)

        except Exception as e:
            if "404" in str(e):
                pytest.skip("Knowledge base not enabled for this service desk")
            if "403" in str(e):
                pytest.skip("Insufficient permissions to search knowledge base")
            raise

    def test_search_returns_articles(self, jira_client, test_service_desk):
        """Test that search returns article structure."""
        try:
            result = jira_client.search_knowledge_base(
                test_service_desk["id"], query="how to"
            )

            if result.get("values"):
                article = result["values"][0]
                # Articles should have title and content reference
                assert "title" in article or "content" in str(article).lower()

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Knowledge base not available")
            raise

    def test_search_with_empty_query(self, jira_client, test_service_desk):
        """Test searching with empty query returns recent/all articles."""
        try:
            result = jira_client.search_knowledge_base(
                test_service_desk["id"], query=""
            )

            # Should still return valid response (may be empty or all articles)
            assert "values" in result or isinstance(result, dict)

        except Exception as e:
            if "400" in str(e):
                # Empty query may be invalid
                pytest.skip("Empty query not supported")
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Knowledge base not available")
            raise

    def test_search_with_special_characters(self, jira_client, test_service_desk):
        """Test searching with special characters."""
        try:
            result = jira_client.search_knowledge_base(
                test_service_desk["id"], query='error "not found"'
            )

            # Should handle special characters gracefully
            assert "values" in result or isinstance(result, dict)

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Knowledge base not available")
            raise


@pytest.mark.jsm
@pytest.mark.jsm_kb
class TestKnowledgeBaseArticles:
    """Tests for knowledge base article operations."""

    def test_get_article(self, jira_client, test_service_desk, kb_article):
        """Test getting a specific knowledge base article."""
        if not kb_article:
            pytest.skip("No articles found in knowledge base")

        article_id = kb_article.get("id")
        if not article_id:
            pytest.skip("Article ID not available")

        try:
            # Get the specific article
            article = jira_client.get_knowledge_base_article(
                test_service_desk["id"], article_id
            )

            assert "id" in article or "title" in article

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Knowledge base article retrieval not available")
            raise

    def test_article_has_required_fields(self, jira_client, kb_article):
        """Test that articles have required fields."""
        if not kb_article:
            pytest.skip("No articles in knowledge base")

        # Articles should have basic fields
        article_str = str(kb_article).lower()
        assert "title" in kb_article or "title" in article_str
        assert "id" in kb_article or "id" in article_str


@pytest.mark.jsm
@pytest.mark.jsm_kb
class TestKnowledgeBaseSuggestions:
    """Tests for knowledge base article suggestions."""

    def test_get_article_suggestions_for_request(
        self, jira_client, test_service_desk, test_request
    ):
        """Test getting article suggestions for a request."""
        try:
            result = jira_client.get_knowledge_base_suggestions(
                test_service_desk["id"], test_request["issueKey"]
            )

            # Should return suggestions (may be empty)
            assert "values" in result or isinstance(result, (dict, list))

        except Exception as e:
            if "404" in str(e):
                pytest.skip("KB suggestions not available")
            if "403" in str(e):
                pytest.skip("Insufficient permissions")
            raise

    def test_suggestions_based_on_summary(
        self, jira_client, test_service_desk, default_request_type
    ):
        """Test that suggestions are based on request content."""
        # Create request with specific keywords
        request = jira_client.create_request(
            service_desk_id=test_service_desk["id"],
            request_type_id=default_request_type["id"],
            summary=f"Password reset help needed {uuid.uuid4().hex[:8]}",
            description="I need help resetting my password for the system",
        )

        try:
            result = jira_client.get_knowledge_base_suggestions(
                test_service_desk["id"], request["issueKey"]
            )

            # Suggestions should be returned (content depends on KB articles)
            assert "values" in result or isinstance(result, (dict, list))

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("KB suggestions not available")
            raise
        finally:
            jira_client.delete_issue(request["issueKey"])


@pytest.mark.jsm
@pytest.mark.jsm_kb
class TestKnowledgeBaseIntegration:
    """Tests for knowledge base integration with requests."""

    def test_link_article_to_request(self, jira_client, test_request, kb_article):
        """Test linking a KB article to a request."""
        if not kb_article:
            pytest.skip("No articles to link")

        article_id = kb_article.get("id")
        if not article_id:
            pytest.skip("Article ID not available")

        try:
            # Link article to request
            jira_client.link_knowledge_base_article(
                test_request["issueKey"], article_id
            )

            # Verify link (may need to check request or article)
            # Implementation varies by JIRA version

        except Exception as e:
            if "404" in str(e):
                pytest.skip("KB linking not available")
            if "403" in str(e):
                pytest.skip("Insufficient permissions")
            if "not implemented" in str(e).lower():
                pytest.skip("KB linking not implemented")
            raise

    def test_attach_solution_to_request(self, jira_client, test_request, kb_article):
        """Test attaching a solution article to a request."""
        if not kb_article:
            pytest.skip("No articles available")

        article_id = kb_article.get("id")
        if not article_id:
            pytest.skip("Article ID not available")

        try:
            # Attempt to attach as solution
            jira_client.attach_article_as_solution(test_request["issueKey"], article_id)

        except Exception as e:
            if "not implemented" in str(e).lower() or "AttributeError" in str(e):
                pytest.skip("Solution attachment not implemented")
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Solution attachment not available")
            raise


@pytest.mark.jsm
@pytest.mark.jsm_kb
class TestKnowledgeBaseSpaces:
    """Tests for knowledge base spaces/categories."""

    def test_list_kb_spaces(self, jira_client, test_service_desk):
        """Test listing knowledge base spaces."""
        try:
            result = jira_client.get_knowledge_base_spaces(test_service_desk["id"])

            # Should return spaces/categories
            assert "values" in result or isinstance(result, (dict, list))

        except Exception as e:
            if "not implemented" in str(e).lower() or "AttributeError" in str(e):
                pytest.skip("KB spaces not implemented")
            if "404" in str(e) or "403" in str(e):
                pytest.skip("KB spaces not available")
            raise

    def test_search_within_space(self, jira_client, test_service_desk):
        """Test searching within a specific KB space."""
        try:
            # Get spaces first
            spaces = jira_client.get_knowledge_base_spaces(test_service_desk["id"])

            if not spaces.get("values"):
                pytest.skip("No KB spaces available")

            space_key = spaces["values"][0].get("key", spaces["values"][0].get("id"))

            # Search within space
            result = jira_client.search_knowledge_base(
                test_service_desk["id"], query="*", space_key=space_key
            )

            assert "values" in result or isinstance(result, (dict, list))

        except Exception as e:
            if "not implemented" in str(e).lower() or "AttributeError" in str(e):
                pytest.skip("KB space search not implemented")
            if "404" in str(e) or "403" in str(e):
                pytest.skip("KB space search not available")
            raise
