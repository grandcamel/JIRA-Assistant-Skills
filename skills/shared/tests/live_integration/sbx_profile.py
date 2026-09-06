"""SBX-only credentials and cleanup support for wrapped live tests."""

from __future__ import annotations

import re
import time
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Mapping
from uuid import uuid4

from jira_as import JiraClient


@dataclass(frozen=True)
class SbxProfile:
    """Credentials injected by ``jira-dev-host --suite``."""

    base_url: str
    email: str = field(repr=False)
    api_token: str = field(repr=False)
    project_key: str = "SBX"


def resolve_sbx_profile(environ: Mapping[str, str]) -> SbxProfile:
    """Resolve the development-only profile without consulting settings files."""
    if environ.get("JIRA_DEFAULT_PROJECT") != "SBX":
        raise ValueError(
            "SBX live profile refused: JIRA_DEFAULT_PROJECT must be SBX; "
            "run through jira-dev-host --suite"
        )

    missing = [
        name
        for name in ("JIRA_SITE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")
        if not environ.get(name)
    ]
    if missing:
        raise ValueError("SBX live profile refused: missing " + ", ".join(missing))
    return SbxProfile(
        base_url=environ["JIRA_SITE_URL"],
        email=environ["JIRA_EMAIL"],
        api_token=environ["JIRA_API_TOKEN"],
    )


