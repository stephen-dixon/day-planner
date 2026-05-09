"""Pydantic request and response schemas for the API."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TaskCreate(BaseModel):
    """Fields accepted when creating a task."""

    title: str = Field(min_length=1, max_length=200)
    notes: str | None = None
    status: str = "todo"
    priority: int = Field(default=3, ge=1, le=5)
    estimated_minutes: int | None = Field(default=None, ge=1)
    deadline: date | None = None
    due_date: date | None = None
    planned_date: date | None = None
    tag_ids: list[int] = Field(default_factory=list)
    project_id: int | None = None
    milestone_id: int | None = None
    is_recurring: bool = False
    recurrence_type: str | None = None
    recurrence_interval_days: int | None = Field(default=None, ge=1)
    recurrence_weekdays: list[int] = Field(default_factory=list)
    recurrence_min_days: int | None = Field(default=None, ge=1)
    recurrence_max_days: int | None = Field(default=None, ge=1)
    is_habit: bool = False


class TaskUpdate(BaseModel):
    """Fields accepted when partially updating a task."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = None
    status: str | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    estimated_minutes: int | None = Field(default=None, ge=1)
    deadline: date | None = None
    due_date: date | None = None
    planned_date: date | None = None
    tag_ids: list[int] | None = None
    project_id: int | None = None
    milestone_id: int | None = None
    is_recurring: bool | None = None
    recurrence_type: str | None = None
    recurrence_interval_days: int | None = Field(default=None, ge=1)
    recurrence_weekdays: list[int] | None = None
    recurrence_min_days: int | None = Field(default=None, ge=1)
    recurrence_max_days: int | None = Field(default=None, ge=1)
    is_habit: bool | None = None


class TagCreate(BaseModel):
    """Fields accepted when creating a tag."""

    name: str = Field(min_length=1, max_length=80)
    color: str = "#2f80ed"


class TagRead(BaseModel):
    """Tag shape returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str


class TaskRead(BaseModel):
    """Task shape returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    notes: str | None
    status: str
    priority: int
    estimated_minutes: int | None
    deadline: date | None
    due_date: date | None
    planned_date: date | None
    tags: list[TagRead] = Field(default_factory=list)
    tag_ids: list[int] = Field(default_factory=list)
    project_id: int | None
    milestone_id: int | None
    is_recurring: bool
    recurrence_type: str | None
    recurrence_interval_days: int | None
    recurrence_weekdays: list[int] = Field(default_factory=list)
    recurrence_min_days: int | None
    recurrence_max_days: int | None
    is_habit: bool
    created_at: datetime
    updated_at: datetime


class TaskCompleteRequest(BaseModel):
    completed_on: date | None = None
    source_block_id: int | None = None


class TaskCompletionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    completed_on: date
    source_block_id: int | None
    created_at: datetime


class HabitStatsRead(BaseModel):
    task: TaskRead
    timeframe_days: int
    completions: list[TaskCompletionRead]
    completion_count: int
    expected_min: int
    expected_max: int
    status: str
    average_gap_days: float | None


class TaskDeleteRead(BaseModel):
    """Small response after deleting a task."""

    deleted: bool


class ProjectCreate(BaseModel):
    """Fields accepted when creating a project."""

    name: str = Field(min_length=1, max_length=160)
    notes: str | None = None


class ProjectRead(BaseModel):
    """Project shape returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class MilestoneCreate(BaseModel):
    """Fields accepted when creating a project milestone."""

    project_id: int
    name: str = Field(min_length=1, max_length=160)
    due_date: date | None = None


class MilestoneRead(BaseModel):
    """Milestone shape returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    due_date: date | None
    created_at: datetime
    updated_at: datetime


class DayBlockBase(BaseModel):
    """Shared validation for day block input."""

    task_id: int
    start_minute: int = Field(ge=0, le=1439)
    end_minute: int = Field(ge=1, le=1440)
    status: str = "planned"

    @model_validator(mode="after")
    def validate_time_order(self):
        if self.end_minute <= self.start_minute:
            raise ValueError("end_minute must be greater than start_minute")
        return self


class DayBlockCreate(DayBlockBase):
    """Fields accepted when creating a scheduled day block."""


class DayBlockUpdate(BaseModel):
    """Fields accepted when partially updating a day block."""

    task_id: int | None = None
    start_minute: int | None = Field(default=None, ge=0, le=1439)
    end_minute: int | None = Field(default=None, ge=1, le=1440)
    status: str | None = None

    @model_validator(mode="after")
    def validate_time_order(self):
        if (
            self.start_minute is not None
            and self.end_minute is not None
            and self.end_minute <= self.start_minute
        ):
            raise ValueError("end_minute must be greater than start_minute")
        return self


class DayBlockRead(BaseModel):
    """Day block shape returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    date: date
    start_minute: int
    end_minute: int
    status: str
    created_at: datetime
    updated_at: datetime


class ExternalCalendarStatus(BaseModel):
    provider: str
    connected: bool
    account_email: str | None
    scope: str | None
    expires_at: datetime | None


class ExternalCalendarBlockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: str
    date: date
    start_minute: int
    end_minute: int
    title: str | None
    busy_status: str


class ExternalCalendarBlockUpdate(BaseModel):
    title: str | None = None
    busy_status: str | None = None


class GitHubConfigRead(BaseModel):
    default_owner: str | None
    default_repo: str | None
    configured: bool


class GitHubMilestoneRead(BaseModel):
    number: int
    title: str
    description: str | None
    state: str
    open_issues: int
    closed_issues: int
    due_on: datetime | None


class GitHubIssueRead(BaseModel):
    external_work_item_id: int | None = None
    external_id: str
    number: int
    title: str
    body: str | None
    url: str
    state: str
    labels: list[str]
    milestone_title: str | None
    imported_task_id: int | None
    ignored: bool


class ExternalWorkItemRead(GitHubIssueRead):
    id: int
    provider: str
    source_type: str
    owner: str
    repo: str
    project_fields_json: str | None
    last_synced_at: datetime


class ImportGitHubIssueRequest(BaseModel):
    owner: str
    repo: str
    issue_number: int
    estimated_minutes: int | None = Field(default=None, ge=1)
    priority: int | None = Field(default=None, ge=1, le=5)


class ExternalWorkItemUpdate(BaseModel):
    ignored: bool | None = None
