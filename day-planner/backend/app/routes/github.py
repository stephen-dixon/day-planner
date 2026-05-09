"""GitHub read-only issue import routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ExternalWorkItem, Task
from app.schemas import (
    ExternalWorkItemRead,
    ExternalWorkItemUpdate,
    GitHubConfigRead,
    GitHubIssueRead,
    GitHubMilestoneRead,
    ImportGitHubIssueRequest,
    TaskRead,
)
from app.services.github import (
    external_item_to_issue,
    fetch_issue,
    list_issues_for_milestone,
    list_repo_milestones,
    upsert_external_work_item,
)
from app.settings import get_settings

router = APIRouter(tags=["github"])


@router.get("/github/config", response_model=GitHubConfigRead)
def github_config():
    settings = get_settings()
    return GitHubConfigRead(
        default_owner=settings.github_default_owner,
        default_repo=settings.github_default_repo,
        configured=bool(settings.github_token),
    )


@router.get("/github/repos/{owner}/{repo}/milestones", response_model=list[GitHubMilestoneRead])
def github_milestones(owner: str, repo: str):
    return list_repo_milestones(owner, repo)


@router.get("/github/repos/{owner}/{repo}/milestones/{milestone_number}/issues", response_model=list[GitHubIssueRead])
def github_milestone_issues(owner: str, repo: str, milestone_number: int, db: Session = Depends(get_db)):
    issues = list_issues_for_milestone(owner, repo, milestone_number)
    return [external_item_to_issue(upsert_external_work_item(db, owner, repo, issue)) for issue in issues]


@router.get("/external-work-items", response_model=list[ExternalWorkItemRead])
def external_work_items(
    provider: str | None = None,
    owner: str | None = None,
    repo: str | None = None,
    imported: bool | None = Query(default=None),
    ignored: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    statement = select(ExternalWorkItem)
    if provider:
        statement = statement.where(ExternalWorkItem.provider == provider)
    if owner:
        statement = statement.where(ExternalWorkItem.owner == owner)
    if repo:
        statement = statement.where(ExternalWorkItem.repo == repo)
    if imported is not None:
        statement = statement.where(ExternalWorkItem.imported_task_id.is_not(None) if imported else ExternalWorkItem.imported_task_id.is_(None))
    if ignored is not None:
        statement = statement.where(ExternalWorkItem.ignored == ignored)

    items = db.scalars(statement.order_by(ExternalWorkItem.last_synced_at.desc())).all()
    return [external_work_item_read(item) for item in items]


@router.post("/github/import-issue", response_model=TaskRead)
def import_github_issue(payload: ImportGitHubIssueRequest, db: Session = Depends(get_db)):
    issue = fetch_issue(payload.owner, payload.repo, payload.issue_number)
    item = upsert_external_work_item(db, payload.owner, payload.repo, issue)

    # Idempotency: once a GitHub issue is linked, importing it again returns the
    # existing local Task instead of creating a duplicate backlog item.
    if item.imported_task_id is not None:
        task = db.get(Task, item.imported_task_id)
        if task is not None:
            return task

    body = (issue.get("body") or "").strip()
    excerpt = f"\n\n{body[:1000]}" if body else ""
    task = Task(
        title=issue["title"],
        notes=f"GitHub: {issue['html_url']}\nRepository: {payload.owner}/{payload.repo}\nIssue: #{issue['number']}{excerpt}",
        status="active",
        priority=payload.priority or 3,
        estimated_minutes=payload.estimated_minutes,
    )
    db.add(task)
    db.flush()
    item.imported_task_id = task.id
    db.commit()
    db.refresh(task)
    return task


@router.patch("/external-work-items/{item_id}", response_model=ExternalWorkItemRead)
def update_external_work_item(item_id: int, payload: ExternalWorkItemUpdate, db: Session = Depends(get_db)):
    item = db.get(ExternalWorkItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="External work item not found")
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return external_work_item_read(item)


def external_work_item_read(item: ExternalWorkItem) -> ExternalWorkItemRead:
    issue = external_item_to_issue(item)
    return ExternalWorkItemRead(
        id=item.id,
        provider=item.provider,
        source_type=item.source_type,
        owner=item.owner,
        repo=item.repo,
        project_fields_json=item.project_fields_json,
        last_synced_at=item.last_synced_at,
        **issue,
    )
