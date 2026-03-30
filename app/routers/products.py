from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_admin
from app.database import get_db
from app.agent_types import AGENT_TYPE_SUB_CENTER
from app.models import Agent, AgentInventory, Product, Sale
from app.schemas import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"], dependencies=[Depends(get_current_admin)])


def get_product_price_for_agent_type(product: Product, agent_type: str) -> int:
    if agent_type == AGENT_TYPE_SUB_CENTER:
        return product.default_price_sub_center
    return product.default_price_general


@router.get("", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db)) -> list[Product]:
    return list(db.scalars(select(Product).order_by(Product.id.asc())).all())


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> Product:
    existing = db.scalar(select(Product).where(Product.name == payload.name))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="มีสินค้านี้อยู่แล้ว")

    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)

    agents = list(db.scalars(select(Agent).order_by(Agent.id.asc())).all())
    for agent in agents:
        db.add(
            AgentInventory(
                agent_id=agent.id,
                product_id=product.id,
                quantity=0,
                unit_price=get_product_price_for_agent_type(product, agent.agent_type),
            )
        )
    if agents:
        db.commit()
    return product


@router.put("/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบสินค้า")

    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != product.name:
        existing = db.scalar(select(Product).where(Product.name == update_data["name"]))
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="มีสินค้านี้อยู่แล้ว")

    for key, value in update_data.items():
        setattr(product, key, value)

    inventory_rows = db.scalars(
        select(AgentInventory)
        .join(Agent, Agent.id == AgentInventory.agent_id)
        .where(AgentInventory.product_id == product_id)
    ).all()
    for row in inventory_rows:
        row.unit_price = get_product_price_for_agent_type(product, row.agent.agent_type)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)) -> None:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบสินค้า")

    has_sales = db.scalar(
        select(func.count()).select_from(Sale).where(Sale.product_id == product_id)
    )
    if has_sales:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ไม่สามารถลบสินค้าที่มีประวัติยอดขายได้",
        )

    db.delete(product)
    db.commit()
