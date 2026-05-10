"""Deterministic analytics based on observed local planning data."""

from collections import Counter
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DayBlock, Task, WorkSession
from app.schemas import ContextAnalyticsRead, TaskAnalyticsRead


def task_statistics(db: Session, task_id: int) -> TaskAnalyticsRead:
    task = db.get(Task, task_id)
    if task is None:
        raise ValueError("Task not found")
    sessions = db.scalars(select(WorkSession).where(WorkSession.task_id == task_id)).all()
    blocks = db.scalars(select(DayBlock).where(DayBlock.task_id == task_id)).all()
    actuals = [session.actual_minutes for session in sessions if session.actual_minutes is not None and session.actual_minutes > 0]
    average_actual = round(mean(actuals), 1) if actuals else None
    estimate_ratio = round(average_actual / task.estimated_minutes, 2) if average_actual and task.estimated_minutes else None
    completed_sessions = [session for session in sessions if session.outcome == "completed"]
    abandonment_rate = round(
        len([session for session in sessions if session.outcome == "abandoned"]) / len(sessions),
        2,
    ) if sessions else None
    return TaskAnalyticsRead(
        task_id=task_id,
        average_actual_minutes=average_actual,
        estimate_ratio=estimate_ratio,
        average_sessions_to_completion=round(len(sessions) / len(completed_sessions), 1) if completed_sessions else None,
        reschedule_count=len([block for block in blocks if block.status == "skipped"]),
        abandonment_rate=abandonment_rate,
        confidence_level=confidence_level(len(sessions), len(blocks)),
        duration_summary=estimate_task_duration(task, actuals),
        activation_risk=estimate_activation_risk(task, sessions, blocks),
        common_friction_reasons=common_friction_reasons(sessions),
        timing_patterns=timing_patterns(sessions, blocks),
        signals_used=signals_used(task, sessions, blocks),
    )


def context_statistics(db: Session, context: str) -> ContextAnalyticsRead:
    tasks = db.scalars(select(Task).where(Task.context == context)).all()
    task_ids = [task.id for task in tasks]
    sessions = db.scalars(select(WorkSession).where(WorkSession.task_id.in_(task_ids))).all() if task_ids else []
    actuals = [session.actual_minutes for session in sessions if session.actual_minutes is not None and session.actual_minutes > 0]
    completed = [session for session in sessions if session.outcome == "completed"]
    abandoned = [session for session in sessions if session.outcome == "abandoned"]
    return ContextAnalyticsRead(
        context=context,
        task_count=len(tasks),
        completed_session_count=len(completed),
        average_actual_minutes=round(mean(actuals), 1) if actuals else None,
        abandonment_rate=round(len(abandoned) / len(sessions), 2) if sessions else None,
        common_friction_reasons=common_friction_reasons(sessions),
        summary=context_summary(context, len(tasks), actuals, sessions),
        signals_used=["task context", "work session outcomes", "actual minutes", "friction reasons"],
    )


def estimate_task_duration(task: Task, actuals: list[int]) -> str:
    if not actuals and task.estimated_minutes:
        return f"No actuals yet; current estimate is {task.estimated_minutes} minutes."
    if not actuals:
        return "No duration pattern yet."
    avg = mean(actuals)
    if len(actuals) >= 2 and max(actuals) >= min(actuals) * 2:
        variance = "High variance"
    else:
        variance = "Fairly consistent"
    if task.estimated_minutes and avg > task.estimated_minutes * 1.25:
        return f"Often underestimated. {variance} across observed sessions."
    if task.estimated_minutes and avg < task.estimated_minutes * 0.75:
        return f"Often shorter than estimated. {variance} across observed sessions."
    return f"Close to estimate so far. {variance} across observed sessions."


def estimate_activation_risk(task: Task, sessions: list[WorkSession], blocks: list[DayBlock]) -> str:
    abandoned = len([session for session in sessions if session.outcome == "abandoned"])
    skipped = len([block for block in blocks if block.status == "skipped"])
    if task.activation_cost == "high" or abandoned + skipped >= 2:
        return "High activation risk based on task metadata and skipped/abandoned attempts."
    if task.activation_cost == "medium" or abandoned + skipped == 1:
        return "Moderate activation risk based on available signals."
    return "No strong activation-risk signal yet."


def find_similar_tasks(db: Session, task: Task) -> list[Task]:
    return db.scalars(
        select(Task)
        .where(Task.id != task.id, Task.context == task.context)
        .limit(5)
    ).all()


def common_friction_reasons(sessions: list[WorkSession]) -> list[str]:
    counts = Counter(session.friction_reason for session in sessions if session.friction_reason)
    return [reason for reason, _ in counts.most_common(3)]


def timing_patterns(sessions: list[WorkSession], blocks: list[DayBlock]) -> list[str]:
    patterns: list[str] = []
    completed_block_ids = {session.day_block_id for session in sessions if session.outcome == "completed" and session.day_block_id}
    completed_blocks = [block for block in blocks if block.id in completed_block_ids]
    if completed_blocks:
        morning = len([block for block in completed_blocks if block.start_minute < 12 * 60])
        if morning > len(completed_blocks) / 2:
            patterns.append("Usually completed successfully in morning blocks.")
    return patterns


def confidence_level(session_count: int, block_count: int) -> str:
    signal_count = session_count + block_count
    if signal_count >= 8:
        return "medium"
    if signal_count >= 3:
        return "low"
    return "very_low"


def signals_used(task: Task, sessions: list[WorkSession], blocks: list[DayBlock]) -> list[str]:
    signals = ["estimated_minutes", "task phase", "context", "activation_cost", "focus_required"]
    if sessions:
        signals.extend(["actual_minutes", "work session outcomes", "friction reasons"])
    if blocks:
        signals.extend(["scheduled blocks", "skipped blocks"])
    return signals


def context_summary(context: str, task_count: int, actuals: list[int], sessions: list[WorkSession]) -> str:
    if not task_count:
        return f"No local tasks with context {context} yet."
    if not sessions:
        return f"{task_count} task(s) use context {context}, but there are no work-session patterns yet."
    if actuals:
        return f"{context} has observed work sessions; use the average as a rough guide, not a precise forecast."
    return f"{context} has session outcomes but no actual-minute data yet."
