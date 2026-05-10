# Day Planner

Personal planning cockpit prototype with a FastAPI backend and a SvelteKit frontend.

The app has two main planning surfaces:

- `Plan Day`: simple backlog plus vertical day timeline for assigning work to time blocks.
- `Support Mode`: ADHD-friendly task selection using energy, activation, focus, context, starter steps, clarity, and momentum.

## Layout

- `day-planner/backend`: FastAPI, SQLite, SQLAlchemy, local models, support recommendations, and integration-shaped routes.
- `day-planner/frontend`: SvelteKit UI for Plan Day, Support Mode, task details, steps, habits, catalogs, and imports.

## Core Model

- `Task`: the unit of work. A task can be local or shaped as coming from an external source such as Todoist, GitHub, Jira, or another system. The app owns local enriched metadata such as energy required, activation cost, focus required, context, phase, clarity progress, momentum, starter step, and friction notes.
- `TaskStep`: fine-grained executable substructure owned locally by the planner. Steps can be scheduled independently later and tracked separately from the parent task.
- `DayBlock`: a scheduled use of time. A block can point to a task, a task step, or stand alone as a break, buffer, goal, admin, calendar, or other block.
- `WorkSession`: a record of what actually happened when work was attempted, including outcome, actual minutes, starting energy/focus, friction, and notes.
- `Support Mode`: a transparent rule-based recommendation layer. It ranks active tasks against current energy, focus, available time, preferred context, activation cost, interest, starter steps, and task phase.
- `Analytics`: deterministic summaries from local evidence such as estimates, actual work-session minutes, skipped blocks, outcomes, context, phase, activation cost, and friction reasons. Analytics should be read as patterns, not precise predictions.
- `AI proposals`: optional LLM-assisted enrichment, breakdown, reflection, and day-planning proposals. AI output never mutates tasks or schedules until the user accepts or edits it.

External systems are intended to provide candidate work or time constraints. This app owns the enriched metadata, scheduling decisions, day blocks, support-mode state, and local task breakdowns. Todoist, Jira, GitHub, and calendar APIs are not implemented as part of this cockpit refactor.

## AI And Analytics

Analytics is evidence. It is local, deterministic, and deliberately avoids fake precision. Examples:

- Good: "Often underestimated", "High variance", "No actuals yet".
- Avoided: exact forecasts like "Expected duration: 127 minutes".

AI is suggestions. The backend exposes a small OpenAI-compatible provider abstraction under `backend/app/llm`. Prompts live in `backend/app/llm/prompts` and are plain text, not hidden.

Configure an OpenAI-compatible provider:

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.5-mini
LLM_API_KEY=...
LLM_BASE_URL=https://api.openai.com/v1
```

`LLM_BASE_URL` is optional for OpenAI and useful for compatible gateways.

Local Ollama setup:

```bash
ollama serve
ollama pull llama3.1
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1
LLM_BASE_URL=http://127.0.0.1:11434/v1
```

If no LLM is configured, deterministic support mode and analytics still work. AI buttons are disabled and `/ai/status` explains what is missing.

## Quick Start

Backend:

```bash
cd day-planner/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd day-planner/frontend
npm install
npm run dev
```

Open:

- `http://127.0.0.1:5173/plan` for simple day planning.
- `http://127.0.0.1:5173/support` for support-mode recommendations.

If the selected SQLite catalog is empty, the backend seeds a few demo tasks for development.

## Deploying To Raspberry Pi

Target shape:

- Caddy is the one web entry point.
- Static SvelteKit files are served from `/opt/dayplanner/frontend/build`.
- FastAPI binds only to `127.0.0.1:8000`.
- Caddy proxies `/api/*` to FastAPI.
- SQLite lives outside the repo at `/var/lib/dayplanner/dayplanner.db`.
- Private access should use Tailscale or a VPN initially.

Install system packages on the Pi:

```bash
sudo apt update
sudo apt install python3 python3-venv nodejs npm sqlite3 rsync caddy
```

Copy or clone this repo onto the Pi, then create backend configuration:

```bash
sudo mkdir -p /etc/dayplanner /var/lib/dayplanner/catalogs
sudo cp day-planner/backend/.env.example /etc/dayplanner/backend.env
sudo nano /etc/dayplanner/backend.env
sudo chmod 600 /etc/dayplanner/backend.env
```

Important production values:

```bash
APP_ENV=production
DATABASE_URL=sqlite:////var/lib/dayplanner/dayplanner.db
CATALOG_DIR=/var/lib/dayplanner/catalogs
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
SECRET_KEY=replace-with-a-long-random-value
OAUTH_STATE_SECRET=replace-with-a-long-random-value
CATALOG_TOKEN_SECRET=replace-with-a-long-random-value
```

For private Caddy same-origin access, the frontend should not set `VITE_API_BASE_URL`; production builds default to `/api`. For local frontend development, use:

```bash
cd day-planner/frontend
cp .env.example .env
npm run dev
```

Manual backend install:

```bash
sudo mkdir -p /opt/dayplanner/backend /opt/dayplanner/frontend /var/lib/dayplanner /var/backups/dayplanner
sudo rsync -a day-planner/backend/ /opt/dayplanner/backend/
cd /opt/dayplanner/backend
sudo python3 -m venv .venv
sudo .venv/bin/pip install -r requirements.txt
```

Manual frontend build:

```bash
sudo rsync -a day-planner/frontend/ /opt/dayplanner/frontend/
cd /opt/dayplanner/frontend
sudo npm ci
sudo npm run build
```

Install the backend service:

```bash
sudo cp deployment/dayplanner-backend.service.example /etc/systemd/system/dayplanner-backend.service
sudo systemctl daemon-reload
sudo systemctl enable --now dayplanner-backend
sudo journalctl -u dayplanner-backend -f
```

Configure Caddy:

```bash
sudo cp deployment/Caddyfile.example /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Access the app at:

- `http://<pi-tailnet-name>:8080`
- `http://<pi-lan-ip>:8080`

The helper script `deployment/install_pi.sh` performs the same install path in a readable way. Review it before running:

```bash
sudo deployment/install_pi.sh
```

Backups:

```bash
sudo deployment/backup_sqlite.sh
```

Backups are written to `/var/backups/dayplanner/dayplanner-YYYY-MM-DD-HHMMSS.db` and backups older than 30 days are deleted.

## Security Notes

- This is a single-user/private deployment. Do not expose it publicly yet.
- Prefer Tailscale or another VPN for remote access.
- Keep FastAPI bound to `127.0.0.1` behind Caddy, not `0.0.0.0`.
- SQLite databases and `/etc/dayplanner/backend.env` should be readable only by the app user/root.
- Backups contain sensitive task data.
- API keys and `.env` files must not be committed.
- Public auth, hardened OAuth callback deployment, and HTTPS automation are intentionally not implemented here.

## Production Paths

Production API routes live under `/api`, for example:

- `/api/health`
- `/api/tasks`
- `/api/days/{date}/blocks`
- `/api/support/recommend-tasks`

Temporary root-level compatibility routes are still registered so local scripts and older dev pages keep working. New deployment and frontend production traffic should use `/api`.
