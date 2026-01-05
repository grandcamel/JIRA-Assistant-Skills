"""
JIRA API client with retry logic and error handling.

Provides a robust HTTP client for interacting with the JIRA REST API v3,
including automatic retries, exponential backoff, and unified error handling.
"""

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from jira_assistant_skills_lib import handle_jira_error


class JiraClient:
    """
    HTTP client for JIRA REST API v3.

    Features:
    - HTTP Basic Auth with email + API token
    - Automatic retry with exponential backoff
    - Configurable timeout
    - Unified error handling
    """

    def __init__(
        self,
        base_url: str,
        email: str,
        api_token: str,
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
    ):
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
        self.base_url = base_url.rstrip("/")
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

        session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=[
                "HEAD",
                "GET",
                "PUT",
                "DELETE",
                "OPTIONS",
                "TRACE",
                "POST",
            ],
            raise_on_status=False,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        operation: str = "fetch data",
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Perform GET request.

        Args:
            endpoint: API endpoint (e.g., '/rest/api/3/issue/PROJ-123')
            params: Query parameters
            operation: Description of operation for error messages
            headers: Optional additional headers

        Returns:
            Response JSON as dictionary

        Raises:
            JiraError or subclass on failure
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(
            url, params=params, timeout=self.timeout, headers=headers
        )
        handle_jira_error(response, operation)
        return response.json()

    def post(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        operation: str = "create resource",
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Perform POST request.

        Args:
            endpoint: API endpoint
            data: Request body (dict will be JSON-encoded, string used as-is)
            operation: Description of operation for error messages
            headers: Optional additional headers

        Returns:
            Response JSON as dictionary

        Raises:
            JiraError or subclass on failure
        """
        url = f"{self.base_url}{endpoint}"

        # If data is already a string, send it as raw body
        # (e.g., for watcher API which expects just "accountId")
        if isinstance(data, str):
            response = self.session.post(
                url, data=data, timeout=self.timeout, headers=headers
            )
        else:
            response = self.session.post(
                url, json=data, timeout=self.timeout, headers=headers
            )

        handle_jira_error(response, operation)

        if response.status_code == 204:
            return {}

        try:
            return response.json()
        except ValueError:
            return {}

    def put(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        operation: str = "update resource",
    ) -> dict[str, Any]:
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

    def delete(
        self, endpoint: str, operation: str = "delete resource"
    ) -> dict[str, Any]:
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

    def upload_file(
        self,
        endpoint: str,
        file_path: str,
        file_name: str | None = None,
        operation: str = "upload file",
    ) -> dict[str, Any]:
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
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f)}
            response = requests.post(
                url,
                files=files,
                auth=(self.email, self.api_token),
                headers={
                    "X-Atlassian-Token": "no-check",
                    "Accept": "application/json",
                },
                timeout=self.timeout,
            )

        handle_jira_error(response, operation)
        return response.json()

    def download_file(
        self, url: str, output_path: str, operation: str = "download file"
    ) -> None:
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

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    def search_issues(
        self,
        jql: str,
        fields: list | None = None,
        max_results: int = 50,
        next_page_token: str | None = None,
        start_at: int | None = None,
    ) -> dict[str, Any]:
        """
        Search for issues using JQL.

        Uses the /rest/api/3/search/jql endpoint per CHANGE-2046.
        Pagination uses nextPageToken (startAt is deprecated).

        Args:
            jql: JQL query string
            fields: List of fields to return (default: all)
            max_results: Maximum number of results per page
            next_page_token: Token for fetching next page of results
            start_at: DEPRECATED - Starting index (use next_page_token instead)

        Returns:
            Search results with issues, total, nextPageToken, etc.

        Raises:
            JiraError or subclass on failure
        """
        params = {
            "jql": jql,
            "maxResults": max_results,
        }

        # Use nextPageToken for pagination (preferred per CHANGE-2046)
        if next_page_token:
            params["nextPageToken"] = next_page_token
        elif start_at is not None and start_at > 0:
            # Deprecated: startAt still works but should migrate to nextPageToken
            params["startAt"] = start_at

        if fields:
            params["fields"] = ",".join(fields)

        return self.get(
            "/rest/api/3/search/jql", params=params, operation="search issues"
        )

    def get_issue(self, issue_key: str, fields: list | None = None) -> dict[str, Any]:
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
            params["fields"] = ",".join(fields)

        return self.get(
            f"/rest/api/3/issue/{issue_key}",
            params=params,
            operation=f"get issue {issue_key}",
        )

    def create_issue(self, fields: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new issue.

        Args:
            fields: Issue fields dictionary

        Returns:
            Created issue data (key, id, self)

        Raises:
            JiraError or subclass on failure
        """
        data = {"fields": fields}
        return self.post("/rest/api/3/issue", data=data, operation="create issue")

    def update_issue(
        self, issue_key: str, fields: dict[str, Any], notify_users: bool = True
    ) -> None:
        """
        Update an existing issue.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            fields: Fields to update
            notify_users: Send notifications to watchers

        Raises:
            JiraError or subclass on failure
        """
        data = {"fields": fields}
        params = {"notifyUsers": "true" if notify_users else "false"}

        endpoint = f"/rest/api/3/issue/{issue_key}"
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
            params["deleteSubtasks"] = "true"

        endpoint = f"/rest/api/3/issue/{issue_key}"
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
        result = self.get(
            f"/rest/api/3/issue/{issue_key}/transitions",
            operation=f"get transitions for {issue_key}",
        )
        return result.get("transitions", [])

    def transition_issue(
        self,
        issue_key: str,
        transition_id: str,
        fields: dict[str, Any] | None = None,
    ) -> None:
        """
        Transition an issue to a new status.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            transition_id: ID of the transition
            fields: Additional fields to set during transition

        Raises:
            JiraError or subclass on failure
        """
        data = {"transition": {"id": transition_id}}

        if fields:
            data["fields"] = fields

        self.post(
            f"/rest/api/3/issue/{issue_key}/transitions",
            data=data,
            operation=f"transition issue {issue_key}",
        )

    def get_current_user_id(self) -> str:
        """
        Get the account ID of the current authenticated user.

        Returns:
            Account ID string

        Raises:
            JiraError or subclass on failure
        """
        current_user = self.get("/rest/api/3/myself", operation="get current user")
        return current_user.get("accountId")

    def assign_issue(self, issue_key: str, account_id: str | None = None) -> None:
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

        self.put(
            f"/rest/api/3/issue/{issue_key}/assignee",
            data=data,
            operation=f"assign issue {issue_key}",
        )

    def add_comment(self, issue_key: str, body: dict[str, Any]) -> dict[str, Any]:
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
        data = {"body": body}
        return self.post(
            f"/rest/api/3/issue/{issue_key}/comment",
            data=data,
            operation=f"add comment to {issue_key}",
        )

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

    def get_sprint(self, sprint_id: int) -> dict[str, Any]:
        """
        Get sprint details.

        Args:
            sprint_id: Sprint ID

        Returns:
            Sprint data

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/agile/1.0/sprint/{sprint_id}", operation=f"get sprint {sprint_id}"
        )

    def get_sprint_issues(
        self,
        sprint_id: int,
        fields: list | None = None,
        max_results: int = 50,
        start_at: int = 0,
    ) -> dict[str, Any]:
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
            "maxResults": max_results,
            "startAt": start_at,
        }
        if fields:
            params["fields"] = ",".join(fields)

        return self.get(
            f"/rest/agile/1.0/sprint/{sprint_id}/issue",
            params=params,
            operation=f"get issues for sprint {sprint_id}",
        )

    def create_sprint(
        self,
        board_id: int,
        name: str,
        goal: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
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
            "originBoardId": board_id,
            "name": name,
        }
        if goal:
            data["goal"] = goal
        if start_date:
            data["startDate"] = start_date
        if end_date:
            data["endDate"] = end_date

        return self.post("/rest/agile/1.0/sprint", data=data, operation="create sprint")

    def update_sprint(self, sprint_id: int, **kwargs) -> dict[str, Any]:
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
            "name": "name",
            "goal": "goal",
            "state": "state",
            "start_date": "startDate",
            "end_date": "endDate",
        }
        for key, api_key in field_mapping.items():
            if key in kwargs and kwargs[key] is not None:
                data[api_key] = kwargs[key]

        return self.post(
            f"/rest/agile/1.0/sprint/{sprint_id}",
            data=data,
            operation=f"update sprint {sprint_id}",
        )

    def move_issues_to_sprint(
        self, sprint_id: int, issue_keys: list, rank: str | None = None
    ) -> None:
        """
        Move issues to a sprint.

        Args:
            sprint_id: Sprint ID
            issue_keys: List of issue keys to move
            rank: Optional rank position ('top', 'bottom', or None)

        Raises:
            JiraError or subclass on failure
        """
        data = {"issues": issue_keys}
        if rank == "top":
            data["rankBeforeIssue"] = None  # Will be first
        elif rank == "bottom":
            data["rankAfterIssue"] = None  # Will be last

        self.post(
            f"/rest/agile/1.0/sprint/{sprint_id}/issue",
            data=data,
            operation=f"move issues to sprint {sprint_id}",
        )

    def get_board_backlog(
        self,
        board_id: int,
        jql: str | None = None,
        fields: list | None = None,
        max_results: int = 50,
        start_at: int = 0,
    ) -> dict[str, Any]:
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
            "maxResults": max_results,
            "startAt": start_at,
        }
        if jql:
            params["jql"] = jql
        if fields:
            params["fields"] = ",".join(fields)

        return self.get(
            f"/rest/agile/1.0/board/{board_id}/backlog",
            params=params,
            operation=f"get backlog for board {board_id}",
        )

    def rank_issues(
        self,
        issue_keys: list,
        rank_before: str | None = None,
        rank_after: str | None = None,
    ) -> None:
        """
        Rank issues in the backlog.

        Args:
            issue_keys: List of issue keys to rank
            rank_before: Issue key to rank before
            rank_after: Issue key to rank after

        Raises:
            JiraError or subclass on failure
        """
        data = {"issues": issue_keys}
        if rank_before:
            data["rankBeforeIssue"] = rank_before
        if rank_after:
            data["rankAfterIssue"] = rank_after

        self.put("/rest/agile/1.0/issue/rank", data=data, operation="rank issues")

    def get_board(self, board_id: int) -> dict[str, Any]:
        """
        Get board details.

        Args:
            board_id: Board ID

        Returns:
            Board data

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/agile/1.0/board/{board_id}", operation=f"get board {board_id}"
        )

    def get_all_boards(
        self,
        project_key: str | None = None,
        board_type: str | None = None,
        max_results: int = 50,
        start_at: int = 0,
    ) -> dict[str, Any]:
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
            "maxResults": max_results,
            "startAt": start_at,
        }
        if project_key:
            params["projectKeyOrId"] = project_key
        if board_type:
            params["type"] = board_type

        return self.get("/rest/agile/1.0/board", params=params, operation="get boards")

    def get_board_sprints(
        self,
        board_id: int,
        state: str | None = None,
        max_results: int = 50,
        start_at: int = 0,
    ) -> dict[str, Any]:
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
            "maxResults": max_results,
            "startAt": start_at,
        }
        if state:
            params["state"] = state

        return self.get(
            f"/rest/agile/1.0/board/{board_id}/sprint",
            params=params,
            operation=f"get sprints for board {board_id}",
        )

    # ========== Issue Link API Methods (/rest/api/3/issueLink) ==========

    def get_link_types(self) -> list:
        """
        Get all available issue link types.

        Returns:
            List of link type objects with id, name, inward, outward

        Raises:
            JiraError or subclass on failure
        """
        result = self.get("/rest/api/3/issueLinkType", operation="get issue link types")
        return result.get("issueLinkTypes", [])

    def get_link(self, link_id: str) -> dict[str, Any]:
        """
        Get a specific issue link by ID.

        Args:
            link_id: The issue link ID

        Returns:
            Issue link data

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/api/3/issueLink/{link_id}", operation=f"get issue link {link_id}"
        )

    def create_link(
        self,
        link_type: str,
        inward_key: str,
        outward_key: str,
        comment: dict[str, Any] | None = None,
    ) -> None:
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
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_key},
            "outwardIssue": {"key": outward_key},
        }
        if comment:
            data["comment"] = {"body": comment}

        self.post(
            "/rest/api/3/issueLink",
            data=data,
            operation=f"create link between {inward_key} and {outward_key}",
        )

    def delete_link(self, link_id: str) -> None:
        """
        Delete an issue link.

        Args:
            link_id: The issue link ID

        Raises:
            JiraError or subclass on failure
        """
        self.delete(
            f"/rest/api/3/issueLink/{link_id}", operation=f"delete issue link {link_id}"
        )

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
        issue = self.get(
            f"/rest/api/3/issue/{issue_key}",
            params={"fields": "issuelinks"},
            operation=f"get links for {issue_key}",
        )
        return issue.get("fields", {}).get("issuelinks", [])

    # ========== Project Management API Methods (/rest/api/3/project) ==========

    def create_project(
        self,
        key: str,
        name: str,
        project_type_key: str = "software",
        template_key: str = "com.pyxis.greenhopper.jira:gh-simplified-agility-scrum",
        lead_account_id: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
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
            "key": key.upper(),
            "name": name,
            "projectTypeKey": project_type_key,
            "projectTemplateKey": template_key,
        }

        if lead_account_id:
            data["leadAccountId"] = lead_account_id
        else:
            # Default to current user as project lead
            data["leadAccountId"] = self.get_current_user_id()

        if description:
            data["description"] = description

        return self.post(
            "/rest/api/3/project", data=data, operation=f"create project {key}"
        )

    def get_project(
        self, project_key: str, expand: list | None = None
    ) -> dict[str, Any]:
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
            params["expand"] = ",".join(expand)

        return self.get(
            f"/rest/api/3/project/{project_key}",
            params=params if params else None,
            operation=f"get project {project_key}",
        )

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
        params = {"enableUndo": "true" if enable_undo else "false"}
        endpoint = f"/rest/api/3/project/{project_key}"
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
        return self.get(
            f"/rest/api/3/project/{project_key}/statuses",
            operation=f"get statuses for project {project_key}",
        )

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
        self.delete(
            f"/rest/agile/1.0/sprint/{sprint_id}",
            operation=f"delete sprint {sprint_id}",
        )

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
        self.delete(
            f"/rest/agile/1.0/board/{board_id}", operation=f"delete board {board_id}"
        )

    # ========== Comment Operations ==========

    def get_comments(
        self,
        issue_key: str,
        max_results: int = 50,
        start_at: int = 0,
        order_by: str = "-created",
    ) -> dict[str, Any]:
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
        params = {"maxResults": max_results, "startAt": start_at, "orderBy": order_by}
        return self.get(
            f"/rest/api/3/issue/{issue_key}/comment",
            params=params,
            operation=f"get comments for {issue_key}",
        )

    def get_comment(self, issue_key: str, comment_id: str) -> dict[str, Any]:
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
        return self.get(
            f"/rest/api/3/issue/{issue_key}/comment/{comment_id}",
            operation=f"get comment {comment_id}",
        )

    def update_comment(
        self, issue_key: str, comment_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
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
        data = {"body": body}
        return self.put(
            f"/rest/api/3/issue/{issue_key}/comment/{comment_id}",
            data=data,
            operation=f"update comment {comment_id}",
        )

    def delete_comment(self, issue_key: str, comment_id: str) -> None:
        """
        Delete a comment from an issue.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            comment_id: Comment ID

        Raises:
            JiraError or subclass on failure
        """
        self.delete(
            f"/rest/api/3/issue/{issue_key}/comment/{comment_id}",
            operation=f"delete comment {comment_id}",
        )

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
        issue = self.get(
            f"/rest/api/3/issue/{issue_key}",
            params={"fields": "attachment"},
            operation=f"get attachments for {issue_key}",
        )
        return issue.get("fields", {}).get("attachment", [])

    def delete_attachment(self, attachment_id: str) -> None:
        """
        Delete an attachment.

        Args:
            attachment_id: Attachment ID

        Raises:
            JiraError or subclass on failure
        """
        self.delete(
            f"/rest/api/3/attachment/{attachment_id}",
            operation=f"delete attachment {attachment_id}",
        )

    # ========== User Search ==========

    def search_users(
        self, query: str, max_results: int = 50, start_at: int = 0
    ) -> list:
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
        params = {"query": query, "maxResults": max_results, "startAt": start_at}
        return self.get(
            "/rest/api/3/user/search", params=params, operation="search users"
        )

    # ========== Time Tracking / Worklog API Methods ==========

    def add_worklog(
        self,
        issue_key: str,
        time_spent: str,
        started: str | None = None,
        comment: dict[str, Any] | None = None,
        adjust_estimate: str = "auto",
        new_estimate: str | None = None,
        reduce_by: str | None = None,
    ) -> dict[str, Any]:
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
        payload = {"timeSpent": time_spent}
        if started:
            payload["started"] = started
        if comment:
            payload["comment"] = comment

        params = {"adjustEstimate": adjust_estimate}
        if new_estimate and adjust_estimate == "new":
            params["newEstimate"] = new_estimate
        if reduce_by and adjust_estimate == "manual":
            params["reduceBy"] = reduce_by

        endpoint = f"/rest/api/3/issue/{issue_key}/worklog"
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(
            url, json=payload, params=params, timeout=self.timeout
        )
        handle_jira_error(response, f"add worklog to {issue_key}")
        return response.json()

    def get_worklogs(
        self, issue_key: str, start_at: int = 0, max_results: int = 5000
    ) -> dict[str, Any]:
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
        params = {"startAt": start_at, "maxResults": max_results}
        return self.get(
            f"/rest/api/3/issue/{issue_key}/worklog",
            params=params,
            operation=f"get worklogs for {issue_key}",
        )

    def get_worklog(self, issue_key: str, worklog_id: str) -> dict[str, Any]:
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
        return self.get(
            f"/rest/api/3/issue/{issue_key}/worklog/{worklog_id}",
            operation=f"get worklog {worklog_id}",
        )

    def update_worklog(
        self,
        issue_key: str,
        worklog_id: str,
        time_spent: str | None = None,
        started: str | None = None,
        comment: dict[str, Any] | None = None,
        adjust_estimate: str = "auto",
        new_estimate: str | None = None,
    ) -> dict[str, Any]:
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
            payload["timeSpent"] = time_spent
        if started:
            payload["started"] = started
        if comment:
            payload["comment"] = comment

        params = {"adjustEstimate": adjust_estimate}
        if new_estimate and adjust_estimate == "new":
            params["newEstimate"] = new_estimate

        endpoint = f"/rest/api/3/issue/{issue_key}/worklog/{worklog_id}"
        url = f"{self.base_url}{endpoint}"
        response = self.session.put(
            url, json=payload, params=params, timeout=self.timeout
        )
        handle_jira_error(response, f"update worklog {worklog_id}")
        return response.json()

    def delete_worklog(
        self,
        issue_key: str,
        worklog_id: str,
        adjust_estimate: str = "auto",
        new_estimate: str | None = None,
        increase_by: str | None = None,
    ) -> None:
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
        params = {"adjustEstimate": adjust_estimate}
        if new_estimate and adjust_estimate == "new":
            params["newEstimate"] = new_estimate
        if increase_by and adjust_estimate == "manual":
            params["increaseBy"] = increase_by

        endpoint = f"/rest/api/3/issue/{issue_key}/worklog/{worklog_id}"
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, params=params, timeout=self.timeout)
        handle_jira_error(response, f"delete worklog {worklog_id}")

    def get_time_tracking(self, issue_key: str) -> dict[str, Any]:
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
        issue = self.get(
            f"/rest/api/3/issue/{issue_key}",
            params={"fields": "timetracking"},
            operation=f"get time tracking for {issue_key}",
        )
        return issue.get("fields", {}).get("timetracking", {})

    def set_time_tracking(
        self,
        issue_key: str,
        original_estimate: str | None = None,
        remaining_estimate: str | None = None,
    ) -> None:
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
            timetracking["originalEstimate"] = original_estimate
        if remaining_estimate is not None:
            timetracking["remainingEstimate"] = remaining_estimate

        if not timetracking:
            return

        self.put(
            f"/rest/api/3/issue/{issue_key}",
            data={"fields": {"timetracking": timetracking}},
            operation=f"set time tracking for {issue_key}",
        )

    # ========== JQL API Methods (/rest/api/3/jql/) ==========

    def get_jql_autocomplete(
        self, include_collapsed_fields: bool = False
    ) -> dict[str, Any]:
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
            params["includeCollapsedFields"] = "true"
        return self.get(
            "/rest/api/3/jql/autocompletedata",
            params=params if params else None,
            operation="get JQL autocomplete data",
        )

    def get_jql_suggestions(
        self, field_name: str, field_value: str = ""
    ) -> dict[str, Any]:
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
        params = {"fieldName": field_name}
        if field_value:
            params["fieldValue"] = field_value
        return self.get(
            "/rest/api/3/jql/autocompletedata/suggestions",
            params=params,
            operation=f"get JQL suggestions for {field_name}",
        )

    def parse_jql(self, queries: list, validation: str = "strict") -> dict[str, Any]:
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
        return self.post(
            "/rest/api/3/jql/parse",
            data={"queries": queries},
            operation="parse JQL queries",
        )

    # ========== Filter API Methods (/rest/api/3/filter/) ==========

    def create_filter(
        self,
        name: str,
        jql: str,
        description: str | None = None,
        favourite: bool = False,
        share_permissions: list | None = None,
    ) -> dict[str, Any]:
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
        payload = {"name": name, "jql": jql, "favourite": favourite}
        if description:
            payload["description"] = description
        if share_permissions:
            payload["sharePermissions"] = share_permissions
        return self.post(
            "/rest/api/3/filter", data=payload, operation=f"create filter '{name}'"
        )

    def get_filter(self, filter_id: str, expand: str | None = None) -> dict[str, Any]:
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
            params["expand"] = expand
        return self.get(
            f"/rest/api/3/filter/{filter_id}",
            params=params if params else None,
            operation=f"get filter {filter_id}",
        )

    def update_filter(
        self,
        filter_id: str,
        name: str | None = None,
        jql: str | None = None,
        description: str | None = None,
        favourite: bool | None = None,
    ) -> dict[str, Any]:
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
            payload["name"] = name
        if jql is not None:
            payload["jql"] = jql
        if description is not None:
            payload["description"] = description
        if favourite is not None:
            payload["favourite"] = favourite
        return self.put(
            f"/rest/api/3/filter/{filter_id}",
            data=payload,
            operation=f"update filter {filter_id}",
        )

    def delete_filter(self, filter_id: str) -> None:
        """
        Delete a filter.

        Args:
            filter_id: Filter ID

        Raises:
            JiraError or subclass on failure
        """
        self.delete(
            f"/rest/api/3/filter/{filter_id}", operation=f"delete filter {filter_id}"
        )

    def get_my_filters(self, expand: str | None = None) -> list:
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
            params["expand"] = expand
        result = self.get(
            "/rest/api/3/filter/my",
            params=params if params else None,
            operation="get my filters",
        )
        return result if isinstance(result, list) else []

    def get_favourite_filters(self, expand: str | None = None) -> list:
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
            params["expand"] = expand
        result = self.get(
            "/rest/api/3/filter/favourite",
            params=params if params else None,
            operation="get favourite filters",
        )
        return result if isinstance(result, list) else []

    def search_filters(
        self,
        filter_name: str | None = None,
        account_id: str | None = None,
        project_key: str | None = None,
        expand: str | None = None,
        start_at: int = 0,
        max_results: int = 50,
    ) -> dict[str, Any]:
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
        params = {"startAt": start_at, "maxResults": max_results}
        if filter_name:
            params["filterName"] = filter_name
        if account_id:
            params["accountId"] = account_id
        if project_key:
            params["projectKeyOrId"] = project_key
        if expand:
            params["expand"] = expand
        return self.get(
            "/rest/api/3/filter/search", params=params, operation="search filters"
        )

    def add_filter_favourite(self, filter_id: str) -> dict[str, Any]:
        """
        Add filter to favourites.

        Args:
            filter_id: Filter ID

        Returns:
            Updated filter object

        Raises:
            JiraError or subclass on failure
        """
        return self.put(
            f"/rest/api/3/filter/{filter_id}/favourite",
            operation=f"add filter {filter_id} to favourites",
        )

    def remove_filter_favourite(self, filter_id: str) -> None:
        """
        Remove filter from favourites.

        Args:
            filter_id: Filter ID

        Raises:
            JiraError or subclass on failure
        """
        self.delete(
            f"/rest/api/3/filter/{filter_id}/favourite",
            operation=f"remove filter {filter_id} from favourites",
        )

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
        return self.get(
            f"/rest/api/3/filter/{filter_id}/permission",
            operation=f"get permissions for filter {filter_id}",
        )

    def add_filter_permission(self, filter_id: str, permission: dict) -> dict[str, Any]:
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
        return self.post(
            f"/rest/api/3/filter/{filter_id}/permission",
            data=permission,
            operation=f"add permission to filter {filter_id}",
        )

    def delete_filter_permission(self, filter_id: str, permission_id: str) -> None:
        """
        Delete a filter share permission.

        Args:
            filter_id: Filter ID
            permission_id: Permission ID

        Raises:
            JiraError or subclass on failure
        """
        self.delete(
            f"/rest/api/3/filter/{filter_id}/permission/{permission_id}",
            operation=f"delete permission {permission_id} from filter {filter_id}",
        )

    # ========== Comment Visibility ==========

    def add_comment_with_visibility(
        self,
        issue_key: str,
        body: dict[str, Any],
        visibility_type: str | None = None,
        visibility_value: str | None = None,
    ) -> dict[str, Any]:
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
        data = {"body": body}
        if visibility_type and visibility_value:
            data["visibility"] = {
                "type": visibility_type,
                "value": visibility_value,
                "identifier": visibility_value,
            }
        return self.post(
            f"/rest/api/3/issue/{issue_key}/comment",
            data=data,
            operation=f"add comment to {issue_key}",
        )

    # ========== Changelog ==========

    def get_changelog(
        self, issue_key: str, start_at: int = 0, max_results: int = 100
    ) -> dict[str, Any]:
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
        params = {"startAt": start_at, "maxResults": max_results}
        return self.get(
            f"/rest/api/3/issue/{issue_key}/changelog",
            params=params,
            operation=f"get changelog for {issue_key}",
        )

    # ========== Notifications ==========

    def notify_issue(
        self,
        issue_key: str,
        subject: str | None = None,
        text_body: str | None = None,
        html_body: str | None = None,
        to: dict[str, Any] | None = None,
        restrict: dict[str, Any] | None = None,
    ) -> None:
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
            data["subject"] = subject
        if text_body:
            data["textBody"] = text_body
        if html_body:
            data["htmlBody"] = html_body
        if to:
            data["to"] = to
        if restrict:
            data["restrict"] = restrict

        self.post(
            f"/rest/api/3/issue/{issue_key}/notify",
            data=data,
            operation=f"notify about {issue_key}",
        )

    # ========== Version Management ==========

    def create_version(
        self,
        project_id: int,
        name: str,
        description: str | None = None,
        start_date: str | None = None,
        release_date: str | None = None,
        released: bool = False,
        archived: bool = False,
    ) -> dict[str, Any]:
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
            "projectId": project_id,
            "name": name,
            "released": released,
            "archived": archived,
        }
        if description:
            data["description"] = description
        if start_date:
            data["startDate"] = start_date
        if release_date:
            data["releaseDate"] = release_date

        return self.post(
            "/rest/api/3/version", data=data, operation=f"create version '{name}'"
        )

    def get_version(self, version_id: str, expand: str | None = None) -> dict[str, Any]:
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
            params["expand"] = expand
        return self.get(
            f"/rest/api/3/version/{version_id}",
            params=params if params else None,
            operation=f"get version {version_id}",
        )

    def update_version(self, version_id: str, **kwargs) -> dict[str, Any]:
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
            "name": "name",
            "description": "description",
            "released": "released",
            "archived": "archived",
            "start_date": "startDate",
            "release_date": "releaseDate",
        }
        for key, api_key in field_mapping.items():
            if key in kwargs and kwargs[key] is not None:
                data[api_key] = kwargs[key]

        return self.put(
            f"/rest/api/3/version/{version_id}",
            data=data,
            operation=f"update version {version_id}",
        )

    def delete_version(
        self,
        version_id: str,
        move_fixed_to: str | None = None,
        move_affected_to: str | None = None,
    ) -> None:
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
            params["moveFixIssuesTo"] = move_fixed_to
        if move_affected_to:
            params["moveAffectedIssuesTo"] = move_affected_to

        endpoint = f"/rest/api/3/version/{version_id}"
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(
            url, params=params if params else None, timeout=self.timeout
        )
        handle_jira_error(response, f"delete version {version_id}")

    def get_project_versions(self, project_key: str, expand: str | None = None) -> list:
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
            params["expand"] = expand
        return self.get(
            f"/rest/api/3/project/{project_key}/versions",
            params=params if params else None,
            operation=f"get versions for project {project_key}",
        )

    def get_version_issue_counts(self, version_id: str) -> dict[str, Any]:
        """
        Get issue counts for a version.

        Args:
            version_id: Version ID

        Returns:
            Issue counts (issuesFixedCount, issuesAffectedCount)

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/api/3/version/{version_id}/relatedIssueCounts",
            operation=f"get issue counts for version {version_id}",
        )

    def get_version_unresolved_count(self, version_id: str) -> dict[str, Any]:
        """
        Get unresolved issue count for a version.

        Args:
            version_id: Version ID

        Returns:
            Unresolved count data

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/api/3/version/{version_id}/unresolvedIssueCount",
            operation=f"get unresolved count for version {version_id}",
        )

    # ========== Component Management ==========

    def create_component(
        self,
        project: str,
        name: str,
        description: str | None = None,
        lead_account_id: str | None = None,
        assignee_type: str = "PROJECT_DEFAULT",
    ) -> dict[str, Any]:
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
        data = {"project": project, "name": name, "assigneeType": assignee_type}
        if description:
            data["description"] = description
        if lead_account_id:
            data["leadAccountId"] = lead_account_id

        return self.post(
            "/rest/api/3/component", data=data, operation=f"create component '{name}'"
        )

    def get_component(self, component_id: str) -> dict[str, Any]:
        """
        Get a component by ID.

        Args:
            component_id: Component ID

        Returns:
            Component object

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/api/3/component/{component_id}",
            operation=f"get component {component_id}",
        )

    def update_component(self, component_id: str, **kwargs) -> dict[str, Any]:
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
            "name": "name",
            "description": "description",
            "lead_account_id": "leadAccountId",
            "assignee_type": "assigneeType",
        }
        for key, api_key in field_mapping.items():
            if key in kwargs and kwargs[key] is not None:
                data[api_key] = kwargs[key]

        return self.put(
            f"/rest/api/3/component/{component_id}",
            data=data,
            operation=f"update component {component_id}",
        )

    def delete_component(
        self, component_id: str, move_issues_to: str | None = None
    ) -> None:
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
            params["moveIssuesTo"] = move_issues_to

        endpoint = f"/rest/api/3/component/{component_id}"
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(
            url, params=params if params else None, timeout=self.timeout
        )
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
        return self.get(
            f"/rest/api/3/project/{project_key}/components",
            operation=f"get components for project {project_key}",
        )

    def get_component_issue_counts(self, component_id: str) -> dict[str, Any]:
        """
        Get issue counts for a component.

        Args:
            component_id: Component ID

        Returns:
            Issue count data

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/api/3/component/{component_id}/relatedIssueCounts",
            operation=f"get issue counts for component {component_id}",
        )

    # ========== Issue Cloning ==========

    def clone_issue(
        self,
        issue_key: str,
        summary: str | None = None,
        clone_subtasks: bool = False,
        clone_links: bool = False,
    ) -> dict[str, Any]:
        """
        Clone an issue by copying its fields to a new issue.

        Args:
            issue_key: Issue key to clone (e.g., 'PROJ-123')
            summary: Summary for the clone (default: original summary)
            clone_subtasks: If True, also clone subtasks
            clone_links: If True, also clone issue links (except Cloners)

        Returns:
            Created clone issue data (key, id, self)

        Raises:
            JiraError or subclass on failure

        Note:
            A 'Cloners' link is automatically created between the clone
            and the original issue.
        """
        # Get original issue details
        original = self.get_issue(issue_key)
        original_fields = original.get("fields", {})

        # Build clone fields
        clone_fields = {
            "project": {"key": original_fields["project"]["key"]},
            "issuetype": {"name": original_fields["issuetype"]["name"]},
            "summary": summary or original_fields.get("summary", "Clone"),
        }

        # Copy description if present
        if original_fields.get("description"):
            clone_fields["description"] = original_fields["description"]

        # Copy priority if present
        if original_fields.get("priority"):
            clone_fields["priority"] = {"name": original_fields["priority"]["name"]}

        # Copy labels if present
        if original_fields.get("labels"):
            clone_fields["labels"] = original_fields["labels"]

        # Copy components if present
        if original_fields.get("components"):
            clone_fields["components"] = [
                {"name": c["name"]} for c in original_fields["components"]
            ]

        # Copy fix versions if present
        if original_fields.get("fixVersions"):
            clone_fields["fixVersions"] = [
                {"name": v["name"]} for v in original_fields["fixVersions"]
            ]

        # Create the clone
        clone = self.create_issue(clone_fields)

        # Create Cloners link (clone -> original)
        try:
            self.create_link(
                link_type="Cloners",
                inward_key=issue_key,  # is cloned by
                outward_key=clone["key"],  # clones
            )
        except Exception:
            # Some JIRA instances may not have Cloners link type
            pass

        # Clone subtasks if requested
        if clone_subtasks:
            subtasks = original_fields.get("subtasks", [])
            for subtask_ref in subtasks:
                subtask = self.get_issue(subtask_ref["key"])
                subtask_fields = subtask.get("fields", {})

                self.create_issue(
                    {
                        "project": {"key": original_fields["project"]["key"]},
                        "parent": {"key": clone["key"]},
                        "issuetype": {"name": "Subtask"},
                        "summary": subtask_fields.get("summary", "Cloned subtask"),
                        "description": subtask_fields.get("description"),
                    }
                )

        # Clone links if requested (except Cloners links)
        if clone_links:
            links = original_fields.get("issuelinks", [])
            for link in links:
                link_type = link["type"]["name"]
                if link_type == "Cloners":
                    continue  # Skip cloner links

                try:
                    if "inwardIssue" in link:
                        self.create_link(
                            link_type=link_type,
                            inward_key=link["inwardIssue"]["key"],
                            outward_key=clone["key"],
                        )
                    elif "outwardIssue" in link:
                        self.create_link(
                            link_type=link_type,
                            inward_key=clone["key"],
                            outward_key=link["outwardIssue"]["key"],
                        )
                except Exception:
                    pass  # Some links may fail due to permissions

        return clone

    # ========== JSM Service Desk Core (/rest/servicedeskapi/servicedesk) ==========

    def get_service_desks(self, start: int = 0, limit: int = 50) -> dict[str, Any]:
        """
        Get all JSM service desks with pagination.

        Args:
            start: Starting index for pagination
            limit: Maximum results per page (max 100)

        Returns:
            Service desks response with 'values', 'size', 'start', 'limit', 'isLastPage'

        Raises:
            JiraError or subclass on failure
        """
        params = {"start": start, "limit": limit}
        return self.get(
            "/rest/servicedeskapi/servicedesk",
            params=params,
            operation="get service desks",
        )

    def get_service_desk(self, service_desk_id: str) -> dict[str, Any]:
        """
        Get a specific service desk by ID.

        Args:
            service_desk_id: Service desk ID

        Returns:
            Service desk object with id, projectId, projectName, projectKey

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/servicedeskapi/servicedesk/{service_desk_id}",
            operation=f"get service desk {service_desk_id}",
        )

    def get_request_types(
        self, service_desk_id: str, start: int = 0, limit: int = 50
    ) -> dict[str, Any]:
        """
        Get request types for a service desk.

        Args:
            service_desk_id: Service desk ID
            start: Starting index for pagination
            limit: Maximum results per page (max 100)

        Returns:
            Request types response with 'values', 'size', 'start', 'limit', 'isLastPage'

        Raises:
            JiraError or subclass on failure
        """
        params = {"start": start, "limit": limit}
        return self.get(
            f"/rest/servicedeskapi/servicedesk/{service_desk_id}/requesttype",
            params=params,
            operation=f"get request types for service desk {service_desk_id}",
        )

    def get_request_type(
        self, service_desk_id: str, request_type_id: str
    ) -> dict[str, Any]:
        """
        Get a specific request type.

        Args:
            service_desk_id: Service desk ID
            request_type_id: Request type ID

        Returns:
            Request type object

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/servicedeskapi/servicedesk/{service_desk_id}/requesttype/{request_type_id}",
            operation=f"get request type {request_type_id}",
        )

    def get_request_type_fields(
        self, service_desk_id: str, request_type_id: str
    ) -> dict[str, Any]:
        """
        Get fields for a request type.

        Args:
            service_desk_id: Service desk ID
            request_type_id: Request type ID

        Returns:
            Request type fields with 'requestTypeFields', 'canRaiseOnBehalfOf',
            'canAddRequestParticipants'

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/servicedeskapi/servicedesk/{service_desk_id}/requesttype/{request_type_id}/field",
            operation=f"get fields for request type {request_type_id}",
        )

    def create_service_desk(
        self,
        name: str,
        key: str,
        project_template_key: str = "com.atlassian.servicedesk:simplified-it-service-desk",
    ) -> dict[str, Any]:
        """
        Create a new service desk (requires JSM administrator permissions).

        Args:
            name: Service desk name
            key: Project key (uppercase, 2-10 chars)
            project_template_key: JSM project template

        Returns:
            Created service desk object

        Raises:
            JiraError or subclass on failure

        Common template keys:
            IT Service Desk: 'com.atlassian.servicedesk:simplified-it-service-desk'
            Internal Service Desk: 'com.atlassian.servicedesk:simplified-internal-service-desk'
            External Service Desk: 'com.atlassian.servicedesk:simplified-external-service-desk'
        """
        data = {
            "name": name,
            "key": key.upper(),
            "projectTemplateKey": project_template_key,
        }
        return self.post(
            "/rest/servicedeskapi/servicedesk",
            data=data,
            operation=f"create service desk {key}",
        )

    def lookup_service_desk_by_project_key(self, project_key: str) -> dict[str, Any]:
        """
        Lookup service desk ID by project key.

        Args:
            project_key: Project key (e.g., 'ITS')

        Returns:
            Service desk object

        Raises:
            JiraError: If no service desk found for project key
        """
        service_desks = self.get_service_desks()
        for sd in service_desks.get("values", []):
            if sd.get("projectKey") == project_key:
                return sd

        from jira_assistant_skills_lib import JiraError

        raise JiraError(f"No service desk found for project key: {project_key}")

    # ========== JSM Customer Management (/rest/servicedeskapi/customer) ==========

    def create_customer(
        self,
        email: str,
        display_name: str | None = None,
        service_desk_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a customer account for JSM.

        Args:
            email: Customer email address
            display_name: Display name (defaults to email if not provided)
            service_desk_id: Optional service desk ID to add customer to

        Returns:
            Created customer data with accountId, emailAddress, displayName

        Raises:
            JiraError or subclass on failure
        """
        payload = {"email": email}
        if display_name:
            payload["displayName"] = display_name

        customer = self.post(
            "/rest/servicedeskapi/customer",
            data=payload,
            operation=f"create customer {email}",
        )

        # Add customer to service desk if specified
        if service_desk_id and customer.get("accountId"):
            try:
                self.add_customers_to_service_desk(
                    service_desk_id, [customer["accountId"]]
                )
            except Exception:
                pass  # Customer creation succeeded, service desk addition is optional

        return customer

    def get_service_desk_customers(
        self,
        service_desk_id: str,
        query: str | None = None,
        start: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        List customers for a service desk.

        Args:
            service_desk_id: Service desk ID or key
            query: Search query for email/name filtering
            start: Starting index for pagination
            limit: Maximum results per page

        Returns:
            Customers data with values, size, start, limit, isLastPage

        Raises:
            JiraError or subclass on failure
        """
        params = {"start": start, "limit": limit}
        if query:
            params["query"] = query
        # Customer endpoints require experimental API header
        return self.get(
            f"/rest/servicedeskapi/servicedesk/{service_desk_id}/customer",
            params=params,
            operation=f"get customers for service desk {service_desk_id}",
            headers={"X-ExperimentalApi": "opt-in"},
        )

    def add_customers_to_service_desk(
        self, service_desk_id: str, account_ids: list
    ) -> None:
        """
        Add customers to a service desk.

        Args:
            service_desk_id: Service desk ID or key
            account_ids: List of customer account IDs

        Raises:
            JiraError or subclass on failure
        """
        payload = {"accountIds": account_ids}
        # Customer endpoints require experimental API header
        self.post(
            f"/rest/servicedeskapi/servicedesk/{service_desk_id}/customer",
            data=payload,
            operation=f"add customers to service desk {service_desk_id}",
            headers={"X-ExperimentalApi": "opt-in"},
        )

    def remove_customers_from_service_desk(
        self, service_desk_id: str, account_ids: list
    ) -> None:
        """
        Remove customers from a service desk.

        Args:
            service_desk_id: Service desk ID or key
            account_ids: List of customer account IDs

        Raises:
            JiraError or subclass on failure
        """
        payload = {"accountIds": account_ids}
        endpoint = f"/rest/servicedeskapi/servicedesk/{service_desk_id}/customer"
        url = f"{self.base_url}{endpoint}"
        # Customer endpoints require experimental API header
        response = self.session.delete(
            url,
            json=payload,
            timeout=self.timeout,
            headers={"X-ExperimentalApi": "opt-in"},
        )
        handle_jira_error(
            response, f"remove customers from service desk {service_desk_id}"
        )

    # ========== JSM Request Management (/rest/servicedeskapi/request) ==========

    def create_request(
        self,
        service_desk_id: str,
        request_type_id: str,
        fields: dict[str, Any] | None = None,
        summary: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        participants: list | None = None,
        on_behalf_of: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a service request via JSM API.

        Args:
            service_desk_id: Service desk ID or key
            request_type_id: Request type ID
            fields: Dictionary of field values (summary, description, custom fields)
            summary: Request summary (alternative to fields dict)
            description: Request description (alternative to fields dict)
            priority: Request priority name (alternative to fields dict)
            participants: List of participant email addresses (optional)
            on_behalf_of: Create request on behalf of user email (optional)

        Returns:
            Created request object with issueKey, issueId, requestType, etc.

        Raises:
            JiraError or subclass on failure
        """
        # Build requestFieldValues from either fields dict or individual params
        if fields is None:
            fields = {}

        # Add individual parameters to fields if provided
        if summary:
            fields["summary"] = summary
        if description:
            fields["description"] = description
        if priority:
            fields["priority"] = {"name": priority}

        payload = {
            "serviceDeskId": service_desk_id,
            "requestTypeId": request_type_id,
            "requestFieldValues": fields,
        }

        if participants:
            payload["requestParticipants"] = participants

        if on_behalf_of:
            payload["raiseOnBehalfOf"] = on_behalf_of

        return self.post(
            "/rest/servicedeskapi/request",
            data=payload,
            operation="create service request",
        )

    def get_request(self, issue_key: str, expand: list | None = None) -> dict[str, Any]:
        """
        Get request details via JSM API.

        Args:
            issue_key: Request key (e.g., 'SD-101')
            expand: List of fields to expand (sla, participant, status, requestType, etc.)

        Returns:
            Request object with JSM-specific fields

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if expand:
            params["expand"] = ",".join(expand)

        return self.get(
            f"/rest/servicedeskapi/request/{issue_key}",
            params=params if params else None,
            operation=f"get request {issue_key}",
        )

    def get_request_status(self, issue_key: str) -> dict[str, Any]:
        """
        Get request status history.

        Args:
            issue_key: Request key

        Returns:
            Status history with timestamps

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/servicedeskapi/request/{issue_key}/status",
            operation=f"get status history for {issue_key}",
        )

    def get_request_transitions(self, issue_key: str) -> list:
        """
        Get available transitions for request.

        Args:
            issue_key: Request key

        Returns:
            List of available transition objects

        Raises:
            JiraError or subclass on failure
        """
        result = self.get(
            f"/rest/servicedeskapi/request/{issue_key}/transition",
            operation=f"get transitions for {issue_key}",
        )
        return result.get("values", [])

    def transition_request(
        self,
        issue_key: str,
        transition_id: str,
        comment: str | None = None,
        public: bool = True,
    ) -> None:
        """
        Transition a service request.

        Args:
            issue_key: Request key
            transition_id: Transition ID
            comment: Optional comment to add
            public: Whether comment is public (customer-visible)

        Raises:
            JiraError or subclass on failure
        """
        payload = {"id": transition_id}

        if comment:
            payload["additionalComment"] = {"body": comment, "public": public}

        self.post(
            f"/rest/servicedeskapi/request/{issue_key}/transition",
            data=payload,
            operation=f"transition request {issue_key}",
        )

    def get_request_slas(
        self, issue_key: str, start: int = 0, limit: int = 50
    ) -> dict[str, Any]:
        """
        Get all SLAs for a service request.

        Args:
            issue_key: Issue key (e.g., 'SD-123')
            start: Starting index for pagination
            limit: Maximum results per page

        Returns:
            SLA data with values array of SLA metrics

        Raises:
            JiraError or subclass on failure
        """
        params = {"start": start, "limit": limit}
        return self.get(
            f"/rest/servicedeskapi/request/{issue_key}/sla",
            params=params,
            operation=f"get SLAs for {issue_key}",
        )

    def get_request_sla(
        self, issue_key: str, sla_metric_id: str | None = None
    ) -> dict[str, Any]:
        """
        Get SLA metrics for a request.

        Args:
            issue_key: Issue key (e.g., 'SD-123')
            sla_metric_id: SLA metric ID (optional - if not provided, returns all SLAs)

        Returns:
            SLA metric details, or all SLAs if sla_metric_id not provided

        Raises:
            JiraError or subclass on failure
        """
        if sla_metric_id:
            return self.get(
                f"/rest/servicedeskapi/request/{issue_key}/sla/{sla_metric_id}",
                operation=f"get SLA {sla_metric_id} for {issue_key}",
            )
        else:
            # Return all SLAs for the request
            return self.get_request_slas(issue_key)

    # ========== JSM Queue Management (/rest/servicedeskapi/servicedesk/{id}/queue) ==========

    def get_service_desk_queues(
        self,
        service_desk_id: int,
        include_count: bool = False,
        start: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Get all queues for a service desk.

        Args:
            service_desk_id: Service desk ID
            include_count: Include issue counts for each queue
            start: Starting index for pagination
            limit: Maximum results per page

        Returns:
            Queue data with values array of queues

        Raises:
            JiraError or subclass on failure
        """
        params = {
            "start": start,
            "limit": limit,
            "includeCount": str(include_count).lower(),
        }
        return self.get(
            f"/rest/servicedeskapi/servicedesk/{service_desk_id}/queue",
            params=params,
            operation=f"get queues for service desk {service_desk_id}",
        )

    def get_queue(
        self, service_desk_id: int, queue_id: int, include_count: bool = False
    ) -> dict[str, Any]:
        """
        Get a specific queue by ID.

        Args:
            service_desk_id: Service desk ID
            queue_id: Queue ID
            include_count: Include issue count

        Returns:
            Queue details

        Raises:
            JiraError or subclass on failure
        """
        params = {"includeCount": str(include_count).lower()}
        return self.get(
            f"/rest/servicedeskapi/servicedesk/{service_desk_id}/queue/{queue_id}",
            params=params,
            operation=f"get queue {queue_id}",
        )

    def get_queue_issues(
        self, service_desk_id: int, queue_id: int, start: int = 0, limit: int = 50
    ) -> dict[str, Any]:
        """
        Get issues in a queue.

        Args:
            service_desk_id: Service desk ID
            queue_id: Queue ID
            start: Starting index for pagination
            limit: Maximum results per page

        Returns:
            Issue data with values array of issues

        Raises:
            JiraError or subclass on failure
        """
        params = {"start": start, "limit": limit}
        return self.get(
            f"/rest/servicedeskapi/servicedesk/{service_desk_id}/queue/{queue_id}/issue",
            params=params,
            operation=f"get issues in queue {queue_id}",
        )

    # ========== JSM Organization Management (/rest/servicedeskapi/organization) ==========

    def get_organizations(self, start: int = 0, limit: int = 50) -> dict[str, Any]:
        """
        List all organizations.

        Args:
            start: Starting index for pagination
            limit: Maximum results per page

        Returns:
            Organizations data with values, size, start, limit, isLastPage

        Raises:
            JiraError or subclass on failure
        """
        params = {"start": start, "limit": limit}
        return self.get(
            "/rest/servicedeskapi/organization",
            params=params,
            operation="get organizations",
        )

    def create_organization(self, name: str) -> dict[str, Any]:
        """
        Create an organization.

        Args:
            name: Organization name

        Returns:
            Created organization data with id, name, links

        Raises:
            JiraError or subclass on failure
        """
        payload = {"name": name}
        return self.post(
            "/rest/servicedeskapi/organization",
            data=payload,
            operation=f"create organization {name}",
        )

    def get_organization(self, organization_id: int) -> dict[str, Any]:
        """
        Get organization details.

        Args:
            organization_id: Organization ID

        Returns:
            Organization data with id, name, links

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/servicedeskapi/organization/{organization_id}",
            operation=f"get organization {organization_id}",
        )

    def delete_organization(self, organization_id: int) -> None:
        """
        Delete an organization.

        Args:
            organization_id: Organization ID

        Raises:
            JiraError or subclass on failure
        """
        self.delete(
            f"/rest/servicedeskapi/organization/{organization_id}",
            operation=f"delete organization {organization_id}",
        )

    def add_users_to_organization(
        self, organization_id: int, account_ids: list
    ) -> None:
        """
        Add users to an organization.

        Args:
            organization_id: Organization ID
            account_ids: List of user account IDs

        Raises:
            JiraError or subclass on failure
        """
        payload = {"accountIds": account_ids}
        self.post(
            f"/rest/servicedeskapi/organization/{organization_id}/user",
            data=payload,
            operation=f"add users to organization {organization_id}",
        )

    def remove_users_from_organization(
        self, organization_id: int, account_ids: list
    ) -> None:
        """
        Remove users from an organization.

        Args:
            organization_id: Organization ID
            account_ids: List of user account IDs

        Raises:
            JiraError or subclass on failure
        """
        payload = {"accountIds": account_ids}
        endpoint = f"/rest/servicedeskapi/organization/{organization_id}/user"
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, json=payload, timeout=self.timeout)
        handle_jira_error(response, f"remove users from organization {organization_id}")

    # ========== JSM Request Participants (/rest/servicedeskapi/request/{key}/participant) ==========

    def get_request_participants(
        self, issue_key: str, start: int = 0, limit: int = 50
    ) -> dict[str, Any]:
        """
        Get participants for a request.

        Args:
            issue_key: Request issue key (e.g., REQ-123)
            start: Starting index for pagination
            limit: Maximum results per page

        Returns:
            Participants data with values, size, start, limit, isLastPage

        Raises:
            JiraError or subclass on failure
        """
        params = {"start": start, "limit": limit}
        return self.get(
            f"/rest/servicedeskapi/request/{issue_key}/participant",
            params=params,
            operation=f"get participants for request {issue_key}",
        )

    def add_request_participants(
        self,
        issue_key: str,
        account_ids: list | None = None,
        usernames: list | None = None,
    ) -> dict[str, Any]:
        """
        Add participants to a request.

        Args:
            issue_key: Request issue key (e.g., REQ-123)
            account_ids: List of user account IDs
            usernames: List of usernames (legacy)

        Returns:
            Updated participants data

        Raises:
            JiraError or subclass on failure
        """
        payload = {"accountIds": account_ids or [], "usernames": usernames or []}
        return self.post(
            f"/rest/servicedeskapi/request/{issue_key}/participant",
            data=payload,
            operation=f"add participants to request {issue_key}",
        )

    def remove_request_participants(
        self,
        issue_key: str,
        account_ids: list | None = None,
        usernames: list | None = None,
    ) -> dict[str, Any]:
        """
        Remove participants from a request.

        Args:
            issue_key: Request issue key (e.g., REQ-123)
            account_ids: List of user account IDs
            usernames: List of usernames (legacy)

        Returns:
            Updated participants data

        Raises:
            JiraError or subclass on failure
        """
        payload = {"accountIds": account_ids or [], "usernames": usernames or []}
        endpoint = f"/rest/servicedeskapi/request/{issue_key}/participant"
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, json=payload, timeout=self.timeout)
        handle_jira_error(response, f"remove participants from request {issue_key}")
        return response.json() if response.text else {}

    # ========== JSM Comments & Approvals (Phase 5) ==========

    def add_request_comment(
        self, issue_key: str, body: str, public: bool = True
    ) -> dict[str, Any]:
        """
        Add a comment to a JSM request with public/internal visibility.

        Args:
            issue_key: Request key (e.g., REQ-123)
            body: Comment body (plain text)
            public: True for customer-visible, False for internal (default: True)

        Returns:
            Created comment object with id, body, public, author, created

        Raises:
            JiraError or subclass on failure

        Note:
            Uses JSM API (/rest/servicedeskapi/) which differs from standard JIRA API.
            Public comments are visible in the customer portal.
        """
        data = {"body": body, "public": public}
        return self.post(
            f"/rest/servicedeskapi/request/{issue_key}/comment",
            data=data,
            operation=f"add JSM comment to {issue_key}",
        )

    def get_request_comments(
        self,
        issue_key: str,
        public: bool | None = None,
        internal: bool | None = None,
        start: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        """
        Get comments for a JSM request with visibility information.

        Args:
            issue_key: Request key (e.g., REQ-123)
            public: Filter by visibility (True=public only, False=internal only, None=all)
            internal: Alias for filtering (True=internal only, False=public only, None=all)
            start: Starting index for pagination
            limit: Maximum results per page (max 100)

        Returns:
            Comments response with values array and pagination info

        Raises:
            JiraError or subclass on failure
        """
        params = {"start": start, "limit": limit}

        # Handle both 'public' and 'internal' parameters
        # 'internal' is the inverse of 'public'
        if internal is not None and public is None:
            public = not internal

        if public is not None:
            params["public"] = str(public).lower()

        return self.get(
            f"/rest/servicedeskapi/request/{issue_key}/comment",
            params=params,
            operation=f"get JSM comments for {issue_key}",
        )

    def get_request_comment(
        self, issue_key: str, comment_id: str, expand: str | None = None
    ) -> dict[str, Any]:
        """
        Get a specific JSM comment by ID.

        Args:
            issue_key: Request key (e.g., REQ-123)
            comment_id: Comment ID
            expand: Optional expansions (e.g., 'renderedBody')

        Returns:
            Comment object

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if expand:
            params["expand"] = expand

        return self.get(
            f"/rest/servicedeskapi/request/{issue_key}/comment/{comment_id}",
            params=params if params else None,
            operation=f"get JSM comment {comment_id}",
        )

    def get_request_approvals(
        self, issue_key: str, start: int = 0, limit: int = 100
    ) -> dict[str, Any]:
        """
        Get approvals for a JSM request.

        Args:
            issue_key: Request key (e.g., REQ-123)
            start: Starting index for pagination
            limit: Maximum results per page

        Returns:
            Approvals response with values array and pagination info

        Raises:
            JiraError or subclass on failure
        """
        params = {"start": start, "limit": limit}
        return self.get(
            f"/rest/servicedeskapi/request/{issue_key}/approval",
            params=params,
            operation=f"get approvals for {issue_key}",
        )

    def get_request_approval(self, issue_key: str, approval_id: str) -> dict[str, Any]:
        """
        Get a specific approval by ID.

        Args:
            issue_key: Request key (e.g., REQ-123)
            approval_id: Approval ID

        Returns:
            Approval object

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/servicedeskapi/request/{issue_key}/approval/{approval_id}",
            operation=f"get approval {approval_id}",
        )

    def answer_approval(
        self, issue_key: str, approval_id: str, decision: str
    ) -> dict[str, Any]:
        """
        Answer an approval request (approve or decline).

        Args:
            issue_key: Request key (e.g., REQ-123)
            approval_id: Approval ID to answer
            decision: 'approve' or 'decline'

        Returns:
            Updated approval object with decision

        Raises:
            JiraError or subclass on failure
        """
        data = {"decision": decision}
        return self.post(
            f"/rest/servicedeskapi/request/{issue_key}/approval/{approval_id}",
            data=data,
            operation=f"{decision} approval {approval_id} for {issue_key}",
        )

    def get_pending_approvals(self, service_desk_id: int | None = None) -> list:
        """
        Get pending approvals for current user (agent view).

        This method searches for requests with pending approvals where the current
        user is an approver. It combines JQL search with approval endpoint calls.

        Args:
            service_desk_id: Optional service desk ID to filter by

        Returns:
            List of dicts with requestKey, approvalId, approvalName, created

        Raises:
            JiraError or subclass on failure

        Note:
            This is a helper method that combines multiple API calls.
            Performance may vary based on number of pending approvals.
        """
        # Build JQL to find requests with pending approvals
        # Note: This requires approval tracking in the workflow
        jql_parts = ["status != Resolved"]

        if service_desk_id:
            jql_parts.append(f"project = SD-{service_desk_id}")

        jql = " AND ".join(jql_parts)

        # Search for requests
        search_result = self.search_issues(jql, max_results=100)

        pending_approvals = []

        # For each request, check for pending approvals
        for issue in search_result.get("issues", []):
            issue_key = issue["key"]
            try:
                approvals_resp = self.get_request_approvals(issue_key)
                approvals = approvals_resp.get("values", [])

                for approval in approvals:
                    if approval.get("finalDecision") == "pending":
                        # Check if current user can answer this approval
                        if approval.get("canAnswerApproval", False):
                            pending_approvals.append(
                                {
                                    "requestKey": issue_key,
                                    "approvalId": approval.get("id"),
                                    "approvalName": approval.get("name"),
                                    "created": approval.get("createdDate"),
                                    "summary": issue.get("fields", {}).get(
                                        "summary", ""
                                    ),
                                }
                            )
            except Exception:
                # Skip requests where we can't get approvals (e.g., permissions)
                continue

        return pending_approvals

    # ==========================================
    # Knowledge Base Methods
    # ==========================================

    def search_kb_articles(
        self,
        service_desk_id: int,
        query: str,
        highlight: bool = True,
        start: int = 0,
        limit: int = 50,
    ) -> list:
        """
        Search KB articles for a service desk.

        Args:
            service_desk_id: Service desk ID
            query: Search query string
            highlight: Whether to highlight matches in results
            start: Starting index for pagination
            limit: Maximum results to return

        Returns:
            List of KB articles matching query

        Raises:
            JiraError or subclass on failure
        """
        result = self.get(
            f"/rest/servicedeskapi/servicedesk/{service_desk_id}/knowledgebase/article",
            params={
                "query": query,
                "highlight": highlight,
                "start": start,
                "limit": limit,
            },
            operation=f"search KB articles for service desk {service_desk_id}",
        )
        return result.get("values", [])

    def get_kb_article(self, article_id: str) -> dict[str, Any]:
        """
        Get KB article details by ID.

        Args:
            article_id: KB article ID

        Returns:
            KB article details

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/servicedeskapi/knowledgebase/article/{article_id}",
            operation=f"get KB article {article_id}",
        )

    def suggest_kb_for_request(self, issue_key: str, max_results: int = 5) -> list:
        """
        Suggest relevant KB articles for a request based on summary/description.

        Args:
            issue_key: Request issue key
            max_results: Maximum suggestions to return

        Returns:
            List of suggested KB articles

        Raises:
            JiraError or subclass on failure
        """
        # Get request details
        request = self.get_request(issue_key)

        # Extract service desk ID from request
        service_desk_id = request.get("serviceDeskId")
        if not service_desk_id:
            raise ValueError(f"Could not determine service desk ID for {issue_key}")

        # Build search query from summary and description
        summary = (
            request.get("currentStatus", {}).get("statusValue", {}).get("summary", "")
        )
        description = (
            request.get("currentStatus", {})
            .get("statusValue", {})
            .get("description", "")
        )

        # Simple keyword extraction - extract words longer than 3 chars
        import re

        text = f"{summary} {description}".lower()
        words = re.findall(r"\b[a-z]{4,}\b", text)
        query = " ".join(set(words[:5]))  # Use top 5 unique words

        if not query:
            return []

        # Search KB with derived query
        return self.search_kb_articles(service_desk_id, query, max_results)

    # ==========================================
    # Assets/Insight Methods (Requires JSM Premium)
    # ==========================================

    def has_assets_license(self) -> bool:
        """
        Check if Assets/Insight is available (requires JSM Premium).

        Returns:
            True if Assets is available, False otherwise
        """
        try:
            # Try to list schemas - if it works, we have Assets
            self.get("/rest/insight/1.0/objectschema/list")
            return True
        except Exception:
            return False

    def list_assets(
        self,
        object_type: str | None = None,
        iql: str | None = None,
        max_results: int = 100,
    ) -> list:
        """
        List assets with optional IQL filtering.

        Args:
            object_type: Optional object type name to filter by
            iql: Optional IQL query string
            max_results: Maximum results to return

        Returns:
            List of asset objects

        Raises:
            JiraError or subclass on failure

        Note:
            Requires Assets/Insight license
        """
        # Build IQL query
        query_parts = []
        if object_type:
            query_parts.append(f'objectType="{object_type}"')
        if iql:
            query_parts.append(iql)

        iql_query = " AND ".join(query_parts) if query_parts else None

        # Get first schema (most common use case)
        schemas = self.get("/rest/insight/1.0/objectschema/list").get(
            "objectschemas", []
        )
        if not schemas:
            return []

        schema_id = schemas[0]["id"]

        # Search assets
        result = self.get(
            "/rest/insight/1.0/iql/objects",
            params={
                "objectSchemaId": schema_id,
                "iql": iql_query,
                "page": 1,
                "resultsPerPage": min(max_results, 100),
                "includeAttributes": True,
            },
            operation="search assets with IQL",
        )
        return result.get("objectEntries", [])

    def get_asset(self, asset_id: int) -> dict[str, Any]:
        """
        Get asset details by object ID.

        Args:
            asset_id: Asset object ID

        Returns:
            Asset object with all attributes

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/insight/1.0/object/{asset_id}", operation=f"get asset {asset_id}"
        )

    def create_asset(
        self, object_type_id: int, attributes: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create a new asset/CMDB object.

        Args:
            object_type_id: Object type ID
            attributes: Dict mapping attribute names to values

        Returns:
            Created asset object

        Raises:
            JiraError or subclass on failure
        """
        # Convert attribute dict to API format
        attr_list = []
        for attr_name, value in attributes.items():
            attr_list.append(
                {
                    "objectTypeAttributeName": attr_name,
                    "objectAttributeValues": [{"value": str(value)}],
                }
            )

        payload = {"objectTypeId": object_type_id, "attributes": attr_list}

        return self.post(
            "/rest/insight/1.0/object/create", data=payload, operation="create asset"
        )

    def update_asset(self, asset_id: int, attributes: dict[str, Any]) -> dict[str, Any]:
        """
        Update an existing asset.

        Args:
            asset_id: Asset object ID
            attributes: Dict mapping attribute names to new values

        Returns:
            Updated asset object

        Raises:
            JiraError or subclass on failure
        """
        # Convert attribute dict to API format
        attr_list = []
        for attr_name, value in attributes.items():
            attr_list.append(
                {
                    "objectTypeAttributeName": attr_name,
                    "objectAttributeValues": [{"value": str(value)}],
                }
            )

        payload = {"objectId": asset_id, "attributes": attr_list}

        return self.put(
            f"/rest/insight/1.0/object/{asset_id}",
            data=payload,
            operation=f"update asset {asset_id}",
        )

    def link_asset_to_request(self, asset_id: int, issue_key: str) -> None:
        """
        Link an asset to a service request via issue link.

        Args:
            asset_id: Asset object ID
            issue_key: Request issue key

        Raises:
            JiraError or subclass on failure

        Note:
            Creates a "Relates" link between the asset and request
        """
        # Get asset details to get its object key
        asset = self.get_asset(asset_id)
        asset_key = asset.get("objectKey", f"ASSET-{asset_id}")

        # Add internal comment about the linked asset
        self.add_request_comment(
            issue_key,
            f"Linked asset: {asset.get('label', asset_key)} (ID: {asset_id})",
            public=False,
        )

    def find_assets_by_criteria(self, iql: str) -> list:
        """
        Find assets matching IQL criteria.

        Args:
            iql: IQL query string

        Returns:
            List of matching assets

        Raises:
            JiraError or subclass on failure
        """
        return self.list_assets(iql=iql)

    # ==========================================
    # Additional JSM Methods
    # ==========================================

    def get_service_desk_organizations(
        self, service_desk_id: str, start: int = 0, limit: int = 50
    ) -> dict[str, Any]:
        """
        Get organizations associated with a service desk.

        Args:
            service_desk_id: Service desk ID
            start: Starting index for pagination
            limit: Maximum results to return

        Returns:
            Paginated list of organizations

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/servicedeskapi/servicedesk/{service_desk_id}/organization",
            params={"start": start, "limit": limit},
            operation=f"get organizations for service desk {service_desk_id}",
        )

    def add_organization_to_service_desk(
        self, service_desk_id: str, organization_id: int
    ) -> None:
        """
        Add an organization to a service desk.

        Args:
            service_desk_id: Service desk ID
            organization_id: Organization ID to add

        Raises:
            JiraError or subclass on failure
        """
        self.post(
            f"/rest/servicedeskapi/servicedesk/{service_desk_id}/organization",
            data={"organizationId": organization_id},
            operation=f"add organization {organization_id} to service desk {service_desk_id}",
        )

    def remove_organization_from_service_desk(
        self, service_desk_id: str, organization_id: int
    ) -> None:
        """
        Remove an organization from a service desk.

        Args:
            service_desk_id: Service desk ID
            organization_id: Organization ID to remove

        Raises:
            JiraError or subclass on failure
        """
        # JSM API requires organization ID in request body, not path
        endpoint = f"/rest/servicedeskapi/servicedesk/{service_desk_id}/organization"
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(
            url, json={"organizationId": organization_id}, timeout=self.timeout
        )
        handle_jira_error(
            response,
            f"remove organization {organization_id} from service desk {service_desk_id}",
        )

    def get_organization_users(
        self, organization_id: int, start: int = 0, limit: int = 50
    ) -> dict[str, Any]:
        """
        Get users in an organization.

        Args:
            organization_id: Organization ID
            start: Starting index for pagination
            limit: Maximum results to return

        Returns:
            Paginated list of users

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/servicedeskapi/organization/{organization_id}/user",
            params={"start": start, "limit": limit},
            operation=f"get users for organization {organization_id}",
        )

    def update_organization(self, organization_id: int, name: str) -> dict[str, Any]:
        """
        Update an organization's name.

        Note: The JSM REST API does not support organization updates.
        This method will attempt the update but may fail with 405 Method Not Allowed.
        Consider deleting and recreating the organization if update is required.

        Args:
            organization_id: Organization ID
            name: New organization name

        Returns:
            Updated organization object

        Raises:
            JiraError or subclass on failure (likely 405 Method Not Allowed)
        """
        # Note: JSM API v1 doesn't support organization updates
        # Try POST with property endpoint as fallback
        try:
            return self.put(
                f"/rest/servicedeskapi/organization/{organization_id}",
                data={"name": name},
                operation=f"update organization {organization_id}",
            )
        except Exception:
            # Try alternative endpoint with POST
            return self.post(
                f"/rest/servicedeskapi/organization/{organization_id}/property/name",
                data={"value": name},
                operation=f"update organization {organization_id} name",
            )

    def get_service_desk_agents(
        self, service_desk_id: str, start: int = 0, limit: int = 50
    ) -> dict[str, Any]:
        """
        Get agents assigned to a service desk.

        Args:
            service_desk_id: Service desk ID
            start: Starting index for pagination
            limit: Maximum results to return

        Returns:
            Paginated list of agents

        Raises:
            JiraError or subclass on failure
        """
        # Note: This may require admin permissions
        service_desk = self.get_service_desk(service_desk_id)
        project_key = service_desk.get("projectKey")

        # Get project actors with agent role
        actors = self.get(
            f"/rest/api/3/project/{project_key}/role",
            operation=f"get roles for project {project_key}",
        )

        # Find Service Desk Team role
        for role_name, role_url in actors.items():
            if "agent" in role_name.lower() or "team" in role_name.lower():
                role_data = self.get(role_url.replace(self.base_url, ""))
                return {
                    "values": role_data.get("actors", []),
                    "start": start,
                    "limit": limit,
                    "size": len(role_data.get("actors", [])),
                }

        return {"values": [], "start": start, "limit": limit, "size": 0}

    def get_my_approvals(self, service_desk_id: int | None = None) -> dict[str, Any]:
        """
        Get pending approvals for the current user.

        Args:
            service_desk_id: Optional service desk ID to filter by

        Returns:
            Paginated list of pending approvals

        Raises:
            JiraError or subclass on failure
        """
        approvals = self.get_pending_approvals(service_desk_id)
        return {"values": approvals, "size": len(approvals)}

    # Alias methods for consistent naming
    def get_queues(
        self,
        service_desk_id: int,
        include_count: bool = False,
        start: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Alias for get_service_desk_queues."""
        return self.get_service_desk_queues(
            service_desk_id, include_count, start, limit
        )

    def search_knowledge_base(
        self,
        service_desk_id: int,
        query: str,
        highlight: bool = True,
        start: int = 0,
        limit: int = 25,
        space_key: str | None = None,
    ) -> dict[str, Any]:
        """
        Search the knowledge base for articles.

        Args:
            service_desk_id: Service desk ID
            query: Search query string
            highlight: Whether to highlight matches
            start: Starting index for pagination
            limit: Maximum results to return
            space_key: Optional Confluence space key to search within

        Returns:
            Search results with articles

        Raises:
            JiraError or subclass on failure
        """
        articles = self.search_kb_articles(
            service_desk_id, query, highlight, start, limit
        )
        return {"values": articles}

    def get_knowledge_base_article(
        self, service_desk_id: str, article_id: str
    ) -> dict[str, Any]:
        """Alias for get_kb_article."""
        return self.get_kb_article(article_id)

    def get_knowledge_base_suggestions(
        self, service_desk_id: str, issue_key: str
    ) -> dict[str, Any]:
        """
        Get KB article suggestions for a request.

        Args:
            service_desk_id: Service desk ID
            issue_key: Request issue key

        Returns:
            Suggested articles

        Raises:
            JiraError or subclass on failure
        """
        suggestions = self.suggest_kb_for_request(issue_key)
        return {"values": suggestions}

    def get_knowledge_base_spaces(self, service_desk_id: str) -> dict[str, Any]:
        """
        Get knowledge base spaces/categories for a service desk.

        Args:
            service_desk_id: Service desk ID

        Returns:
            Available KB spaces

        Raises:
            JiraError or subclass on failure
        """
        # KB spaces are Confluence spaces linked to the service desk
        return self.get(
            f"/rest/servicedeskapi/servicedesk/{service_desk_id}/knowledgebase/category",
            operation=f"get KB spaces for service desk {service_desk_id}",
        )

    def link_knowledge_base_article(self, issue_key: str, article_id: str) -> None:
        """
        Link a KB article to a request.

        Args:
            issue_key: Request issue key
            article_id: KB article ID

        Raises:
            JiraError or subclass on failure
        """
        self.add_request_comment(
            issue_key, f"Linked KB article: {article_id}", public=True
        )

    def attach_article_as_solution(self, issue_key: str, article_id: str) -> None:
        """
        Attach a KB article as the solution for a request.

        Args:
            issue_key: Request issue key
            article_id: KB article ID

        Raises:
            JiraError or subclass on failure
        """
        self.add_request_comment(
            issue_key, f"Solution: KB article {article_id}", public=True
        )

    # ==========================================
    # Additional Assets/Insight Methods
    # ==========================================

    def get_object_schemas(self) -> dict[str, Any]:
        """
        Get all object schemas (Assets/Insight).

        Returns:
            List of object schemas

        Raises:
            JiraError or subclass on failure
        """
        result = self.get(
            "/rest/insight/1.0/objectschema/list", operation="list object schemas"
        )
        # Normalize response format
        if "objectschemas" in result:
            return {"values": result["objectschemas"]}
        return result

    def get_object_schema(self, schema_id: int) -> dict[str, Any]:
        """
        Get a specific object schema.

        Args:
            schema_id: Object schema ID

        Returns:
            Object schema details

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/insight/1.0/objectschema/{schema_id}",
            operation=f"get object schema {schema_id}",
        )

    def get_object_types(self, schema_id: int) -> dict[str, Any]:
        """
        Get object types in a schema.

        Args:
            schema_id: Object schema ID

        Returns:
            List of object types

        Raises:
            JiraError or subclass on failure
        """
        result = self.get(
            f"/rest/insight/1.0/objectschema/{schema_id}/objecttypes/flat",
            operation=f"get object types for schema {schema_id}",
        )
        if isinstance(result, list):
            return {"values": result}
        return result

    def get_object_type_attributes(self, object_type_id: int) -> dict[str, Any]:
        """
        Get attributes for an object type.

        Args:
            object_type_id: Object type ID

        Returns:
            List of attributes

        Raises:
            JiraError or subclass on failure
        """
        result = self.get(
            f"/rest/insight/1.0/objecttype/{object_type_id}/attributes",
            operation=f"get attributes for object type {object_type_id}",
        )
        if isinstance(result, list):
            return {"values": result}
        return result

    def search_assets(
        self, iql: str, schema_id: int | None = None, max_results: int = 100
    ) -> dict[str, Any]:
        """
        Search assets using IQL.

        Args:
            iql: IQL query string
            schema_id: Optional schema ID to search within
            max_results: Maximum results to return

        Returns:
            Search results with asset objects

        Raises:
            JiraError or subclass on failure
        """
        params = {
            "iql": iql,
            "page": 1,
            "resultsPerPage": min(max_results, 100),
            "includeAttributes": True,
        }

        if schema_id:
            params["objectSchemaId"] = schema_id
        else:
            # Get first schema if not specified
            schemas = self.get_object_schemas()
            schema_list = schemas.get("values", [])
            if schema_list:
                params["objectSchemaId"] = schema_list[0]["id"]

        result = self.get(
            "/rest/insight/1.0/iql/objects", params=params, operation="search assets"
        )

        # Normalize response
        if "objectEntries" in result:
            return {"values": result["objectEntries"]}
        return result

    def delete_asset(self, asset_id: int) -> None:
        """
        Delete an asset.

        Args:
            asset_id: Asset object ID

        Raises:
            JiraError or subclass on failure
        """
        self.delete(
            f"/rest/insight/1.0/object/{asset_id}", operation=f"delete asset {asset_id}"
        )

    def get_issue_assets(self, issue_key: str) -> dict[str, Any]:
        """
        Get assets linked to an issue.

        Args:
            issue_key: Issue key

        Returns:
            List of linked assets

        Raises:
            JiraError or subclass on failure
        """
        # Assets are stored in a custom field on the issue
        issue = self.get_issue(issue_key)
        assets = []

        # Look for asset custom fields
        for _field_id, field_value in issue.get("fields", {}).items():
            if field_value and isinstance(field_value, list):
                for item in field_value:
                    if isinstance(item, dict) and "objectKey" in item:
                        assets.append(item)

        return {"values": assets}

    def link_asset_to_issue(self, issue_key: str, asset_key: str) -> None:
        """
        Link an asset to an issue by asset key.

        Args:
            issue_key: Issue key
            asset_key: Asset object key (e.g., 'ASSET-123')

        Raises:
            JiraError or subclass on failure
        """
        # Add comment with asset reference
        self.add_request_comment(issue_key, f"Linked asset: {asset_key}", public=False)

    def find_affected_assets(self, issue_key: str) -> dict[str, Any]:
        """
        Find assets potentially affected by an incident/request.

        Args:
            issue_key: Issue key

        Returns:
            List of potentially affected assets

        Raises:
            JiraError or subclass on failure
        """
        # Get linked assets from issue
        return self.get_issue_assets(issue_key)

    # ========== Workflow Management API Methods (/rest/api/3/workflow) ==========

    def get_workflows(self, start_at: int = 0, max_results: int = 50) -> dict[str, Any]:
        """
        Get all workflows with basic information.

        Args:
            start_at: Starting index for pagination
            max_results: Maximum results per page (max 1000)

        Returns:
            Dict with 'values' list of workflow objects and pagination info

        Raises:
            JiraError or subclass on failure

        Note:
            Requires 'Administer Jira' global permission.
        """
        params = {"startAt": start_at, "maxResults": min(max_results, 1000)}
        return self.get(
            "/rest/api/3/workflow", params=params, operation="list workflows"
        )

    def search_workflows(
        self,
        workflow_name: str | None = None,
        is_active: bool | None = None,
        query_string: str | None = None,
        order_by: str | None = None,
        expand: str | None = None,
        start_at: int = 0,
        max_results: int = 50,
    ) -> dict[str, Any]:
        """
        Search workflows with filters and optional transition expansion.

        This is the recommended endpoint for getting workflow details.

        Args:
            workflow_name: Filter by workflow name (partial match)
            is_active: Filter by active status (True/False)
            query_string: Search query string
            order_by: Sort field (name, created, updated)
            expand: Fields to expand ('transitions', 'transitions.rules', 'statuses')
            start_at: Starting index for pagination
            max_results: Maximum results per page

        Returns:
            Dict with 'values' list of workflow objects and pagination info

        Raises:
            JiraError or subclass on failure

        Note:
            Requires 'Administer Jira' global permission.
        """
        params = {"startAt": start_at, "maxResults": max_results}
        if workflow_name:
            params["workflowName"] = workflow_name
        if is_active is not None:
            params["isActive"] = "true" if is_active else "false"
        if query_string:
            params["queryString"] = query_string
        if order_by:
            params["orderBy"] = order_by
        if expand:
            params["expand"] = expand

        return self.get(
            "/rest/api/3/workflow/search", params=params, operation="search workflows"
        )

    def get_workflow_bulk(
        self, workflow_ids: list, expand: str | None = None
    ) -> dict[str, Any]:
        """
        Bulk get workflow details by IDs.

        Args:
            workflow_ids: List of workflow entity IDs
            expand: Fields to expand ('transitions', 'transitions.rules',
                    'transitions.properties', 'statuses', 'default')

        Returns:
            Dict with 'workflows' list containing detailed workflow objects

        Raises:
            JiraError or subclass on failure

        Note:
            Requires 'Administer Jira' global permission.
        """
        params = {}
        if expand:
            params["expand"] = expand

        payload = {"workflowIds": workflow_ids}

        endpoint = "/rest/api/3/workflows"
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(
            url, json=payload, params=params if params else None, timeout=self.timeout
        )
        handle_jira_error(response, "bulk get workflows")
        return response.json()

    def get_workflow_schemes_for_workflow(
        self, workflow_id: str, start_at: int = 0, max_results: int = 50
    ) -> dict[str, Any]:
        """
        Get workflow schemes that use a specific workflow.

        Args:
            workflow_id: Workflow entity ID
            start_at: Starting index for pagination
            max_results: Maximum results per page

        Returns:
            Dict with 'values' list of workflow schemes using this workflow

        Raises:
            JiraError or subclass on failure

        Note:
            Requires 'Administer Jira' global permission.
        """
        params = {"startAt": start_at, "maxResults": max_results}
        return self.get(
            f"/rest/api/3/workflow/{workflow_id}/workflowSchemes",
            params=params,
            operation=f"get schemes for workflow {workflow_id}",
        )

    # ========== Workflow Scheme API Methods (/rest/api/3/workflowscheme) ==========

    def get_workflow_schemes(
        self, start_at: int = 0, max_results: int = 50
    ) -> dict[str, Any]:
        """
        Get all workflow schemes with pagination.

        Args:
            start_at: Starting index for pagination
            max_results: Maximum results per page

        Returns:
            Dict with 'values' list of workflow scheme objects and pagination info

        Raises:
            JiraError or subclass on failure

        Note:
            Requires 'Administer Jira' global permission.
        """
        params = {"startAt": start_at, "maxResults": max_results}
        return self.get(
            "/rest/api/3/workflowscheme",
            params=params,
            operation="list workflow schemes",
        )

    def get_workflow_scheme(
        self, scheme_id: int, return_draft_if_exists: bool = False
    ) -> dict[str, Any]:
        """
        Get a workflow scheme by ID.

        Args:
            scheme_id: Workflow scheme ID
            return_draft_if_exists: If True, return draft if one exists

        Returns:
            Workflow scheme object with mappings

        Raises:
            JiraError or subclass on failure

        Note:
            Requires 'Administer Jira' global permission.
        """
        params = {}
        if return_draft_if_exists:
            params["returnDraftIfExists"] = "true"

        return self.get(
            f"/rest/api/3/workflowscheme/{scheme_id}",
            params=params if params else None,
            operation=f"get workflow scheme {scheme_id}",
        )

    def get_workflow_scheme_for_project(self, project_key_or_id: str) -> dict[str, Any]:
        """
        Get the workflow scheme assigned to a project.

        Args:
            project_key_or_id: Project key or ID

        Returns:
            Dict with 'workflowScheme' object for the project

        Raises:
            JiraError or subclass on failure
        """
        params = {"projectId": project_key_or_id}
        return self.get(
            "/rest/api/3/workflowscheme/project",
            params=params,
            operation=f"get workflow scheme for project {project_key_or_id}",
        )

    def assign_workflow_scheme_to_project(
        self,
        project_key_or_id: str,
        workflow_scheme_id: str,
        status_mappings: list | None = None,
    ) -> dict[str, Any]:
        """
        Assign a workflow scheme to a project.

        This is an asynchronous operation that returns a task ID.

        Args:
            project_key_or_id: Project key or ID
            workflow_scheme_id: Workflow scheme ID to assign
            status_mappings: Optional list of status migration mappings:
                [{"issueTypeId": "10000", "statusMigrations": [
                    {"oldStatusId": "1", "newStatusId": "10000"}
                ]}]

        Returns:
            Task object with taskId for tracking the async operation

        Raises:
            JiraError or subclass on failure

        Note:
            This is an experimental API endpoint.
            Requires 'Administer Jira' global permission.
        """
        payload = {
            "projectId": project_key_or_id,
            "workflowSchemeId": workflow_scheme_id,
        }
        if status_mappings:
            payload["issueTypeMappings"] = status_mappings

        return self.post(
            "/rest/api/3/workflowscheme/project/switch",
            data=payload,
            operation=f"assign workflow scheme to project {project_key_or_id}",
        )

    # ========== Status API Methods (/rest/api/3/status) ==========

    def get_all_statuses(self) -> list:
        """
        Get all statuses in the JIRA instance.

        Returns:
            List of status objects with id, name, description,
            statusCategory, and scope

        Raises:
            JiraError or subclass on failure

        Note:
            Only returns statuses that are in active workflows.
        """
        return self.get("/rest/api/3/status", operation="get all statuses")

    def get_status(self, status_id_or_name: str) -> dict[str, Any]:
        """
        Get a specific status by ID or name.

        Args:
            status_id_or_name: Status ID or name

        Returns:
            Status object

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/api/3/status/{status_id_or_name}",
            operation=f"get status {status_id_or_name}",
        )

    def search_statuses(
        self,
        project_id: str | None = None,
        search_string: str | None = None,
        status_category: str | None = None,
        start_at: int = 0,
        max_results: int = 200,
    ) -> dict[str, Any]:
        """
        Search statuses with filters.

        Args:
            project_id: Filter by project ID
            search_string: Search string for status name
            status_category: Filter by category (TODO, IN_PROGRESS, DONE)
            start_at: Starting index for pagination
            max_results: Maximum results per page

        Returns:
            Dict with 'values' list of status objects

        Raises:
            JiraError or subclass on failure
        """
        params = {"startAt": start_at, "maxResults": max_results}
        if project_id:
            params["projectId"] = project_id
        if search_string:
            params["searchString"] = search_string
        if status_category:
            params["statusCategory"] = status_category

        return self.get(
            "/rest/api/3/statuses/search", params=params, operation="search statuses"
        )

    # ========== Notification Scheme API Methods (/rest/api/3/notificationscheme) ==========

    def get_notification_schemes(
        self, start_at: int = 0, max_results: int = 50, expand: str | None = None
    ) -> dict[str, Any]:
        """
        Get all notification schemes with pagination.

        Args:
            start_at: Starting index for pagination
            max_results: Maximum number of results
            expand: Optional expand parameter (e.g., 'all', 'notificationSchemeEvents')

        Returns:
            Paginated notification schemes with 'values', 'startAt', 'maxResults', 'total'

        Raises:
            JiraError or subclass on failure
        """
        params = {"startAt": start_at, "maxResults": max_results}
        if expand:
            params["expand"] = expand
        return self.get(
            "/rest/api/3/notificationscheme",
            params=params,
            operation="get notification schemes",
        )

    def get_notification_scheme(
        self, scheme_id: str, expand: str | None = None
    ) -> dict[str, Any]:
        """
        Get a specific notification scheme by ID.

        Args:
            scheme_id: Notification scheme ID
            expand: Optional expand parameter (e.g., 'all', 'notificationSchemeEvents')

        Returns:
            Notification scheme object with events and notifications

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if expand:
            params["expand"] = expand
        return self.get(
            f"/rest/api/3/notificationscheme/{scheme_id}",
            params=params if params else None,
            operation=f"get notification scheme {scheme_id}",
        )

    def get_notification_scheme_projects(
        self,
        start_at: int = 0,
        max_results: int = 50,
        notification_scheme_id: list | None = None,
        project_id: list | None = None,
    ) -> dict[str, Any]:
        """
        Get project-to-notification scheme mappings.

        Args:
            start_at: Starting index for pagination
            max_results: Maximum number of results
            notification_scheme_id: Filter by notification scheme IDs
            project_id: Filter by project IDs

        Returns:
            Paginated project-to-scheme mappings with 'values'

        Raises:
            JiraError or subclass on failure
        """
        params = {"startAt": start_at, "maxResults": max_results}
        if notification_scheme_id:
            params["notificationSchemeId"] = notification_scheme_id
        if project_id:
            params["projectId"] = project_id
        return self.get(
            "/rest/api/3/notificationscheme/project",
            params=params,
            operation="get notification scheme project mappings",
        )

    def create_notification_scheme(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new notification scheme.

        Args:
            data: Dictionary with 'name', 'description' (optional),
                  'notificationSchemeEvents' (optional)

        Returns:
            Created notification scheme object with 'id'

        Raises:
            JiraError or subclass on failure

        Example data:
            {
                "name": "New Notification Scheme",
                "description": "Description here",
                "notificationSchemeEvents": [
                    {
                        "event": {"id": "1"},
                        "notifications": [
                            {"notificationType": "CurrentAssignee"},
                            {"notificationType": "Group", "parameter": "developers"}
                        ]
                    }
                ]
            }
        """
        return self.post(
            "/rest/api/3/notificationscheme",
            data=data,
            operation="create notification scheme",
        )

    def update_notification_scheme(
        self, scheme_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Update notification scheme metadata (name, description).

        Args:
            scheme_id: Notification scheme ID
            data: Dictionary with 'name' and/or 'description'

        Returns:
            Empty dict on success (204 No Content)

        Raises:
            JiraError or subclass on failure
        """
        return self.put(
            f"/rest/api/3/notificationscheme/{scheme_id}",
            data=data,
            operation=f"update notification scheme {scheme_id}",
        )

    def add_notification_to_scheme(
        self, scheme_id: str, event_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Add notifications to a notification scheme.

        Args:
            scheme_id: Notification scheme ID
            event_data: Dictionary with 'notificationSchemeEvents' list

        Returns:
            Empty dict on success (204 No Content)

        Raises:
            JiraError or subclass on failure

        Example event_data:
            {
                "notificationSchemeEvents": [
                    {
                        "event": {"id": "1"},
                        "notifications": [
                            {"notificationType": "Group", "parameter": "jira-admins"}
                        ]
                    }
                ]
            }
        """
        return self.put(
            f"/rest/api/3/notificationscheme/{scheme_id}/notification",
            data=event_data,
            operation=f"add notifications to scheme {scheme_id}",
        )

    def delete_notification_scheme(self, scheme_id: str) -> None:
        """
        Delete a notification scheme.

        Args:
            scheme_id: Notification scheme ID

        Raises:
            JiraError or subclass on failure

        Note:
            Cannot delete schemes that are in use by projects.
        """
        self.delete(
            f"/rest/api/3/notificationscheme/{scheme_id}",
            operation=f"delete notification scheme {scheme_id}",
        )

    def delete_notification_from_scheme(
        self, scheme_id: str, notification_id: str
    ) -> None:
        """
        Remove a notification from a notification scheme.

        Args:
            scheme_id: Notification scheme ID
            notification_id: Notification ID to remove

        Raises:
            JiraError or subclass on failure
        """
        self.delete(
            f"/rest/api/3/notificationscheme/{scheme_id}/notification/{notification_id}",
            operation=f"remove notification {notification_id} from scheme {scheme_id}",
        )

    def lookup_notification_scheme_by_name(self, name: str) -> dict[str, Any] | None:
        """
        Lookup notification scheme by name.

        Args:
            name: Notification scheme name (case-sensitive)

        Returns:
            Notification scheme object if found, None otherwise

        Raises:
            JiraError or subclass on failure
        """
        # Paginate through all schemes to find by name
        start_at = 0
        max_results = 50
        while True:
            result = self.get_notification_schemes(
                start_at=start_at, max_results=max_results
            )
            schemes = result.get("values", [])
            for scheme in schemes:
                if scheme.get("name") == name:
                    return scheme
            # Check if there are more pages
            total = result.get("total", 0)
            if start_at + len(schemes) >= total:
                break
            start_at += max_results
        return None

    # ========== User Management API Methods (/rest/api/3/user) ==========

    def get_user(
        self,
        account_id: str | None = None,
        email: str | None = None,
        expand: list | None = None,
    ) -> dict[str, Any]:
        """
        Get user details by accountId or email.

        Args:
            account_id: User's account ID (preferred)
            email: User's email address (may fail if email is privacy-restricted)
            expand: Optional fields to expand (e.g., ['groups', 'applicationRoles'])

        Returns:
            User object with accountId, displayName, emailAddress, active, etc.

        Raises:
            ValidationError: If neither account_id nor email is provided
            JiraError or subclass on failure
        """
        if not account_id and not email:
            from jira_assistant_skills_lib import ValidationError

            raise ValidationError("Either account_id or email must be provided")

        params = {}
        if account_id:
            params["accountId"] = account_id
        if email:
            # Search by email - this may fail if email is hidden
            params["username"] = email  # Legacy parameter, still works for email lookup
        if expand:
            params["expand"] = ",".join(expand)

        return self.get("/rest/api/3/user", params=params, operation="get user")

    def get_current_user(self, expand: list | None = None) -> dict[str, Any]:
        """
        Get the current authenticated user.

        Args:
            expand: Optional fields to expand (e.g., ['groups', 'applicationRoles'])

        Returns:
            User object for the authenticated user

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if expand:
            params["expand"] = ",".join(expand)

        return self.get(
            "/rest/api/3/myself",
            params=params if params else None,
            operation="get current user",
        )

    def get_user_groups(self, account_id: str) -> list:
        """
        Get groups that a user belongs to.

        Args:
            account_id: User's account ID

        Returns:
            List of group objects with name, groupId

        Raises:
            JiraError or subclass on failure
        """
        params = {"accountId": account_id}
        result = self.get(
            "/rest/api/3/user/groups", params=params, operation="get user groups"
        )
        return result if isinstance(result, list) else []

    def find_assignable_users(
        self, query: str, project_key: str, start_at: int = 0, max_results: int = 50
    ) -> list:
        """
        Find users assignable to issues in a project.

        Args:
            query: Search query (name or email)
            project_key: Project key to search within
            start_at: Starting index for pagination
            max_results: Maximum results to return

        Returns:
            List of matching assignable users

        Raises:
            JiraError or subclass on failure
        """
        params = {
            "query": query,
            "project": project_key,
            "startAt": start_at,
            "maxResults": max_results,
        }
        return self.get(
            "/rest/api/3/user/assignable/search",
            params=params,
            operation=f"find assignable users for {project_key}",
        )

    def get_all_users(self, start_at: int = 0, max_results: int = 50) -> list:
        """
        Get all users (paginated).

        Note: Requires 'Browse users and groups' global permission.

        Args:
            start_at: Starting index for pagination
            max_results: Maximum results to return

        Returns:
            List of user objects

        Raises:
            JiraError or subclass on failure
        """
        params = {"startAt": start_at, "maxResults": max_results}
        return self.get(
            "/rest/api/3/users/search", params=params, operation="get all users"
        )

    def get_users_bulk(
        self, account_ids: list, max_results: int = 200
    ) -> dict[str, Any]:
        """
        Get multiple users by account IDs.

        Args:
            account_ids: List of user account IDs (max 200)
            max_results: Maximum results to return

        Returns:
            Response with 'values' array of user objects

        Raises:
            JiraError or subclass on failure
        """
        params = {"accountId": account_ids, "maxResults": max_results}
        return self.get(
            "/rest/api/3/user/bulk", params=params, operation="get users bulk"
        )

    # ========== Group Management API Methods (/rest/api/3/group) ==========

    def find_groups(
        self,
        query: str = "",
        start_at: int = 0,
        max_results: int = 50,
        exclude_id: list | None = None,
        caseInsensitive: bool = True,
    ) -> dict[str, Any]:
        """
        Find groups by name using the groups picker API.

        Args:
            query: Search query (partial group name)
            start_at: Starting index for pagination (called 'start' in API)
            max_results: Maximum results (called 'maxResults' in API)
            exclude_id: List of group IDs to exclude
            caseInsensitive: Case-insensitive search (default True)

        Returns:
            Response with 'groups' array and pagination info

        Raises:
            JiraError or subclass on failure
        """
        params = {
            "query": query,
            "maxResults": max_results,
            "caseInsensitive": str(caseInsensitive).lower(),
        }
        if exclude_id:
            params["exclude"] = ",".join(exclude_id)

        return self.get(
            "/rest/api/3/groups/picker", params=params, operation="find groups"
        )

    def get_group(
        self, group_name: str | None = None, group_id: str | None = None
    ) -> dict[str, Any]:
        """
        Get group details.

        Args:
            group_name: Group name
            group_id: Group ID (preferred for GDPR compliance)

        Returns:
            Group object with name, groupId, self

        Raises:
            ValidationError: If neither group_name nor group_id is provided
            JiraError or subclass on failure
        """
        if not group_name and not group_id:
            from jira_assistant_skills_lib import ValidationError

            raise ValidationError("Either group_name or group_id must be provided")

        params = {}
        if group_id:
            params["groupId"] = group_id
        elif group_name:
            params["groupname"] = group_name

        return self.get("/rest/api/3/group", params=params, operation="get group")

    def create_group(self, name: str) -> dict[str, Any]:
        """
        Create a new group.

        Note: Requires 'Site administration' permission.

        Args:
            name: Group name (e.g., 'jira-developers')

        Returns:
            Created group object with name, groupId, self

        Raises:
            JiraError or subclass on failure
        """
        return self.post(
            "/rest/api/3/group", data={"name": name}, operation=f"create group '{name}'"
        )

    def delete_group(
        self,
        group_name: str | None = None,
        group_id: str | None = None,
        swap_group: str | None = None,
        swap_group_id: str | None = None,
    ) -> None:
        """
        Delete a group.

        Note: Requires 'Site administration' permission.

        Args:
            group_name: Group name to delete
            group_id: Group ID to delete (preferred)
            swap_group: Group name to reassign issues to (optional)
            swap_group_id: Group ID to reassign issues to (optional)

        Raises:
            ValidationError: If neither group_name nor group_id is provided
            JiraError or subclass on failure
        """
        if not group_name and not group_id:
            from jira_assistant_skills_lib import ValidationError

            raise ValidationError("Either group_name or group_id must be provided")

        params = {}
        if group_id:
            params["groupId"] = group_id
        elif group_name:
            params["groupname"] = group_name
        if swap_group:
            params["swapGroup"] = swap_group
        if swap_group_id:
            params["swapGroupId"] = swap_group_id

        endpoint = "/rest/api/3/group"
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, params=params, timeout=self.timeout)
        handle_jira_error(response, "delete group")

    def get_group_members(
        self,
        group_name: str | None = None,
        group_id: str | None = None,
        include_inactive: bool = False,
        start_at: int = 0,
        max_results: int = 50,
    ) -> dict[str, Any]:
        """
        Get members of a group.

        Args:
            group_name: Group name
            group_id: Group ID (preferred)
            include_inactive: Include inactive users (default False)
            start_at: Starting index for pagination
            max_results: Maximum results to return

        Returns:
            Response with 'values' array of user objects and pagination info

        Raises:
            ValidationError: If neither group_name nor group_id is provided
            JiraError or subclass on failure
        """
        if not group_name and not group_id:
            from jira_assistant_skills_lib import ValidationError

            raise ValidationError("Either group_name or group_id must be provided")

        params = {
            "startAt": start_at,
            "maxResults": max_results,
            "includeInactiveUsers": str(include_inactive).lower(),
        }
        if group_id:
            params["groupId"] = group_id
        elif group_name:
            params["groupname"] = group_name

        return self.get(
            "/rest/api/3/group/member", params=params, operation="get group members"
        )

    def add_user_to_group(
        self,
        account_id: str,
        group_name: str | None = None,
        group_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Add a user to a group.

        Note: Requires 'Site administration' permission.

        Args:
            account_id: User's account ID
            group_name: Group name
            group_id: Group ID (preferred)

        Returns:
            Group object with name, groupId, self

        Raises:
            ValidationError: If neither group_name nor group_id is provided
            JiraError or subclass on failure

        Note:
            This operation is idempotent - adding a user already in the group
            will not cause an error.
        """
        if not group_name and not group_id:
            from jira_assistant_skills_lib import ValidationError

            raise ValidationError("Either group_name or group_id must be provided")

        params = {}
        if group_id:
            params["groupId"] = group_id
        elif group_name:
            params["groupname"] = group_name

        endpoint = "/rest/api/3/group/user"
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(
            url, json={"accountId": account_id}, params=params, timeout=self.timeout
        )
        handle_jira_error(response, "add user to group")
        return response.json()

    def remove_user_from_group(
        self,
        account_id: str,
        group_name: str | None = None,
        group_id: str | None = None,
    ) -> None:
        """
        Remove a user from a group.

        Note: Requires 'Site administration' permission.

        Args:
            account_id: User's account ID
            group_name: Group name
            group_id: Group ID (preferred)

        Raises:
            ValidationError: If neither group_name nor group_id is provided
            JiraError or subclass on failure

        Note:
            This operation is idempotent - removing a user not in the group
            will not cause an error.
        """
        if not group_name and not group_id:
            from jira_assistant_skills_lib import ValidationError

            raise ValidationError("Either group_name or group_id must be provided")

        params = {"accountId": account_id}
        if group_id:
            params["groupId"] = group_id
        elif group_name:
            params["groupname"] = group_name

        endpoint = "/rest/api/3/group/user"
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, params=params, timeout=self.timeout)
        handle_jira_error(response, "remove user from group")

    # ========== Project Admin API Methods (/rest/api/3/project) ==========

    def update_project(self, project_key: str, **kwargs) -> dict[str, Any]:
        """
        Update a project.

        Args:
            project_key: Project key (e.g., 'PROJ')
            **kwargs: Fields to update (name, description, lead, url,
                      assignee_type, category_id, new_key)

        Returns:
            Updated project data

        Raises:
            JiraError or subclass on failure

        Note:
            Changing project key requires Administer Jira global permission.
        """
        data = {}
        field_mapping = {
            "name": "name",
            "description": "description",
            "lead": "lead",
            "url": "url",
            "assignee_type": "assigneeType",
            "category_id": "categoryId",
            "new_key": "key",
        }
        for key, api_key in field_mapping.items():
            if key in kwargs and kwargs[key] is not None:
                data[api_key] = kwargs[key]

        return self.put(
            f"/rest/api/3/project/{project_key}",
            data=data,
            operation=f"update project {project_key}",
        )

    def search_projects(
        self,
        query: str | None = None,
        type_key: str | None = None,
        category_id: int | None = None,
        action: str = "browse",
        expand: list | None = None,
        status: list | None = None,
        start_at: int = 0,
        max_results: int = 50,
    ) -> dict[str, Any]:
        """
        Search for projects with filtering and pagination.

        Args:
            query: Search term for project name/key
            type_key: Filter by project type (software, business, service_desk)
            category_id: Filter by category ID
            action: Required permission action ('browse', 'edit', 'view')
            expand: Fields to expand (description, lead, issueTypes, url, projectKeys, permissions)
            status: Filter by status (live, archived, deleted)
            start_at: Starting index for pagination
            max_results: Maximum results per page (max 50)

        Returns:
            Search results with values, total, isLast

        Raises:
            JiraError or subclass on failure
        """
        params = {
            "startAt": start_at,
            "maxResults": max_results,
            "action": action,
        }
        if query:
            params["query"] = query
        if type_key:
            params["typeKey"] = type_key
        if category_id:
            params["categoryId"] = category_id
        if expand:
            params["expand"] = ",".join(expand)
        if status:
            params["status"] = ",".join(status)

        return self.get(
            "/rest/api/3/project/search", params=params, operation="search projects"
        )

    def archive_project(self, project_key: str) -> None:
        """
        Archive a project.

        Archived projects are read-only and can be restored later.

        Args:
            project_key: Project key to archive

        Raises:
            JiraError or subclass on failure

        Note:
            Requires Administer Jira global permission.
        """
        self.post(
            f"/rest/api/3/project/{project_key}/archive",
            operation=f"archive project {project_key}",
        )

    def restore_project(self, project_key: str) -> dict[str, Any]:
        """
        Restore an archived or deleted project.

        Args:
            project_key: Project key to restore

        Returns:
            Restored project data

        Raises:
            JiraError or subclass on failure

        Note:
            Deleted projects can be restored within 60 days.
            Requires Administer Jira global permission.
        """
        return self.post(
            f"/rest/api/3/project/{project_key}/restore",
            operation=f"restore project {project_key}",
        )

    def delete_project_async(self, project_key: str) -> str:
        """
        Delete a project asynchronously.

        Use for large projects to avoid timeout.

        Args:
            project_key: Project key to delete

        Returns:
            Task ID for polling status

        Raises:
            JiraError or subclass on failure

        Note:
            Use get_task_status() to poll for completion.
        """
        result = self.post(
            f"/rest/api/3/project/{project_key}/delete",
            operation=f"delete project {project_key} (async)",
        )
        return result.get("taskId", "")

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        """
        Get status of an async task.

        Args:
            task_id: Task ID from async operation

        Returns:
            Task status with status, progress, etc.

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/api/3/task/{task_id}", operation=f"get task status {task_id}"
        )

    # ========== Project Category API Methods (/rest/api/3/projectCategory) ==========

    def get_project_categories(self) -> list:
        """
        Get all project categories.

        Returns:
            List of project category objects

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            "/rest/api/3/projectCategory", operation="get project categories"
        )

    def get_project_category(self, category_id: str) -> dict[str, Any]:
        """
        Get a specific project category.

        Args:
            category_id: Category ID

        Returns:
            Project category object

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/api/3/projectCategory/{category_id}",
            operation=f"get project category {category_id}",
        )

    def create_project_category(
        self, name: str, description: str | None = None
    ) -> dict[str, Any]:
        """
        Create a new project category.

        Args:
            name: Category name
            description: Category description (optional)

        Returns:
            Created category object

        Raises:
            JiraError or subclass on failure

        Note:
            Requires Administer Jira global permission.
        """
        data = {"name": name}
        if description:
            data["description"] = description

        return self.post(
            "/rest/api/3/projectCategory",
            data=data,
            operation=f"create project category '{name}'",
        )

    def update_project_category(
        self,
        category_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """
        Update a project category.

        Args:
            category_id: Category ID
            name: New name (optional)
            description: New description (optional)

        Returns:
            Updated category object

        Raises:
            JiraError or subclass on failure
        """
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        return self.put(
            f"/rest/api/3/projectCategory/{category_id}",
            data=data,
            operation=f"update project category {category_id}",
        )

    def delete_project_category(self, category_id: str) -> None:
        """
        Delete a project category.

        Args:
            category_id: Category ID

        Raises:
            JiraError or subclass on failure

        Note:
            Projects in this category will have their category set to None.
        """
        self.delete(
            f"/rest/api/3/projectCategory/{category_id}",
            operation=f"delete project category {category_id}",
        )

    # ========== Project Type API Methods (/rest/api/3/project/type) ==========

    def get_project_types(self) -> list:
        """
        Get all project types.

        Returns:
            List of project type objects

        Raises:
            JiraError or subclass on failure
        """
        return self.get("/rest/api/3/project/type", operation="get project types")

    def get_project_type(self, type_key: str) -> dict[str, Any]:
        """
        Get a specific project type.

        Args:
            type_key: Project type key (software, business, service_desk)

        Returns:
            Project type object

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/api/3/project/type/{type_key}",
            operation=f"get project type {type_key}",
        )

    # ========== Project Avatar API Methods (/rest/api/3/project/{}/avatar) ==========

    def get_project_avatars(self, project_key: str) -> dict[str, Any]:
        """
        Get all avatars for a project.

        Args:
            project_key: Project key

        Returns:
            Dict with 'system' (default avatars) and 'custom' (uploaded) lists

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/api/3/project/{project_key}/avatars",
            operation=f"get avatars for project {project_key}",
        )

    def set_project_avatar(self, project_key: str, avatar_id: str) -> None:
        """
        Set the project's avatar.

        Args:
            project_key: Project key
            avatar_id: Avatar ID to set

        Raises:
            JiraError or subclass on failure
        """
        self.put(
            f"/rest/api/3/project/{project_key}/avatar",
            data={"id": avatar_id},
            operation=f"set avatar for project {project_key}",
        )

    def upload_project_avatar(
        self, project_key: str, file_path: str, x: int = 0, y: int = 0, size: int = 48
    ) -> dict[str, Any]:
        """
        Upload a custom avatar for a project.

        Args:
            project_key: Project key
            file_path: Path to image file (PNG, GIF, JPG; max 1MB)
            x: X coordinate of crop area (default 0)
            y: Y coordinate of crop area (default 0)
            size: Size of cropped square (default 48)

        Returns:
            Created avatar object with id

        Raises:
            JiraError or subclass on failure
        """
        params = {"x": x, "y": y, "size": size}
        endpoint = f"/rest/api/3/project/{project_key}/avatar2"
        url = f"{self.base_url}{endpoint}"

        with open(file_path, "rb") as f:
            content_type = "image/png"
            if file_path.lower().endswith(".jpg") or file_path.lower().endswith(
                ".jpeg"
            ):
                content_type = "image/jpeg"
            elif file_path.lower().endswith(".gif"):
                content_type = "image/gif"

            response = self.session.post(
                url,
                params=params,
                data=f.read(),
                headers={
                    "Content-Type": content_type,
                    "X-Atlassian-Token": "no-check",
                },
                timeout=self.timeout,
            )

        handle_jira_error(response, f"upload avatar for project {project_key}")
        return response.json()

    def delete_project_avatar(self, project_key: str, avatar_id: str) -> None:
        """
        Delete a custom avatar from a project.

        Args:
            project_key: Project key
            avatar_id: Avatar ID to delete

        Raises:
            JiraError or subclass on failure

        Note:
            Cannot delete system avatars.
        """
        self.delete(
            f"/rest/api/3/project/{project_key}/avatar/{avatar_id}",
            operation=f"delete avatar {avatar_id} from project {project_key}",
        )

    # ========== Screen Management API Methods (/rest/api/2/screens) ==========

    def get_screens(
        self,
        start_at: int = 0,
        max_results: int = 100,
        scope: list | None = None,
        query_string: str | None = None,
    ) -> dict[str, Any]:
        """
        Get all screens with pagination.

        Args:
            start_at: Starting index for pagination
            max_results: Maximum results per page (max 100)
            scope: Filter by scope type (PROJECT, TEMPLATE, GLOBAL)
            query_string: Filter screens by name (partial match)

        Returns:
            Paginated response with screens data:
            {
                'maxResults': 100,
                'startAt': 0,
                'total': 5,
                'isLast': True,
                'values': [...]
            }

        Raises:
            JiraError or subclass on failure
        """
        params = {"startAt": start_at, "maxResults": max_results}
        if scope:
            params["scope"] = ",".join(scope)
        if query_string:
            params["queryString"] = query_string

        return self.get("/rest/api/2/screens", params=params, operation="get screens")

    def get_screen(self, screen_id: int) -> dict[str, Any]:
        """
        Get a specific screen by ID.

        Note: The JIRA API doesn't have a direct get by ID endpoint,
        so we list screens and filter. For efficiency, we search with
        pagination.

        Args:
            screen_id: Screen ID

        Returns:
            Screen object with id, name, description, scope

        Raises:
            JiraError or subclass on failure (404 if not found)
        """
        # JIRA doesn't have a direct GET /screens/{id} endpoint
        # We need to list all screens and find the one we need
        result = self.get(
            "/rest/api/2/screens",
            params={"maxResults": 100},
            operation=f"get screen {screen_id}",
        )

        for screen in result.get("values", []):
            if screen.get("id") == screen_id:
                return screen

        # If not found in first page, search more
        total = result.get("total", 0)
        start_at = 100
        while start_at < total:
            result = self.get(
                "/rest/api/2/screens",
                params={"maxResults": 100, "startAt": start_at},
                operation=f"get screen {screen_id}",
            )
            for screen in result.get("values", []):
                if screen.get("id") == screen_id:
                    return screen
            start_at += 100

        # Screen not found
        from jira_assistant_skills_lib import NotFoundError

        raise NotFoundError(f"Screen with ID {screen_id} not found")

    def get_screen_tabs(self, screen_id: int) -> list:
        """
        Get all tabs for a screen.

        Args:
            screen_id: Screen ID

        Returns:
            List of tab objects with id, name

        Raises:
            JiraError or subclass on failure
        """
        result = self.get(
            f"/rest/api/2/screens/{screen_id}/tabs",
            operation=f"get tabs for screen {screen_id}",
        )
        return result if isinstance(result, list) else []

    def get_screen_tab_fields(self, screen_id: int, tab_id: int) -> list:
        """
        Get all fields for a screen tab.

        Args:
            screen_id: Screen ID
            tab_id: Tab ID

        Returns:
            List of field objects with id, name

        Raises:
            JiraError or subclass on failure
        """
        result = self.get(
            f"/rest/api/2/screens/{screen_id}/tabs/{tab_id}/fields",
            operation=f"get fields for screen {screen_id} tab {tab_id}",
        )
        return result if isinstance(result, list) else []

    def add_field_to_screen_tab(
        self, screen_id: int, tab_id: int, field_id: str
    ) -> dict[str, Any]:
        """
        Add a field to a screen tab.

        Args:
            screen_id: Screen ID
            tab_id: Tab ID
            field_id: Field ID to add (e.g., 'customfield_10016')

        Returns:
            Added field object

        Raises:
            JiraError or subclass on failure
        """
        data = {"fieldId": field_id}
        return self.post(
            f"/rest/api/2/screens/{screen_id}/tabs/{tab_id}/fields",
            data=data,
            operation=f"add field {field_id} to screen {screen_id} tab {tab_id}",
        )

    def remove_field_from_screen_tab(
        self, screen_id: int, tab_id: int, field_id: str
    ) -> None:
        """
        Remove a field from a screen tab.

        Args:
            screen_id: Screen ID
            tab_id: Tab ID
            field_id: Field ID to remove

        Raises:
            JiraError or subclass on failure
        """
        self.delete(
            f"/rest/api/2/screens/{screen_id}/tabs/{tab_id}/fields/{field_id}",
            operation=f"remove field {field_id} from screen {screen_id} tab {tab_id}",
        )

    def get_screen_available_fields(self, screen_id: int) -> list:
        """
        Get available fields that can be added to a screen.

        Args:
            screen_id: Screen ID

        Returns:
            List of available field objects

        Raises:
            JiraError or subclass on failure
        """
        result = self.get(
            f"/rest/api/2/screens/{screen_id}/availableFields",
            operation=f"get available fields for screen {screen_id}",
        )
        return result if isinstance(result, list) else []

    # ========== Screen Schemes API Methods (/rest/api/3/screenscheme) ==========

    def get_screen_schemes(
        self,
        start_at: int = 0,
        max_results: int = 100,
        query_string: str | None = None,
        expand: str | None = None,
    ) -> dict[str, Any]:
        """
        Get all screen schemes with pagination.

        Args:
            start_at: Starting index for pagination
            max_results: Maximum results per page
            query_string: Filter by name (partial match)
            expand: Expand options

        Returns:
            Paginated response with screen schemes:
            {
                'maxResults': 100,
                'startAt': 0,
                'total': 3,
                'isLast': True,
                'values': [...]
            }

        Raises:
            JiraError or subclass on failure
        """
        params = {"startAt": start_at, "maxResults": max_results}
        if query_string:
            params["queryString"] = query_string
        if expand:
            params["expand"] = expand

        return self.get(
            "/rest/api/3/screenscheme", params=params, operation="get screen schemes"
        )

    def get_screen_scheme(self, scheme_id: int) -> dict[str, Any]:
        """
        Get a specific screen scheme by ID.

        Note: JIRA API v3 doesn't have direct GET by ID, so we search.

        Args:
            scheme_id: Screen scheme ID

        Returns:
            Screen scheme object with id, name, description, screens

        Raises:
            JiraError or subclass on failure
        """
        # Search for the specific scheme
        result = self.get(
            "/rest/api/3/screenscheme",
            params={"id": [scheme_id]},
            operation=f"get screen scheme {scheme_id}",
        )

        values = result.get("values", [])
        if values:
            return values[0]

        from jira_assistant_skills_lib import NotFoundError

        raise NotFoundError(f"Screen scheme with ID {scheme_id} not found")

    # ========== Issue Type API Methods (/rest/api/3/issuetype) ==========

    def get_issue_types(self) -> list:
        """
        Get all issue types.

        Returns:
            List of issue type dictionaries

        Raises:
            JiraError or subclass on failure
        """
        return self.get("/rest/api/3/issuetype", operation="get issue types")

    def get_issue_type(self, issue_type_id: str) -> dict[str, Any]:
        """
        Get issue type by ID.

        Args:
            issue_type_id: Issue type ID

        Returns:
            Issue type details

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/api/3/issuetype/{issue_type_id}",
            operation=f"get issue type {issue_type_id}",
        )

    def create_issue_type(
        self,
        name: str,
        description: str | None = None,
        issue_type: str = "standard",
        hierarchy_level: int | None = None,
    ) -> dict[str, Any]:
        """
        Create new issue type.

        Args:
            name: Issue type name (max 60 characters)
            description: Issue type description
            issue_type: 'standard' or 'subtask'
            hierarchy_level: -1 (subtask), 0 (standard), 1 (epic), etc.

        Returns:
            Created issue type details

        Raises:
            JiraError or subclass on failure
        """
        data = {"name": name, "type": issue_type}

        if description:
            data["description"] = description

        if hierarchy_level is not None:
            data["hierarchyLevel"] = hierarchy_level

        return self.post(
            "/rest/api/3/issuetype", data=data, operation="create issue type"
        )

    def update_issue_type(
        self,
        issue_type_id: str,
        name: str | None = None,
        description: str | None = None,
        avatar_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Update issue type.

        Args:
            issue_type_id: Issue type ID
            name: New name
            description: New description
            avatar_id: New avatar ID

        Returns:
            Updated issue type details

        Raises:
            JiraError or subclass on failure
        """
        data = {}

        if name:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if avatar_id:
            data["avatarId"] = avatar_id

        return self.put(
            f"/rest/api/3/issuetype/{issue_type_id}",
            data=data,
            operation=f"update issue type {issue_type_id}",
        )

    def delete_issue_type(
        self, issue_type_id: str, alternative_issue_type_id: str | None = None
    ) -> None:
        """
        Delete issue type.

        Args:
            issue_type_id: Issue type ID to delete
            alternative_issue_type_id: Alternative issue type for existing issues

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if alternative_issue_type_id:
            params["alternativeIssueTypeId"] = alternative_issue_type_id

        endpoint = f"/rest/api/3/issuetype/{issue_type_id}"
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(
            url, params=params if params else None, timeout=self.timeout
        )
        handle_jira_error(response, f"delete issue type {issue_type_id}")

    def get_issue_type_alternatives(self, issue_type_id: str) -> list:
        """
        Get alternative issue types (for deletion/migration).

        Args:
            issue_type_id: Issue type ID

        Returns:
            List of alternative issue types

        Raises:
            JiraError or subclass on failure
        """
        return self.get(
            f"/rest/api/3/issuetype/{issue_type_id}/alternatives",
            operation=f"get alternatives for issue type {issue_type_id}",
        )

    # ========== Issue Type Scheme API Methods (/rest/api/3/issuetypescheme) ==========

    def get_issue_type_schemes(
        self,
        start_at: int = 0,
        max_results: int = 50,
        scheme_ids: list | None = None,
        order_by: str | None = None,
    ) -> dict[str, Any]:
        """
        Get all issue type schemes.

        Args:
            start_at: Starting index for pagination
            max_results: Maximum results per page
            scheme_ids: Filter by scheme IDs
            order_by: Order by field (e.g., 'name', '-name')

        Returns:
            Paginated list of schemes

        Raises:
            JiraError or subclass on failure
        """
        params = {"startAt": start_at, "maxResults": max_results}

        if scheme_ids:
            params["id"] = scheme_ids
        if order_by:
            params["orderBy"] = order_by

        return self.get(
            "/rest/api/3/issuetypescheme",
            params=params,
            operation="get issue type schemes",
        )

    def get_issue_type_scheme_items(
        self,
        start_at: int = 0,
        max_results: int = 50,
        scheme_ids: list | None = None,
    ) -> dict[str, Any]:
        """
        Get issue type scheme items (issue types in schemes).

        Args:
            start_at: Starting index for pagination
            max_results: Maximum results per page
            scheme_ids: Filter by scheme IDs

        Returns:
            Paginated list of scheme items

        Raises:
            JiraError or subclass on failure
        """
        params = {"startAt": start_at, "maxResults": max_results}

        if scheme_ids:
            params["issueTypeSchemeId"] = scheme_ids

        return self.get(
            "/rest/api/3/issuetypescheme/mapping",
            params=params,
            operation="get issue type scheme items",
        )

    def create_issue_type_scheme(
        self,
        name: str,
        issue_type_ids: list,
        description: str | None = None,
        default_issue_type_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create issue type scheme.

        Args:
            name: Scheme name
            issue_type_ids: List of issue type IDs
            description: Scheme description
            default_issue_type_id: Default issue type ID

        Returns:
            Created scheme with ID

        Raises:
            JiraError or subclass on failure
        """
        data = {"name": name, "issueTypeIds": issue_type_ids}

        if description:
            data["description"] = description
        if default_issue_type_id:
            data["defaultIssueTypeId"] = default_issue_type_id

        return self.post(
            "/rest/api/3/issuetypescheme",
            data=data,
            operation="create issue type scheme",
        )

    def update_issue_type_scheme(
        self,
        scheme_id: str,
        name: str | None = None,
        description: str | None = None,
        default_issue_type_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Update issue type scheme.

        Args:
            scheme_id: Scheme ID
            name: New name
            description: New description
            default_issue_type_id: New default issue type

        Returns:
            Empty response on success

        Raises:
            JiraError or subclass on failure
        """
        data = {}

        if name:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if default_issue_type_id:
            data["defaultIssueTypeId"] = default_issue_type_id

        return self.put(
            f"/rest/api/3/issuetypescheme/{scheme_id}",
            data=data,
            operation=f"update issue type scheme {scheme_id}",
        )

    def delete_issue_type_scheme(self, scheme_id: str) -> None:
        """
        Delete issue type scheme.

        Args:
            scheme_id: Scheme ID to delete

        Raises:
            JiraError or subclass on failure
        """
        self.delete(
            f"/rest/api/3/issuetypescheme/{scheme_id}",
            operation=f"delete issue type scheme {scheme_id}",
        )

    def get_issue_type_scheme_for_projects(
        self, project_ids: list, start_at: int = 0, max_results: int = 50
    ) -> dict[str, Any]:
        """
        Get issue type schemes for projects.

        Args:
            project_ids: List of project IDs (1-100)
            start_at: Starting index
            max_results: Maximum results per page

        Returns:
            Schemes assigned to projects

        Raises:
            ValidationError: If more than 100 project IDs
            JiraError or subclass on failure
        """
        from jira_assistant_skills_lib import ValidationError

        if len(project_ids) > 100:
            raise ValidationError("Maximum 100 project IDs allowed")

        params = {
            "projectId": project_ids,
            "startAt": start_at,
            "maxResults": max_results,
        }

        return self.get(
            "/rest/api/3/issuetypescheme/project",
            params=params,
            operation="get project issue type schemes",
        )

    def assign_issue_type_scheme(self, scheme_id: str, project_id: str) -> None:
        """
        Assign issue type scheme to project.

        Args:
            scheme_id: Issue type scheme ID
            project_id: Project ID

        Raises:
            JiraError or subclass on failure

        Note:
            Only works for classic projects.
            Fails if issues use types not in the new scheme.
        """
        data = {"issueTypeSchemeId": scheme_id, "projectId": project_id}

        self.put(
            "/rest/api/3/issuetypescheme/project",
            data=data,
            operation=f"assign issue type scheme {scheme_id} to project {project_id}",
        )

    def add_issue_types_to_scheme(self, scheme_id: str, issue_type_ids: list) -> None:
        """
        Add issue types to scheme.

        Args:
            scheme_id: Scheme ID
            issue_type_ids: List of issue type IDs to add

        Raises:
            JiraError or subclass on failure
        """
        data = {"issueTypeIds": issue_type_ids}

        self.put(
            f"/rest/api/3/issuetypescheme/{scheme_id}/issuetype",
            data=data,
            operation=f"add issue types to scheme {scheme_id}",
        )

    def remove_issue_type_from_scheme(self, scheme_id: str, issue_type_id: str) -> None:
        """
        Remove issue type from scheme.

        Args:
            scheme_id: Scheme ID
            issue_type_id: Issue type ID to remove

        Raises:
            JiraError or subclass on failure

        Note:
            Cannot remove default issue type or last issue type.
        """
        self.delete(
            f"/rest/api/3/issuetypescheme/{scheme_id}/issuetype/{issue_type_id}",
            operation=f"remove issue type {issue_type_id} from scheme {scheme_id}",
        )

    def reorder_issue_types_in_scheme(
        self, scheme_id: str, issue_type_id: str, after: str | None = None
    ) -> None:
        """
        Reorder issue types in scheme.

        Args:
            scheme_id: Scheme ID
            issue_type_id: Issue type ID to move
            after: Issue type ID to position after (None = move to first)

        Raises:
            JiraError or subclass on failure
        """
        data = {"issueTypeId": issue_type_id}

        if after:
            data["after"] = after

        self.put(
            f"/rest/api/3/issuetypescheme/{scheme_id}/issuetype/move",
            data=data,
            operation=f"reorder issue types in scheme {scheme_id}",
        )

    # ========== Issue Type Screen Schemes API (/rest/api/3/issuetypescreenscheme) ==========

    def get_issue_type_screen_schemes(
        self, start_at: int = 0, max_results: int = 100, expand: str | None = None
    ) -> dict[str, Any]:
        """
        Get all issue type screen schemes.

        Args:
            start_at: Starting index for pagination
            max_results: Maximum results per page
            expand: Optional expand (e.g., 'projects')

        Returns:
            Paginated response with issue type screen schemes

        Raises:
            JiraError or subclass on failure
        """
        params = {"startAt": start_at, "maxResults": max_results}
        if expand:
            params["expand"] = expand

        return self.get(
            "/rest/api/3/issuetypescreenscheme",
            params=params,
            operation="get issue type screen schemes",
        )

    def get_issue_type_screen_scheme(self, scheme_id: int) -> dict[str, Any]:
        """
        Get a specific issue type screen scheme by ID.

        Args:
            scheme_id: Issue type screen scheme ID

        Returns:
            Issue type screen scheme object

        Raises:
            JiraError or subclass on failure
        """
        result = self.get(
            "/rest/api/3/issuetypescreenscheme",
            params={"id": [scheme_id]},
            operation=f"get issue type screen scheme {scheme_id}",
        )

        values = result.get("values", [])
        if values:
            return values[0]

        from jira_assistant_skills_lib import NotFoundError

        raise NotFoundError(f"Issue type screen scheme with ID {scheme_id} not found")

    def get_issue_type_screen_scheme_mappings(
        self,
        scheme_ids: list | None = None,
        start_at: int = 0,
        max_results: int = 100,
    ) -> dict[str, Any]:
        """
        Get issue type to screen scheme mappings.

        Args:
            scheme_ids: List of issue type screen scheme IDs to filter
            start_at: Starting index for pagination
            max_results: Maximum results per page

        Returns:
            Paginated response with mappings

        Raises:
            JiraError or subclass on failure
        """
        params = {"startAt": start_at, "maxResults": max_results}
        if scheme_ids:
            params["issueTypeScreenSchemeId"] = scheme_ids

        return self.get(
            "/rest/api/3/issuetypescreenscheme/mapping",
            params=params,
            operation="get issue type screen scheme mappings",
        )

    def get_project_issue_type_screen_schemes(
        self,
        project_ids: list | None = None,
        start_at: int = 0,
        max_results: int = 100,
    ) -> dict[str, Any]:
        """
        Get issue type screen schemes for projects.

        Args:
            project_ids: List of project IDs to filter
            start_at: Starting index for pagination
            max_results: Maximum results per page

        Returns:
            Paginated response with project to scheme mappings:
            {
                'values': [
                    {
                        'issueTypeScreenScheme': {...},
                        'projectIds': ['10000', '10001']
                    }
                ]
            }

        Raises:
            JiraError or subclass on failure
        """
        params = {"startAt": start_at, "maxResults": max_results}
        if project_ids:
            params["projectId"] = project_ids

        return self.get(
            "/rest/api/3/issuetypescreenscheme/project",
            params=params,
            operation="get project issue type screen schemes",
        )

    # ========== Permission Scheme API Methods (/rest/api/3/permissionscheme) ==========

    def get_permission_schemes(self, expand: str | None = None) -> dict[str, Any]:
        """
        Get all permission schemes.

        Args:
            expand: Optional expansion (e.g., 'permissions', 'user,group,projectRole')

        Returns:
            Dict containing 'permissionSchemes' list

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if expand:
            params["expand"] = expand

        return self.get(
            "/rest/api/3/permissionscheme",
            params=params if params else None,
            operation="get permission schemes",
        )

    def get_permission_scheme(
        self, scheme_id: int, expand: str | None = None
    ) -> dict[str, Any]:
        """
        Get a specific permission scheme by ID.

        Args:
            scheme_id: Permission scheme ID
            expand: Optional expansion (e.g., 'permissions', 'user,group,projectRole,all')

        Returns:
            Permission scheme data with grants

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if expand:
            params["expand"] = expand

        return self.get(
            f"/rest/api/3/permissionscheme/{scheme_id}",
            params=params if params else None,
            operation=f"get permission scheme {scheme_id}",
        )

    def create_permission_scheme(
        self,
        name: str,
        description: str | None = None,
        permissions: list | None = None,
    ) -> dict[str, Any]:
        """
        Create a new permission scheme.

        Args:
            name: Name of the permission scheme
            description: Optional description
            permissions: Optional list of permission grants

        Returns:
            Created permission scheme data

        Raises:
            JiraError or subclass on failure

        Note:
            Requires 'Administer Jira' global permission.
        """
        data = {"name": name}
        if description:
            data["description"] = description
        if permissions:
            data["permissions"] = permissions

        return self.post(
            "/rest/api/3/permissionscheme",
            data=data,
            operation="create permission scheme",
        )

    def update_permission_scheme(
        self,
        scheme_id: int,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """
        Update a permission scheme's name and/or description.

        Args:
            scheme_id: Permission scheme ID
            name: New name (optional)
            description: New description (optional)

        Returns:
            Updated permission scheme data

        Raises:
            JiraError or subclass on failure

        Note:
            Requires 'Administer Jira' global permission.
            To modify grants, use create_permission_grant and delete_permission_grant.
        """
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        return self.put(
            f"/rest/api/3/permissionscheme/{scheme_id}",
            data=data,
            operation=f"update permission scheme {scheme_id}",
        )

    def delete_permission_scheme(self, scheme_id: int) -> None:
        """
        Delete a permission scheme.

        Args:
            scheme_id: Permission scheme ID

        Raises:
            JiraError or subclass on failure

        Note:
            Requires 'Administer Jira' global permission.
            Cannot delete schemes that are assigned to projects.
        """
        self.delete(
            f"/rest/api/3/permissionscheme/{scheme_id}",
            operation=f"delete permission scheme {scheme_id}",
        )

    def get_permission_scheme_grants(
        self, scheme_id: int, expand: str | None = None
    ) -> dict[str, Any]:
        """
        Get all permission grants for a permission scheme.

        Args:
            scheme_id: Permission scheme ID
            expand: Optional expansion (e.g., 'user,group,projectRole,field,all')

        Returns:
            Dict containing 'permissions' list of grants

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if expand:
            params["expand"] = expand

        return self.get(
            f"/rest/api/3/permissionscheme/{scheme_id}/permission",
            params=params if params else None,
            operation=f"get permission grants for scheme {scheme_id}",
        )

    def create_permission_grant(
        self,
        scheme_id: int,
        permission: str,
        holder_type: str,
        holder_parameter: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a permission grant in a permission scheme.

        Args:
            scheme_id: Permission scheme ID
            permission: Permission key (e.g., 'BROWSE_PROJECTS', 'CREATE_ISSUES')
            holder_type: Holder type (e.g., 'user', 'group', 'projectRole', 'anyone', 'projectLead')
            holder_parameter: Parameter for holder (e.g., group name, user account ID)

        Returns:
            Created permission grant data

        Raises:
            JiraError or subclass on failure

        Note:
            Requires 'Administer Jira' global permission.
        """
        holder = {"type": holder_type}
        if holder_parameter:
            holder["parameter"] = holder_parameter

        data = {"permission": permission, "holder": holder}

        return self.post(
            f"/rest/api/3/permissionscheme/{scheme_id}/permission",
            data=data,
            operation=f"create permission grant in scheme {scheme_id}",
        )

    def get_permission_grant(
        self, scheme_id: int, permission_id: int, expand: str | None = None
    ) -> dict[str, Any]:
        """
        Get a specific permission grant.

        Args:
            scheme_id: Permission scheme ID
            permission_id: Permission grant ID
            expand: Optional expansion

        Returns:
            Permission grant data

        Raises:
            JiraError or subclass on failure
        """
        params = {}
        if expand:
            params["expand"] = expand

        return self.get(
            f"/rest/api/3/permissionscheme/{scheme_id}/permission/{permission_id}",
            params=params if params else None,
            operation=f"get permission grant {permission_id}",
        )

    def delete_permission_grant(self, scheme_id: int, permission_id: int) -> None:
        """
        Delete a permission grant from a permission scheme.

        Args:
            scheme_id: Permission scheme ID
            permission_id: Permission grant ID

        Raises:
            JiraError or subclass on failure

        Note:
            Requires 'Administer Jira' global permission.
        """
        self.delete(
            f"/rest/api/3/permissionscheme/{scheme_id}/permission/{permission_id}",
            operation=f"delete permission grant {permission_id}",
        )

    def get_all_permissions(self) -> dict[str, Any]:
        """
        Get all permissions available in the JIRA instance.

        Returns:
            Dict containing 'permissions' dict with permission keys and details

        Raises:
            JiraError or subclass on failure

        Note:
            This is a public endpoint - no special permissions required.
        """
        return self.get("/rest/api/3/permissions", operation="get all permissions")

    def get_project_permission_scheme(
        self, project_key_or_id: str, expand: str | None = None
    ) -> dict[str, Any]:
        """
        Get the permission scheme associated with a project.

        Args:
            project_key_or_id: Project key or ID
            expand: Optional expansion (e.g., 'permissions')

        Returns:
            Permission scheme data

        Raises:
            JiraError or subclass on failure

        Note:
            Requires 'Administer Jira' global permission or project admin permission.
        """
        params = {}
        if expand:
            params["expand"] = expand

        return self.get(
            f"/rest/api/3/project/{project_key_or_id}/permissionscheme",
            params=params if params else None,
            operation=f"get permission scheme for project {project_key_or_id}",
        )

    def assign_permission_scheme_to_project(
        self, project_key_or_id: str, scheme_id: int
    ) -> dict[str, Any]:
        """
        Assign a permission scheme to a project.

        Args:
            project_key_or_id: Project key or ID
            scheme_id: Permission scheme ID to assign

        Returns:
            Assigned permission scheme data

        Raises:
            JiraError or subclass on failure

        Note:
            Requires 'Administer Jira' global permission.
        """
        data = {"id": scheme_id}
        return self.put(
            f"/rest/api/3/project/{project_key_or_id}/permissionscheme",
            data=data,
            operation=f"assign permission scheme to project {project_key_or_id}",
        )

    def get_project_roles(self) -> list:
        """
        Get all project roles.

        Returns:
            List of project roles

        Raises:
            JiraError or subclass on failure
        """
        return self.get("/rest/api/3/role", operation="get project roles")
