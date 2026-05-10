"""Optional AI proposal service for planning cockpit workflows."""

import json
from pathlib import Path
from typing import Any, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel

from app.llm.base import LLMProvider
from app.llm.providers.ollama_provider import OllamaProvider
from app.llm.providers.openai_provider import OpenAIProvider
from app.llm.schemas import PlannedDayProposal, SessionReflection, TaskBreakdown, TaskEnrichment
from app.models import Task
from app.settings import get_settings

PROMPT_DIR = Path(__file__).resolve().parents[1] / "llm" / "prompts"
T = TypeVar("T", bound=BaseModel)


def provider_status() -> dict[str, Any]:
    settings = get_settings()
    configured = settings.llm_provider == "ollama" or bool(settings.llm_api_key)
    return {
        "configured": configured,
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "base_url": settings.llm_base_url,
        "message": None if configured else "Set LLM_API_KEY or use LLM_PROVIDER=ollama.",
    }


def get_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider.lower()
    if provider == "ollama":
        return OllamaProvider(model=settings.llm_model, base_url=settings.llm_base_url)
    if not settings.llm_api_key:
        raise HTTPException(status_code=503, detail="LLM is not configured. Set LLM_API_KEY or use LLM_PROVIDER=ollama.")
    return OpenAIProvider(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
    )


async def enrich_task(task: Task) -> TaskEnrichment:
    return await generate_model(
        prompt_name="enrich_task.txt",
        output_model=TaskEnrichment,
        payload={"task": task_payload(task)},
    )


async def break_down_task(task: Task) -> TaskBreakdown:
    return await generate_model(
        prompt_name="break_down_task.txt",
        output_model=TaskBreakdown,
        payload={"task": task_payload(task)},
    )


async def reflect_session(task: Task, session_note: str, outcome: str | None = None) -> SessionReflection:
    return await generate_model(
        prompt_name="reflect_session.txt",
        output_model=SessionReflection,
        payload={"task": task_payload(task), "session_note": session_note, "outcome": outcome},
    )


async def plan_day(planning_context: dict[str, Any]) -> PlannedDayProposal:
    return await generate_model(
        prompt_name="plan_day.txt",
        output_model=PlannedDayProposal,
        payload=planning_context,
    )


async def generate_model(prompt_name: str, output_model: type[T], payload: dict[str, Any]) -> T:
    provider = get_provider()
    raw = await provider.generate_json(
        system_prompt=load_prompt(prompt_name),
        user_prompt=json.dumps(payload, default=str, indent=2),
        schema=output_model.model_json_schema(),
    )
    return output_model.model_validate(raw)


def load_prompt(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def task_payload(task: Task) -> dict[str, Any]:
    return {
        "id": task.id,
        "title": task.title,
        "notes": task.notes,
        "status": task.status,
        "priority": task.priority,
        "estimated_minutes": task.estimated_minutes,
        "deadline": task.deadline,
        "source_type": task.source_type,
        "source_label": task.source_label,
        "energy_required": task.energy_required,
        "activation_cost": task.activation_cost,
        "focus_required": task.focus_required,
        "interest_level": task.interest_level,
        "context": task.context,
        "task_phase": task.task_phase,
        "clarity_progress": task.clarity_progress,
        "momentum_state": task.momentum_state,
        "starter_step": task.starter_step,
        "friction_notes": task.friction_notes,
    }
