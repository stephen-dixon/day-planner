"""Pydantic request and response schemas for the API."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

TaskStatus = Literal["active", "done", "archived", "todo"]
EnergyLevel = Literal["low", "medium", "high", "unknown"]
FocusRequired = Literal["shallow", "medium", "deep", "unknown"]
InterestLevel = Literal["low", "medium", "high", "unknown"]
TaskContext = Literal["coding", "writing", "admin", "household", "errands", "social", "research", "planning", "other", "unknown"]
TaskPhase = Literal["vague", "clarifying", "decomposing", "executable", "executing", "refining", "blocked", "done"]
MomentumState = Literal["stalled", "warming_up", "engaged", "flowing", "finishing", "unknown"]
TaskStepStatus = Literal["todo", "done", "skipped"]
DayBlockType = Literal["task", "step", "goal", "break", "buffer", "admin", "calendar", "other"]
DayBlockStatus = Literal["planned", "done", "skipped"]
CommitmentStrength = Literal["hard", "soft", "optional"]
WorkOutcome = Literal["completed", "partial", "abandoned", "unknown"]
FocusState = Literal["scattered", "okay", "deep", "unknown"]


class TaskCreate(BaseModel):
    """Fields accepted when creating a task."""

    title: str = Field(min_length=1, max_length=200)
    notes: str | None = None
    status: TaskStatus = "active"
    priority: int | None = Field(default=3, ge=1, le=5)
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
    source_type: Literal["local", "todoist", "github", "jira", "external"] = "local"
    source_id: str | None = None
    source_url: str | None = None
    source_label: str | None = None
    energy_required: EnergyLevel = "unknown"
    activation_cost: EnergyLevel = "unknown"
    focus_required: FocusRequired = "unknown"
    interest_level: InterestLevel = "unknown"
    context: TaskContext = "unknown"
    task_phase: TaskPhase = "vague"
    clarity_progress: int | None = Field(default=None, ge=0, le=100)
    momentum_state: MomentumState = "unknown"
    starter_step: str | None = None
    friction_notes: str | None = None


class TaskUpdate(BaseModel):
    """Fields accepted when partially updating a task."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = None
    status: TaskStatus | None = None
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
    source_type: Literal["local", "todoist", "github", "jira", "external"] | None = None
    source_id: str | None = None
    source_url: str | None = None
    source_label: str | None = None
    energy_required: EnergyLevel | None = None
    activation_cost: EnergyLevel | None = None
    focus_required: FocusRequired | None = None
    interest_level: InterestLevel | None = None
    context: TaskContext | None = None
    task_phase: TaskPhase | None = None
    clarity_progress: int | None = Field(default=None, ge=0, le=100)
    momentum_state: MomentumState | None = None
    starter_step: str | None = None
    friction_notes: str | None = None


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
    priority: int | None
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
    source_type: str
    source_id: str | None
    source_url: str | None
    source_label: str | None
    energy_required: str
    activation_cost: str
    focus_required: str
    interest_level: str
    context: str
    task_phase: str
    clarity_progress: int | None
    momentum_state: str
    starter_step: str | None
    friction_notes: str | None
    created_at: datetime
    updated_at: datetime


class TaskStepCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    notes: str | None = None
    status: TaskStepStatus = "todo"
    order_index: int | None = Field(default=None, ge=0)
    estimated_minutes: int | None = Field(default=None, ge=1)
    activation_cost: EnergyLevel = "unknown"
    can_do_low_energy: bool = False


class TaskStepUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    notes: str | None = None
    status: TaskStepStatus | None = None
    order_index: int | None = Field(default=None, ge=0)
    estimated_minutes: int | None = Field(default=None, ge=1)
    activation_cost: EnergyLevel | None = None
    can_do_low_energy: bool | None = None


class TaskStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    title: str
    notes: str | None
    status: str
    order_index: int
    estimated_minutes: int | None
    activation_cost: str
    can_do_low_energy: bool
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

    task_id: int | None = None
    task_step_id: int | None = None
    start_minute: int = Field(ge=0, le=1439)
    end_minute: int = Field(ge=1, le=1440)
    block_type: DayBlockType = "task"
    title_override: str | None = None
    status: DayBlockStatus = "planned"
    commitment_strength: CommitmentStrength = "soft"

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
    task_step_id: int | None = None
    start_minute: int | None = Field(default=None, ge=0, le=1439)
    end_minute: int | None = Field(default=None, ge=1, le=1440)
    block_type: DayBlockType | None = None
    title_override: str | None = None
    status: DayBlockStatus | None = None
    commitment_strength: CommitmentStrength | None = None

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
    task_id: int | None
    task_step_id: int | None
    date: date
    start_minute: int
    end_minute: int
    block_type: str
    title_override: str | None
    status: str
    commitment_strength: str
    created_at: datetime
    updated_at: datetime


class WorkSessionCreate(BaseModel):
    task_id: int | None = None
    task_step_id: int | None = None
    day_block_id: int | None = None
    started_at: datetime
    ended_at: datetime | None = None
    outcome: WorkOutcome = "unknown"
    actual_minutes: int | None = Field(default=None, ge=0)
    energy_at_start: EnergyLevel = "unknown"
    focus_at_start: FocusState = "unknown"
    friction_reason: str | None = None
    notes: str | None = None


class WorkSessionUpdate(BaseModel):
    task_id: int | None = None
    task_step_id: int | None = None
    day_block_id: int | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    outcome: WorkOutcome | None = None
    actual_minutes: int | None = Field(default=None, ge=0)
    energy_at_start: EnergyLevel | None = None
    focus_at_start: FocusState | None = None
    friction_reason: str | None = None
    notes: str | None = None


class WorkSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int | None
    task_step_id: int | None
    day_block_id: int | None
    started_at: datetime
    ended_at: datetime | None
    outcome: str
    actual_minutes: int | None
    energy_at_start: str
    focus_at_start: str
    friction_reason: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class SupportRecommendRequest(BaseModel):
    energy: EnergyLevel
    focus: FocusState
    mood: str | None = None
    available_minutes: int | None = Field(default=None, ge=1)
    preferred_context: TaskContext | None = None


class TaskRecommendationRead(BaseModel):
    task: TaskRead
    score: int
    reasons: list[str]


class TaskAnalyticsRead(BaseModel):
    task_id: int
    average_actual_minutes: float | None
    estimate_ratio: float | None
    average_sessions_to_completion: float | None
    reschedule_count: int
    abandonment_rate: float | None
    confidence_level: str
    duration_summary: str
    activation_risk: str
    common_friction_reasons: list[str] = Field(default_factory=list)
    timing_patterns: list[str] = Field(default_factory=list)
    signals_used: list[str] = Field(default_factory=list)


class ContextAnalyticsRead(BaseModel):
    context: str
    task_count: int
    completed_session_count: int
    average_actual_minutes: float | None
    abandonment_rate: float | None
    common_friction_reasons: list[str] = Field(default_factory=list)
    summary: str
    signals_used: list[str] = Field(default_factory=list)


class AIStatusRead(BaseModel):
    configured: bool
    provider: str
    model: str
    base_url: str | None
    message: str | None


class ReflectSessionRequest(BaseModel):
    task_id: int
    session_note: str = Field(min_length=1)
    outcome: WorkOutcome | None = None


class PlanDayRequest(BaseModel):
    date: date
    energy: EnergyLevel
    focus: FocusState
    available_minutes: int | None = Field(default=None, ge=1)
    free_text: str | None = None
    preferred_context: TaskContext | None = None


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
