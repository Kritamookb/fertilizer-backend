from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_password_hash
from app.config import get_settings
from app.models import AdminUser, Agent, AgentInventory, Product, Sale

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
        for product in products:
            pair = (agent.id, product.id)
            if pair in existing_inventory_pairs:
                continue
            db.add(
                AgentInventory(
                    agent_id=agent.id,
                    product_id=product.id,
                    quantity=0,
                    unit_price=(
                        product.default_price_sub_center
                        if agent.agent_type == "sub_center"
                        else product.default_price_general
                    ),
                )
            )

    db.flush()

    inventory_totals = {
        agent_id: total_quantity
        for agent_id, total_quantity in db.execute(
            select(
                Agent.id,
                func.coalesce(func.sum(AgentInventory.quantity), 0),
            )
            .outerjoin(AgentInventory, AgentInventory.agent_id == Agent.id)
            .group_by(Agent.id)
        ).all()
    }
    for agent in agents:
        agent.stock_quantity = inventory_totals.get(agent.id, 0)

    sales = list(
        db.scalars(
            select(Sale)
            .order_by(Sale.id.asc())
        ).all()
    )
    products_by_id = {product.id: product for product in products}
    agents_by_id = {agent.id: agent for agent in agents}
    for sale in sales:
        product = products_by_id.get(sale.product_id)
        agent = agents_by_id.get(sale.agent_id)
        if product is None or agent is None:
            continue

        if sale.total_amount <= 0 or sale.total_cost <= 0:
            sale.unit_price = (
                product.default_price_sub_center
                if agent.agent_type == "sub_center"
                else product.default_price_general
            )
            sale.unit_cost = product.cost_price_hq
            sale.total_amount = sale.quantity * sale.unit_price
            sale.total_cost = sale.quantity * sale.unit_cost
            sale.gross_profit = sale.total_amount - sale.total_cost

    db.commit()
