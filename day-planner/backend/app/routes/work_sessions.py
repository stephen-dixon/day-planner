"""Work session REST endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DayBlock, Task, TaskStep, WorkSession
from app.schemas import WorkSessionCreate, WorkSessionRead, WorkSessionUpdate

router = APIRouter(prefix="/work-sessions", tags=["work sessions"])


@router.post("", response_model=WorkSessionRead, status_code=status.HTTP_201_CREATED)
def create_work_session(payload: WorkSessionCreate, db: Session = Depends(get_db)):
    validate_links(db, payload.task_id, payload.task_step_id, payload.day_block_id)
    session = WorkSession(**payload.model_dump())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.patch("/{session_id}", response_model=WorkSessionRead)
def update_work_session(session_id: int, payload: WorkSessionUpdate, db: Session = Depends(get_db)):
    session = db.get(WorkSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Work session not found")
    updates = payload.model_dump(exclude_unset=True)
    validate_links(
        db,
        updates.get("task_id", session.task_id),
        updates.get("task_step_id", session.task_step_id),
        updates.get("day_block_id", session.day_block_id),
    )
    for field, value in updates.items():
        setattr(session, field, value)
    db.commit()
    db.refresh(session)
    return session


def validate_links(db: Session, task_id: int | None, step_id: int | None, block_id: int | None) -> None:
    if task_id is not None and db.get(Task, task_id) is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if step_id is not None and db.get(TaskStep, step_id) is None:
        raise HTTPException(status_code=404, detail="Step not found")
    if block_id is not None and db.get(DayBlock, block_id) is None:
        raise HTTPException(status_code=404, detail="Block not found")
