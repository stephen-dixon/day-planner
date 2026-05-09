"""Read-only GitHub milestone issue import helpers."""

import json
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ExternalWorkItem
from app.settings import get_settings

GITHUB_API = "https://api.github.com"


def get_github_client() -> httpx.Client:
    """Return an authenticated GitHub REST client."""

    token = get_settings().github_token
    if not token:
        raise HTTPException(status_code=500, detail="GitHub integration is not configured; set GITHUB_TOKEN")
    return httpx.Client(
        base_url=GITHUB_API,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=20,
    )


def list_repo_milestones(owner: str, repo: str) -> list[dict[str, Any]]:
    with get_github_client() as client:
        response = client.get(f"/repos/{owner}/{repo}/milestones", params={"state": "open"})
    handle_github_response(response)
    return response.json()


def list_issues_for_milestone(owner: str, repo: str, milestone_number: int) -> list[dict[str, Any]]:
    with get_github_client() as client:
        response = client.get(
            f"/repos/{owner}/{repo}/issues",
            params={"state": "open", "milestone": milestone_number, "per_page": 100},
        )
    handle_github_response(response)
    return [issue for issue in response.json() if "pull_request" not in issue]


def fetch_issue(owner: str, repo: str, issue_number: int) -> dict[str, Any]:
    with get_github_client() as client:
        response = client.get(f"/repos/{owner}/{repo}/issues/{issue_number}")
    handle_github_response(response)
    issue = response.json()
    if "pull_request" in issue:
        raise HTTPException(status_code=400, detail="Pull requests cannot be imported as tasks")
    return issue


def normalize_github_issue(issue: dict[str, Any]) -> dict[str, Any]:
    labels = [label["name"] for label in issue.get("labels", [])]
    milestone = issue.get("milestone")
    return {
        "external_id": str(issue["id"]),
        "number": issue["number"],
        "title": issue["title"],
        "body": issue.get("body"),
        "url": issue["html_url"],
        "state": issue["state"],
        "labels": labels,
        "milestone_title": milestone["title"] if milestone else None,
        "imported_task_id": None,
        "ignored": False,
    }


def upsert_external_work_item(db: Session, owner: str, repo: str, issue: dict[str, Any]) -> ExternalWorkItem:
    """Cache a GitHub issue by provider/owner/repo/number without duplicating rows."""

    normalized = normalize_github_issue(issue)
    item = db.scalar(
        select(ExternalWorkItem).where(
            ExternalWorkItem.provider == "github",
            ExternalWorkItem.owner == owner,
            ExternalWorkItem.repo == repo,
            ExternalWorkItem.external_number == normalized["number"],
        )
    )
    if item is None:
        item = ExternalWorkItem(
            provider="github",
            source_type="repo_milestone",
            owner=owner,
            repo=repo,
            external_number=normalized["number"],
            external_id=normalized["external_id"],
            title=normalized["title"],
            body=normalized["body"],
            url=normalized["url"],
            state=normalized["state"],
            labels_json=json.dumps(normalized["labels"]),
            milestone_title=normalized["milestone_title"],
            last_synced_at=datetime.now(timezone.utc),
        )
    else:
        item.external_id = normalized["external_id"]
        item.title = normalized["title"]
        item.body = normalized["body"]
        item.url = normalized["url"]
        item.state = normalized["state"]
        item.labels_json = json.dumps(normalized["labels"])
        item.milestone_title = normalized["milestone_title"]
        item.last_synced_at = datetime.now(timezone.utc)

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def external_item_to_issue(item: ExternalWorkItem) -> dict[str, Any]:
    return {
        "external_work_item_id": item.id,
        "external_id": item.external_id,
        "number": item.external_number or 0,
        "title": item.title,
        "body": item.body,
        "url": item.url,
        "state": item.state,
        "labels": json.loads(item.labels_json or "[]"),
        "milestone_title": item.milestone_title,
        "imported_task_id": item.imported_task_id,
        "ignored": item.ignored,
    }


def handle_github_response(response: httpx.Response) -> None:
    if response.is_success:
        return
    if response.status_code in {401, 403}:
        raise HTTPException(status_code=403, detail="GitHub token lacks access or permissions for this repository")
    if response.status_code == 429 or response.headers.get("x-ratelimit-remaining") == "0":
        raise HTTPException(status_code=429, detail="GitHub API rate limit reached")
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="GitHub repository or issue not found")
    raise HTTPException(status_code=502, detail="GitHub API request failed")


def list_project_v2_items(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
    """TODO: Use GitHub GraphQL Projects v2 when project import is needed."""

    return []


def normalize_project_v2_item(item: dict[str, Any]) -> dict[str, Any]:
    """TODO: Normalize GitHub Projects v2 items into ExternalWorkItem."""

    return item
