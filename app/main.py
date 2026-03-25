from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.agent_types import AGENT_TYPE_GENERAL, get_agent_unit_price
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.routers import agents, auth, products, reports, sales
from app.seed import seed_initial_data

settings = get_settings()


def ensure_sqlite_agent_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "agents" not in table_names:
        return

    column_names = {column["name"] for column in inspector.get_columns("agents")}
    statements: list[str] = []

    if "agent_type" not in column_names:
        statements.append(
            "ALTER TABLE agents ADD COLUMN agent_type VARCHAR(50) NOT NULL DEFAULT 'general'"
        )
    if "stock_quantity" not in column_names:
        statements.append(
            "ALTER TABLE agents ADD COLUMN stock_quantity INTEGER NOT NULL DEFAULT 0"
        )
    if "stock_unit_price" not in column_names:
        statements.append(
            f"ALTER TABLE agents ADD COLUMN stock_unit_price INTEGER NOT NULL DEFAULT {get_agent_unit_price(AGENT_TYPE_GENERAL)}"
        )

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def ensure_sqlite_product_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "products" not in table_names:
        return

    column_names = {column["name"] for column in inspector.get_columns("products")}
    statements: list[str] = []

    if "is_commissionable" not in column_names:
        statements.append(
            "ALTER TABLE products ADD COLUMN is_commissionable BOOLEAN NOT NULL DEFAULT 1"
        )
    if "default_price_general" not in column_names:
        statements.append(
            "ALTER TABLE products ADD COLUMN default_price_general INTEGER NOT NULL DEFAULT 800"
        )
    if "default_price_sub_center" not in column_names:
        statements.append(
            "ALTER TABLE products ADD COLUMN default_price_sub_center INTEGER NOT NULL DEFAULT 770"
        )

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
        ensure_sqlite_agent_columns()
        ensure_sqlite_product_columns()
    with SessionLocal() as db:
        seed_initial_data(db)
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(agents.router, prefix=settings.api_prefix)
app.include_router(products.router, prefix=settings.api_prefix)
app.include_router(sales.router, prefix=settings.api_prefix)
app.include_router(reports.router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Fertilizer backend is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
