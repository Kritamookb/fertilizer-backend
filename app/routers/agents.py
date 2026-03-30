from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased, joinedload

from app.agent_types import AGENT_TYPE_SUB_CENTER, get_agent_unit_price
from app.auth import get_current_admin
from app.config import get_settings
from app.database import get_db
from app.models import Agent, AgentInventory, Product, Sale
from app.schemas import (
    AgentCreate,
    AgentDetail,
    AgentInventoryBulkUpdate,
    AgentInventoryRead,
    AgentListItem,
    AgentRead,
    AgentUpdate,
    SaleRead,
)

router = APIRouter(prefix="/agents", tags=["agents"], dependencies=[Depends(get_current_admin)])
settings = get_settings()


def ensure_referrer_exists(db: Session, referred_by_id: int | None) -> None:
    if referred_by_id is None:
        return
    if db.get(Agent, referred_by_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบผู้แนะนำ")


def ensure_agent_referral_is_valid(db: Session, agent_id: int, referred_by_id: int | None) -> None:
    if referred_by_id is None:
        return
    if referred_by_id == agent_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ตัวแทนไม่สามารถแนะนำตัวเองได้")

    current = db.get(Agent, referred_by_id)
    while current is not None:
        if current.referred_by_id == agent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="โครงสร้างการแนะนำแบบวนซ้ำไม่ถูกต้อง",
            )
        current = db.get(Agent, current.referred_by_id) if current.referred_by_id else None


def validate_agent_inventory(agent_type: str, stock_unit_price: int) -> None:
    expected_price = get_agent_unit_price(agent_type)
    if stock_unit_price != expected_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ราคาสต๊อกสำหรับประเภทตัวแทนนี้ต้องเป็น {expected_price} บาท",
        )


def build_inventory_rows(
    db: Session, agent: Agent, inventory_items: list
) -> list[AgentInventory]:
    products = list(db.scalars(select(Product).order_by(Product.id.asc())).all())
    products_by_id = {product.id: product for product in products}
    requested_by_product = {item.product_id: item for item in inventory_items}

    unknown_product_ids = sorted(set(requested_by_product) - set(products_by_id))
    if unknown_product_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ไม่พบสินค้า product_id={unknown_product_ids[0]}",
        )

    rows: list[AgentInventory] = []
    for product in products:
        payload_item = requested_by_product.get(product.id)
        quantity = payload_item.quantity if payload_item else 0
        expected_unit_price = (
            product.default_price_sub_center
            if agent.agent_type == AGENT_TYPE_SUB_CENTER
            else product.default_price_general
        )
        unit_price = payload_item.unit_price if payload_item else expected_unit_price
        if unit_price != expected_unit_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ราคาตั้งต้นของ {product.name} ต้องตรงกับราคาของประเภทตัวแทน",
            )
        rows.append(
            AgentInventory(
                agent=agent,
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
            )
        )
    return rows


def serialize_inventory_items(items: list[AgentInventory]) -> list[AgentInventoryRead]:
    return [
        AgentInventoryRead(
            product_id=item.product_id,
            product_name=item.product.name,
            product_unit=item.product.unit,
            quantity=item.quantity,
            unit_price=item.unit_price,
            is_commissionable=item.product.is_commissionable,
        )
        for item in sorted(items, key=lambda entry: (entry.product.name.lower(), entry.product_id))
    ]


def sync_agent_stock_quantity(agent: Agent) -> None:
    agent.stock_quantity = sum(item.quantity for item in agent.inventory_items)


def get_inventory_price_for_agent_type(product: Product, agent_type: str) -> int:
    if agent_type == AGENT_TYPE_SUB_CENTER:
        return product.default_price_sub_center
    return product.default_price_general


