"""Tests for PDF generator module."""

import tempfile
from pathlib import Path
import pytest

from src.pdf_generator import html_to_pdf


class TestHTMLToPDF:
    """Tests for html_to_pdf function."""

    def test_html_to_pdf_generates_file(self):
        """Test that PDF file is created."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body><h1>Test Invoice</h1></body>
        </html>
        """
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            html_to_pdf(html_content, pdf_path)
            
            assert pdf_path.exists()
            assert pdf_path.suffix == ".pdf"

    def test_html_to_pdf_file_exists(self):
        """Test that output file exists and has PDF extension."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <body><p>Test content</p></body>
        </html>
        """
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "invoice.pdf"
            html_to_pdf(html_content, pdf_path)
            
            assert pdf_path.exists()
            assert pdf_path.is_file()
            assert pdf_path.suffix == ".pdf"

    def test_html_to_pdf_valid_content(self):
        """Test that PDF is valid (non-empty and has PDF magic bytes)."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Invoice</title></head>
        <body>
            <h1>Invoice</h1>
            <p>Transaction ID: TXN-001</p>
            <p>Amount: 100.00</p>
        </body>
        </html>
        """
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            html_to_pdf(html_content, pdf_path)
            
            # Check file exists and is non-empty
            assert pdf_path.exists()
            assert pdf_path.stat().st_size > 0
            
            # Check PDF magic bytes (%PDF)
            with open(pdf_path, "rb") as f:
                first_bytes = f.read(4)
                assert first_bytes == b"%PDF"

    def test_html_to_pdf_creates_directory(self):
        """Test that parent directory is created if needed."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <body><p>Test</p></body>
        </html>
        """
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested directory path
            nested_dir = Path(tmpdir) / "nested" / "subdirectory"
            pdf_path = nested_dir / "invoice.pdf"
            
            # Directory doesn't exist yet
            assert not nested_dir.exists()
            
            # Generate PDF (should create directory)
            html_to_pdf(html_content, pdf_path)
            
            # Directory should now exist
            assert nested_dir.exists()
            assert pdf_path.exists()

    def test_html_to_pdf_path_handling(self):
        """Test that both str and Path types work for output_path."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <body><p>Test</p></body>
        </html>
        """
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test with Path object
            pdf_path_path = Path(tmpdir) / "test_path.pdf"
            html_to_pdf(html_content, pdf_path_path)
            assert pdf_path_path.exists()
            
            # Test with string
            pdf_path_str = str(Path(tmpdir) / "test_str.pdf")
            html_to_pdf(html_content, pdf_path_str)
            assert Path(pdf_path_str).exists()

    def test_html_to_pdf_invalid_html(self):
        """Test error handling for malformed HTML."""
        # WeasyPrint is quite forgiving, but let's test with very broken HTML
        # Actually, WeasyPrint handles most HTML gracefully, so this might not raise
        # But we can test that it still produces a PDF (even if empty/broken)
        html_content = "<invalid>not a proper html document"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            # WeasyPrint is forgiving, so this might succeed
            # If it fails, it should raise ValueError
            try:
                html_to_pdf(html_content, pdf_path)
                # If it succeeds, that's fine - WeasyPrint is forgiving
                assert pdf_path.exists()
            except ValueError:
                # If it fails with ValueError, that's also acceptable
                pass

    def test_html_to_pdf_with_invoice_content(self):
        """Test PDF generation with realistic invoice HTML."""
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Invoice TXN-001</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h1 { color: #333; }
                table { border-collapse: collapse; width: 100%; }
                td { padding: 10px; border: 1px solid #ddd; }
            </style>
        </head>
        <body>
            <h1>INVOICE</h1>
            <p><strong>Transaction ID:</strong> TXN-001</p>
            <p><strong>Customer:</strong> Acme Corp</p>
            <p><strong>Date:</strong> 2026-01-15</p>
            <table>
                <tr>
                    <td>Consulting Services</td>
                    <td>1500.00 CZK</td>
                </tr>
            </table>
            <p><strong>Total: 1500.00 CZK</strong></p>
        </body>
        </html>
        """
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "invoice.pdf"
            html_to_pdf(html_content, pdf_path)
            
            assert pdf_path.exists()
            assert pdf_path.stat().st_size > 1000  # Should be substantial size
            
            # Verify PDF magic bytes
            with open(pdf_path, "rb") as f:
                assert f.read(4) == b"%PDF"

    def test_html_to_pdf_file_size_reasonable(self):
        """Test that generated PDF has reasonable file size."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
            <h1>Test Invoice</h1>
            <p>This is a test invoice with some content.</p>
            <p>It should generate a PDF of reasonable size.</p>
        </body>
        </html>
        """
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            html_to_pdf(html_content, pdf_path)
            
            file_size = pdf_path.stat().st_size
            # PDF should be at least a few KB for basic content
            assert file_size > 1000  # At least 1KB
            # But not unreasonably large for simple content
            assert file_size < 10 * 1024 * 1024  # Less than 10MB
