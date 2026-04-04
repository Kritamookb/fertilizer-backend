from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.agent_types import AgentType, get_agent_unit_price

SaleType = str
PaymentMethod = str


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
    company_stock_quantity: int = Field(ge=0)
    cost_price_hq: int = Field(gt=0)
    default_price_retail: int = Field(gt=0)
    default_price_general: int = Field(gt=0)
    default_price_sub_center: int = Field(gt=0)
    is_commissionable: bool = True
    retail_price_tiers: list["ProductRetailPriceTierCreate"] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_bulk_retail_pricing(self) -> "ProductBase":
        min_quantities = [tier.min_quantity for tier in self.retail_price_tiers]
        if len(min_quantities) != len(set(min_quantities)):
            raise ValueError("จำนวนขั้นต่ำของราคาปลีกพิเศษต้องไม่ซ้ำกัน")
        return self


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=50)
    company_stock_quantity: Optional[int] = Field(default=None, ge=0)
    cost_price_hq: Optional[int] = Field(default=None, gt=0)
    default_price_retail: Optional[int] = Field(default=None, gt=0)
    default_price_general: Optional[int] = Field(default=None, gt=0)
    default_price_sub_center: Optional[int] = Field(default=None, gt=0)
    is_commissionable: Optional[bool] = None
    retail_price_tiers: Optional[list["ProductRetailPriceTierCreate"]] = None

    @model_validator(mode="after")
    def validate_bulk_retail_pricing(self) -> "ProductUpdate":
        if self.retail_price_tiers is None:
            return self
        min_quantities = [tier.min_quantity for tier in self.retail_price_tiers]
        if len(min_quantities) != len(set(min_quantities)):
            raise ValueError("จำนวนขั้นต่ำของราคาปลีกพิเศษต้องไม่ซ้ำกัน")
        return self


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_stock_quantity: int = 0
    total_stock_quantity: int = 0
    retail_price_tiers: list["ProductRetailPriceTierRead"] = Field(default_factory=list)


class ProductRetailPriceTierBase(BaseModel):
    min_quantity: int = Field(gt=0)
    unit_price: int = Field(gt=0)


class ProductRetailPriceTierCreate(ProductRetailPriceTierBase):
    pass


