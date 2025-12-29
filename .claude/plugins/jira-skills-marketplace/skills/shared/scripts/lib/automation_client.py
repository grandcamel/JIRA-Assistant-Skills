"""
Atlassian Automation REST API client.

Provides HTTP client for interacting with the Jira Automation API,
which uses a different base URL than the standard Jira REST API.

API Documentation: https://developer.atlassian.com/cloud/automation/rest/
"""

import requests
from typing import Dict, Any, Optional, List
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class AutomationClient:
    """
    HTTP client for Atlassian Automation REST API.

    The Automation API uses a different base URL than the standard Jira API:
    - Primary: https://api.atlassian.com/automation/public/{product}/{cloudId}/rest/v1/
    - Site-specific: https://{site}/gateway/api/automation/public/{product}/{cloudId}/rest/v1/

    Features:
    - HTTP Basic Auth with email + API token
    - Automatic retry with exponential backoff
    - Cloud ID auto-discovery from tenant info
    - Unified error handling
    """

    def __init__(
        self,
        site_url: str,
        email: str,
        api_token: str,
        cloud_id: Optional[str] = None,
        product: str = 'jira',
        use_gateway: bool = False,
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff: float = 2.0
    ):
        """
        Initialize Automation API client.

        Args:
            site_url: JIRA instance URL (e.g., https://company.atlassian.net)
            email: User email for authentication
            api_token: API token for authentication
            cloud_id: Atlassian Cloud ID (will be auto-fetched if not provided)
            product: Product context ('jira' or 'confluence')
            use_gateway: Use site gateway instead of api.atlassian.com
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_backoff: Backoff factor for retries (exponential)
        """
        self.site_url = site_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.product = product
        self.use_gateway = use_gateway
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        self._cloud_id = cloud_id
        self.session = self._create_session()

    @property
    def cloud_id(self) -> str:
        """Get the cloud ID, fetching it if not already available."""
        if self._cloud_id is None:
            self._cloud_id = self._fetch_cloud_id()
        return self._cloud_id

    @property
    def base_url(self) -> str:
        """Get the base URL for the Automation API."""
        if self.use_gateway:
            return f"{self.site_url}/gateway/api/automation/public/{self.product}/{self.cloud_id}"
        else:
            return f"https://api.atlassian.com/automation/public/{self.product}/{self.cloud_id}"

    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry configuration.

        Returns:
            Configured requests.Session
        """
        session = requests.Session()

        session.auth = (self.email, self.api_token)

        session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
            raise_on_status=False
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _fetch_cloud_id(self) -> str:
        """
        Fetch the cloud ID from the tenant info endpoint.

        Returns:
            Cloud ID string

        Raises:
            AutomationError: If cloud ID cannot be retrieved
        """
        tenant_url = f"{self.site_url}/_edge/tenant_info"

        try:
            response = self.session.get(tenant_url, timeout=self.timeout)
            if response.ok:
                data = response.json()
                return data['cloudId']
            else:
                from error_handler import AutomationError
                raise AutomationError(
                    f"Failed to fetch cloud ID: HTTP {response.status_code}",
                    status_code=response.status_code
                )
        except requests.RequestException as e:
            from error_handler import AutomationError
            raise AutomationError(f"Failed to fetch cloud ID: {str(e)}")

    def _handle_response(self, response: requests.Response, operation: str) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions.

        Args:
            response: requests.Response object
            operation: Description of the operation for error messages

        Returns:
            Response JSON as dictionary

        Raises:
            Appropriate AutomationError subclass based on status code
        """
        if response.ok:
            if response.status_code == 204:
                return {}
            try:
                return response.json()
            except ValueError:
                return {}

        # Import error classes here to avoid circular imports
        from error_handler import (
            AutomationError, AutomationNotFoundError,
            AutomationPermissionError, AutomationValidationError
        )

        status_code = response.status_code

        try:
            error_data = response.json()
            message = error_data.get('message', response.text or 'Unknown error')
        except ValueError:
            message = response.text or f"HTTP {status_code} error"
            error_data = {}

        message = f"Failed to {operation}: {message}"

        if status_code == 400:
            raise AutomationValidationError(message, status_code=status_code, response_data=error_data)
        elif status_code == 401:
            from error_handler import AuthenticationError
            raise AuthenticationError(message, status_code=status_code, response_data=error_data)
        elif status_code == 403:
            raise AutomationPermissionError(message, status_code=status_code, response_data=error_data)
        elif status_code == 404:
            raise AutomationNotFoundError("Automation resource", message, status_code=status_code, response_data=error_data)
        elif status_code == 429:
            from error_handler import RateLimitError
            retry_after = response.headers.get('Retry-After')
            raise RateLimitError(
                retry_after=int(retry_after) if retry_after else None,
                status_code=status_code,
                response_data=error_data
            )
        elif status_code >= 500:
            from error_handler import ServerError
            raise ServerError(message, status_code=status_code, response_data=error_data)
        else:
            raise AutomationError(message, status_code=status_code, response_data=error_data)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
            operation: str = "fetch automation data") -> Dict[str, Any]:
        """
        Perform GET request to Automation API.

        Args:
            endpoint: API endpoint (e.g., '/rest/v1/rule/summary')
            params: Query parameters
            operation: Description of operation for error messages

        Returns:
            Response JSON as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        return self._handle_response(response, operation)

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
             operation: str = "create automation resource") -> Dict[str, Any]:
        """
        Perform POST request to Automation API.

        Args:
            endpoint: API endpoint
            data: Request body
            operation: Description of operation for error messages

        Returns:
            Response JSON as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=data, timeout=self.timeout)
        return self._handle_response(response, operation)

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
            operation: str = "update automation resource") -> Dict[str, Any]:
        """
        Perform PUT request to Automation API.

        Args:
            endpoint: API endpoint
            data: Request body
            operation: Description of operation for error messages

        Returns:
            Response JSON as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.put(url, json=data, timeout=self.timeout)
        return self._handle_response(response, operation)

    def delete(self, endpoint: str, operation: str = "delete automation resource") -> Dict[str, Any]:
        """
        Perform DELETE request to Automation API.

        Args:
            endpoint: API endpoint
            operation: Description of operation for error messages

        Returns:
            Response JSON as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, timeout=self.timeout)
        return self._handle_response(response, operation)

    # -------------------------------------------------------------------------
    # Rule Discovery & Inspection
    # -------------------------------------------------------------------------

    def get_rules(self, limit: int = 50, cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        List automation rules with pagination.

        Args:
            limit: Maximum results per page (1-100, default 50)
            cursor: Pagination cursor for next page

        Returns:
            Dictionary with 'values' (rules), 'links' (pagination), 'hasMore'
        """
        params = {'limit': min(max(1, limit), 100)}
        if cursor:
            params['cursor'] = cursor

        return self.get('/rest/v1/rule/summary', params=params, operation='list automation rules')

    def search_rules(
        self,
        trigger: Optional[str] = None,
        state: Optional[str] = None,
        scope: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search automation rules with filters.

        Args:
            trigger: Filter by trigger type (e.g., 'jira.issue.event.trigger:created')
            state: Filter by state ('ENABLED' or 'DISABLED')
            scope: Filter by scope (project ARI)
            limit: Maximum results per page (1-100, default 50)
            cursor: Pagination cursor for next page

        Returns:
            Dictionary with 'values' (rules), 'links' (pagination), 'hasMore'
        """
        filters = {}
        if trigger:
            filters['trigger'] = trigger
        if state:
            filters['state'] = state.upper()
        if scope:
            filters['scope'] = scope

        params = {'limit': min(max(1, limit), 100)}
        if cursor:
            params['cursor'] = cursor

        data = {'filters': filters} if filters else {}

        # Use POST for search with filters
        url = f"{self.base_url}/rest/v1/rule/summary"
        if params:
            url += '?' + '&'.join(f"{k}={v}" for k, v in params.items())

        response = self.session.post(url, json=data, timeout=self.timeout)
        return self._handle_response(response, 'search automation rules')

    def get_rule(self, rule_uuid: str) -> Dict[str, Any]:
        """
        Get detailed automation rule configuration.

        Args:
            rule_uuid: Rule UUID (ARI format)

        Returns:
            Full rule configuration
        """
        return self.get(f'/rest/v1/rule/{rule_uuid}', operation='get automation rule')

    # -------------------------------------------------------------------------
    # Rule State Management
    # -------------------------------------------------------------------------

    def update_rule_state(self, rule_uuid: str, state: str) -> Dict[str, Any]:
        """
        Enable or disable an automation rule.

        Args:
            rule_uuid: Rule UUID (ARI format)
            state: 'ENABLED' or 'DISABLED'

        Returns:
            Updated rule data
        """
        return self.put(
            f'/rest/v1/rule/{rule_uuid}/state',
            data={'state': state.upper()},
            operation=f'update automation rule state to {state}'
        )

    def enable_rule(self, rule_uuid: str) -> Dict[str, Any]:
        """
        Enable an automation rule.

        Args:
            rule_uuid: Rule UUID (ARI format)

        Returns:
            Updated rule data
        """
        return self.update_rule_state(rule_uuid, 'ENABLED')

    def disable_rule(self, rule_uuid: str) -> Dict[str, Any]:
        """
        Disable an automation rule.

        Args:
            rule_uuid: Rule UUID (ARI format)

        Returns:
            Updated rule data
        """
        return self.update_rule_state(rule_uuid, 'DISABLED')

    # -------------------------------------------------------------------------
    # Manual Rules
    # -------------------------------------------------------------------------

    def get_manual_rules(
        self,
        context_type: str = 'issue',
        limit: int = 50,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List manually-triggered automation rules.

        Args:
            context_type: Context type ('issue', 'alert', etc.)
            limit: Maximum results per page
            cursor: Pagination cursor

        Returns:
            Dictionary with manual rules
        """
        params = {
            'contextType': context_type,
            'limit': min(max(1, limit), 100)
        }
        if cursor:
            params['cursor'] = cursor

        return self.get('/rest/v1/rule/manual/search', params=params, operation='list manual rules')

    def invoke_manual_rule(
        self,
        rule_id: str,
        context: Dict[str, Any],
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Invoke a manual automation rule.

        Args:
            rule_id: Rule ID (not UUID)
            context: Context object (e.g., {'issue': {'key': 'PROJ-123'}})
            properties: Optional input properties for the rule

        Returns:
            Invocation result
        """
        data = {'context': context}
        if properties:
            data['properties'] = properties

        return self.post(
            f'/rest/v1/rule/manual/{rule_id}/invocation',
            data=data,
            operation='invoke manual rule'
        )

    # -------------------------------------------------------------------------
    # Templates
    # -------------------------------------------------------------------------

    def get_templates(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List available automation templates.

        Args:
            category: Filter by category
            limit: Maximum results per page
            cursor: Pagination cursor

        Returns:
            Dictionary with templates
        """
        params = {'limit': min(max(1, limit), 100)}
        if cursor:
            params['cursor'] = cursor

        data = {}
        if category:
            data['category'] = category

        if data:
            url = f"{self.base_url}/rest/v1/template/search"
            if params:
                url += '?' + '&'.join(f"{k}={v}" for k, v in params.items())
            response = self.session.post(url, json=data, timeout=self.timeout)
            return self._handle_response(response, 'search automation templates')
        else:
            return self.get('/rest/v1/template/search', params=params, operation='list automation templates')

    def get_template(self, template_id: str) -> Dict[str, Any]:
        """
        Get automation template details.

        Args:
            template_id: Template ID

        Returns:
            Template configuration
        """
        return self.get(f'/rest/v1/template/{template_id}', operation='get automation template')

    def create_rule_from_template(
        self,
        template_id: str,
        parameters: Dict[str, Any],
        name: Optional[str] = None,
        scope: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an automation rule from a template.

        Args:
            template_id: Template ID
            parameters: Template parameters
            name: Optional custom rule name
            scope: Optional scope (project ARI)

        Returns:
            Created rule data
        """
        data = {
            'templateId': template_id,
            'parameters': parameters
        }
        if name:
            data['name'] = name
        if scope:
            data['scope'] = scope

        return self.post('/rest/v1/template/create', data=data, operation='create rule from template')

    # -------------------------------------------------------------------------
    # Rule Creation & Updates
    # -------------------------------------------------------------------------

    def create_rule(
        self,
        name: str,
        trigger: Dict[str, Any],
        components: List[Dict[str, Any]],
        scope: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        state: str = 'ENABLED'
    ) -> Dict[str, Any]:
        """
        Create a new automation rule.

        Args:
            name: Rule name
            trigger: Trigger configuration
            components: List of action/condition components
            scope: Rule scope configuration
            description: Optional description
            state: Initial state ('ENABLED' or 'DISABLED')

        Returns:
            Created rule data
        """
        data = {
            'name': name,
            'trigger': trigger,
            'components': components,
            'state': state.upper()
        }
        if scope:
            data['ruleScope'] = scope
        if description:
            data['description'] = description

        return self.post('/rest/v1/rule', data=data, operation='create automation rule')

    def update_rule(self, rule_uuid: str, rule_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an automation rule configuration.

        Args:
            rule_uuid: Rule UUID (ARI format)
            rule_config: Updated rule configuration

        Returns:
            Updated rule data
        """
        return self.put(f'/rest/v1/rule/{rule_uuid}', data=rule_config, operation='update automation rule')

    def update_rule_scope(self, rule_uuid: str, scope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update automation rule scope.

        Args:
            rule_uuid: Rule UUID (ARI format)
            scope: New scope configuration

        Returns:
            Updated rule data
        """
        return self.put(
            f'/rest/v1/rule/{rule_uuid}/rule-scope',
            data=scope,
            operation='update automation rule scope'
        )

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
