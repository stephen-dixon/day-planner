"""Day block REST endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DayBlock, Task
from app.schemas import DayBlockCreate, DayBlockRead, DayBlockUpdate

router = APIRouter(tags=["day blocks"])


@router.get("/days/{block_date}/blocks", response_model=list[DayBlockRead])
def list_day_blocks(block_date: date, db: Session = Depends(get_db)):
    """Return scheduled blocks for one date, ordered by start time."""

    statement = (
        select(DayBlock)
        .where(DayBlock.date == block_date)
        .order_by(DayBlock.start_minute)
    )
    return db.scalars(statement).all()


@router.post(
    "/days/{block_date}/blocks",
    response_model=DayBlockRead,
    status_code=status.HTTP_201_CREATED,
)
def create_day_block(
    block_date: date,
    payload: DayBlockCreate,
    db: Session = Depends(get_db),
):
    """Schedule a task into a block on a date."""

    if db.get(Task, payload.task_id) is None:
        raise HTTPException(status_code=404, detail="Task not found")

    block = DayBlock(date=block_date, **payload.model_dump())
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


@router.patch("/blocks/{block_id}", response_model=DayBlockRead)
def update_day_block(
    block_id: int,
    payload: DayBlockUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a scheduled block."""

    block = db.get(DayBlock, block_id)
    if block is None:
        raise HTTPException(status_code=404, detail="Block not found")

    updates = payload.model_dump(exclude_unset=True)
    task_id = updates.get("task_id")
    if task_id is not None and db.get(Task, task_id) is None:
        raise HTTPException(status_code=404, detail="Task not found")

    start_minute = updates.get("start_minute", block.start_minute)
    end_minute = updates.get("end_minute", block.end_minute)
    if end_minute <= start_minute:
        raise HTTPException(
            status_code=422,
            detail="end_minute must be greater than start_minute",
        )

    for field, value in updates.items():
        setattr(block, field, value)

    db.commit()
    db.refresh(block)
    return block


@router.delete("/blocks/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_day_block(block_id: int, db: Session = Depends(get_db)):
    """Delete a scheduled block."""

    block = db.get(DayBlock, block_id)
    if block is None:
        raise HTTPException(status_code=404, detail="Block not found")

    db.delete(block)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
