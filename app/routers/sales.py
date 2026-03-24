from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_admin
from app.database import get_db
from app.models import Agent, Product, Sale
from app.schemas import SaleCreate, SaleRead

router = APIRouter(prefix="/sales", tags=["sales"], dependencies=[Depends(get_current_admin)])


def parse_week(week: str) -> tuple[date, date]:
    try:
        year_str, week_str = week.split("-W")
        week_start = date.fromisocalendar(int(year_str), int(week_str), 1)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="รูปแบบสัปดาห์ไม่ถูกต้อง") from exc

    return week_start, date.fromisocalendar(int(year_str), int(week_str), 7)


@router.get("", response_model=list[SaleRead])
def list_sales(
    agent_id: int | None = None,
    week: str | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[SaleRead]:
    statement = (
        select(Sale)
        .options(joinedload(Sale.agent), joinedload(Sale.product))
        .order_by(Sale.sale_date.desc(), Sale.id.desc())
    )

    if agent_id is not None:
        statement = statement.where(Sale.agent_id == agent_id)

    if week:
        week_start, week_end = parse_week(week)
        statement = statement.where(Sale.sale_date.between(week_start, week_end))

    if date_from is not None:
        statement = statement.where(Sale.sale_date >= date_from)

    if date_to is not None:
        statement = statement.where(Sale.sale_date <= date_to)

    sales = db.scalars(statement).unique().all()
    return [
        SaleRead(
            **SaleRead.model_validate(sale).model_dump(
                exclude={"agent_name", "product_name", "product_unit"}
            ),
            agent_name=sale.agent.name,
            product_name=sale.product.name,
            product_unit=sale.product.unit,
        )
        for sale in sales
    ]


@router.post("", response_model=SaleRead, status_code=status.HTTP_201_CREATED)
def create_sale(payload: SaleCreate, db: Session = Depends(get_db)) -> SaleRead:
    agent = db.get(Agent, payload.agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบตัวแทน")

    product = db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบสินค้า")

    sale = Sale(**payload.model_dump())
    db.add(sale)
    db.commit()
    db.refresh(sale)

    return SaleRead(
        **SaleRead.model_validate(sale).model_dump(
            exclude={"agent_name", "product_name", "product_unit"}
        ),
        agent_name=agent.name,
        product_name=product.name,
        product_unit=product.unit,
    )


@router.delete("/{sale_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sale(sale_id: int, db: Session = Depends(get_db)) -> None:
    sale = db.get(Sale, sale_id)
    if sale is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบรายการขาย")

    db.delete(sale)
    db.commit()
