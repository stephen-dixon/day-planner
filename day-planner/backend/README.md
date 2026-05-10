# Day Planner Backend

Simple synchronous FastAPI backend for a personal day planner.

## Files

- `app/main.py`: creates the FastAPI app, registers routes, and creates tables on startup.
- `app/database.py`: configures SQLite, SQLAlchemy 2.x engine/session setup, and the `get_db` dependency.
- `app/models.py`: SQLAlchemy ORM models for `Task` and `DayBlock`.
- `app/schemas.py`: Pydantic request and response schemas.
- `app/routes/tasks.py`: task endpoints.
- `app/routes/blocks.py`: day block endpoints.
- `app/routes/calendar.py`: read-only Google/Microsoft calendar OAuth and busy-block endpoints.
- `app/routes/github.py`: read-only GitHub milestone issue import endpoints.
- `app/services/`: small provider wrappers for calendar and GitHub APIs.

## Setup

Run these commands from `day-planner/backend`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The app serves OpenAPI docs at `http://127.0.0.1:8000/docs`. Production traffic should use `/api/*` behind Caddy; root-level routes are kept temporarily for local compatibility.

## Task Catalogs

SQLite data is persisted to files. The default catalog uses `DATABASE_URL`, which defaults to `sqlite:///./dayplanner-dev.db`. For Raspberry Pi deployment use `sqlite:////var/lib/dayplanner/dayplanner.db`. Additional catalogs are separate SQLite files under `CATALOG_DIR`, which defaults to `catalogs/`.

Use the frontend Catalogs page, or call the API directly:

```bash
curl http://127.0.0.1:8000/catalogs

curl -X POST http://127.0.0.1:8000/catalogs \
  -H "Content-Type: application/json" \
  -d '{ "name": "work", "password": "change-me" }'

curl -X POST http://127.0.0.1:8000/catalogs/load \
  -H "Content-Type: application/json" \
  -d '{ "name": "work", "password": "change-me" }'
```

Loading a catalog returns a signed token. The frontend stores it in `localStorage` and sends it as `X-Catalog-Token` on normal API calls. Requests without a token continue to use the default `planner.db` catalog for local compatibility.

## Recurring Tasks And Habits

Tasks support simple recurrence metadata:

- `recurrence_type="from_completion"` with `recurrence_interval_days`, for tasks such as watering a plant every 10 days after the last completion.
- `recurrence_type="fixed_weekly"` with `recurrence_weekdays`, where Monday is `0` and Sunday is `6`.
- `is_habit=true` with optional `recurrence_min_days` and `recurrence_max_days` for flexible habits such as running every 2-4 days.

Completing a recurring task logs a row in `task_completions` and advances the task's next planned date rather than permanently closing it:

```bash
curl -X POST http://127.0.0.1:8000/tasks/1/complete \
  -H "Content-Type: application/json" \
  -d '{ "completed_on": "2026-05-09" }'
```

Habit adherence stats:

```bash
curl 'http://127.0.0.1:8000/tasks/habits/stats?days=30'
```

## External Calendars

This app treats Google/Microsoft calendar events as read-only constraints. They are not converted into tasks.

Set these in `.env`:

```bash
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
MICROSOFT_REDIRECT_URI=http://localhost:8000/auth/microsoft/callback
MICROSOFT_TENANT=common

OAUTH_STATE_SECRET=replace-this
FRONTEND_URL=http://127.0.0.1:5173
```

Register these local redirect URIs with the providers:

- `http://localhost:8000/auth/google/callback`
- `http://localhost:8000/auth/microsoft/callback`

Google uses `https://www.googleapis.com/auth/calendar.freebusy`. Microsoft uses delegated `offline_access Calendars.Read User.Read`.

Connect from the planner UI, or open:

- `http://127.0.0.1:8000/auth/google/start`
- `http://127.0.0.1:8000/auth/microsoft/start`

Busy blocks are returned from:

```bash
curl http://127.0.0.1:8000/calendar-blocks/2026-05-09
```

Fetched busy intervals are cached locally so you can add planner-only context:

```bash
curl -X PATCH http://127.0.0.1:8000/calendar-blocks/1 \
  -H "Content-Type: application/json" \
  -d '{ "title": "Optional sync", "busy_status": "non_blocking" }'
```

Hide a block locally without deleting the provider event:

```bash
curl -X DELETE http://127.0.0.1:8000/calendar-blocks/1
```

## GitHub Import

Create a fine-grained GitHub personal access token with read-only access to the repositories you want to browse. For public/private repo issues, grant the minimum repository read permissions that allow reading metadata and issues.

Add this to `.env`:

```bash
GITHUB_TOKEN=github_pat_...
GITHUB_DEFAULT_OWNER=your-org-or-user
GITHUB_DEFAULT_REPO=your-repo
```

Use the Tasks page to load repo milestones, view milestone issues, and import selected issues into the local backlog. Imported GitHub issues become local `Task` rows; the app does not write back to GitHub.

## Security Notes

This is for a private single-user server only. OAuth tokens are stored server-side in SQLite. Do not expose this publicly without app login, HTTPS, CSRF review, and better token encryption. Prefer Tailscale or VPN access while developing. For later Pi/domain deployment, register equivalent HTTPS redirect URLs with Google and Microsoft.

## Example requests

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

Create a task:

```bash
curl -X POST http://127.0.0.1:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Write weekly plan",
    "notes": "Draft priorities for the week",
    "priority": 2,
    "estimated_minutes": 45,
    "deadline": "2026-05-10"
  }'
```

List tasks:

```bash
curl http://127.0.0.1:8000/api/tasks
```

Schedule a block for task `1` on May 10, 2026 from 09:00 to 09:45:

```bash
curl -X POST http://127.0.0.1:8000/api/days/2026-05-10/blocks \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": 1,
    "start_minute": 540,
    "end_minute": 585
  }'
```

List blocks for a day:

```bash
curl http://127.0.0.1:8000/api/days/2026-05-10/blocks
```

Update a block:

```bash
curl -X PATCH http://127.0.0.1:8000/api/blocks/1 \
  -H "Content-Type: application/json" \
  -d '{ "status": "done" }'
```

Delete a block:

```bash
curl -X DELETE http://127.0.0.1:8000/api/blocks/1
```
