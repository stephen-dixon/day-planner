"""Task REST endpoints."""

import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Milestone, Project, Tag, Task, TaskCompletion, TaskStep, WorkSession
from app.schemas import (
    HabitStatsRead,
    TaskCompleteRequest,
    TaskCompletionRead,
    TaskCreate,
    TaskRead,
    TaskStepCreate,
    TaskStepRead,
    TaskUpdate,
    WorkSessionRead,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def list_tasks(db: Session = Depends(get_db)):
    """Return all tasks ordered by newest first."""

    statement = (
        select(Task)
        .options(selectinload(Task.tags))
        .order_by(Task.created_at.desc())
    )
    return db.scalars(statement).all()


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""

    data = payload.model_dump()
    tag_ids = data.pop("tag_ids", [])
    validate_task_links(db, data.get("project_id"), data.get("milestone_id"), tag_ids)

    recurrence_weekdays = data.pop("recurrence_weekdays", [])
    task = Task(**data)
    task.recurrence_weekdays_json = json.dumps(recurrence_weekdays)
    task.tags = list(db.scalars(select(Tag).where(Tag.id.in_(tag_ids))).all()) if tag_ids else []
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}/steps", response_model=list[TaskStepRead])
def list_task_steps(task_id: int, db: Session = Depends(get_db)):
    if db.get(Task, task_id) is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db.scalars(
        select(TaskStep)
        .where(TaskStep.task_id == task_id)
        .order_by(TaskStep.order_index, TaskStep.id)
    ).all()


@router.post("/{task_id}/steps", response_model=TaskStepRead, status_code=status.HTTP_201_CREATED)
def create_task_step(task_id: int, payload: TaskStepCreate, db: Session = Depends(get_db)):
    if db.get(Task, task_id) is None:
        raise HTTPException(status_code=404, detail="Task not found")
    data = payload.model_dump()
    if data.get("order_index") is None:
        current_max = db.scalar(select(func.max(TaskStep.order_index)).where(TaskStep.task_id == task_id))
        data["order_index"] = 0 if current_max is None else current_max + 1
    step = TaskStep(task_id=task_id, **data)
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


@router.get("/{task_id}/work-sessions", response_model=list[WorkSessionRead])
def task_work_sessions(task_id: int, db: Session = Depends(get_db)):
    if db.get(Task, task_id) is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db.scalars(
        select(WorkSession)
        .where(WorkSession.task_id == task_id)
        .order_by(WorkSession.started_at.desc())
    ).all()


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    """Partially update an existing task."""

    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    updates = payload.model_dump(exclude_unset=True)
    tag_ids = updates.pop("tag_ids", None)
    recurrence_weekdays = updates.pop("recurrence_weekdays", None)
    validate_task_links(
        db,
        updates.get("project_id", task.project_id),
        updates.get("milestone_id", task.milestone_id),
        tag_ids,
    )

    for field, value in updates.items():
        setattr(task, field, value)

    if tag_ids is not None:
        task.tags = list(db.scalars(select(Tag).where(Tag.id.in_(tag_ids))).all()) if tag_ids else []
    if recurrence_weekdays is not None:
        task.recurrence_weekdays_json = json.dumps(recurrence_weekdays)

    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/complete", response_model=TaskRead)
def complete_task(task_id: int, payload: TaskCompleteRequest, db: Session = Depends(get_db)):
    """Log a completion and advance recurring tasks instead of closing them."""

    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    completed_on = payload.completed_on or date.today()
    completion = TaskCompletion(
        task_id=task.id,
        completed_on=completed_on,
        source_block_id=payload.source_block_id,
    )
    db.add(completion)

    if task.is_recurring:
        task.status = "todo"
        task.planned_date = next_recurring_date(task, completed_on)
        task.due_date = task.planned_date
    else:
        task.status = "done"

    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}/completions", response_model=list[TaskCompletionRead])
