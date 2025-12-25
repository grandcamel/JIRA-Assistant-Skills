"""
JIRA API client with retry logic and error handling.

Provides a robust HTTP client for interacting with the JIRA REST API v3,
including automatic retries, exponential backoff, and unified error handling.
"""

import time
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from error_handler import handle_jira_error


class JiraClient:
    """
    HTTP client for JIRA REST API v3.

    Features:
    - HTTP Basic Auth with email + API token
    - Automatic retry with exponential backoff
    - Configurable timeout
    - Unified error handling
    """

    def __init__(self, base_url: str, email: str, api_token: str,
                 timeout: int = 30, max_retries: int = 3,
                 retry_backoff: float = 2.0):
        """
        Initialize JIRA client.

        Args:
            base_url: JIRA instance URL (e.g., https://company.atlassian.net)
            email: User email for authentication
            api_token: API token for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_backoff: Backoff factor for retries (exponential)
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        self.session = self._create_session()

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

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
            operation: str = "fetch data") -> Dict[str, Any]:
        """
        Perform GET request.

        Args:
            endpoint: API endpoint (e.g., '/rest/api/3/issue/PROJ-123')
            params: Query parameters
            operation: Description of operation for error messages

        Returns:
            Response JSON as dictionary

        Raises:
            JiraError or subclass on failure
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        handle_jira_error(response, operation)
        return response.json()

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
             operation: str = "create resource") -> Dict[str, Any]:
        """
        Perform POST request.

        Args:
            endpoint: API endpoint
            data: Request body (will be JSON-encoded)
            operation: Description of operation for error messages

        Returns:
            Response JSON as dictionary

        Raises:
            JiraError or subclass on failure
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=data, timeout=self.timeout)
        handle_jira_error(response, operation)

        if response.status_code == 204:
            return {}

        try:
            return response.json()
        except ValueError:
            return {}

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
            operation: str = "update resource") -> Dict[str, Any]:
        """
        Perform PUT request.

        Args:
            endpoint: API endpoint
            data: Request body (will be JSON-encoded)
            operation: Description of operation for error messages

        Returns:
            Response JSON as dictionary (empty dict if 204 No Content)

        Raises:
            JiraError or subclass on failure
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.put(url, json=data, timeout=self.timeout)
        handle_jira_error(response, operation)

        if response.status_code == 204:
            return {}

        try:
            return response.json()
        except ValueError:
            return {}

    def delete(self, endpoint: str, operation: str = "delete resource") -> Dict[str, Any]:
        """
        Perform DELETE request.

        Args:
            endpoint: API endpoint
            operation: Description of operation for error messages

        Returns:
            Response JSON as dictionary (empty dict if 204 No Content)

        Raises:
            JiraError or subclass on failure
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, timeout=self.timeout)
        handle_jira_error(response, operation)

        if response.status_code == 204:
            return {}

        try:
            return response.json()
        except ValueError:
            return {}

    def upload_file(self, endpoint: str, file_path: str, file_name: Optional[str] = None,
                    operation: str = "upload file") -> Dict[str, Any]:
        """
        Upload a file (multipart/form-data).

        Args:
            endpoint: API endpoint
            file_path: Path to file to upload
            file_name: Name for the uploaded file (default: use file_path basename)
            operation: Description of operation for error messages

        Returns:
            Response JSON as dictionary

        Raises:
            JiraError or subclass on failure
        """
        import os

        if file_name is None:
            file_name = os.path.basename(file_path)

        url = f"{self.base_url}{endpoint}"

        headers = {
            'X-Atlassian-Token': 'no-check',
            'Accept': 'application/json',
        }

        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f)}
            response = self.session.post(
                url,
                files=files,
                headers=headers,
                timeout=self.timeout
            )

        handle_jira_error(response, operation)
        return response.json()

    def download_file(self, url: str, output_path: str,
                      operation: str = "download file") -> None:
        """
        Download a file from URL.

        Args:
            url: Full URL to download from
            output_path: Path where file should be saved
            operation: Description of operation for error messages

        Raises:
            JiraError or subclass on failure
        """
        response = self.session.get(url, stream=True, timeout=self.timeout)
        handle_jira_error(response, operation)

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    def search_issues(self, jql: str, fields: Optional[list] = None,
                      max_results: int = 50, start_at: int = 0) -> Dict[str, Any]:
        """
        Search for issues using JQL.

        Args:
            jql: JQL query string
            fields: List of fields to return (default: all)
            max_results: Maximum number of results per page
            start_at: Starting index for pagination

        Returns:
            Search results with issues, total, etc.

        Raises:
            JiraError or subclass on failure
        """
        params = {
            'jql': jql,
            'maxResults': max_results,
            'startAt': start_at,
        }

        if fields:
            params['fields'] = ','.join(fields)

        return self.get('/rest/api/3/search/jql', params=params, operation="search issues")

    def get_issue(self, issue_key: str, fields: Optional[list] = None) -> Dict[str, Any]:
        """
        Get a specific issue.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            fields: List of fields to return (default: all)

        Returns:
            Issue data

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if fields:
            params['fields'] = ','.join(fields)

        return self.get(f'/rest/api/3/issue/{issue_key}', params=params,
                       operation=f"get issue {issue_key}")

    def create_issue(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new issue.

        Args:
            fields: Issue fields dictionary

        Returns:
            Created issue data (key, id, self)

        Raises:
            JiraError or subclass on failure
        """
        data = {'fields': fields}
        return self.post('/rest/api/3/issue', data=data, operation="create issue")

    def update_issue(self, issue_key: str, fields: Dict[str, Any],
                     notify_users: bool = True) -> None:
        """
        Update an existing issue.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            fields: Fields to update
            notify_users: Send notifications to watchers

        Raises:
            JiraError or subclass on failure
        """
        data = {'fields': fields}
        params = {'notifyUsers': 'true' if notify_users else 'false'}

        endpoint = f'/rest/api/3/issue/{issue_key}'
        url = f"{self.base_url}{endpoint}"
        response = self.session.put(url, json=data, params=params, timeout=self.timeout)
        handle_jira_error(response, f"update issue {issue_key}")

    def delete_issue(self, issue_key: str) -> None:
        """
        Delete an issue.

        Args:
            issue_key: Issue key (e.g., PROJ-123)

        Raises:
            JiraError or subclass on failure
        """
        self.delete(f'/rest/api/3/issue/{issue_key}',
                   operation=f"delete issue {issue_key}")

    def get_transitions(self, issue_key: str) -> list:
        """
        Get available transitions for an issue.

        Args:
            issue_key: Issue key (e.g., PROJ-123)

        Returns:
            List of available transitions

        Raises:
            JiraError or subclass on failure
        """
        result = self.get(f'/rest/api/3/issue/{issue_key}/transitions',
                         operation=f"get transitions for {issue_key}")
        return result.get('transitions', [])

    def transition_issue(self, issue_key: str, transition_id: str,
                        fields: Optional[Dict[str, Any]] = None) -> None:
        """
        Transition an issue to a new status.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            transition_id: ID of the transition
            fields: Additional fields to set during transition

        Raises:
            JiraError or subclass on failure
        """
        data = {
            'transition': {'id': transition_id}
        }

        if fields:
            data['fields'] = fields

        self.post(f'/rest/api/3/issue/{issue_key}/transitions', data=data,
                 operation=f"transition issue {issue_key}")

    def get_current_user_id(self) -> str:
        """
        Get the account ID of the current authenticated user.

        Returns:
            Account ID string

        Raises:
            JiraError or subclass on failure
        """
        current_user = self.get('/rest/api/3/myself', operation='get current user')
        return current_user.get('accountId')

    def assign_issue(self, issue_key: str, account_id: Optional[str] = None) -> None:
        """
        Assign an issue to a user.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            account_id: User account ID (None to unassign, "-1" for current user)

        Raises:
            JiraError or subclass on failure
        """
        if account_id == "-1":
            # Get current user's account ID
            account_id = self.get_current_user_id()
            data = {"accountId": account_id}
        elif account_id is None:
            data = None
        else:
            data = {"accountId": account_id}

        self.put(f'/rest/api/3/issue/{issue_key}/assignee', data=data,
                operation=f"assign issue {issue_key}")

    def add_comment(self, issue_key: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a comment to an issue.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            body: Comment body (ADF format)

        Returns:
            Created comment data

        Raises:
            JiraError or subclass on failure
        """
        data = {'body': body}
        return self.post(f'/rest/api/3/issue/{issue_key}/comment', data=data,
                        operation=f"add comment to {issue_key}")

    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    # ========== Agile API Methods (/rest/agile/1.0/) ==========

    def get_sprint(self, sprint_id: int) -> Dict[str, Any]:
        """
        Get sprint details.

        Args:
            sprint_id: Sprint ID

        Returns:
            Sprint data

        Raises:
            JiraError or subclass on failure
        """
        return self.get(f'/rest/agile/1.0/sprint/{sprint_id}',
                       operation=f"get sprint {sprint_id}")

    def get_sprint_issues(self, sprint_id: int, fields: Optional[list] = None,
                          max_results: int = 50, start_at: int = 0) -> Dict[str, Any]:
        """
        Get issues in a sprint.

        Args:
            sprint_id: Sprint ID
            fields: List of fields to return
            max_results: Maximum results per page
            start_at: Starting index for pagination

        Returns:
            Issues in the sprint

        Raises:
            JiraError or subclass on failure
        """
        params = {
            'maxResults': max_results,
            'startAt': start_at,
        }
        if fields:
            params['fields'] = ','.join(fields)

        return self.get(f'/rest/agile/1.0/sprint/{sprint_id}/issue',
                       params=params,
                       operation=f"get issues for sprint {sprint_id}")

    def create_sprint(self, board_id: int, name: str, goal: Optional[str] = None,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new sprint.

        Args:
            board_id: Board ID to create sprint on
            name: Sprint name
            goal: Sprint goal (optional)
            start_date: Start date in ISO format (optional)
            end_date: End date in ISO format (optional)

        Returns:
            Created sprint data

        Raises:
            JiraError or subclass on failure
        """
        data = {
            'originBoardId': board_id,
            'name': name,
        }
        if goal:
            data['goal'] = goal
        if start_date:
            data['startDate'] = start_date
        if end_date:
            data['endDate'] = end_date

        return self.post('/rest/agile/1.0/sprint', data=data,
                        operation="create sprint")

    def update_sprint(self, sprint_id: int, **kwargs) -> Dict[str, Any]:
        """
        Update a sprint.

        Args:
            sprint_id: Sprint ID
            **kwargs: Fields to update (name, goal, state, startDate, endDate)

        Returns:
            Updated sprint data

        Raises:
            JiraError or subclass on failure
        """
        data = {}
        field_mapping = {
            'name': 'name',
            'goal': 'goal',
            'state': 'state',
            'start_date': 'startDate',
            'end_date': 'endDate',
        }
        for key, api_key in field_mapping.items():
            if key in kwargs and kwargs[key] is not None:
                data[api_key] = kwargs[key]

        return self.post(f'/rest/agile/1.0/sprint/{sprint_id}',
                        data=data,
                        operation=f"update sprint {sprint_id}")

    def move_issues_to_sprint(self, sprint_id: int, issue_keys: list,
                               rank: Optional[str] = None) -> None:
        """
        Move issues to a sprint.

        Args:
            sprint_id: Sprint ID
            issue_keys: List of issue keys to move
            rank: Optional rank position ('top', 'bottom', or None)

        Raises:
            JiraError or subclass on failure
        """
        data = {'issues': issue_keys}
        if rank == 'top':
            data['rankBeforeIssue'] = None  # Will be first
        elif rank == 'bottom':
            data['rankAfterIssue'] = None  # Will be last

        self.post(f'/rest/agile/1.0/sprint/{sprint_id}/issue',
                 data=data,
                 operation=f"move issues to sprint {sprint_id}")

    def get_board_backlog(self, board_id: int, jql: Optional[str] = None,
                          fields: Optional[list] = None,
                          max_results: int = 50, start_at: int = 0) -> Dict[str, Any]:
        """
        Get backlog issues for a board.

        Args:
            board_id: Board ID
            jql: Additional JQL filter
            fields: List of fields to return
            max_results: Maximum results per page
            start_at: Starting index for pagination

        Returns:
            Backlog issues

        Raises:
            JiraError or subclass on failure
        """
        params = {
            'maxResults': max_results,
            'startAt': start_at,
        }
        if jql:
            params['jql'] = jql
        if fields:
            params['fields'] = ','.join(fields)

        return self.get(f'/rest/agile/1.0/board/{board_id}/backlog',
                       params=params,
                       operation=f"get backlog for board {board_id}")

    def rank_issues(self, issue_keys: list, rank_before: Optional[str] = None,
                    rank_after: Optional[str] = None) -> None:
        """
        Rank issues in the backlog.

        Args:
            issue_keys: List of issue keys to rank
            rank_before: Issue key to rank before
            rank_after: Issue key to rank after

        Raises:
            JiraError or subclass on failure
        """
        data = {'issues': issue_keys}
        if rank_before:
            data['rankBeforeIssue'] = rank_before
        if rank_after:
            data['rankAfterIssue'] = rank_after

        self.put('/rest/agile/1.0/issue/rank', data=data,
                operation="rank issues")

    def get_board(self, board_id: int) -> Dict[str, Any]:
        """
        Get board details.

        Args:
            board_id: Board ID

        Returns:
            Board data

        Raises:
            JiraError or subclass on failure
        """
        return self.get(f'/rest/agile/1.0/board/{board_id}',
                       operation=f"get board {board_id}")

    def get_all_boards(self, project_key: Optional[str] = None,
                       board_type: Optional[str] = None,
                       max_results: int = 50, start_at: int = 0) -> Dict[str, Any]:
        """
        Get all boards.

        Args:
            project_key: Filter by project
            board_type: Filter by type (scrum, kanban)
            max_results: Maximum results per page
            start_at: Starting index for pagination

        Returns:
            Boards list

        Raises:
            JiraError or subclass on failure
        """
        params = {
            'maxResults': max_results,
            'startAt': start_at,
        }
        if project_key:
            params['projectKeyOrId'] = project_key
        if board_type:
            params['type'] = board_type

        return self.get('/rest/agile/1.0/board',
                       params=params,
                       operation="get boards")

    def get_board_sprints(self, board_id: int, state: Optional[str] = None,
                          max_results: int = 50, start_at: int = 0) -> Dict[str, Any]:
        """
        Get sprints for a board.

        Args:
            board_id: Board ID
            state: Filter by state (future, active, closed)
            max_results: Maximum results per page
            start_at: Starting index for pagination

        Returns:
            Sprints list

        Raises:
            JiraError or subclass on failure
        """
        params = {
            'maxResults': max_results,
            'startAt': start_at,
        }
        if state:
            params['state'] = state

        return self.get(f'/rest/agile/1.0/board/{board_id}/sprint',
                       params=params,
                       operation=f"get sprints for board {board_id}")

    # ========== Issue Link API Methods (/rest/api/3/issueLink) ==========

    def get_link_types(self) -> list:
        """
        Get all available issue link types.

        Returns:
            List of link type objects with id, name, inward, outward

        Raises:
            JiraError or subclass on failure
        """
        result = self.get('/rest/api/3/issueLinkType',
                         operation="get issue link types")
        return result.get('issueLinkTypes', [])

    def get_link(self, link_id: str) -> Dict[str, Any]:
        """
        Get a specific issue link by ID.

        Args:
            link_id: The issue link ID

        Returns:
            Issue link data

        Raises:
            JiraError or subclass on failure
        """
        return self.get(f'/rest/api/3/issueLink/{link_id}',
                       operation=f"get issue link {link_id}")

    def create_link(self, link_type: str, inward_key: str, outward_key: str,
                    comment: Optional[Dict[str, Any]] = None) -> None:
        """
        Create a link between two issues.

        Args:
            link_type: Name of the link type (e.g., "Blocks", "Duplicate")
            inward_key: Key of the inward issue (e.g., "is blocked by" side)
            outward_key: Key of the outward issue (e.g., "blocks" side)
            comment: Optional comment in ADF format

        Raises:
            JiraError or subclass on failure
        """
        data = {
            'type': {'name': link_type},
            'inwardIssue': {'key': inward_key},
            'outwardIssue': {'key': outward_key}
        }
        if comment:
            data['comment'] = {'body': comment}

        self.post('/rest/api/3/issueLink', data=data,
                 operation=f"create link between {inward_key} and {outward_key}")

    def delete_link(self, link_id: str) -> None:
        """
        Delete an issue link.

        Args:
            link_id: The issue link ID

        Raises:
            JiraError or subclass on failure
        """
        self.delete(f'/rest/api/3/issueLink/{link_id}',
                   operation=f"delete issue link {link_id}")

    def get_issue_links(self, issue_key: str) -> list:
        """
        Get all links for an issue.

        Args:
            issue_key: Issue key (e.g., PROJ-123)

        Returns:
            List of issue links

        Raises:
            JiraError or subclass on failure
        """
        issue = self.get(f'/rest/api/3/issue/{issue_key}',
                        params={'fields': 'issuelinks'},
                        operation=f"get links for {issue_key}")
        return issue.get('fields', {}).get('issuelinks', [])
