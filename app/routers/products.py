from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_admin
from app.database import get_db
from app.models import Product, ProductRetailPriceTier, Sale
from app.schemas import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"], dependencies=[Depends(get_current_admin)])

def replace_retail_price_tiers(
    db: Session,
    product: Product,
    tiers: list[dict[str, int]] | list,
) -> None:
    product.retail_price_tiers.clear()
    db.flush()
    product.retail_price_tiers.extend(
        ProductRetailPriceTier(min_quantity=tier["min_quantity"], unit_price=tier["unit_price"])
        if isinstance(tier, dict)
        else ProductRetailPriceTier(min_quantity=tier.min_quantity, unit_price=tier.unit_price)
        for tier in sorted(tiers, key=lambda item: item["min_quantity"] if isinstance(item, dict) else item.min_quantity)
    )


def serialize_product(product: Product) -> ProductRead:
    return ProductRead(
        **ProductRead.model_validate(product).model_dump(
            exclude={"retail_price_tiers", "agent_stock_quantity", "total_stock_quantity"}
        ),
        retail_price_tiers=product.retail_price_tiers,
        agent_stock_quantity=0,
        total_stock_quantity=product.company_stock_quantity,
    )


@router.get("", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db)) -> list[Product]:
    products = list(
        db.scalars(
            select(Product)
            .options(selectinload(Product.retail_price_tiers))
            .order_by(Product.id.asc())
        ).all()
    )
    return [serialize_product(product) for product in products]


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> ProductRead:
    existing = db.scalar(select(Product).where(Product.name == payload.name))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="มีสินค้านี้อยู่แล้ว")

    product_data = payload.model_dump(exclude={"retail_price_tiers"})
    product = Product(**product_data)
    db.add(product)
    replace_retail_price_tiers(db, product, payload.retail_price_tiers)
    db.commit()
    db.refresh(product)
    refreshed_product = db.scalar(
        select(Product)
        .options(selectinload(Product.retail_price_tiers))
        .where(Product.id == product.id)
    )
    return serialize_product(refreshed_product or product)


@router.put("/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)) -> ProductRead:
    product = db.scalar(
        select(Product)
        .options(selectinload(Product.retail_price_tiers))
        .where(Product.id == product_id)
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบสินค้า")

    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != product.name:
        existing = db.scalar(select(Product).where(Product.name == update_data["name"]))
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="มีสินค้านี้อยู่แล้ว")

    for key, value in update_data.items():
        if key == "retail_price_tiers":
            replace_retail_price_tiers(db, product, value)
            continue
        setattr(product, key, value)

    db.commit()
    refreshed_product = db.scalar(
        select(Product)
        .options(selectinload(Product.retail_price_tiers))
        .where(Product.id == product.id)
    )
    return serialize_product(refreshed_product or product)


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
