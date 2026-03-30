from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.agent_types import AGENT_TYPE_GENERAL, get_agent_unit_price
from app.database import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, default=AGENT_TYPE_GENERAL)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_unit_price: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=get_agent_unit_price(AGENT_TYPE_GENERAL),
    )
    referred_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("agents.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=func.true()
    )

    referrer: Mapped[Optional["Agent"]] = relationship(
        "Agent", remote_side=[id], back_populates="direct_referrals"
    )
    direct_referrals: Mapped[list["Agent"]] = relationship(
        "Agent", back_populates="referrer", cascade="save-update"
    )
    inventory_items: Mapped[list["AgentInventory"]] = relationship(
        "AgentInventory", back_populates="agent", cascade="all, delete-orphan"
    )
    sales: Mapped[list["Sale"]] = relationship(
        "Sale", back_populates="agent", cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    cost_price_hq: Mapped[int] = mapped_column(Integer, nullable=False, default=550)
    default_price_retail: Mapped[int] = mapped_column(Integer, nullable=False, default=890)
    default_price_general: Mapped[int] = mapped_column(Integer, nullable=False, default=800)
    default_price_sub_center: Mapped[int] = mapped_column(Integer, nullable=False, default=770)
    is_commissionable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=func.true()
    )
    retail_price_tiers: Mapped[list["ProductRetailPriceTier"]] = relationship(
        "ProductRetailPriceTier",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductRetailPriceTier.min_quantity",
    )

    inventory_items: Mapped[list["AgentInventory"]] = relationship(
        "AgentInventory", back_populates="product", cascade="all, delete-orphan"
    )
    sales: Mapped[list["Sale"]] = relationship(
        "Sale", back_populates="product", cascade="save-update"
    )


class AgentInventory(Base):
    __tablename__ = "agent_inventories"
    __table_args__ = (UniqueConstraint("agent_id", "product_id", name="uq_agent_product_inventory"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)

    agent: Mapped["Agent"] = relationship("Agent", back_populates="inventory_items")
    product: Mapped["Product"] = relationship("Product", back_populates="inventory_items")


class ProductRetailPriceTier(Base):
    __tablename__ = "product_retail_price_tiers"
    __table_args__ = (
        UniqueConstraint("product_id", "min_quantity", name="uq_product_retail_price_tier_quantity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    min_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="retail_price_tiers")


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    total_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    gross_profit: Mapped[int] = mapped_column(Integer, nullable=False)
    sale_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    agent: Mapped["Agent"] = relationship("Agent", back_populates="sales")
    product: Mapped["Product"] = relationship("Product", back_populates="sales")
