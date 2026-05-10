"""Rule-based support mode recommendations."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Task
from app.schemas import SupportRecommendRequest, TaskRecommendationRead

router = APIRouter(prefix="/support", tags=["support"])

ENERGY_RANK = {"unknown": 1, "low": 1, "medium": 2, "high": 3}
FOCUS_RANK = {"unknown": 1, "scattered": 1, "okay": 2, "deep": 3, "shallow": 1, "medium": 2}
INTEREST_RANK = {"unknown": 0, "low": 0, "medium": 1, "high": 2}


@router.post("/recommend-tasks", response_model=list[TaskRecommendationRead])
def recommend_tasks(payload: SupportRecommendRequest, db: Session = Depends(get_db)):
    tasks = db.scalars(
        select(Task)
        .options(selectinload(Task.tags))
        .where(Task.status.in_(["active", "todo"]))
        .order_by(Task.created_at.desc())
    ).all()
    ranked = [score_task(task, payload) for task in tasks]
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:12]


def score_task(task: Task, payload: SupportRecommendRequest) -> dict:
    score = 0
    reasons: list[str] = []
    current_energy = ENERGY_RANK[payload.energy]
    task_energy = ENERGY_RANK.get(task.energy_required, 1)
    current_focus = FOCUS_RANK[payload.focus]
    task_focus = FOCUS_RANK.get(task.focus_required, 1)

    if task_energy <= current_energy:
        score += 3
        reasons.append("energy fit")
    else:
        score -= 2
        reasons.append("may need more energy")

    if task_focus <= current_focus:
        score += 3
        reasons.append("focus fit")
    else:
        score -= 2
        reasons.append("may need more focus")

    if (payload.energy == "low" or payload.focus == "scattered") and task.activation_cost == "low":
        score += 3
        reasons.append("low activation")
    elif task.activation_cost == "high":
        score -= 1

    interest = INTEREST_RANK.get(task.interest_level, 0)
    if interest:
        score += interest
        reasons.append(f"{task.interest_level} interest")

    if payload.available_minutes and task.estimated_minutes:
        if task.estimated_minutes <= payload.available_minutes:
            score += 2
            reasons.append("fits available time")
        else:
            score -= 2
            reasons.append("longer than available time")

    if task.activation_cost == "high" and task.starter_step:
        score += 2
        reasons.append("has starter step")

    if task.task_phase in {"executable", "decomposing"}:
        score += 2
        reasons.append(f"{task.task_phase} phase")
    elif task.task_phase == "vague":
        score -= 1
        reasons.append("needs clarification")

    if payload.preferred_context and task.context == payload.preferred_context:
        score += 2
        reasons.append("context match")

    return {"task": task, "score": score, "reasons": reasons or ["available candidate"]}
