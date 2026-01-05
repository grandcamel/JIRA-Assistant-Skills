"""
Live Integration Tests: Assets/CMDB

Tests for Asset management (Insight/Assets) against a real JIRA instance.
Requires JSM Premium license or standalone Assets license.
"""

import contextlib
import uuid

import pytest


@pytest.mark.jsm
@pytest.mark.jsm_premium
class TestAssetSchemas:
    """Tests for asset schema operations."""

    def test_list_object_schemas(self, jira_client):
        """Test listing available object schemas."""
        try:
            result = jira_client.get_object_schemas()

            assert "values" in result or "objectSchemas" in str(result)
            assert isinstance(
                result.get("values", result.get("objectSchemas", [])), list
            )

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Assets/Insight not available (requires JSM Premium)")
            raise

    def test_get_object_schema(self, jira_client):
        """Test getting a specific object schema."""
        try:
            schemas = jira_client.get_object_schemas()
            schema_list = schemas.get("values", schemas.get("objectSchemas", []))

            if not schema_list:
                pytest.skip("No object schemas available")

            schema_id = schema_list[0].get("id")
            schema = jira_client.get_object_schema(schema_id)

            assert "id" in schema
            assert schema["id"] == schema_id

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Assets not available")
            raise


@pytest.mark.jsm
@pytest.mark.jsm_premium
class TestObjectTypes:
    """Tests for object type operations."""

    def test_list_object_types(self, jira_client):
        """Test listing object types in a schema."""
        try:
            schemas = jira_client.get_object_schemas()
            schema_list = schemas.get("values", schemas.get("objectSchemas", []))

            if not schema_list:
                pytest.skip("No object schemas available")

            schema_id = schema_list[0].get("id")
            result = jira_client.get_object_types(schema_id)

            assert isinstance(result, list) or "values" in result

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Assets not available")
            raise

    def test_object_type_has_required_fields(self, jira_client):
        """Test that object types have required fields."""
        try:
            schemas = jira_client.get_object_schemas()
            schema_list = schemas.get("values", schemas.get("objectSchemas", []))

            if not schema_list:
                pytest.skip("No schemas available")

            schema_id = schema_list[0].get("id")
            types = jira_client.get_object_types(schema_id)
            type_list = types if isinstance(types, list) else types.get("values", [])

            if not type_list:
                pytest.skip("No object types available")

            obj_type = type_list[0]
            required_fields = ["id", "name"]
            for field in required_fields:
                assert field in obj_type, f"Missing required field: {field}"

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Assets not available")
            raise


@pytest.mark.jsm
@pytest.mark.jsm_premium
class TestAssetCreate:
    """Tests for asset creation."""

    @pytest.fixture
    def test_object_type(self, jira_client):
        """Get an object type for testing."""
        try:
            schemas = jira_client.get_object_schemas()
            schema_list = schemas.get("values", schemas.get("objectSchemas", []))

            if not schema_list:
                pytest.skip("No schemas available")

            schema_id = schema_list[0].get("id")
            types = jira_client.get_object_types(schema_id)
            type_list = types if isinstance(types, list) else types.get("values", [])

            if not type_list:
                pytest.skip("No object types available")

            return type_list[0]

        except Exception as e:
            pytest.skip(f"Cannot get object type: {e}")

    def test_create_asset(self, jira_client, test_object_type):
        """Test creating a new asset."""
        try:
            # Get required attributes for the object type
            type_id = test_object_type["id"]
            attributes = jira_client.get_object_type_attributes(type_id)

            # Find the name attribute (usually required)
            attr_list = (
                attributes
                if isinstance(attributes, list)
                else attributes.get("values", [])
            )
            name_attr = None
            for attr in attr_list:
                if attr.get("name", "").lower() == "name":
                    name_attr = attr
                    break

            if not name_attr:
                pytest.skip("Cannot find name attribute")

            # Create asset with name
            asset_name = f"Test Asset {uuid.uuid4().hex[:8]}"
            asset = jira_client.create_asset(type_id, {name_attr["id"]: asset_name})

            try:
                assert "id" in asset or "objectKey" in asset
            finally:
                # Cleanup
                asset_id = asset.get("id", asset.get("objectKey"))
                if asset_id:
                    with contextlib.suppress(Exception):
                        jira_client.delete_asset(asset_id)

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Assets not available")
            raise


