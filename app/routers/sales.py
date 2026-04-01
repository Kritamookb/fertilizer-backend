from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.auth import get_current_admin
from app.database import get_db
from app.models import Agent, Customer, Product, Sale
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


def serialize_sale(sale: Sale) -> SaleRead:
    return SaleRead(
        **SaleRead.model_validate(sale).model_dump(
            exclude={"agent_name", "product_name", "product_unit", "customer_name", "customer_phone"}
        ),
        agent_name=sale.agent.name if sale.agent else None,
        product_name=sale.product.name if sale.product else None,
        product_unit=sale.product.unit if sale.product else None,
        customer_name=sale.customer.name if sale.customer else None,
        customer_phone=sale.customer.phone if sale.customer else None,
    )


def resolve_customer(db: Session, payload: SaleCreate) -> Customer | None:
    if payload.sale_type != "customer_purchase" or not payload.customer_name:
        return None

    statement = select(Customer).where(
        Customer.agent_id == payload.agent_id,
        Customer.name == payload.customer_name.strip(),
    )
    if payload.customer_phone:
        statement = statement.where(Customer.phone == payload.customer_phone.strip())

    customer = db.scalar(statement)
    if customer is not None:
        if payload.customer_phone and customer.phone != payload.customer_phone.strip():
            customer.phone = payload.customer_phone.strip()
        return customer

    customer = Customer(
        agent_id=payload.agent_id,
        name=payload.customer_name.strip(),
        phone=payload.customer_phone.strip() if payload.customer_phone else None,
    )
    db.add(customer)
    db.flush()
    return customer


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
        .options(joinedload(Sale.agent), joinedload(Sale.product), joinedload(Sale.customer))
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
    return [serialize_sale(sale) for sale in sales]


@router.post("", response_model=SaleRead, status_code=status.HTTP_201_CREATED)
def create_sale(payload: SaleCreate, db: Session = Depends(get_db)) -> SaleRead:
    agent = db.scalar(
        select(Agent)
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

    if product.company_stock_quantity < payload.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="สต๊อกสินค้าไม่เพียงพอ")

    resolved_unit_price = payload.unit_price or resolve_retail_unit_price(product, payload.quantity)
    unit_cost = product.cost_price_hq
    total_amount = payload.quantity * resolved_unit_price
    total_cost = payload.quantity * unit_cost
    customer = resolve_customer(db, payload)

    sale = Sale(
        agent_id=payload.agent_id,
        product_id=payload.product_id,
        customer_id=customer.id if customer else None,
        sale_type=payload.sale_type,
        payment_method=payload.payment_method,
        quantity=payload.quantity,
        unit_price=resolved_unit_price,
        unit_cost=unit_cost,
        total_amount=total_amount,
        total_cost=total_cost,
        gross_profit=total_amount - total_cost,
        sale_date=payload.sale_date,
    )
    db.add(sale)
    product.company_stock_quantity -= payload.quantity
    db.commit()
    db.refresh(sale)
    sale = db.scalar(
        select(Sale)
        .options(joinedload(Sale.agent), joinedload(Sale.product), joinedload(Sale.customer))
        .where(Sale.id == sale.id)
    ) or sale

    return serialize_sale(sale)


@router.delete("/{sale_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sale(sale_id: int, db: Session = Depends(get_db)) -> None:
    sale = db.get(Sale, sale_id)
    if sale is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบรายการขาย")

    product = db.get(Product, sale.product_id)
    if product is not None:
        product.company_stock_quantity += sale.quantity

    db.delete(sale)
    db.commit()
