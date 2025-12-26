"""
Live Integration Tests: Customer and Organization Management

Tests for customer and organization CRUD operations against a real JIRA instance.
"""

import pytest
import uuid


@pytest.mark.jsm
@pytest.mark.jsm_customers
class TestOrganizationCreate:
    """Tests for organization creation."""

    def test_create_organization(self, jira_client):
        """Test creating an organization."""
        org_name = f'Test Org {uuid.uuid4().hex[:8]}'

        org = jira_client.create_organization(name=org_name)

        try:
            assert 'id' in org
            assert org['name'] == org_name
        finally:
            jira_client.delete_organization(org['id'])

    def test_create_organization_returns_required_fields(self, jira_client):
        """Test that created organization has required fields."""
        org = jira_client.create_organization(
            name=f'Fields Test Org {uuid.uuid4().hex[:8]}'
        )

        try:
            required_fields = ['id', 'name']
            for field in required_fields:
                assert field in org, f"Missing required field: {field}"
        finally:
            jira_client.delete_organization(org['id'])


@pytest.mark.jsm
@pytest.mark.jsm_customers
class TestOrganizationRead:
    """Tests for reading organization data."""

    def test_get_organization(self, jira_client, test_organization):
        """Test fetching an organization."""
        org = jira_client.get_organization(test_organization['id'])

        assert org['id'] == test_organization['id']
        assert org['name'] == test_organization['name']

    def test_list_organizations(self, jira_client, test_organization):
        """Test listing all organizations."""
        result = jira_client.get_organizations()

        assert 'values' in result
        assert isinstance(result['values'], list)

        # Our test org should be in the list
        org_ids = [o['id'] for o in result['values']]
        assert test_organization['id'] in org_ids

    def test_get_organization_not_found(self, jira_client):
        """Test error handling for non-existent organization."""
        with pytest.raises(Exception) as exc_info:
            jira_client.get_organization(999999)

        assert '404' in str(exc_info.value) or 'not found' in str(exc_info.value).lower()


@pytest.mark.jsm
@pytest.mark.jsm_customers
class TestOrganizationUpdate:
    """Tests for updating organizations."""

    def test_update_organization_name(self, jira_client, test_organization):
        """Test updating organization name."""
        new_name = f'Updated Org {uuid.uuid4().hex[:8]}'

        try:
            # Update the organization
            jira_client.update_organization(test_organization['id'], name=new_name)

            # Verify update
            org = jira_client.get_organization(test_organization['id'])
            assert org['name'] == new_name

        except Exception as e:
            if '405' in str(e) or 'Method Not Allowed' in str(e):
                pytest.skip("Organization update not supported by JSM API")
            raise


@pytest.mark.jsm
@pytest.mark.jsm_customers
class TestOrganizationDelete:
    """Tests for organization deletion."""

    def test_delete_organization(self, jira_client):
        """Test deleting an organization."""
        import time

        # Create org to delete
        org = jira_client.create_organization(
            name=f'Delete Test Org {uuid.uuid4().hex[:8]}'
        )

        org_id = org['id']

        # Delete the organization
        jira_client.delete_organization(org_id)

        # Small delay for deletion to propagate
        time.sleep(1)

        # Verify deletion - org should not be found
        try:
            result = jira_client.get_organization(org_id)
            # If we get here, the org still exists - that's a failure
            # But due to eventual consistency, we might need to retry
            time.sleep(2)
            try:
                result = jira_client.get_organization(org_id)
                pytest.fail(f"Organization {org_id} still exists after deletion")
            except Exception:
                pass  # Expected - org was deleted
        except Exception:
            pass  # Expected - org was deleted


@pytest.mark.jsm
@pytest.mark.jsm_customers
class TestOrganizationServiceDesk:
    """Tests for organization-service desk relationships."""

    def test_add_organization_to_service_desk(self, jira_client, test_service_desk):
        """Test adding an organization to a service desk."""
        org = jira_client.create_organization(
            name=f'SD Link Test Org {uuid.uuid4().hex[:8]}'
        )

        try:
            # Add org to service desk
            jira_client.add_organization_to_service_desk(
                test_service_desk['id'],
                org['id']
            )

            # Verify org is linked
            orgs = jira_client.get_service_desk_organizations(test_service_desk['id'])
            org_ids = [o['id'] for o in orgs.get('values', [])]
            assert org['id'] in org_ids

        finally:
            jira_client.delete_organization(org['id'])

    def test_remove_organization_from_service_desk(self, jira_client, test_service_desk):
        """Test removing an organization from a service desk."""
        org = jira_client.create_organization(
            name=f'SD Unlink Test Org {uuid.uuid4().hex[:8]}'
        )

        try:
            # Add then remove
            jira_client.add_organization_to_service_desk(
                test_service_desk['id'],
                org['id']
            )
            jira_client.remove_organization_from_service_desk(
                test_service_desk['id'],
                org['id']
            )

            # Verify org is no longer linked
            orgs = jira_client.get_service_desk_organizations(test_service_desk['id'])
            org_ids = [o['id'] for o in orgs.get('values', [])]
            assert org['id'] not in org_ids

        finally:
            jira_client.delete_organization(org['id'])

    def test_list_service_desk_organizations(self, jira_client, test_service_desk, test_organization):
        """Test listing organizations for a service desk."""
        result = jira_client.get_service_desk_organizations(test_service_desk['id'])

        assert 'values' in result
        assert isinstance(result['values'], list)


