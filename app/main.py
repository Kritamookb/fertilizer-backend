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


def ensure_columns(table_name: str, statements_by_column: dict[str, str]) -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if table_name not in table_names:
        return

    column_names = {column["name"] for column in inspector.get_columns(table_name)}
    statements: list[str] = []
    for column_name, statement in statements_by_column.items():
        if column_name not in column_names:
            statements.append(statement)

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def ensure_agent_columns() -> None:
    ensure_columns(
        "agents",
        {
            "nickname": "ALTER TABLE agents ADD COLUMN nickname VARCHAR(255) NULL",
            "agent_type": "ALTER TABLE agents ADD COLUMN agent_type VARCHAR(50) NOT NULL DEFAULT 'general'",
            "line_id": "ALTER TABLE agents ADD COLUMN line_id VARCHAR(100) NULL",
            "bank_name": "ALTER TABLE agents ADD COLUMN bank_name VARCHAR(255) NULL",
            "bank_account_name": "ALTER TABLE agents ADD COLUMN bank_account_name VARCHAR(255) NULL",
            "bank_account_number": "ALTER TABLE agents ADD COLUMN bank_account_number VARCHAR(100) NULL",
            "stock_quantity": "ALTER TABLE agents ADD COLUMN stock_quantity INTEGER NOT NULL DEFAULT 0",
            "stock_unit_price": f"ALTER TABLE agents ADD COLUMN stock_unit_price INTEGER NOT NULL DEFAULT {get_agent_unit_price(AGENT_TYPE_GENERAL)}",
        },
    )


def ensure_product_columns() -> None:
    ensure_columns(
        "products",
        {
            "is_commissionable": "ALTER TABLE products ADD COLUMN is_commissionable BOOLEAN NOT NULL DEFAULT 1",
            "company_stock_quantity": "ALTER TABLE products ADD COLUMN company_stock_quantity INTEGER NOT NULL DEFAULT 0",
            "cost_price_hq": "ALTER TABLE products ADD COLUMN cost_price_hq INTEGER NOT NULL DEFAULT 550",
            "default_price_retail": "ALTER TABLE products ADD COLUMN default_price_retail INTEGER NOT NULL DEFAULT 890",
            "default_price_general": "ALTER TABLE products ADD COLUMN default_price_general INTEGER NOT NULL DEFAULT 800",
            "default_price_sub_center": "ALTER TABLE products ADD COLUMN default_price_sub_center INTEGER NOT NULL DEFAULT 770",
        },
    )


def ensure_sale_columns() -> None:
    ensure_columns(
        "sales",
        {
            "customer_id": "ALTER TABLE sales ADD COLUMN customer_id INTEGER NULL",
            "sale_type": "ALTER TABLE sales ADD COLUMN sale_type VARCHAR(50) NOT NULL DEFAULT 'agent_pickup'",
            "payment_method": "ALTER TABLE sales ADD COLUMN payment_method VARCHAR(50) NOT NULL DEFAULT 'transfer'",
            "unit_price": "ALTER TABLE sales ADD COLUMN unit_price INTEGER NOT NULL DEFAULT 800",
            "unit_cost": "ALTER TABLE sales ADD COLUMN unit_cost INTEGER NOT NULL DEFAULT 550",
            "total_amount": "ALTER TABLE sales ADD COLUMN total_amount INTEGER NOT NULL DEFAULT 0",
            "total_cost": "ALTER TABLE sales ADD COLUMN total_cost INTEGER NOT NULL DEFAULT 0",
            "gross_profit": "ALTER TABLE sales ADD COLUMN gross_profit INTEGER NOT NULL DEFAULT 0",
        },
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_agent_columns()
    ensure_product_columns()
    ensure_sale_columns()
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
