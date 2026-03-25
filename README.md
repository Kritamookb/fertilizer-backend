# Fertilizer Backend

FastAPI backend for the fertilizer membership and single-level commission system described in `PLAN.md`.

## Run locally

1. Create a virtual environment and install dependencies:
   `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and update the values.
3. Run migrations:
   `alembic upgrade head`
4. Start the API:
   `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Migration naming

- This project uses readable Alembic filenames such as `001_initial.py`.
- Create the next migration with an explicit revision id, for example:
  `alembic revision --autogenerate -m "add weekly summary" --rev-id 002`

## Default seeded data

- Admin user from `.env`: `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`
- Products: `ปุ๋ย A`, `ปุ๋ย B`, `ปุ๋ย C` (default to commissionable)
