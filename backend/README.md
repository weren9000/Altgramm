# Tescord Backend

FastAPI backend for Tescord.

## Local Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .[dev]
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Useful Commands

```powershell
alembic upgrade head
pytest
```
