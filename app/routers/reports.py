from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.auth import get_current_admin
from app.config import get_settings
from app.database import get_db
from app.models import Agent, Product, Sale
from app.schemas import (
    SummaryByAgentItem,
    SummaryByProductItem,
    SummaryReportResponse,
    WeeklyCommissionItem,
    WeeklyReportResponse,
)

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(get_current_admin)])
settings = get_settings()


def parse_iso_week(week: str) -> tuple[date, date]:
    try:
        year_str, week_str = week.split("-W")
        year = int(year_str)
        week_number = int(week_str)
        week_start = date.fromisocalendar(year, week_number, 1)
        week_end = date.fromisocalendar(year, week_number, 7)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="รูปแบบสัปดาห์ไม่ถูกต้อง") from exc

    return week_start, week_end


@router.get("/weekly", response_model=WeeklyReportResponse)
def weekly_report(week: str, db: Session = Depends(get_db)) -> WeeklyReportResponse:
    week_start, week_end = parse_iso_week(week)
    child_agent = aliased(Agent)

    statement = (
        select(
            Agent.id,
            Agent.name,
            func.coalesce(func.sum(Sale.quantity), 0).label("team_sales_qty"),
        )
        .select_from(Agent)
        .outerjoin(child_agent, child_agent.referred_by_id == Agent.id)
        .outerjoin(
            Sale,
            (Sale.agent_id == child_agent.id) & Sale.sale_date.between(week_start, week_end),
        )
        .group_by(Agent.id, Agent.name)
        .order_by(Agent.name.asc(), Agent.id.asc())
    )
    rows = db.execute(statement).all()

    items = [
        WeeklyCommissionItem(
            agent_id=agent_id,
            agent_name=agent_name,
            direct_team_sales_qty=int(team_sales_qty or 0),
            commission_amount=int(team_sales_qty or 0) * settings.commission_rate_per_unit,
        )
        for agent_id, agent_name, team_sales_qty in rows
    ]

    return WeeklyReportResponse(
        week=week,
        week_start=week_start,
        week_end=week_end,
        rate_per_unit=settings.commission_rate_per_unit,
        items=items,
    )


@router.get("/summary", response_model=SummaryReportResponse)
def summary_report(db: Session = Depends(get_db)) -> SummaryReportResponse:
    by_agent_rows = db.execute(
        select(
            Agent.id,
            Agent.name,
            func.coalesce(func.sum(Sale.quantity), 0).label("total_quantity"),
        )
        .select_from(Agent)
        .outerjoin(Sale, Sale.agent_id == Agent.id)
        .group_by(Agent.id, Agent.name)
        .order_by(Agent.name.asc(), Agent.id.asc())
    ).all()

    by_product_rows = db.execute(
        select(
            Product.id,
            Product.name,
            Product.unit,
            func.coalesce(func.sum(Sale.quantity), 0).label("total_quantity"),
        )
        .select_from(Product)
        .outerjoin(Sale, Sale.product_id == Product.id)
        .group_by(Product.id, Product.name, Product.unit)
        .order_by(Product.name.asc(), Product.id.asc())
    ).all()

    total_sales_quantity = db.scalar(select(func.coalesce(func.sum(Sale.quantity), 0)).select_from(Sale)) or 0

    return SummaryReportResponse(
        total_sales_quantity=int(total_sales_quantity),
        by_agent=[
            SummaryByAgentItem(
                agent_id=agent_id,
                agent_name=agent_name,
                total_quantity=int(total_quantity or 0),
            )
            for agent_id, agent_name, total_quantity in by_agent_rows
        ],
        by_product=[
            SummaryByProductItem(
                product_id=product_id,
                product_name=product_name,
                unit=unit,
                total_quantity=int(total_quantity or 0),
            )
            for product_id, product_name, unit, total_quantity in by_product_rows
        ],
    )
