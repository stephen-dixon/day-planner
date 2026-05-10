"""Structured AI proposal schemas."""

from pydantic import BaseModel, Field

from app.schemas import EnergyLevel, FocusRequired, InterestLevel, TaskContext, TaskPhase


class TaskEnrichment(BaseModel):
    suggested_energy_required: EnergyLevel
    suggested_activation_cost: EnergyLevel
    suggested_focus_required: FocusRequired
    suggested_interest_level: InterestLevel
    suggested_context: TaskContext
    suggested_task_phase: TaskPhase
    suggested_starter_step: str | None = None
    reasoning: str | None = None


class TaskBreakdown(BaseModel):
    starter_step: str
    suggested_steps: list[str] = Field(default_factory=list)
    suggested_block_minutes: int | None = Field(default=None, ge=1)
    reasoning: str | None = None


class SessionReflection(BaseModel):
    inferred_friction_reason: str | None = None
    suggested_task_phase: TaskPhase
    suggested_next_action: str
    reasoning: str | None = None


class SuggestedBlock(BaseModel):
    task_id: int | None = None
    task_step_id: int | None = None
    title: str
    start_minute: int = Field(ge=0, le=1439)
    end_minute: int = Field(ge=1, le=1440)
    reasoning: str


class PlannedDayProposal(BaseModel):
    summary: str
    warnings: list[str] = Field(default_factory=list)
    suggested_blocks: list[SuggestedBlock] = Field(default_factory=list)
    rationale: str
