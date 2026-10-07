"""Request and response models for the quote service."""

from typing import List

from pydantic import BaseModel, Field, field_validator

KNOWN_TIERS = ("standard", "partner", "enterprise")


class OrderLine(BaseModel):
    sku: str = Field(min_length=3)
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)


class OrderRequest(BaseModel):
    customer_tier: str = "standard"
    lines: List[OrderLine] = Field(min_length=1)

    @field_validator("customer_tier")
    @classmethod
    def tier_must_be_known(cls, value: str) -> str:
        if value not in KNOWN_TIERS:
            raise ValueError(f"unknown tier {value!r}")
        return value


class OrderQuote(BaseModel):
    subtotal: float
    discount: float
    total: float
    line_count: int