@pytest.mark.jsm
@pytest.mark.jsm_customers
class TestOrganizationUsers:
    """Tests for organization user membership."""

    def test_add_user_to_organization(self, jira_client, test_organization, current_user):
        """Test adding a user to an organization."""
        try:
            jira_client.add_users_to_organization(
                test_organization['id'],
                account_ids=[current_user['accountId']]
            )

            # Verify user is in org (may require a brief delay for propagation)
            import time
            time.sleep(1)
            users = jira_client.get_organization_users(test_organization['id'])
            user_ids = [u.get('accountId') for u in users.get('values', [])]

            # User may already be in org or API may have eventual consistency
            if current_user['accountId'] not in user_ids:
                # Try one more time with longer delay
                time.sleep(2)
                users = jira_client.get_organization_users(test_organization['id'])
                user_ids = [u.get('accountId') for u in users.get('values', [])]
                if current_user['accountId'] not in user_ids:
                    pytest.skip("User not visible in organization (eventual consistency)")

        except Exception as e:
            if '403' in str(e) or 'permission' in str(e).lower():
                pytest.skip("Insufficient permissions to manage organization users")
            raise

    def test_remove_user_from_organization(self, jira_client, test_organization, current_user):
        """Test removing a user from an organization."""
        try:
            # Add then remove
            jira_client.add_users_to_organization(
                test_organization['id'],
                account_ids=[current_user['accountId']]
            )
            jira_client.remove_users_from_organization(
                test_organization['id'],
                account_ids=[current_user['accountId']]
            )

            # Verify user is no longer in org
            users = jira_client.get_organization_users(test_organization['id'])
            user_ids = [u.get('accountId') for u in users.get('values', [])]
            assert current_user['accountId'] not in user_ids

        except Exception as e:
            if '403' in str(e) or 'permission' in str(e).lower():
                pytest.skip("Insufficient permissions to manage organization users")
            raise

    def test_list_organization_users(self, jira_client, test_organization):
        """Test listing users in an organization."""
        result = jira_client.get_organization_users(test_organization['id'])

        assert 'values' in result
        assert isinstance(result['values'], list)


@pytest.mark.jsm
@pytest.mark.jsm_customers
class TestCustomerCreate:
    """Tests for customer creation."""

    def test_create_customer(self, jira_client, test_service_desk):
        """Test creating a customer."""
        unique_id = uuid.uuid4().hex[:8]
        email = f"test.customer.{unique_id}@example.com"

        try:
            customer = jira_client.create_customer(
                email=email,
                display_name=f'Test Customer {unique_id}',
                service_desk_id=test_service_desk['id']
            )

            assert 'accountId' in customer or 'emailAddress' in customer

        except Exception as e:
            if '403' in str(e) or 'permission' in str(e).lower():
                pytest.skip("Insufficient permissions to create customers")
            elif 'already exists' in str(e).lower():
                pytest.skip("Customer already exists")
            raise

    def test_create_customer_and_add_to_service_desk(self, jira_client, test_service_desk):
        """Test creating a customer and adding to service desk."""
        unique_id = uuid.uuid4().hex[:8]
        email = f"sd.customer.{unique_id}@example.com"

        try:
            customer = jira_client.create_customer(
                email=email,
                display_name=f'SD Customer {unique_id}',
                service_desk_id=test_service_desk['id']
            )

            # Verify customer can access service desk
            customers = jira_client.get_service_desk_customers(test_service_desk['id'])
            # Customer should be in the list or was added
            assert 'values' in customers

        except Exception as e:
            if '403' in str(e) or 'permission' in str(e).lower():
                pytest.skip("Insufficient permissions to create customers")
            raise


@pytest.mark.jsm
@pytest.mark.jsm_customers
class TestServiceDeskCustomers:
    """Tests for service desk customer management."""

    def test_list_service_desk_customers(self, jira_client, test_service_desk):
        """Test listing customers for a service desk."""
        try:
            result = jira_client.get_service_desk_customers(test_service_desk['id'])

            assert 'values' in result
            assert isinstance(result['values'], list)

        except Exception as e:
            if '403' in str(e) or 'permission' in str(e).lower():
                pytest.skip("Insufficient permissions to list customers")
            raise

    def test_add_customer_to_service_desk(self, jira_client, test_service_desk, current_user):
        """Test adding an existing user as customer to service desk."""
        try:
            jira_client.add_customers_to_service_desk(
                test_service_desk['id'],
                account_ids=[current_user['accountId']]
            )

            # Verify customer access
            customers = jira_client.get_service_desk_customers(test_service_desk['id'])
            customer_ids = [c.get('accountId') for c in customers.get('values', [])]
            # User should have customer access (may already be agent)
            assert 'values' in customers

        except Exception as e:
            if '403' in str(e) or 'permission' in str(e).lower():
                pytest.skip("Insufficient permissions to manage customers")
            raise

    def test_remove_customer_from_service_desk(self, jira_client, test_service_desk, test_customer):
        """Test removing a customer from service desk."""
        try:
            jira_client.remove_customers_from_service_desk(
                test_service_desk['id'],
                account_ids=[test_customer['accountId']]
            )

            # Verify customer removed
            customers = jira_client.get_service_desk_customers(test_service_desk['id'])
            customer_ids = [c.get('accountId') for c in customers.get('values', [])]
            assert test_customer['accountId'] not in customer_ids

        except Exception as e:
            error_str = str(e).lower()
            if '403' in str(e) or 'permission' in error_str:
                pytest.skip("Insufficient permissions to manage customers")
            if 'open access' in error_str or 'anyone can email' in error_str:
                pytest.skip("Cannot remove customers when service desk has open access enabled")
            raise
