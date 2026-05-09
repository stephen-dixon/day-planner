# Day Planner

Personal day planner with a FastAPI backend and a SvelteKit frontend.

## Layout

- `day-planner/backend`: FastAPI, SQLite, SQLAlchemy, and integration routes.
- `day-planner/frontend`: SvelteKit UI for the planner, habits, catalogs, and imports.

## Quick Start

Backend:

```bash
cd day-planner/backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Frontend:

```bash
cd day-planner/frontend
npm install
npm run dev
```

The backend and frontend each have their own README files with setup details and environment notes.
