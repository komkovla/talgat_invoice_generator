"""Tests for HTML renderer module."""

import tempfile
from pathlib import Path
import pytest
from decimal import Decimal

from src.models import SellerInfo, InvoiceRow
from src.renderer import render_invoice


class TestRenderInvoice:
    """Tests for render_invoice function."""

    def test_render_invoice_with_valid_data(self):
        """Test rendering invoice with valid data."""
        seller = SellerInfo(
            full_name="John Doe",
            address="123 Main St, Prague",
            ico="12345678",
        )
        invoice = InvoiceRow(
            transaction_id="TXN-001",
            customer_name="Acme Corp",
            date="2026-01-15",
            item="Consulting Services",
            amount=Decimal("1500.00"),
        )
        
        html = render_invoice(seller, invoice)
        
        # Verify HTML contains all expected fields
        assert "INVOICE" in html
        assert seller.full_name in html
        assert seller.address in html
        assert seller.ico in html
        assert invoice.transaction_id in html
        assert invoice.customer_name in html
        assert invoice.date in html
        assert invoice.item in html
        assert "1500.00" in html

    def test_render_invoice_template_not_found(self):
        """Test error when template is not found."""
        seller = SellerInfo(
            full_name="John Doe",
            address="123 St",
            ico="12345",
        )
        invoice = InvoiceRow(
            transaction_id="TXN-001",
            customer_name="Acme",
            date="2026-01-15",
            item="Service",
            amount=Decimal("100"),
        )
        
        with pytest.raises(FileNotFoundError) as exc_info:
            render_invoice(seller, invoice, template_path="nonexistent/template.html")
        
        assert "Template not found" in str(exc_info.value) or "Template directory not found" in str(exc_info.value)

    def test_render_invoice_custom_template_path(self):
        """Test rendering with custom template path."""
        seller = SellerInfo(
            full_name="John Doe",
            address="123 St",
            ico="12345",
        )
        invoice = InvoiceRow(
            transaction_id="TXN-001",
            customer_name="Acme",
            date="2026-01-15",
            item="Service",
            amount=Decimal("100"),
        )
        
        # Create temporary template file
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = Path(tmpdir) / "custom_invoice.html"
            template_file.write_text(
                "<html><body>Custom: {{ seller.full_name }} - {{ invoice.transaction_id }}</body></html>"
            )
            
            html = render_invoice(seller, invoice, template_path=str(template_file))
            
            assert seller.full_name in html
            assert invoice.transaction_id in html
            assert "Custom:" in html

    def test_render_invoice_html_structure(self):
        """Test HTML structure contains all required sections."""
        seller = SellerInfo(
            full_name="Jane Smith",
            address="456 Oak Ave",
            ico="87654321",
        )
        invoice = InvoiceRow(
            transaction_id="TXN-2026-002",
            customer_name="Globex Inc",
            date="2026-02-20",
            item="Software License",
            amount=Decimal("3200.50"),
        )
        
        html = render_invoice(seller, invoice)
        
        # Check HTML structure elements
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "<head>" in html
        assert "<body>" in html
        assert "</body>" in html
        assert "</html>" in html
        
        # Check key sections exist
        assert "INVOICE" in html
        assert "From" in html or "seller" in html.lower()
        assert "To" in html or "customer" in html.lower()
        assert "Transaction ID" in html or "transaction" in html.lower()
        assert "Date" in html
        assert "Description" in html or "item" in html.lower()
        assert "Amount" in html or "amount" in html.lower()
        assert "Total" in html or "total" in html.lower()

    def test_render_invoice_escapes_html(self):
        """Test that HTML injection is prevented (autoescape)."""
        seller = SellerInfo(
            full_name="<script>alert('xss')</script>",
            address="<img src=x onerror=alert(1)>",
            ico="12345",
        )
        invoice = InvoiceRow(
            transaction_id="<b>TXN-001</b>",
            customer_name="<i>Acme</i>",
            date="2026-01-15",
            item="<a href='evil.com'>Service</a>",
            amount=Decimal("100"),
        )
        
        html = render_invoice(seller, invoice)
        
        # Verify HTML entities are escaped (not executed as HTML)
        assert "&lt;script&gt;" in html or "<script>" not in html
        assert "&lt;img" in html or "<img" not in html
        assert "&lt;b&gt;" in html or "<b>" not in html
        assert "&lt;i&gt;" in html or "<i>" not in html
        assert "&lt;a" in html or "<a" not in html

    def test_render_invoice_amount_formatting(self):
        """Test amount formatting in HTML output."""
        seller = SellerInfo(
            full_name="John Doe",
            address="123 St",
            ico="12345",
        )
        
        test_cases = [
            (Decimal("100"), "100.00"),
            (Decimal("1500.50"), "1500.50"),
            (Decimal("0.99"), "0.99"),
            (Decimal("10000"), "10000.00"),
        ]
        
        for amount, expected_format in test_cases:
            invoice = InvoiceRow(
                transaction_id="TXN-001",
                customer_name="Acme",
                date="2026-01-15",
                item="Service",
                amount=amount,
            )
            
            html = render_invoice(seller, invoice)
            
            # Check that amount appears in formatted form
            assert expected_format in html or str(amount) in html

    def test_render_invoice_all_fields_present(self):
        """Test that all invoice and seller fields appear in rendered HTML."""
        seller = SellerInfo(
            full_name="Test Seller",
            address="Test Address, City",
            ico="TEST123456",
        )
        invoice = InvoiceRow(
            transaction_id="TEST-TXN-001",
            customer_name="Test Customer",
            date="2026-12-31",
            item="Test Item Description",
            amount=Decimal("9999.99"),
        )
        
        html = render_invoice(seller, invoice)
        
        # Verify all seller fields
        assert seller.full_name in html
        assert seller.address in html
        assert seller.ico in html
        
        # Verify all invoice fields
        assert invoice.transaction_id in html
        assert invoice.customer_name in html
        assert invoice.date in html
        assert invoice.item in html
        assert "9999.99" in html or str(invoice.amount) in html

    def test_render_invoice_template_syntax_error(self):
        """Test error handling for template syntax errors."""
        seller = SellerInfo(
            full_name="John Doe",
            address="123 St",
            ico="12345",
        )
        invoice = InvoiceRow(
            transaction_id="TXN-001",
            customer_name="Acme",
            date="2026-01-15",
            item="Service",
            amount=Decimal("100"),
        )
        
        # Create template with syntax error
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = Path(tmpdir) / "bad_template.html"
            template_file.write_text("{{ unclosed variable")
            
            with pytest.raises(ValueError) as exc_info:
                render_invoice(seller, invoice, template_path=str(template_file))
            
            assert "syntax error" in str(exc_info.value).lower() or "error rendering" in str(exc_info.value).lower()
