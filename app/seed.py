from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_password_hash
from app.config import get_settings
from app.models import AdminUser, Agent, AgentInventory, Product

settings = get_settings()


def seed_initial_data(db: Session) -> None:
    existing_admin = db.scalar(select(AdminUser).where(AdminUser.username == settings.admin_username))
    if existing_admin is None:
        db.add(
            AdminUser(
                username=settings.admin_username,
                email=settings.admin_email,
                hashed_password=get_password_hash(settings.admin_password),
            )
        )

    product_names = {"ปุ๋ย A", "ปุ๋ย B", "ปุ๋ย C"}
    existing_products = set(db.scalars(select(Product.name)).all())
    missing_products = product_names - existing_products
    for product_name in sorted(missing_products):
        db.add(
            Product(
                name=product_name,
                unit="กระสอบ",
                default_price_general=800,
                default_price_sub_center=770,
                is_commissionable=True,
            )
        )

    db.flush()

    products = list(db.scalars(select(Product).order_by(Product.id.asc())).all())
    agents = list(db.scalars(select(Agent).order_by(Agent.id.asc())).all())
    existing_inventory_pairs = {
        (agent_id, product_id)
        for agent_id, product_id in db.execute(
            select(AgentInventory.agent_id, AgentInventory.product_id)
        ).all()
    }
    for agent in agents:
        legacy_stock_assigned = False
        for product in products:
            pair = (agent.id, product.id)
            if pair in existing_inventory_pairs:
                continue
            quantity = 0
            if not legacy_stock_assigned and agent.stock_quantity > 0:
                quantity = agent.stock_quantity
                legacy_stock_assigned = True
            db.add(
                AgentInventory(
                    agent_id=agent.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=(
                        product.default_price_sub_center
                        if agent.agent_type == "sub_center"
                        else product.default_price_general
                    ),
                )
            )

    db.commit()