class ProductRetailPriceTierRead(ProductRetailPriceTierBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class AgentInventoryBase(BaseModel):
    product_id: int
    quantity: int = Field(ge=0)
    unit_price: int = Field(gt=0)


class AgentInventoryCreate(AgentInventoryBase):
    pass


class AgentInventoryUpdate(BaseModel):
    product_id: int
    quantity: int = Field(ge=0)


class AgentInventoryRead(BaseModel):
    product_id: int
    product_name: str
    product_unit: str
    quantity: int
    unit_price: int
    is_commissionable: bool
    company_stock_quantity: int


class StockTransferRead(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_unit: str
    quantity: int
    direction: str
    reason: str
    created_at: datetime


class AgentBase(BaseModel):
    agent_code: Optional[str] = Field(default=None, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    nickname: Optional[str] = Field(default=None, max_length=255)
    phone: str = Field(min_length=1, max_length=50)
    address: Optional[str] = Field(default=None, max_length=1000)
    line_id: Optional[str] = Field(default=None, max_length=100)
    bank_name: Optional[str] = Field(default=None, max_length=255)
    bank_account_name: Optional[str] = Field(default=None, max_length=255)
    bank_account_number: Optional[str] = Field(default=None, max_length=100)
    agent_type: AgentType
    stock_quantity: int = Field(default=0, ge=0)
    stock_unit_price: int = Field(gt=0)
    referred_by_id: Optional[int] = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_inventory_pricing(self) -> "AgentBase":
        expected_price = get_agent_unit_price(self.agent_type)
        if self.stock_unit_price != expected_price:
            raise ValueError(f"ราคาสต๊อกสำหรับประเภทตัวแทนนี้ต้องเป็น {expected_price} บาท")
        return self


class AgentCreate(AgentBase):
    inventory_items: list[AgentInventoryCreate] = Field(default_factory=list)


class AgentUpdate(BaseModel):
    agent_code: Optional[str] = Field(default=None, max_length=100)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    nickname: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, min_length=1, max_length=50)
    address: Optional[str] = Field(default=None, max_length=1000)
    line_id: Optional[str] = Field(default=None, max_length=100)
    bank_name: Optional[str] = Field(default=None, max_length=255)
    bank_account_name: Optional[str] = Field(default=None, max_length=255)
    bank_account_number: Optional[str] = Field(default=None, max_length=100)
    agent_type: Optional[AgentType] = None
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    stock_unit_price: Optional[int] = Field(default=None, gt=0)
    referred_by_id: Optional[int] = None
    is_active: Optional[bool] = None


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_code: Optional[str] = None
    name: str
    nickname: Optional[str] = None
    phone: str
    address: Optional[str] = None
    line_id: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    agent_type: AgentType
    stock_quantity: int
    stock_unit_price: int
    referred_by_id: Optional[int]
    created_at: datetime
    is_active: bool


class AgentListItem(AgentRead):
    referrer_name: Optional[str] = None
    team_size: int = 0


class SaleBase(BaseModel):
    agent_id: int
    product_id: int
    sale_type: SaleType
    payment_method: PaymentMethod
    quantity: int = Field(gt=0)
    sale_date: date
    customer_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    customer_phone: Optional[str] = Field(default=None, min_length=1, max_length=50)

    @model_validator(mode="after")
    def validate_customer_fields(self) -> "SaleBase":
        if self.sale_type not in {"agent_pickup", "customer_purchase"}:
            raise ValueError("ประเภทการเบิกไม่ถูกต้อง")
        if self.payment_method not in {"transfer", "cash", "credit"}:
            raise ValueError("วิธีจ่ายเงินไม่ถูกต้อง")
        if self.sale_type == "customer_purchase" and not self.customer_name:
            raise ValueError("กรุณากรอกชื่อลูกค้าเมื่อเป็นรายการลูกค้ามาเบิก")
        if self.sale_type == "agent_pickup":
            self.customer_name = None
            self.customer_phone = None
        return self


class SaleCreate(SaleBase):
    unit_price: Optional[int] = Field(default=None, gt=0)


class SaleBulkItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    unit_price: Optional[int] = Field(default=None, gt=0)


class SaleBulkCreate(BaseModel):
    agent_id: int
    sale_type: SaleType
    payment_method: PaymentMethod
    sale_date: date
    customer_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    customer_phone: Optional[str] = Field(default=None, min_length=1, max_length=50)
    items: list[SaleBulkItemCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_customer_fields(self) -> "SaleBulkCreate":
        if self.sale_type not in {"agent_pickup", "customer_purchase"}:
            raise ValueError("ประเภทการเบิกไม่ถูกต้อง")
        if self.payment_method not in {"transfer", "cash", "credit"}:
            raise ValueError("วิธีจ่ายเงินไม่ถูกต้อง")
        if self.sale_type == "customer_purchase" and not self.customer_name:
            raise ValueError("กรุณากรอกชื่อลูกค้าเมื่อเป็นรายการลูกค้ามาเบิก")
        if self.sale_type == "agent_pickup":
            self.customer_name = None
            self.customer_phone = None
        return self


class SaleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: int
    product_id: int
    customer_id: Optional[int] = None
    sale_type: SaleType
    payment_method: PaymentMethod
    quantity: int
    unit_price: int
    unit_cost: int
    total_amount: int
    total_cost: int
    gross_profit: int
    sale_date: date
    created_at: datetime
    agent_name: Optional[str] = None
    product_name: Optional[str] = None
    product_unit: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None


class AgentDetail(AgentRead):
    referrer_name: Optional[str] = None
    direct_referrals: list[AgentRead]
    inventory_items: list[AgentInventoryRead]
    stock_transfers: list[StockTransferRead] = Field(default_factory=list)
    sales_history: list[SaleRead]


class AgentInventoryBulkUpdate(BaseModel):
    items: list[AgentInventoryUpdate]


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
    total_amount: int
    total_cost: int
    gross_profit: int


class SummaryByProductItem(BaseModel):
    product_id: int
    product_name: str
    unit: str
    total_quantity: int
    total_amount: int
    total_cost: int
    gross_profit: int


class SummaryReportResponse(BaseModel):
    total_sales_quantity: int
    total_amount: int
    total_cost: int
    gross_profit: int
    by_agent: list[SummaryByAgentItem]
    by_product: list[SummaryByProductItem]
