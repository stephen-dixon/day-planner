# Day Planner Frontend

Minimal SvelteKit prototype for the FastAPI day planner backend.

## Run the backend

From `day-planner/backend`:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

For local development, copy `.env.example` to `.env` so the frontend calls `http://127.0.0.1:8000`. Production builds default to same-origin `/api` for Caddy reverse proxy deployment.

## Run the frontend

From `day-planner/frontend`:

```bash
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

Pages:

- `/`: single-day planner with backlog, external busy blocks, and calendar connection controls.
- `/plan`: simplified planning cockpit day view.
- `/support`: support mode with deterministic recommendations plus optional AI proposals.
- `/tasks`: focused task creation, backlog editing, and GitHub milestone issue import.
- `/habits`: rolling habit adherence view for recurring tasks marked as habits.
- `/projects`: project view showing complete and outstanding tasks by milestone.
- `/projects/{id}/gantt`: Gantt-style project view using task planned and due dates.
- `/catalogs`: browse, create, and load separate password-protected task catalogs.

## Task Catalogs

Use `/catalogs` to switch contexts such as work, home, or weekend planning. Each catalog is a separate SQLite database file on the backend. Loading a protected catalog stores a signed catalog token in browser `localStorage`; all API calls then use that selected catalog until you switch back to default or load another catalog.

## Recurring Tasks And Habits

Tasks can be marked recurring from the planner or focused task page. A recurring task can repeat from the last completion, such as every 10 days, or on a fixed weekly schedule. Marking a recurring task as a habit lets `/habits` compare logged completions against the expected range for a week, month, or three months.

## External Calendars

Set the backend `.env` values from `backend/.env.example`, start FastAPI, then use the Calendar integrations panel on `/`.

Connect buttons navigate through the configured API base:

- `/auth/google/start` in dev via `VITE_API_BASE_URL`
- `/api/auth/google/start` in production behind Caddy

External events render as grey locked blocks. They are not draggable, resizable, or marked done. You can add a local label, mark one as non-blocking, or hide it from the planner without changing the provider calendar. If a planned task overlaps a blocking busy block, the UI asks whether to schedule anyway.

## GitHub Issues

Set `GITHUB_TOKEN` in the backend `.env`, plus optional `GITHUB_DEFAULT_OWNER` and `GITHUB_DEFAULT_REPO`. On `/tasks`, load milestones, load issues for a milestone, then import selected issues into local tasks. Ignored issues are dimmed locally.

## Static Build

This app uses `@sveltejs/adapter-static`; `npm run build` writes deployable static files to `frontend/build`.

## CORS

Backend CORS origins are configured with `CORS_ORIGINS` in the backend environment. Same-origin production traffic through Caddy should not need CORS.
