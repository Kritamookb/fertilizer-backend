# Fertilizer Backend

FastAPI backend for a fertilizer distributor's agent membership, product stock, sales
and single-level commission system.

## Status

**Client project** (confirmed by Simify, 29 Oct 2026). The client's deployment is not
documented in this repo and it is not hosted on Simify infrastructure.

Evidence: last commit 2026-04-04; 20 commits between 2026-03-24 and 2026-04-04.

## What it does

- **Auth** — admin login (`POST /auth/login`) issuing a JWT; `GET /auth/me`. All other
  routers require an admin token.
- **Agents** (`/agents`) — CRUD for agents with type (`general` / `sub_center`), agent
  code, contact, address and bank details; per-agent inventory (`PUT /agents/{id}/inventory`);
  the number of agents is capped by `MAX_AGENTS`.
- **Products** (`/products`) — CRUD with company stock, cost and default prices per agent
  type, retail price tiers and a commissionable flag. Stock transfers to agents are recorded.
- **Sales** (`/sales`) — agent pickups and customer purchases (single and `POST /sales/bulk`),
  payment by transfer, cash or credit, with per-sale totals, cost and gross profit; filter by
  ISO week.
- **Reports** (`/reports/weekly`, `/reports/summary`) — weekly commission per agent
  (commissionable units × `COMMISSION_RATE_PER_UNIT`) and an overall summary.
- `GET /health` health check. API error messages are in Thai.

## Tech stack

Python · FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL (psycopg 3) · pydantic-settings ·
python-jose (JWT) · passlib/bcrypt · Uvicorn

## Architecture

```
app/
  main.py         FastAPI app, CORS, startup (create_all, column patches, seeding)
  config.py       Settings from environment / .env
  database.py     Engine and session
  models.py       AdminUser, Agent, Product, AgentInventory, StockTransfer,
                  ProductRetailPriceTier, Customer, Sale
  schemas.py      Pydantic request/response models
  auth.py         Password hashing, JWT, admin dependency
  agent_types.py  Agent type definitions
  seed.py         Initial admin user and default data
  routers/        auth, agents, products, sales, reports
alembic/versions/ Migrations 001 ... 013 (readable filenames)
```

## Related repositories

- `fertilizer-admin-ui` — Next.js admin interface for this API.

## Getting started

1. Create a virtual environment and install dependencies:
   `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in values locally (never commit `.env`).
   Variables: `APP_NAME`, `DEBUG`, `DATABASE_URL` (must be PostgreSQL), `JWT_SECRET`,
   `ACCESS_TOKEN_EXPIRE_MINUTES`, `COMMISSION_RATE_PER_UNIT`, `MAX_AGENTS`,
   `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`.
3. Run migrations:
   `alembic upgrade head`
4. Start the API:
   `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

Note: `fertilizer-admin-ui` calls `http://localhost:9997` in development, so either run the
API on port `9997` or change `src/utils/api.ts` in the UI.

### Migration naming

- This project uses readable Alembic filenames such as `001_initial.py`.
- Create the next migration with an explicit revision id, for example:
  `alembic revision --autogenerate -m "add weekly summary" --rev-id 014`

### Default seeded data

- On startup an admin user is created from `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`
  if it does not exist.
- Products carry default prices for the `general` and `sub_center` agent types.

## Demo & data policy

Use synthetic agents, customers and sales only. Agent records hold personal and bank
details, so never commit or share real data or database dumps.

## Limitations / known gaps

- No automated tests.
- Single admin role; no agent-facing login.
- On startup the app also runs `Base.metadata.create_all()` and ad-hoc `ALTER TABLE`
  column patches alongside Alembic, so schema changes are managed in two places.
- `JWT_SECRET` is required (32+ characters, no fallback): the app refuses to start without it.
  `ADMIN_PASSWORD` (12+ characters) is only needed to create the first admin on an empty
  database; startup fails rather than creating an admin with a default password.
- The CORS origin list is hard-coded in `app/config.py`.
- Two migration files share the `012_` prefix (`012_stock_transfer_history.py` is revision
  `012`, `012_agent_code_and_address.py` is revision `013`).

---

Built and maintained by Simify — https://simify.dev
