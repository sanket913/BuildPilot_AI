# BuildPilot AI

BuildPilot AI turns a hackathon brief into a team workspace with a saved analysis, solution proposal, eight-phase roadmap, task board, workload profiles, risk recommendations, README export, and submission checklist.

The app automatically creates an isolated, clearly labeled **SAMPLE** project on first launch. If no user project is selected, it opens the sample workspace so reviewers can explore a populated product immediately. The sample includes four team profiles, all four task statuses, all eight roadmap phases, upcoming and overdue dates, an unassigned task, activity history, saved documentation, and an incomplete checklist. Reset sample data from Settings or Projects; this only deletes rows marked as sample data.

## Run locally

Requirements: Python 3.10+ and Node.js 20.19+.

In one terminal:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. API health: <http://localhost:8000/api/health>. Interactive API reference: <http://localhost:8000/docs>.

## Demo walkthrough

1. Open the sample project and review its command center metrics and recent activity.
2. Open **AI Problem Analyzer**; inspect the saved brief and editable analysis.
3. Open **Solution Studio** and edit or regenerate the saved proposal.
4. Review the eight roadmap phases and update a task status.
5. In **Task Management**, search and filter tasks, then create or edit a task.
6. In **Team Workspace**, inspect skills and workload, or recommend assignments.
7. Open **Risk Center** to review the overdue and unassigned task recommendations.
8. Generate or edit the README in **Documentation**, then export the Markdown file.
9. Toggle checklist items in **Submission Center** and see readiness recalculate.
10. Reset the sample when you want to replay the walkthrough.

## AI and credentials

- The AI service is integrated. Without a provider key, the app clearly labels schema-validated fallback guidance as demo output.
- For real responses, create an **OpenAI API key** at <https://platform.openai.com/api-keys> and place it only in `backend/.env` as `AI_API_KEY=...`. Your account may need API billing or credits enabled. The default model, `gpt-6-luna`, is available through the API; change it with `AI_MODEL`. `AI_BASE_URL` defaults to `https://api.openai.com/v1`, and `AI_TIMEOUT_SECONDS` controls request timeout. The current integration calls the OpenAI-compatible Chat Completions endpoint and validates responses with Pydantic schemas.
- The key stays server-side. Never put it in a `VITE_` variable, commit `.env`, or share it in chat. On Render, configure it in the API service's environment variables.
- Local persistence uses SQLite at `backend/buildpilot.db`. Use Render's managed PostgreSQL through `DATABASE_URL` in deployment.
- Nonilion remains unconfigured because no verified API documentation or connection details are available; no endpoints or credentials are fabricated.

## Access control and production deployment

- Local development is open by default. For deployment, set `APP_ENV=production` and configure `APP_ACCESS_TOKEN` with a unique random value of at least 32 characters. Production startup fails if the token is missing or too short. The API requires this code for workspace routes; the browser prompts for it and keeps it in session storage for the current tab. Treat this as a **single shared workspace code**, not individual user accounts or roles.
- Generate a token locally with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Never commit it. Render's blueprint marks `APP_ACCESS_TOKEN` as a secret you must set.
- Set `VITE_API_URL` to the deployed API origin ending in `/api`, and API `FRONTEND_ORIGIN` to the exact deployed frontend origin. The health endpoint checks database connectivity; production disables interactive API docs.
- Before inviting real users, add an organization identity provider if you need distinct accounts, roles, auditability, or project-level privacy. The shared code protects the entire workspace but does not provide those capabilities.
- Configure database backups and monitor AI provider spend and request limits before using real data.

## Checks

From `backend`, run `python -m pytest -q`. From `frontend`, run `npm test` and `npm run build`. Use `npm ci` for clean, lockfile-based frontend installs.

## Render deployment

Use `render.yaml` as the starting point. Set `VITE_API_URL`, `FRONTEND_ORIGIN`, and the required secret `APP_ACCESS_TOKEN` in Render. The blueprint provisions PostgreSQL. Set `AI_API_KEY` to enable real model responses; otherwise, labeled demo output remains available. Confirm `/api/health` reports `status: ok` after deployment.

## Submission notes and limits

- Demo mode is fully usable without network access to an AI provider. AI fallback content is labeled.
- Access control uses one shared code. Individual accounts, roles, project ownership, and per-user data isolation are not implemented; add a managed identity layer before opening the service broadly.
- The sample challenge data is fictional and exists to demonstrate UI workflows; it is not validated operational food-safety guidance.
- Nonilion cannot be connected without official integration details.