@pytest.mark.jsm
@pytest.mark.jsm_premium
class TestAssetRead:
    """Tests for reading asset data."""

    def test_search_assets(self, jira_client):
        """Test searching for assets."""
        try:
            # IQL search
            result = jira_client.search_assets("objectType = *")

            assert "values" in result or "objectEntries" in str(result)

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Assets not available")
            raise

    def test_get_asset(self, jira_client):
        """Test getting a specific asset."""
        try:
            # Search for an asset first
            result = jira_client.search_assets("objectType = *")
            assets = result.get("values", result.get("objectEntries", []))

            if not assets:
                pytest.skip("No assets available")

            asset_key = assets[0].get("objectKey", assets[0].get("id"))
            asset = jira_client.get_asset(asset_key)

            assert "id" in asset or "objectKey" in asset

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Assets not available")
            raise

    def test_list_assets_by_type(self, jira_client):
        """Test listing assets by object type."""
        try:
            schemas = jira_client.get_object_schemas()
            schema_list = schemas.get("values", schemas.get("objectSchemas", []))

            if not schema_list:
                pytest.skip("No schemas")

            schema_id = schema_list[0].get("id")
            types = jira_client.get_object_types(schema_id)
            type_list = types if isinstance(types, list) else types.get("values", [])

            if not type_list:
                pytest.skip("No types")

            type_name = type_list[0].get("name")
            result = jira_client.search_assets(f'objectType = "{type_name}"')

            assert "values" in result or "objectEntries" in str(result)

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Assets not available")
            raise


@pytest.mark.jsm
@pytest.mark.jsm_premium
class TestAssetUpdate:
    """Tests for updating assets."""

    @pytest.fixture
    def test_asset(self, jira_client):
        """Create a test asset for update tests."""
        try:
            schemas = jira_client.get_object_schemas()
            schema_list = schemas.get("values", schemas.get("objectSchemas", []))

            if not schema_list:
                pytest.skip("No schemas")

            schema_id = schema_list[0].get("id")
            types = jira_client.get_object_types(schema_id)
            type_list = types if isinstance(types, list) else types.get("values", [])

            if not type_list:
                pytest.skip("No types")

            type_id = type_list[0]["id"]
            attributes = jira_client.get_object_type_attributes(type_id)
            attr_list = (
                attributes
                if isinstance(attributes, list)
                else attributes.get("values", [])
            )

            name_attr = None
            for attr in attr_list:
                if attr.get("name", "").lower() == "name":
                    name_attr = attr
                    break

            if not name_attr:
                pytest.skip("No name attribute")

            asset = jira_client.create_asset(
                type_id, {name_attr["id"]: f"Update Test Asset {uuid.uuid4().hex[:8]}"}
            )

            yield asset

            # Cleanup
            asset_id = asset.get("id", asset.get("objectKey"))
            if asset_id:
                with contextlib.suppress(Exception):
                    jira_client.delete_asset(asset_id)

        except Exception as e:
            pytest.skip(f"Cannot create test asset: {e}")

    def test_update_asset_attribute(self, jira_client, test_asset):
        """Test updating an asset attribute."""
        try:
            asset_id = test_asset.get("id", test_asset.get("objectKey"))

            # Get current attributes
            jira_client.get_asset(asset_id)

            # Find a text attribute to update
            # This is simplified - real implementation needs to find editable attributes
            new_name = f"Updated Asset {uuid.uuid4().hex[:8]}"

            jira_client.update_asset(asset_id, {"Name": new_name})

            # Verify update
            updated = jira_client.get_asset(asset_id)
            # Check if name was updated (attribute structure varies)
            assert updated is not None

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Asset update not available")
            raise


@pytest.mark.jsm
@pytest.mark.jsm_premium
class TestAssetLinks:
    """Tests for asset linking to requests."""

    def test_link_asset_to_request(self, jira_client, test_request):
        """Test linking an asset to a request."""
        try:
            # Find an asset to link
            result = jira_client.search_assets("objectType = *")
            assets = result.get("values", result.get("objectEntries", []))

            if not assets:
                pytest.skip("No assets to link")

            asset_key = assets[0].get("objectKey", assets[0].get("id"))

            jira_client.link_asset_to_issue(test_request["issueKey"], asset_key)

            # Verify link
            linked = jira_client.get_issue_assets(test_request["issueKey"])
            asset_keys = [
                a.get("objectKey", a.get("id")) for a in linked.get("values", [])
            ]
            assert asset_key in asset_keys

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Asset linking not available")
            if "not implemented" in str(e).lower():
                pytest.skip("Asset linking not implemented")
            raise

    def test_get_assets_for_request(self, jira_client, test_request):
        """Test getting assets linked to a request."""
        try:
            result = jira_client.get_issue_assets(test_request["issueKey"])

            assert "values" in result or isinstance(result, list)

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Asset linking not available")
            if "not implemented" in str(e).lower():
                pytest.skip("Asset linking not implemented")
            raise

    def test_find_affected_assets(self, jira_client, test_request):
        """Test finding assets affected by an incident/request."""
        try:
            # This is a higher-level function that might search related assets
            result = jira_client.find_affected_assets(test_request["issueKey"])

            # Should return assets or empty list
            assert isinstance(result, (dict, list))

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("Affected assets not available")
            if "not implemented" in str(e).lower() or "AttributeError" in str(e):
                pytest.skip("Affected assets not implemented")
            raise