@router.get("", response_model=list[AgentListItem])
def list_agents(db: Session = Depends(get_db)) -> list[AgentListItem]:
    referrer = aliased(Agent)
    team_size_subquery = (
        select(
            Agent.referred_by_id.label("agent_id"),
            func.count(Agent.id).label("team_size"),
        )
        .where(Agent.referred_by_id.is_not(None))
        .group_by(Agent.referred_by_id)
        .subquery()
    )
    stock_quantity_subquery = (
        select(
            AgentInventory.agent_id.label("agent_id"),
            func.coalesce(func.sum(AgentInventory.quantity), 0).label("stock_quantity"),
        )
        .group_by(AgentInventory.agent_id)
        .subquery()
    )
    statement = (
        select(
            Agent,
            referrer.name.label("referrer_name"),
            func.coalesce(team_size_subquery.c.team_size, 0).label("team_size"),
            func.coalesce(stock_quantity_subquery.c.stock_quantity, 0).label("stock_quantity"),
        )
        .outerjoin(referrer, Agent.referred_by_id == referrer.id)
        .outerjoin(team_size_subquery, team_size_subquery.c.agent_id == Agent.id)
        .outerjoin(stock_quantity_subquery, stock_quantity_subquery.c.agent_id == Agent.id)
        .order_by(Agent.created_at.desc(), Agent.id.desc())
    )
    rows = db.execute(statement).all()

    return [
        AgentListItem(
            **(AgentRead.model_validate(agent).model_dump() | {"stock_quantity": stock_quantity}),
            referrer_name=referrer_name,
            team_size=team_size,
        )
        for agent, referrer_name, team_size, stock_quantity in rows
    ]


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
def create_agent(payload: AgentCreate, db: Session = Depends(get_db)) -> Agent:
    existing_count = db.scalar(select(func.count()).select_from(Agent)) or 0
    if existing_count >= settings.max_agents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"จำนวนตัวแทนถึงขีดจำกัดสูงสุด {settings.max_agents} คนแล้ว",
        )

    ensure_referrer_exists(db, payload.referred_by_id)
    validate_agent_inventory(payload.agent_type, payload.stock_unit_price)

    duplicate_phone = db.scalar(select(Agent).where(Agent.phone == payload.phone))
    if duplicate_phone is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="เบอร์โทรนี้ถูกใช้งานแล้ว")

    agent = Agent(
        name=payload.name,
        phone=payload.phone,
        agent_type=payload.agent_type,
        stock_unit_price=payload.stock_unit_price,
        referred_by_id=payload.referred_by_id,
        is_active=payload.is_active,
    )
    build_inventory_rows(db, agent, payload.inventory_items)
    sync_agent_stock_quantity(agent)
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentDetail)
def get_agent(agent_id: int, db: Session = Depends(get_db)) -> AgentDetail:
    agent = db.scalar(
        select(Agent)
        .options(joinedload(Agent.referrer), joinedload(Agent.inventory_items).joinedload(AgentInventory.product))
        .where(Agent.id == agent_id)
    )
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบตัวแทน")

    direct_referrals = db.scalars(
        select(Agent).where(Agent.referred_by_id == agent_id).order_by(Agent.created_at.desc())
    ).all()

    sales = db.scalars(
        select(Sale)
        .options(joinedload(Sale.agent), joinedload(Sale.product))
        .where(Sale.agent_id == agent_id)
        .order_by(Sale.sale_date.desc(), Sale.id.desc())
    ).all()

    sales_history = [
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

    return AgentDetail(
        **AgentRead.model_validate(agent).model_dump(),
        referrer_name=agent.referrer.name if agent.referrer else None,
        direct_referrals=[AgentRead.model_validate(item) for item in direct_referrals],
        inventory_items=serialize_inventory_items(agent.inventory_items),
        sales_history=sales_history,
    )


@router.put("/{agent_id}", response_model=AgentRead)
def update_agent(agent_id: int, payload: AgentUpdate, db: Session = Depends(get_db)) -> Agent:
    agent = db.scalar(
        select(Agent)
        .options(joinedload(Agent.inventory_items).joinedload(AgentInventory.product))
        .where(Agent.id == agent_id)
    )
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบตัวแทน")

    update_data = payload.model_dump(exclude_unset=True)

    if "phone" in update_data and update_data["phone"] != agent.phone:
        duplicate_phone = db.scalar(select(Agent).where(Agent.phone == update_data["phone"]))
        if duplicate_phone is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="เบอร์โทรนี้ถูกใช้งานแล้ว")

    if "referred_by_id" in update_data:
        ensure_referrer_exists(db, update_data["referred_by_id"])
        ensure_agent_referral_is_valid(db, agent_id, update_data["referred_by_id"])

    next_agent_type = update_data.get("agent_type", agent.agent_type)
    next_stock_unit_price = update_data.get("stock_unit_price")
    if next_stock_unit_price is None and "agent_type" in update_data:
        next_stock_unit_price = get_agent_unit_price(next_agent_type)
        update_data["stock_unit_price"] = next_stock_unit_price
    else:
        next_stock_unit_price = next_stock_unit_price or agent.stock_unit_price

    validate_agent_inventory(next_agent_type, next_stock_unit_price)

    for key, value in update_data.items():
        setattr(agent, key, value)

    if "stock_unit_price" in update_data or "agent_type" in update_data:
        for item in agent.inventory_items:
            item.unit_price = get_inventory_price_for_agent_type(item.product, agent.agent_type)

    db.commit()
    db.refresh(agent)
    return agent


@router.put("/{agent_id}/inventory", response_model=list[AgentInventoryRead])
def update_agent_inventory(
    agent_id: int,
    payload: AgentInventoryBulkUpdate,
    db: Session = Depends(get_db),
) -> list[AgentInventoryRead]:
    agent = db.scalar(
        select(Agent)
        .options(joinedload(Agent.inventory_items).joinedload(AgentInventory.product))
        .where(Agent.id == agent_id)
    )
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบตัวแทน")

    inventory_by_product = {item.product_id: item for item in agent.inventory_items}
    known_product_ids = set(inventory_by_product)

    for item in payload.items:
        if item.product_id not in known_product_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ไม่พบสินค้าสำหรับตัวแทน product_id={item.product_id}",
            )
        inventory_by_product[item.product_id].quantity = item.quantity

    sync_agent_stock_quantity(agent)
    db.commit()
    db.refresh(agent)
    return serialize_inventory_items(agent.inventory_items)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(agent_id: int, db: Session = Depends(get_db)) -> None:
    agent = db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบตัวแทน")

    has_direct_referrals = db.scalar(
        select(func.count()).select_from(Agent).where(Agent.referred_by_id == agent_id)
    )
    if has_direct_referrals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ไม่สามารถลบตัวแทนที่ยังมีลูกทีมตรงได้",
        )

    has_sales = db.scalar(
        select(func.count()).select_from(Sale).where(Sale.agent_id == agent_id)
    )
    if has_sales:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ไม่สามารถลบตัวแทนที่มีประวัติยอดขายได้",
        )

    db.delete(agent)
    db.commit()
