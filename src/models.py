"""Pydantic data models for invoice generation."""

from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class SellerInfo(BaseModel):
    """Seller information (same for all invoices, provided via CLI)."""

    full_name: str = Field(..., min_length=1, description="Seller's full name")
    address: str = Field(..., min_length=1, description="Seller's address")
    ico: str = Field(..., min_length=1, description="Seller's IČO (identification number)")


class InvoiceRow(BaseModel):
    """Single invoice row parsed from CSV."""

    transaction_id: str = Field(..., min_length=1, description="Unique transaction identifier")
    customer_name: str = Field(..., min_length=1, description="Customer name")
    date: str = Field(..., description="Invoice date in YYYY-MM-DD format")
    item: str = Field(..., min_length=1, description="Purchase item description")
    amount: Decimal = Field(..., gt=0, description="Invoice amount (must be positive)")

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date is in YYYY-MM-DD format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v
