# BuildPilot AI API

FastAPI, SQLAlchemy, and Pydantic service for BuildPilot AI. See the root [README](../README.md) for the full setup and deployment guide.

## Local development

Copy `.env.example` to `.env`, activate a Python 3.10+ virtual environment, install `requirements.txt`, then run `uvicorn app.main:app --reload`. The local API docs are available at `/docs`.

## Provider configuration

Set `AI_API_KEY`, `AI_BASE_URL`, and `AI_MODEL` in this backend environment. Credentials are only read by the server. Without a provider key, AI routes return validated, clearly labeled fallback results.

## Production

Set `APP_ENV=production`, a random `APP_ACCESS_TOKEN` with at least 32 characters, an exact `FRONTEND_ORIGIN`, and a PostgreSQL `DATABASE_URL`. Production refuses to start without the access token. Configure database backups and an identity provider before broad multi-user access; the shared token does not implement individual accounts or roles.
