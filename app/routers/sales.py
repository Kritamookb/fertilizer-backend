from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.auth import get_current_admin
from app.database import get_db
from app.models import Agent, AgentInventory, Product, Sale
from app.schemas import SaleCreate, SaleRead

router = APIRouter(prefix="/sales", tags=["sales"], dependencies=[Depends(get_current_admin)])


def parse_week(week: str) -> tuple[date, date]:
    try:
        year_str, week_str = week.split("-W")
        week_start = date.fromisocalendar(int(year_str), int(week_str), 1)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="รูปแบบสัปดาห์ไม่ถูกต้อง") from exc

    return week_start, date.fromisocalendar(int(year_str), int(week_str), 7)


def resolve_retail_unit_price(product: Product, quantity: int) -> int:
    resolved_price = product.default_price_retail
    for tier in sorted(product.retail_price_tiers, key=lambda item: item.min_quantity):
        if quantity >= tier.min_quantity:
            resolved_price = tier.unit_price
    return resolved_price


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
    agent = db.scalar(
        select(Agent)
        .options(joinedload(Agent.inventory_items))
        .where(Agent.id == payload.agent_id)
    )
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบตัวแทน")

    product = db.scalar(
        select(Product)
        .options(selectinload(Product.retail_price_tiers))
        .where(Product.id == payload.product_id)
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบสินค้า")

    inventory_item = next(
        (item for item in agent.inventory_items if item.product_id == payload.product_id),
        None,
    )
    if inventory_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบสต๊อกสินค้าของตัวแทน")
    if inventory_item.quantity < payload.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="สต๊อกสินค้าไม่เพียงพอ")

    resolved_unit_price = payload.unit_price or resolve_retail_unit_price(product, payload.quantity)
    unit_cost = product.cost_price_hq
    total_amount = payload.quantity * resolved_unit_price
    total_cost = payload.quantity * unit_cost

    sale = Sale(
        agent_id=payload.agent_id,
        product_id=payload.product_id,
        quantity=payload.quantity,
        unit_price=resolved_unit_price,
        unit_cost=unit_cost,
        total_amount=total_amount,
        total_cost=total_cost,
        gross_profit=total_amount - total_cost,
        sale_date=payload.sale_date,
    )
    db.add(sale)
    inventory_item.quantity -= payload.quantity
    agent.stock_quantity = sum(item.quantity for item in agent.inventory_items)
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

    inventory_item = db.scalar(
        select(AgentInventory).where(
            AgentInventory.agent_id == sale.agent_id,
            AgentInventory.product_id == sale.product_id,
        )
    )
    agent = db.get(Agent, sale.agent_id)
    if inventory_item is not None:
        inventory_item.quantity += sale.quantity
    if agent is not None:
        inventory_rows = db.scalars(
            select(AgentInventory).where(AgentInventory.agent_id == sale.agent_id)
        ).all()
        agent.stock_quantity = sum(item.quantity for item in inventory_rows)

    db.delete(sale)
    db.commit()
