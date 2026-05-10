"""Task step REST endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TaskStep
from app.schemas import TaskStepRead, TaskStepUpdate

router = APIRouter(prefix="/steps", tags=["task steps"])


@router.patch("/{step_id}", response_model=TaskStepRead)
def update_task_step(step_id: int, payload: TaskStepUpdate, db: Session = Depends(get_db)):
    step = db.get(TaskStep, step_id)
    if step is None:
        raise HTTPException(status_code=404, detail="Step not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(step, field, value)
    db.commit()
    db.refresh(step)
    return step


@router.delete("/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_step(step_id: int, db: Session = Depends(get_db)):
    step = db.get(TaskStep, step_id)
    if step is None:
        raise HTTPException(status_code=404, detail="Step not found")
    db.delete(step)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
