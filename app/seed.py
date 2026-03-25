from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_password_hash
from app.config import get_settings
from app.models import AdminUser, Product

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
        db.add(Product(name=product_name, unit="กระสอบ", is_commissionable=True))

    db.commit()
