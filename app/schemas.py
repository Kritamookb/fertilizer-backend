from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminLoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str

    @model_validator(mode="after")
    def validate_identifier(self) -> "AdminLoginRequest":
        if not self.username and not self.email:
            raise ValueError("กรุณากรอกชื่อผู้ใช้หรืออีเมล")
        return self

    @property
    def identifier(self) -> str:
        return self.email or self.username or ""


class AdminUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: Optional[str] = None


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    unit: str = Field(min_length=1, max_length=50)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=50)


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class AgentBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=50)
    referred_by_id: Optional[int] = None
    is_active: bool = True


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    phone: Optional[str] = Field(default=None, min_length=1, max_length=50)
    referred_by_id: Optional[int] = None
    is_active: Optional[bool] = None


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    referred_by_id: Optional[int]
    created_at: datetime
    is_active: bool


class AgentListItem(AgentRead):
    referrer_name: Optional[str] = None
    team_size: int = 0


class SaleBase(BaseModel):
    agent_id: int
    product_id: int
    quantity: int = Field(gt=0)
    sale_date: date


class SaleCreate(SaleBase):
    pass


class SaleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: int
    product_id: int
    quantity: int
    sale_date: date
    created_at: datetime
    agent_name: Optional[str] = None
    product_name: Optional[str] = None
    product_unit: Optional[str] = None


class AgentDetail(AgentRead):
    referrer_name: Optional[str] = None
    direct_referrals: list[AgentRead]
    sales_history: list[SaleRead]


class WeeklyCommissionItem(BaseModel):
    agent_id: int
    agent_name: str
    direct_team_sales_qty: int
    commission_amount: int


class WeeklyReportResponse(BaseModel):
    week: str
    week_start: date
    week_end: date
    rate_per_unit: int
    items: list[WeeklyCommissionItem]


class SummaryByAgentItem(BaseModel):
    agent_id: int
    agent_name: str
    total_quantity: int


class SummaryByProductItem(BaseModel):
    product_id: int
    product_name: str
    unit: str
    total_quantity: int


class SummaryReportResponse(BaseModel):
    total_sales_quantity: int
    by_agent: list[SummaryByAgentItem]
    by_product: list[SummaryByProductItem]
