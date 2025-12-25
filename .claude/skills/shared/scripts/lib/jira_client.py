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
            data: Request body (dict will be JSON-encoded, string used as-is)
            operation: Description of operation for error messages

        Returns:
            Response JSON as dictionary

        Raises:
            JiraError or subclass on failure
        """
        url = f"{self.base_url}{endpoint}"

        # If data is already a string, send it as raw body
        # (e.g., for watcher API which expects just "accountId")
        if isinstance(data, str):
            response = self.session.post(url, data=data, timeout=self.timeout)
        else:
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

        # For file uploads, we need to NOT include the session's default
        # Content-Type header (application/json). The requests library will
        # automatically set the proper multipart/form-data Content-Type.
        # We make a direct request instead of using the session to avoid
        # the default Content-Type header interfering.
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f)}
            response = requests.post(
                url,
                files=files,
                auth=(self.email, self.api_token),
                headers={
                    'X-Atlassian-Token': 'no-check',
                    'Accept': 'application/json',
                },
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

    def delete_issue(self, issue_key: str, delete_subtasks: bool = True) -> None:
        """
        Delete an issue.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            delete_subtasks: If True, also delete subtasks (default: True)

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if delete_subtasks:
            params['deleteSubtasks'] = 'true'

        endpoint = f'/rest/api/3/issue/{issue_key}'
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, params=params, timeout=self.timeout)
        handle_jira_error(response, f"delete issue {issue_key}")

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

    # ========== Project Management API Methods (/rest/api/3/project) ==========

    def create_project(self, key: str, name: str,
                       project_type_key: str = 'software',
                       template_key: str = 'com.pyxis.greenhopper.jira:gh-simplified-agility-scrum',
                       lead_account_id: Optional[str] = None,
                       description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new project.

        Args:
            key: Project key (e.g., 'TEST', 'INTG') - must be uppercase, 2-10 chars
            name: Project name
            project_type_key: 'software', 'business', or 'service_desk'
            template_key: Project template (determines board type)
            lead_account_id: Account ID of project lead (defaults to current user)
            description: Project description

        Returns:
            Created project data with 'id', 'key', 'self'

        Raises:
            JiraError or subclass on failure

        Common template_keys:
            Scrum: 'com.pyxis.greenhopper.jira:gh-simplified-agility-scrum'
            Kanban: 'com.pyxis.greenhopper.jira:gh-simplified-agility-kanban'
            Basic: 'com.pyxis.greenhopper.jira:gh-simplified-basic'
        """
        data = {
            'key': key.upper(),
            'name': name,
            'projectTypeKey': project_type_key,
            'projectTemplateKey': template_key,
        }

        if lead_account_id:
            data['leadAccountId'] = lead_account_id
        else:
            # Default to current user as project lead
            data['leadAccountId'] = self.get_current_user_id()

        if description:
            data['description'] = description

        return self.post('/rest/api/3/project', data=data,
                        operation=f"create project {key}")

    def get_project(self, project_key: str,
                    expand: Optional[list] = None) -> Dict[str, Any]:
        """
        Get project details.

        Args:
            project_key: Project key (e.g., 'PROJ')
            expand: Optional list of fields to expand (e.g., ['description', 'lead'])

        Returns:
            Project data

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if expand:
            params['expand'] = ','.join(expand)

        return self.get(f'/rest/api/3/project/{project_key}',
                       params=params if params else None,
                       operation=f"get project {project_key}")

    def delete_project(self, project_key: str, enable_undo: bool = True) -> None:
        """
        Delete a project.

        Args:
            project_key: Project key to delete
            enable_undo: If True, project goes to trash (recoverable for 60 days)

        Raises:
            JiraError or subclass on failure

        Note:
            Deleting a project also deletes all issues, boards, and sprints.
            Requires JIRA administrator permissions.
        """
        params = {'enableUndo': 'true' if enable_undo else 'false'}
        endpoint = f'/rest/api/3/project/{project_key}'
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, params=params, timeout=self.timeout)
        handle_jira_error(response, f"delete project {project_key}")

    def get_project_statuses(self, project_key: str) -> list:
        """
        Get all statuses available in a project, grouped by issue type.

        Args:
            project_key: Project key

        Returns:
            List of issue types with their available statuses

        Raises:
            JiraError or subclass on failure
        """
        return self.get(f'/rest/api/3/project/{project_key}/statuses',
                       operation=f"get statuses for project {project_key}")

    # ========== Sprint Deletion ==========

    def delete_sprint(self, sprint_id: int) -> None:
        """
        Delete a sprint.

        Args:
            sprint_id: Sprint ID to delete

        Raises:
            JiraError or subclass on failure

        Note:
            Only future (not started) sprints can be deleted.
            Active or closed sprints cannot be deleted via API.
        """
        self.delete(f'/rest/agile/1.0/sprint/{sprint_id}',
                   operation=f"delete sprint {sprint_id}")

    # ========== Board Deletion ==========

    def delete_board(self, board_id: int) -> None:
        """
        Delete a board.

        Args:
            board_id: Board ID to delete

        Raises:
            JiraError or subclass on failure

        Note:
            Deleting a project typically deletes associated boards automatically.
            Use this for explicit board cleanup if needed.
        """
        self.delete(f'/rest/agile/1.0/board/{board_id}',
                   operation=f"delete board {board_id}")

    # ========== Comment Operations ==========

    def get_comments(self, issue_key: str, max_results: int = 50,
                     start_at: int = 0, order_by: str = '-created') -> Dict[str, Any]:
        """
        Get comments on an issue.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            max_results: Maximum number of comments to return
            start_at: Starting index for pagination
            order_by: Order by field (prefix with - for descending)

        Returns:
            Comments data with 'comments', 'total', 'startAt', 'maxResults'

        Raises:
            JiraError or subclass on failure
        """
        params = {
            'maxResults': max_results,
            'startAt': start_at,
            'orderBy': order_by
        }
        return self.get(f'/rest/api/3/issue/{issue_key}/comment',
                       params=params,
                       operation=f"get comments for {issue_key}")

    def get_comment(self, issue_key: str, comment_id: str) -> Dict[str, Any]:
        """
        Get a specific comment.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            comment_id: Comment ID

        Returns:
            Comment data

        Raises:
            JiraError or subclass on failure
        """
        return self.get(f'/rest/api/3/issue/{issue_key}/comment/{comment_id}',
                       operation=f"get comment {comment_id}")

    def update_comment(self, issue_key: str, comment_id: str,
                       body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a comment on an issue.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            comment_id: Comment ID
            body: New comment body in ADF format

        Returns:
            Updated comment data

        Raises:
            JiraError or subclass on failure
        """
        data = {'body': body}
        return self.put(f'/rest/api/3/issue/{issue_key}/comment/{comment_id}',
                       data=data,
                       operation=f"update comment {comment_id}")

    def delete_comment(self, issue_key: str, comment_id: str) -> None:
        """
        Delete a comment from an issue.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            comment_id: Comment ID

        Raises:
            JiraError or subclass on failure
        """
        self.delete(f'/rest/api/3/issue/{issue_key}/comment/{comment_id}',
                   operation=f"delete comment {comment_id}")

    # ========== Attachment Operations ==========

    def get_attachments(self, issue_key: str) -> list:
        """
        Get attachments for an issue.

        Args:
            issue_key: Issue key (e.g., PROJ-123)

        Returns:
            List of attachment objects

        Raises:
            JiraError or subclass on failure
        """
        issue = self.get(f'/rest/api/3/issue/{issue_key}',
                        params={'fields': 'attachment'},
                        operation=f"get attachments for {issue_key}")
        return issue.get('fields', {}).get('attachment', [])

    def delete_attachment(self, attachment_id: str) -> None:
        """
        Delete an attachment.

        Args:
            attachment_id: Attachment ID

        Raises:
            JiraError or subclass on failure
        """
        self.delete(f'/rest/api/3/attachment/{attachment_id}',
                   operation=f"delete attachment {attachment_id}")

    # ========== User Search ==========

    def search_users(self, query: str, max_results: int = 50,
                     start_at: int = 0) -> list:
        """
        Search for users by email or display name.

        Args:
            query: Search query (email or name)
            max_results: Maximum results to return
            start_at: Starting index for pagination

        Returns:
            List of matching users

        Raises:
            JiraError or subclass on failure
        """
        params = {
            'query': query,
            'maxResults': max_results,
            'startAt': start_at
        }
        return self.get('/rest/api/3/user/search',
                       params=params,
                       operation="search users")

    # ========== Time Tracking / Worklog API Methods ==========

    def add_worklog(self, issue_key: str, time_spent: str,
                    started: Optional[str] = None,
                    comment: Optional[Dict[str, Any]] = None,
                    adjust_estimate: str = 'auto',
                    new_estimate: Optional[str] = None,
                    reduce_by: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a worklog to an issue.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            time_spent: Time spent in JIRA format (e.g., '2h', '1d 4h')
            started: When work started (ISO format, e.g., '2025-01-15T09:00:00.000+0000')
            comment: Optional comment in ADF format
            adjust_estimate: How to adjust remaining estimate:
                           'auto' (default), 'leave', 'new', 'manual'
            new_estimate: New remaining estimate (when adjust_estimate='new')
            reduce_by: Amount to reduce estimate (when adjust_estimate='manual')

        Returns:
            Created worklog object

        Raises:
            JiraError or subclass on failure
        """
        payload = {
            'timeSpent': time_spent
        }
        if started:
            payload['started'] = started
        if comment:
            payload['comment'] = comment

        params = {'adjustEstimate': adjust_estimate}
        if new_estimate and adjust_estimate == 'new':
            params['newEstimate'] = new_estimate
        if reduce_by and adjust_estimate == 'manual':
            params['reduceBy'] = reduce_by

        endpoint = f'/rest/api/3/issue/{issue_key}/worklog'
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=payload, params=params,
                                     timeout=self.timeout)
        handle_jira_error(response, f"add worklog to {issue_key}")
        return response.json()

    def get_worklogs(self, issue_key: str, start_at: int = 0,
                     max_results: int = 5000) -> Dict[str, Any]:
        """
        Get all worklogs for an issue.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            start_at: Starting index for pagination
            max_results: Maximum number of worklogs to return

        Returns:
            Worklogs response with 'worklogs', 'total', 'startAt', 'maxResults'

        Raises:
            JiraError or subclass on failure
        """
        params = {
            'startAt': start_at,
            'maxResults': max_results
        }
        return self.get(f'/rest/api/3/issue/{issue_key}/worklog',
                       params=params,
                       operation=f"get worklogs for {issue_key}")

    def get_worklog(self, issue_key: str, worklog_id: str) -> Dict[str, Any]:
        """
        Get a specific worklog.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            worklog_id: Worklog ID

        Returns:
            Worklog object

        Raises:
            JiraError or subclass on failure
        """
        return self.get(f'/rest/api/3/issue/{issue_key}/worklog/{worklog_id}',
                       operation=f"get worklog {worklog_id}")

    def update_worklog(self, issue_key: str, worklog_id: str,
                       time_spent: Optional[str] = None,
                       started: Optional[str] = None,
                       comment: Optional[Dict[str, Any]] = None,
                       adjust_estimate: str = 'auto',
                       new_estimate: Optional[str] = None) -> Dict[str, Any]:
        """
        Update an existing worklog.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            worklog_id: Worklog ID
            time_spent: New time spent (optional)
            started: New start time (optional)
            comment: New comment in ADF format (optional)
            adjust_estimate: How to adjust remaining estimate
            new_estimate: New remaining estimate (when adjust_estimate='new')

        Returns:
            Updated worklog object

        Raises:
            JiraError or subclass on failure
        """
        payload = {}
        if time_spent:
            payload['timeSpent'] = time_spent
        if started:
            payload['started'] = started
        if comment:
            payload['comment'] = comment

        params = {'adjustEstimate': adjust_estimate}
        if new_estimate and adjust_estimate == 'new':
            params['newEstimate'] = new_estimate

        endpoint = f'/rest/api/3/issue/{issue_key}/worklog/{worklog_id}'
        url = f"{self.base_url}{endpoint}"
        response = self.session.put(url, json=payload, params=params,
                                    timeout=self.timeout)
        handle_jira_error(response, f"update worklog {worklog_id}")
        return response.json()

    def delete_worklog(self, issue_key: str, worklog_id: str,
                       adjust_estimate: str = 'auto',
                       new_estimate: Optional[str] = None,
                       increase_by: Optional[str] = None) -> None:
        """
        Delete a worklog.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            worklog_id: Worklog ID
            adjust_estimate: How to adjust remaining estimate:
                           'auto' (default), 'leave', 'new', 'manual'
            new_estimate: New remaining estimate (when adjust_estimate='new')
            increase_by: Amount to increase estimate (when adjust_estimate='manual')

        Raises:
            JiraError or subclass on failure
        """
        params = {'adjustEstimate': adjust_estimate}
        if new_estimate and adjust_estimate == 'new':
            params['newEstimate'] = new_estimate
        if increase_by and adjust_estimate == 'manual':
            params['increaseBy'] = increase_by

        endpoint = f'/rest/api/3/issue/{issue_key}/worklog/{worklog_id}'
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, params=params, timeout=self.timeout)
        handle_jira_error(response, f"delete worklog {worklog_id}")

    def get_time_tracking(self, issue_key: str) -> Dict[str, Any]:
        """
        Get time tracking info for an issue.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')

        Returns:
            Time tracking data with originalEstimate, remainingEstimate,
            timeSpent and their *Seconds equivalents

        Raises:
            JiraError or subclass on failure
        """
        issue = self.get(f'/rest/api/3/issue/{issue_key}',
                        params={'fields': 'timetracking'},
                        operation=f"get time tracking for {issue_key}")
        return issue.get('fields', {}).get('timetracking', {})

    def set_time_tracking(self, issue_key: str,
                          original_estimate: Optional[str] = None,
                          remaining_estimate: Optional[str] = None) -> None:
        """
        Set time tracking estimates on an issue.

        Note: Due to JIRA bug JRACLOUD-67539, updating only remainingEstimate
        may overwrite originalEstimate. Always set both together when possible.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            original_estimate: Original estimate (e.g., '2d', '16h')
            remaining_estimate: Remaining estimate (e.g., '1d 4h')

        Raises:
            JiraError or subclass on failure
        """
        timetracking = {}
        if original_estimate is not None:
            timetracking['originalEstimate'] = original_estimate
        if remaining_estimate is not None:
            timetracking['remainingEstimate'] = remaining_estimate

        if not timetracking:
            return

        self.put(f'/rest/api/3/issue/{issue_key}',
                data={'fields': {'timetracking': timetracking}},
                operation=f"set time tracking for {issue_key}")

    # ========== JQL API Methods (/rest/api/3/jql/) ==========

    def get_jql_autocomplete(self, include_collapsed_fields: bool = False) -> Dict[str, Any]:
        """
        Get JQL reference data (fields, functions, reserved words).

        Args:
            include_collapsed_fields: Include collapsed fields in response

        Returns:
            dict with visibleFieldNames, visibleFunctionNames, jqlReservedWords

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if include_collapsed_fields:
            params['includeCollapsedFields'] = 'true'
        return self.get('/rest/api/3/jql/autocompletedata',
                       params=params if params else None,
                       operation="get JQL autocomplete data")

    def get_jql_suggestions(self, field_name: str, field_value: str = '') -> Dict[str, Any]:
        """
        Get autocomplete suggestions for a JQL field value.

        Args:
            field_name: Field to get suggestions for (e.g., 'project', 'status')
            field_value: Partial value to filter suggestions

        Returns:
            dict with results array of suggestion objects

        Raises:
            JiraError or subclass on failure
        """
        params = {'fieldName': field_name}
        if field_value:
            params['fieldValue'] = field_value
        return self.get('/rest/api/3/jql/autocompletedata/suggestions',
                       params=params,
                       operation=f"get JQL suggestions for {field_name}")

    def parse_jql(self, queries: list, validation: str = 'strict') -> Dict[str, Any]:
        """
        Parse and validate JQL queries.

        Args:
            queries: List of JQL query strings to parse
            validation: Validation level: 'strict', 'warn', or 'none'

        Returns:
            dict with queries array containing structure and errors

        Raises:
            JiraError or subclass on failure
        """
        params = {'validation': validation}
        return self.post('/rest/api/3/jql/parse',
                        data={'queries': queries},
                        operation="parse JQL queries")

    # ========== Filter API Methods (/rest/api/3/filter/) ==========

    def create_filter(self, name: str, jql: str, description: str = None,
                      favourite: bool = False,
                      share_permissions: list = None) -> Dict[str, Any]:
        """
        Create a new filter.

        Args:
            name: Filter name
            jql: JQL query string
            description: Optional description
            favourite: Whether to mark as favourite
            share_permissions: List of share permission objects

        Returns:
            Created filter object

        Raises:
            JiraError or subclass on failure
        """
        payload = {
            'name': name,
            'jql': jql,
            'favourite': favourite
        }
        if description:
            payload['description'] = description
        if share_permissions:
            payload['sharePermissions'] = share_permissions
        return self.post('/rest/api/3/filter', data=payload,
                        operation=f"create filter '{name}'")

    def get_filter(self, filter_id: str, expand: str = None) -> Dict[str, Any]:
        """
        Get a filter by ID.

        Args:
            filter_id: Filter ID
            expand: Optional expansions (e.g., 'sharedUsers,subscriptions')

        Returns:
            Filter object

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if expand:
            params['expand'] = expand
        return self.get(f'/rest/api/3/filter/{filter_id}',
                       params=params if params else None,
                       operation=f"get filter {filter_id}")

    def update_filter(self, filter_id: str, name: str = None, jql: str = None,
                      description: str = None, favourite: bool = None) -> Dict[str, Any]:
        """
        Update a filter.

        Args:
            filter_id: Filter ID
            name: New name (optional)
            jql: New JQL (optional)
            description: New description (optional)
            favourite: New favourite status (optional)

        Returns:
            Updated filter object

        Raises:
            JiraError or subclass on failure
        """
        payload = {}
        if name is not None:
            payload['name'] = name
        if jql is not None:
            payload['jql'] = jql
        if description is not None:
            payload['description'] = description
        if favourite is not None:
            payload['favourite'] = favourite
        return self.put(f'/rest/api/3/filter/{filter_id}', data=payload,
                       operation=f"update filter {filter_id}")

    def delete_filter(self, filter_id: str) -> None:
        """
        Delete a filter.

        Args:
            filter_id: Filter ID

        Raises:
            JiraError or subclass on failure
        """
        self.delete(f'/rest/api/3/filter/{filter_id}',
                   operation=f"delete filter {filter_id}")

    def get_my_filters(self, expand: str = None) -> list:
        """
        Get current user's filters.

        Args:
            expand: Optional expansions

        Returns:
            List of filter objects

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if expand:
            params['expand'] = expand
        result = self.get('/rest/api/3/filter/my',
                         params=params if params else None,
                         operation="get my filters")
        return result if isinstance(result, list) else []

    def get_favourite_filters(self, expand: str = None) -> list:
        """
        Get current user's favourite filters.

        Args:
            expand: Optional expansions

        Returns:
            List of filter objects

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if expand:
            params['expand'] = expand
        result = self.get('/rest/api/3/filter/favourite',
                         params=params if params else None,
                         operation="get favourite filters")
        return result if isinstance(result, list) else []

    def search_filters(self, filter_name: str = None, account_id: str = None,
                       project_key: str = None, expand: str = None,
                       start_at: int = 0, max_results: int = 50) -> Dict[str, Any]:
        """
        Search for filters.

        Args:
            filter_name: Filter name to search for
            account_id: Filter by owner account ID
            project_key: Filter by project
            expand: Expansions
            start_at: Pagination offset
            max_results: Max results per page

        Returns:
            dict with values array and pagination info

        Raises:
            JiraError or subclass on failure
        """
        params = {'startAt': start_at, 'maxResults': max_results}
        if filter_name:
            params['filterName'] = filter_name
        if account_id:
            params['accountId'] = account_id
        if project_key:
            params['projectKeyOrId'] = project_key
        if expand:
            params['expand'] = expand
        return self.get('/rest/api/3/filter/search', params=params,
                       operation="search filters")

    def add_filter_favourite(self, filter_id: str) -> Dict[str, Any]:
        """
        Add filter to favourites.

        Args:
            filter_id: Filter ID

        Returns:
            Updated filter object

        Raises:
            JiraError or subclass on failure
        """
        return self.put(f'/rest/api/3/filter/{filter_id}/favourite',
                       operation=f"add filter {filter_id} to favourites")

    def remove_filter_favourite(self, filter_id: str) -> None:
        """
        Remove filter from favourites.

        Args:
            filter_id: Filter ID

        Raises:
            JiraError or subclass on failure
        """
        self.delete(f'/rest/api/3/filter/{filter_id}/favourite',
                   operation=f"remove filter {filter_id} from favourites")

    def get_filter_permissions(self, filter_id: str) -> list:
        """
        Get filter share permissions.

        Args:
            filter_id: Filter ID

        Returns:
            List of share permission objects

        Raises:
            JiraError or subclass on failure
        """
        return self.get(f'/rest/api/3/filter/{filter_id}/permission',
                       operation=f"get permissions for filter {filter_id}")

    def add_filter_permission(self, filter_id: str, permission: dict) -> Dict[str, Any]:
        """
        Add share permission to filter.

        Args:
            filter_id: Filter ID
            permission: Permission object with type and relevant fields:
                       - type: 'global', 'loggedin', 'project', 'project-role', 'group', 'user'
                       - project: {id: '10000'} (for project/project-role)
                       - role: {id: '10001'} (for project-role)
                       - group: {name: 'developers'} or {groupId: 'abc123'}
                       - user: {accountId: '...'} (for user)

        Returns:
            Created permission object

        Raises:
            JiraError or subclass on failure
        """
        return self.post(f'/rest/api/3/filter/{filter_id}/permission',
                        data=permission,
                        operation=f"add permission to filter {filter_id}")

    def delete_filter_permission(self, filter_id: str, permission_id: str) -> None:
        """
        Delete a filter share permission.

        Args:
            filter_id: Filter ID
            permission_id: Permission ID

        Raises:
            JiraError or subclass on failure
        """
        self.delete(f'/rest/api/3/filter/{filter_id}/permission/{permission_id}',
                   operation=f"delete permission {permission_id} from filter {filter_id}")

    # ========== Comment Visibility ==========

    def add_comment_with_visibility(self, issue_key: str, body: Dict[str, Any],
                                    visibility_type: str = None,
                                    visibility_value: str = None) -> Dict[str, Any]:
        """
        Add a comment with visibility restrictions.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            body: Comment body in ADF format
            visibility_type: 'role' or 'group' (None for public)
            visibility_value: Role or group name

        Returns:
            Created comment object

        Raises:
            JiraError or subclass on failure
        """
        data = {'body': body}
        if visibility_type and visibility_value:
            data['visibility'] = {
                'type': visibility_type,
                'value': visibility_value,
                'identifier': visibility_value
            }
        return self.post(f'/rest/api/3/issue/{issue_key}/comment',
                        data=data, operation=f"add comment to {issue_key}")

    # ========== Changelog ==========

    def get_changelog(self, issue_key: str, start_at: int = 0,
                      max_results: int = 100) -> Dict[str, Any]:
        """
        Get issue changelog (activity history).

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            start_at: Starting index for pagination
            max_results: Maximum results per page

        Returns:
            Changelog with values array of change entries

        Raises:
            JiraError or subclass on failure
        """
        params = {'startAt': start_at, 'maxResults': max_results}
        return self.get(f'/rest/api/3/issue/{issue_key}/changelog',
                       params=params,
                       operation=f"get changelog for {issue_key}")

    # ========== Notifications ==========

    def notify_issue(self, issue_key: str, subject: str = None,
                     text_body: str = None, html_body: str = None,
                     to: Dict[str, Any] = None,
                     restrict: Dict[str, Any] = None) -> None:
        """
        Send notification about an issue.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            subject: Notification subject
            text_body: Plain text body
            html_body: HTML body
            to: Recipients dict (reporter, assignee, watchers, voters, users, groups)
            restrict: Restriction dict (permissions, groups)

        Raises:
            JiraError or subclass on failure
        """
        data = {}
        if subject:
            data['subject'] = subject
        if text_body:
            data['textBody'] = text_body
        if html_body:
            data['htmlBody'] = html_body
        if to:
            data['to'] = to
        if restrict:
            data['restrict'] = restrict

        self.post(f'/rest/api/3/issue/{issue_key}/notify',
                 data=data, operation=f"notify about {issue_key}")

    # ========== Version Management ==========

    def create_version(self, project_id: int, name: str,
                       description: str = None,
                       start_date: str = None,
                       release_date: str = None,
                       released: bool = False,
                       archived: bool = False) -> Dict[str, Any]:
        """
        Create a new project version.

        Args:
            project_id: Project ID (numeric)
            name: Version name (e.g., 'v1.0.0')
            description: Version description
            start_date: Start date (YYYY-MM-DD)
            release_date: Release date (YYYY-MM-DD)
            released: Whether version is released
            archived: Whether version is archived

        Returns:
            Created version object

        Raises:
            JiraError or subclass on failure
        """
        data = {
            'projectId': project_id,
            'name': name,
            'released': released,
            'archived': archived
        }
        if description:
            data['description'] = description
        if start_date:
            data['startDate'] = start_date
        if release_date:
            data['releaseDate'] = release_date

        return self.post('/rest/api/3/version', data=data,
                        operation=f"create version '{name}'")

    def get_version(self, version_id: str, expand: str = None) -> Dict[str, Any]:
        """
        Get a version by ID.

        Args:
            version_id: Version ID
            expand: Optional expansions (e.g., 'issueStatusCounts')

        Returns:
            Version object

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if expand:
            params['expand'] = expand
        return self.get(f'/rest/api/3/version/{version_id}',
                       params=params if params else None,
                       operation=f"get version {version_id}")

    def update_version(self, version_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update a version.

        Args:
            version_id: Version ID
            **kwargs: Fields to update (name, description, released, archived,
                      start_date, release_date)

        Returns:
            Updated version object

        Raises:
            JiraError or subclass on failure
        """
        data = {}
        field_mapping = {
            'name': 'name',
            'description': 'description',
            'released': 'released',
            'archived': 'archived',
            'start_date': 'startDate',
            'release_date': 'releaseDate'
        }
        for key, api_key in field_mapping.items():
            if key in kwargs and kwargs[key] is not None:
                data[api_key] = kwargs[key]

        return self.put(f'/rest/api/3/version/{version_id}',
                       data=data,
                       operation=f"update version {version_id}")

    def delete_version(self, version_id: str,
                       move_fixed_to: str = None,
                       move_affected_to: str = None) -> None:
        """
        Delete a version.

        Args:
            version_id: Version ID
            move_fixed_to: Version ID to move fixVersion issues to
            move_affected_to: Version ID to move affectedVersion issues to

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if move_fixed_to:
            params['moveFixIssuesTo'] = move_fixed_to
        if move_affected_to:
            params['moveAffectedIssuesTo'] = move_affected_to

        endpoint = f'/rest/api/3/version/{version_id}'
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, params=params if params else None,
                                      timeout=self.timeout)
        handle_jira_error(response, f"delete version {version_id}")

    def get_project_versions(self, project_key: str,
                             expand: str = None) -> list:
        """
        Get all versions for a project.

        Args:
            project_key: Project key (e.g., 'PROJ')
            expand: Optional expansions

        Returns:
            List of version objects

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if expand:
            params['expand'] = expand
        return self.get(f'/rest/api/3/project/{project_key}/versions',
                       params=params if params else None,
                       operation=f"get versions for project {project_key}")

    def get_version_issue_counts(self, version_id: str) -> Dict[str, Any]:
        """
        Get issue counts for a version.

        Args:
            version_id: Version ID

        Returns:
            Issue counts (issuesFixedCount, issuesAffectedCount)

        Raises:
            JiraError or subclass on failure
        """
        return self.get(f'/rest/api/3/version/{version_id}/relatedIssueCounts',
                       operation=f"get issue counts for version {version_id}")

    def get_version_unresolved_count(self, version_id: str) -> Dict[str, Any]:
        """
        Get unresolved issue count for a version.

        Args:
            version_id: Version ID

        Returns:
            Unresolved count data

        Raises:
            JiraError or subclass on failure
        """
        return self.get(f'/rest/api/3/version/{version_id}/unresolvedIssueCount',
                       operation=f"get unresolved count for version {version_id}")

    # ========== Component Management ==========

    def create_component(self, project: str, name: str,
                         description: str = None,
                         lead_account_id: str = None,
                         assignee_type: str = 'PROJECT_DEFAULT') -> Dict[str, Any]:
        """
        Create a new component.

        Args:
            project: Project key (e.g., 'PROJ')
            name: Component name
            description: Component description
            lead_account_id: Account ID of component lead
            assignee_type: 'PROJECT_DEFAULT', 'COMPONENT_LEAD', 'PROJECT_LEAD', 'UNASSIGNED'

        Returns:
            Created component object

        Raises:
            JiraError or subclass on failure
        """
        data = {
            'project': project,
            'name': name,
            'assigneeType': assignee_type
        }
        if description:
            data['description'] = description
        if lead_account_id:
            data['leadAccountId'] = lead_account_id

        return self.post('/rest/api/3/component', data=data,
                        operation=f"create component '{name}'")

    def get_component(self, component_id: str) -> Dict[str, Any]:
        """
        Get a component by ID.

        Args:
            component_id: Component ID

        Returns:
            Component object

        Raises:
            JiraError or subclass on failure
        """
        return self.get(f'/rest/api/3/component/{component_id}',
                       operation=f"get component {component_id}")

    def update_component(self, component_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update a component.

        Args:
            component_id: Component ID
            **kwargs: Fields to update (name, description, lead_account_id, assignee_type)

        Returns:
            Updated component object

        Raises:
            JiraError or subclass on failure
        """
        data = {}
        field_mapping = {
            'name': 'name',
            'description': 'description',
            'lead_account_id': 'leadAccountId',
            'assignee_type': 'assigneeType'
        }
        for key, api_key in field_mapping.items():
            if key in kwargs and kwargs[key] is not None:
                data[api_key] = kwargs[key]

        return self.put(f'/rest/api/3/component/{component_id}',
                       data=data,
                       operation=f"update component {component_id}")

    def delete_component(self, component_id: str,
                         move_issues_to: str = None) -> None:
        """
        Delete a component.

        Args:
            component_id: Component ID
            move_issues_to: Component ID to move issues to

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if move_issues_to:
            params['moveIssuesTo'] = move_issues_to

        endpoint = f'/rest/api/3/component/{component_id}'
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, params=params if params else None,
                                      timeout=self.timeout)
        handle_jira_error(response, f"delete component {component_id}")

    def get_project_components(self, project_key: str) -> list:
        """
        Get all components for a project.

        Args:
            project_key: Project key (e.g., 'PROJ')

        Returns:
            List of component objects

        Raises:
            JiraError or subclass on failure
        """
        return self.get(f'/rest/api/3/project/{project_key}/components',
                       operation=f"get components for project {project_key}")

    def get_component_issue_counts(self, component_id: str) -> Dict[str, Any]:
        """
        Get issue counts for a component.

        Args:
            component_id: Component ID

        Returns:
            Issue count data

        Raises:
            JiraError or subclass on failure
        """
        return self.get(f'/rest/api/3/component/{component_id}/relatedIssueCounts',
                       operation=f"get issue counts for component {component_id}")
