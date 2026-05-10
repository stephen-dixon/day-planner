"""AI proposal endpoints. These never mutate tasks or plans automatically."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.llm.schemas import PlannedDayProposal, SessionReflection, TaskBreakdown, TaskEnrichment
from app.models import DayBlock, Task
from app.schemas import AIStatusRead, PlanDayRequest, ReflectSessionRequest
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status", response_model=AIStatusRead)
def ai_status():
    return ai_service.provider_status()


@router.post("/enrich-task/{task_id}", response_model=TaskEnrichment)
async def enrich_task(task_id: int, db: Session = Depends(get_db)):
    task = get_task_or_404(db, task_id)
    return await ai_service.enrich_task(task)


@router.post("/break-down-task/{task_id}", response_model=TaskBreakdown)
async def break_down_task(task_id: int, db: Session = Depends(get_db)):
    task = get_task_or_404(db, task_id)
    return await ai_service.break_down_task(task)


@router.post("/reflect-session", response_model=SessionReflection)
async def reflect_session(payload: ReflectSessionRequest, db: Session = Depends(get_db)):
    task = get_task_or_404(db, payload.task_id)
    return await ai_service.reflect_session(task, payload.session_note, payload.outcome)


@router.post("/plan-day", response_model=PlannedDayProposal)
async def plan_day(payload: PlanDayRequest, db: Session = Depends(get_db)):
    tasks = db.scalars(
        select(Task)
        .where(Task.status.in_(["active", "todo"]))
        .order_by(Task.deadline.is_(None), Task.deadline, Task.created_at.desc())
        .limit(30)
    ).all()
    blocks = db.scalars(
        select(DayBlock)
        .where(DayBlock.date == payload.date)
        .order_by(DayBlock.start_minute)
    ).all()
    context = {
        "date": payload.date,
        "state": payload.model_dump(),
        "tasks": [ai_service.task_payload(task) for task in tasks],
        "existing_blocks": [
            {
                "id": block.id,
                "task_id": block.task_id,
                "task_step_id": block.task_step_id,
                "title_override": block.title_override,
                "start_minute": block.start_minute,
                "end_minute": block.end_minute,
                "status": block.status,
                "commitment_strength": block.commitment_strength,
            }
            for block in blocks
        ],
    }
    return await ai_service.plan_day(context)


def get_task_or_404(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
