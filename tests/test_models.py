"""Tests for Pydantic models."""

import pytest
from decimal import Decimal
from pydantic import ValidationError

from src.models import SellerInfo, InvoiceRow


class TestSellerInfo:
    """Tests for SellerInfo model."""

    def test_valid_seller_info(self):
        """Test valid seller info succeeds."""
        seller = SellerInfo(
            full_name="John Doe",
            address="123 Main St, Prague",
            ico="12345678",
        )
        assert seller.full_name == "John Doe"
        assert seller.address == "123 Main St, Prague"
        assert seller.ico == "12345678"

    def test_missing_fields_raises_error(self):
        """Test missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            SellerInfo(full_name="John Doe")

    def test_empty_strings_raise_error(self):
        """Test empty strings raise ValidationError."""
        with pytest.raises(ValidationError):
            SellerInfo(full_name="", address="123 St", ico="12345")

        with pytest.raises(ValidationError):
            SellerInfo(full_name="John", address="", ico="12345")

        with pytest.raises(ValidationError):
            SellerInfo(full_name="John", address="123 St", ico="")


class TestInvoiceRow:
    """Tests for InvoiceRow model."""

    def test_valid_invoice_row(self):
        """Test valid invoice row succeeds."""
        invoice = InvoiceRow(
            transaction_id="TXN-001",
            customer_name="Acme Corp",
            date="2026-01-15",
            item="Consulting Services",
            amount=Decimal("1500.00"),
        )
        assert invoice.transaction_id == "TXN-001"
        assert invoice.customer_name == "Acme Corp"
        assert invoice.date == "2026-01-15"
        assert invoice.item == "Consulting Services"
        assert invoice.amount == Decimal("1500.00")

    def test_missing_fields_raises_error(self):
        """Test missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            InvoiceRow(
                transaction_id="TXN-001",
                customer_name="Acme Corp",
                date="2026-01-15",
                item="Consulting",
            )

    def test_empty_strings_raise_error(self):
        """Test empty strings raise ValidationError."""
        with pytest.raises(ValidationError):
            InvoiceRow(
                transaction_id="",
                customer_name="Acme",
                date="2026-01-15",
                item="Consulting",
                amount=Decimal("100"),
            )

    def test_invalid_date_format_raises_error(self):
        """Test invalid date format raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            InvoiceRow(
                transaction_id="TXN-001",
                customer_name="Acme",
                date="01/15/2026",
                item="Consulting",
                amount=Decimal("100"),
            )
        assert "YYYY-MM-DD" in str(exc_info.value)

        with pytest.raises(ValidationError):
            InvoiceRow(
                transaction_id="TXN-001",
                customer_name="Acme",
                date="2026-13-45",
                item="Consulting",
                amount=Decimal("100"),
            )

    def test_negative_amount_raises_error(self):
        """Test negative amount raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            InvoiceRow(
                transaction_id="TXN-001",
                customer_name="Acme",
                date="2026-01-15",
                item="Consulting",
                amount=Decimal("-100"),
            )
        assert "greater than 0" in str(exc_info.value).lower()

    def test_zero_amount_raises_error(self):
        """Test zero amount raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            InvoiceRow(
                transaction_id="TXN-001",
                customer_name="Acme",
                date="2026-01-15",
                item="Consulting",
                amount=Decimal("0"),
            )
        assert "greater than 0" in str(exc_info.value).lower()

    def test_valid_date_formats(self):
        """Test various valid date formats."""
        valid_dates = [
            "2026-01-15",
            "2026-12-31",
            "2024-02-29",  # Leap year
        ]
        
        for date_str in valid_dates:
            invoice = InvoiceRow(
                transaction_id="TXN-001",
                customer_name="Acme",
                date=date_str,
                item="Consulting",
                amount=Decimal("100"),
            )
            assert invoice.date == date_str
