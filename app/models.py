from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
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
    sales: Mapped[list["Sale"]] = relationship(
        "Sale", back_populates="agent", cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)

    sales: Mapped[list["Sale"]] = relationship(
        "Sale", back_populates="product", cascade="save-update"
    )


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    sale_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    agent: Mapped["Agent"] = relationship("Agent", back_populates="sales")
    product: Mapped["Product"] = relationship("Product", back_populates="sales")
