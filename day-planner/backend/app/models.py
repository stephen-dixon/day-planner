"""SQLAlchemy ORM models for planner data."""

import json
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Table, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", ForeignKey("tasks.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class Tag(Base):
    """A lightweight category label for grouping and coloring tasks."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#2f80ed", nullable=False)

    tasks: Mapped[list["Task"]] = relationship(
        secondary=task_tags,
        back_populates="tags",
    )


class Project(Base):
    """A longer-running project that can contain tasks and milestones."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    milestones: Mapped[list["Milestone"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list["Task"]] = relationship(back_populates="project")


class Milestone(Base):
    """Optional grouping inside a project."""

    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project: Mapped[Project] = relationship(back_populates="milestones")
    tasks: Mapped[list["Task"]] = relationship(back_populates="milestone")


class Task(Base):
    """A task that may later be scheduled into one or more day blocks."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="todo", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    planned_date: Mapped[Optional[date]] = mapped_column(Date, index=True, nullable=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    milestone_id: Mapped[Optional[int]] = mapped_column(ForeignKey("milestones.id"), nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurrence_type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    recurrence_interval_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recurrence_weekdays_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recurrence_min_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recurrence_max_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_habit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    blocks: Mapped[list["DayBlock"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )
    completions: Mapped[list["TaskCompletion"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list[Tag]] = relationship(
        secondary=task_tags,
        back_populates="tasks",
    )
    project: Mapped[Optional[Project]] = relationship(back_populates="tasks")
    milestone: Mapped[Optional[Milestone]] = relationship(back_populates="tasks")

    @property
    def tag_ids(self) -> list[int]:
        return [tag.id for tag in self.tags]

    @property
    def recurrence_weekdays(self) -> list[int]:
        if not self.recurrence_weekdays_json:
            return []
        return json.loads(self.recurrence_weekdays_json)


class DayBlock(Base):
    """A scheduled block on a calendar date.

    Times are stored as integer minutes since midnight, for example 540 for
    09:00 and 1020 for 17:00.
    """

    __tablename__ = "day_blocks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    start_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    end_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="planned", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    task: Mapped[Task] = relationship(back_populates="blocks")


class TaskCompletion(Base):
    """A log entry for each time a task or habit was actually completed."""

    __tablename__ = "task_completions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    completed_on: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    source_block_id: Mapped[Optional[int]] = mapped_column(ForeignKey("day_blocks.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    task: Mapped[Task] = relationship(back_populates="completions")


class ExternalCalendarAccount(Base):
    """Server-side OAuth tokens for one connected external calendar account."""

    __tablename__ = "external_calendar_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    account_email: Mapped[Optional[str]] = mapped_column(String(240), nullable=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ExternalCalendarBlock(Base):
    """Optional cache row for external busy blocks."""

    __tablename__ = "external_calendar_blocks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    external_calendar_id: Mapped[Optional[str]] = mapped_column(String(240), nullable=True)
    external_event_id: Mapped[Optional[str]] = mapped_column(String(240), nullable=True)
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    start_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    end_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(240), nullable=True)
    busy_status: Mapped[str] = mapped_column(String(40), default="busy", nullable=False)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ExternalWorkItem(Base):
    """A cached external candidate task, currently from GitHub issues."""

    __tablename__ = "external_work_items"
    __table_args__ = (
        UniqueConstraint("provider", "owner", "repo", "external_number", name="uq_external_work_item_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), default="github", nullable=False)
    source_type: Mapped[str] = mapped_column(String(60), nullable=False)
    external_id: Mapped[str] = mapped_column(String(120), nullable=False)
    external_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    repo: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(40), nullable=False)
    labels_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    milestone_title: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    project_fields_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    imported_task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id"), nullable=True)
    ignored: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