class TrackedJiraClient(JiraClient):
    """A Jira client that creates and removes only labeled SBX issues."""

    _CREATE_ENDPOINTS = {"/rest/api/2/issue", "/rest/api/3/issue"}
    _BULK_ENDPOINTS = {"/rest/api/2/issue/bulk", "/rest/api/3/issue/bulk"}
    _CLEANUP_ATTEMPTS = 5
    _CLEANUP_DELAY_SECONDS = 2.0
    _SBX_KEY = re.compile(r"^SBX-[0-9]+$")
    _RUN_LABEL = re.compile(r"^[A-Za-z0-9_-]+$")

    def __init__(self, *args: Any, run_label: str | None = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.run_label = run_label or f"jas-sbx-live-{uuid4()}"
        if not self._RUN_LABEL.fullmatch(self.run_label):
            raise ValueError("SBX live profile refused: run label is invalid")
        self._created_keys: set[str] = set()
        self._created_ids: set[str] = set()
        self._invalid_response_key = False

    @property
    def created_keys(self) -> frozenset[str]:
        """The retained cleanup ledger, including already deleted issues."""
        return frozenset(self._created_keys)

    @property
    def created_ids(self) -> frozenset[str]:
        """The retained issue-id ledger, including already deleted issues."""
        return frozenset(self._created_ids)

    def post(
        self,
        endpoint: str,
        data: dict[str, Any] | str | None = None,
        operation: str = "create resource",
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        *,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Guard and label issue creation while retaining JiraClient's API."""
        if json is not None:
            if data is not None:
                raise TypeError("post accepts either data or json, not both")
            data = json
        if endpoint not in self._CREATE_ENDPOINTS | self._BULK_ENDPOINTS:
            return super().post(endpoint, data, operation, headers, params)

        if not isinstance(data, dict):
            raise ValueError(
                "SBX live profile refused: issue payload must be an object"
            )
        payload = deepcopy(data)
        if endpoint in self._CREATE_ENDPOINTS:
            fields_list = [payload.get("fields")]
        else:
            updates = payload.get("issueUpdates")
            if not isinstance(updates, list) or any(
                not isinstance(item, dict) for item in updates
            ):
                raise ValueError(
                    "SBX live profile refused: bulk issueUpdates must be objects"
                )
            fields_list = [item.get("fields") for item in updates]
        if not fields_list or any(
            not isinstance(fields, dict) for fields in fields_list
        ):
            raise ValueError("SBX live profile refused: issue payload requires fields")
        for fields in fields_list:
            self._require_sbx_project(fields)
            labels = fields.get("labels", [])
            if not isinstance(labels, list):
                raise ValueError("SBX live profile refused: labels must be a list")
            if self.run_label not in labels:
                fields["labels"] = [*labels, self.run_label]

        response = super().post(endpoint, payload, operation, headers, params)
        self._track_response(response)
        created = response.get("issues", []) if isinstance(response, Mapping) else []
        if endpoint in self._CREATE_ENDPOINTS:
            created = [response]
        if (
            not isinstance(created, list)
            or not created
            or any(
                not isinstance(issue, Mapping)
                or not isinstance(issue.get("key"), str)
                or not self._SBX_KEY.fullmatch(issue["key"])
                for issue in created
            )
        ):
            self._invalid_response_key = True
            raise RuntimeError("SBX live profile: malformed issue creation response")
        return response

    def cleanup_created_issues(self) -> str:
        """Delete ledger and lost-response SBX creations, then verify by label."""
        delete_errors: list[str] = (
            ["invalid SBX issue key returned by create"]
            if self._invalid_response_key
            else []
        )
        self._delete_keys(self._created_keys, delete_errors)

        survivors: list[dict[str, Any]] = []
        for attempt in range(self._CLEANUP_ATTEMPTS):
            recovered = self._search_labeled_issues(max_results=100)
            pending = {issue["key"] for issue in recovered}
            self._track_response({"issues": recovered})
            self._delete_keys(pending, delete_errors)
            survivors = self._search_labeled_issues(max_results=1)
            if not survivors:
                break
            if attempt + 1 < self._CLEANUP_ATTEMPTS:
                time.sleep(self._CLEANUP_DELAY_SECONDS)
        else:
            survivors = self._search_labeled_issues(max_results=1)

        survivors.extend(self._remaining_tracked_keys())

        if delete_errors:
            raise RuntimeError(
                "SBX cleanup failed: deletion errors for "
                + ", ".join(delete_errors)
                + f" run_label={self.run_label}"
            )
        if survivors:
            raise RuntimeError(
                f"SBX cleanup failed: labeled SBX issues remain run_label={self.run_label}"
            )
        return (
            f"SBX cleanup verified: tracked={len(self._created_keys)} "
            f"remaining=0 run_label={self.run_label}"
        )

    def _require_sbx_project(self, fields: dict[str, Any]) -> None:
        project = fields.get("project")
        if isinstance(project, str):
            project_key = project
        elif isinstance(project, Mapping):
            project_key = project.get("key")
        else:
            project_key = None
        if project_key != "SBX":
            raise ValueError("SBX live profile refused: issue project must be SBX")

    def _track_response(self, response: Any) -> None:
        if not isinstance(response, Mapping):
            return
        items = response.get("issues")
        if isinstance(items, list):
            for item in items:
                self._track_response(item)
        issue_updates = response.get("issueUpdates")
        if isinstance(issue_updates, list):
            for item in issue_updates:
                self._track_response(item)
        key = response.get("key")
        issue_id = response.get("id")
        if isinstance(key, str) and self._SBX_KEY.fullmatch(key):
            self._created_keys.add(key)
        elif key is not None:
            self._invalid_response_key = True
        if isinstance(issue_id, (str, int)):
            self._created_ids.add(str(issue_id))

    def _delete_keys(self, keys: set[str], errors: list[str]) -> None:
        for key in sorted(keys):
            if not self._SBX_KEY.fullmatch(key):
                errors.append("invalid SBX issue key")
                continue
            try:
                self.delete(f"/rest/api/3/issue/{key}")
            except Exception as exc:  # noqa: BLE001 - normalize third-party errors
                if not self._is_not_found(exc):
                    errors.append(key)

    def _search_labeled_issues(self, max_results: int) -> list[dict[str, Any]]:
        request = {
            "jql": f'project = SBX AND labels = "{self.run_label}"',
            "fields": ["key", "id"],
            "maxResults": max_results,
        }
        try:
            response = super().post(
                "/rest/api/3/search/jql",
                request,
                "search SBX cleanup labels",
            )
        except Exception:  # noqa: BLE001 - normalize third-party errors
            raise RuntimeError(
                f"SBX cleanup failed: label search unavailable run_label={self.run_label}"
            ) from None
        if not isinstance(response, Mapping) or not isinstance(
            response.get("issues"), list
        ):
            raise RuntimeError(
                f"SBX cleanup failed: label search returned malformed data "
                f"run_label={self.run_label}"
            )
        issues = response["issues"]
        if not all(
            isinstance(issue, Mapping)
            and isinstance(issue.get("key"), str)
            and self._SBX_KEY.fullmatch(issue["key"])
            for issue in issues
        ):
            raise RuntimeError(
                f"SBX cleanup failed: label search returned malformed issues "
                f"run_label={self.run_label}"
            )
        return list(issues)

    def _remaining_tracked_keys(self) -> list[dict[str, Any]]:
        """Ensure a removed label cannot hide a surviving tracked issue."""
        remaining = []
        for key in sorted(self._created_keys):
            try:
                super().get(f"/rest/api/3/issue/{key}")
            except Exception as exc:  # noqa: BLE001 - normalize third-party errors
                if self._is_not_found(exc):
                    continue
                raise RuntimeError(
                    f"SBX cleanup failed: issue verification unavailable run_label={self.run_label}"
                ) from None
            remaining.append({"key": key})
        return remaining

    @staticmethod
    def _is_not_found(exc: Exception) -> bool:
        return (
            getattr(exc, "status_code", None) == 404
            or getattr(getattr(exc, "response", None), "status_code", None) == 404
        )
