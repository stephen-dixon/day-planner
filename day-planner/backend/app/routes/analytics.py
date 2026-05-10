"""Transparent deterministic analytics endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ContextAnalyticsRead, TaskAnalyticsRead
from app.services.analytics_service import context_statistics, task_statistics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/task/{task_id}", response_model=TaskAnalyticsRead)
def task_analytics(task_id: int, db: Session = Depends(get_db)):
    try:
        return task_statistics(db, task_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Task not found")


@router.get("/context/{context}", response_model=ContextAnalyticsRead)
def context_analytics(context: str, db: Session = Depends(get_db)):
    return context_statistics(db, context)
