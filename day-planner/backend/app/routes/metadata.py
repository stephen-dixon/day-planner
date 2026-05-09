"""Project, milestone, and tag endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Milestone, Project, Tag
from app.schemas import (
    MilestoneCreate,
    MilestoneRead,
    ProjectCreate,
    ProjectRead,
    TagCreate,
    TagRead,
)

router = APIRouter(tags=["metadata"])


@router.get("/tags", response_model=list[TagRead])
def list_tags(db: Session = Depends(get_db)):
    """Return all task tags."""

    return db.scalars(select(Tag).order_by(Tag.name)).all()


@router.post("/tags", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(payload: TagCreate, db: Session = Depends(get_db)):
    """Create a custom task tag."""

    existing = db.scalar(select(Tag).where(Tag.name == payload.name))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Tag already exists")

    tag = Tag(**payload.model_dump())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.get("/projects", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    """Return all projects."""

    return db.scalars(select(Project).order_by(Project.created_at.desc())).all()


@router.post("/projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    """Create a longer-running project."""

    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/milestones", response_model=list[MilestoneRead])
def list_milestones(db: Session = Depends(get_db)):
    """Return all milestones."""

    return db.scalars(select(Milestone).order_by(Milestone.created_at.desc())).all()


@router.post(
    "/milestones",
    response_model=MilestoneRead,
    status_code=status.HTTP_201_CREATED,
)
def create_milestone(payload: MilestoneCreate, db: Session = Depends(get_db)):
    """Create a milestone under a project."""

    if db.get(Project, payload.project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    milestone = Milestone(**payload.model_dump())
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone
