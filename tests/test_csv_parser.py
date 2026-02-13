"""Tests for CSV parser."""

import tempfile
from pathlib import Path
import pytest

from src.csv_parser import parse_csv, CSVValidationError
from src.models import InvoiceRow


class TestParseCSV:
    """Tests for parse_csv function."""

    def test_valid_csv(self):
        """Test parsing valid CSV file."""
        csv_content = """transaction_id,customer_name,date,item,amount
TXN-001,Acme Corp,2026-01-15,Consulting Services,1500.00
TXN-002,Globex Inc,2026-01-20,Software License,3200.00"""
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            invoices = parse_csv(temp_path)
            assert len(invoices) == 2
            assert invoices[0].transaction_id == "TXN-001"
            assert invoices[0].customer_name == "Acme Corp"
            assert invoices[0].amount == 1500.00
            assert invoices[1].transaction_id == "TXN-002"
        finally:
            Path(temp_path).unlink()

    def test_missing_file_raises_error(self):
        """Test missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_csv("nonexistent_file.csv")

    def test_missing_columns_raises_error(self):
        """Test missing required columns raises ValueError."""
        csv_content = """transaction_id,customer_name,date
TXN-001,Acme Corp,2026-01-15"""
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError) as exc_info:
                parse_csv(temp_path)
            assert "Missing required columns" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    def test_invalid_data_raises_csv_validation_error(self):
        """Test invalid data raises CSVValidationError with details."""
        csv_content = """transaction_id,customer_name,date,item,amount
TXN-001,Acme Corp,2026-01-15,Consulting Services,1500.00
TXN-002,Globex Inc,invalid-date,Software License,3200.00
TXN-003,Initech Ltd,2026-02-01,Training,-100.00"""
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            with pytest.raises(CSVValidationError) as exc_info:
                parse_csv(temp_path)
            
            error_message = str(exc_info.value)
            assert "Row 3" in error_message
            assert "Row 4" in error_message
            assert "date" in error_message.lower()
            assert "amount" in error_message.lower()
        finally:
            Path(temp_path).unlink()

    def test_empty_csv_returns_empty_list(self):
        """Test empty CSV (only headers) returns empty list."""
        csv_content = """transaction_id,customer_name,date,item,amount"""
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            invoices = parse_csv(temp_path)
            assert invoices == []
        finally:
            Path(temp_path).unlink()

    def test_csv_with_whitespace(self):
        """Test CSV with whitespace in fields is handled correctly."""
        csv_content = """transaction_id,customer_name,date,item,amount
TXN-001,  Acme Corp  ,2026-01-15,  Consulting Services  ,1500.00"""
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            invoices = parse_csv(temp_path)
            assert len(invoices) == 1
            # Note: CSV reader preserves whitespace, Pydantic validation will catch empty after strip
            # This test verifies the parser doesn't crash on whitespace
            assert invoices[0].transaction_id == "TXN-001"
        finally:
            Path(temp_path).unlink()

    def test_multiple_validation_errors_collected(self):
        """Test that multiple validation errors are collected and reported."""
        csv_content = """transaction_id,customer_name,date,item,amount
TXN-001,Acme Corp,2026-01-15,Consulting Services,1500.00
,Globex Inc,invalid-date,Software License,-100.00
TXN-003,,2026-02-01,,0"""
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            with pytest.raises(CSVValidationError) as exc_info:
                parse_csv(temp_path)
            
            error_message = str(exc_info.value)
            # Should report errors for rows 3 and 4
            assert "Row 3" in error_message
            assert "Row 4" in error_message
        finally:
            Path(temp_path).unlink()