def task_completions(task_id: int, db: Session = Depends(get_db)):
    """Return completion history for one task."""

    return db.scalars(
        select(TaskCompletion)
        .where(TaskCompletion.task_id == task_id)
        .order_by(TaskCompletion.completed_on.desc())
    ).all()


@router.get("/habits/stats", response_model=list[HabitStatsRead])
def habit_stats(days: int = 30, db: Session = Depends(get_db)):
    """Summarize habit adherence for a rolling timeframe."""

    end = date.today()
    start = end - timedelta(days=days - 1)
    habits = db.scalars(
        select(Task)
        .options(selectinload(Task.tags))
        .where(Task.is_habit == True)  # noqa: E712
        .order_by(Task.title)
    ).all()
    results = []
    for task in habits:
        completions = db.scalars(
            select(TaskCompletion)
            .where(
                TaskCompletion.task_id == task.id,
                TaskCompletion.completed_on >= start,
                TaskCompletion.completed_on <= end,
            )
            .order_by(TaskCompletion.completed_on)
        ).all()
        expected_min, expected_max = expected_completion_range(task, days)
        completion_count = len(completions)
        results.append(
            HabitStatsRead(
                task=task,
                timeframe_days=days,
                completions=completions,
                completion_count=completion_count,
                expected_min=expected_min,
                expected_max=expected_max,
                status=habit_status(completion_count, expected_min, expected_max),
                average_gap_days=average_gap([completion.completed_on for completion in completions]),
            )
        )
    return results


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task and its local day blocks."""

    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def validate_task_links(
    db: Session,
    project_id: int | None,
    milestone_id: int | None,
    tag_ids: list[int] | None,
) -> None:
    """Keep optional task relationships pointing at existing rows."""

    if project_id is not None and db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    if milestone_id is not None:
        milestone = db.get(Milestone, milestone_id)
        if milestone is None:
            raise HTTPException(status_code=404, detail="Milestone not found")
        if project_id is not None and milestone.project_id != project_id:
            raise HTTPException(
                status_code=422,
                detail="Milestone does not belong to selected project",
            )

    if tag_ids:
        existing_count = db.scalar(select(func.count(Tag.id)).where(Tag.id.in_(tag_ids)))
        if existing_count != len(set(tag_ids)):
            raise HTTPException(status_code=404, detail="One or more tags not found")


def next_recurring_date(task: Task, completed_on: date) -> date:
    """Compute the next planned date for simple recurring task rules."""

    if task.recurrence_type == "fixed_weekly" and task.recurrence_weekdays:
        for offset in range(1, 8):
            candidate = completed_on + timedelta(days=offset)
            if candidate.weekday() in task.recurrence_weekdays:
                return candidate
    interval = task.recurrence_interval_days or task.recurrence_max_days or task.recurrence_min_days or 1
    return completed_on + timedelta(days=interval)


def expected_completion_range(task: Task, days: int) -> tuple[int, int]:
    if task.recurrence_type == "fixed_weekly" and task.recurrence_weekdays:
        weekly = max(1, len(task.recurrence_weekdays))
        expected = round(days / 7 * weekly)
        return expected, expected
    min_days = task.recurrence_min_days or task.recurrence_interval_days or 1
    max_days = task.recurrence_max_days or task.recurrence_interval_days or min_days
    expected_min = max(1, days // max_days)
    expected_max = max(expected_min, round(days / min_days))
    return expected_min, expected_max


def habit_status(count: int, expected_min: int, expected_max: int) -> str:
    if count < expected_min:
        return "behind"
    if count > expected_max:
        return "ahead"
    return "on_track"


def average_gap(completed_dates: list[date]) -> float | None:
    if len(completed_dates) < 2:
        return None
    gaps = [
        (completed_dates[index] - completed_dates[index - 1]).days
        for index in range(1, len(completed_dates))
    ]
    return round(sum(gaps) / len(gaps), 1)
