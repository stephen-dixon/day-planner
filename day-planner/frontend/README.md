# Day Planner Frontend

Minimal SvelteKit prototype for the FastAPI day planner backend.

## Run the backend

From `day-planner/backend`:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

The frontend expects the API at `http://127.0.0.1:8000`.

## Run the frontend

From `day-planner/frontend`:

```bash
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

Pages:

- `/`: single-day planner with backlog, external busy blocks, and calendar connection controls.
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

Connect buttons navigate to:

- `http://127.0.0.1:8000/auth/google/start`
- `http://127.0.0.1:8000/auth/microsoft/start`

External events render as grey locked blocks. They are not draggable, resizable, or marked done. You can add a local label, mark one as non-blocking, or hide it from the planner without changing the provider calendar. If a planned task overlaps a blocking busy block, the UI asks whether to schedule anyway.

## GitHub Issues

Set `GITHUB_TOKEN` in the backend `.env`, plus optional `GITHUB_DEFAULT_OWNER` and `GITHUB_DEFAULT_REPO`. On `/tasks`, load milestones, load issues for a milestone, then import selected issues into local tasks. Ignored issues are dimmed locally.

## CORS

The backend is configured with FastAPI `CORSMiddleware` for:

- `http://localhost:5173`
- `http://127.0.0.1:5173`

The relevant backend setup is in `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
