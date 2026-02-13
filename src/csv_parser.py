"""CSV parsing and validation module."""

import csv
from pathlib import Path
from typing import List
from pydantic import ValidationError

from .models import InvoiceRow


class CSVValidationError(Exception):
    """Raised when CSV data fails validation."""

    def __init__(self, errors: List[tuple[int, dict]]):
        """
        Initialize with list of (row_number, error_dict) tuples.
        
        Args:
            errors: List of tuples containing (row_number, validation_errors_dict)
        """
        self.errors = errors
        error_messages = []
        for row_num, error_dict in errors:
            field_errors = ", ".join(f"'{field}': {msg}" for field, msg in error_dict.items())
            error_messages.append(f"Row {row_num}: {field_errors}")
        super().__init__("\n".join(error_messages))


def parse_csv(file_path: str) -> List[InvoiceRow]:
    """
    Parse CSV file and validate each row.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of validated InvoiceRow objects
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        ValueError: If required columns are missing
        CSVValidationError: If any row fails validation
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    required_columns = {"transaction_id", "customer_name", "date", "item", "amount"}
    validation_errors = []
    invoice_rows = []
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            # Check if all required columns are present
            if not reader.fieldnames:
                raise ValueError("CSV file is empty or has no header row")
            
            missing_columns = required_columns - set(reader.fieldnames)
            if missing_columns:
                raise ValueError(
                    f"Missing required columns: {', '.join(sorted(missing_columns))}"
                )
            
            # Parse and validate each row
            for row_num, row_dict in enumerate(reader, start=2):  # Start at 2 (row 1 is header)
                try:
                    invoice_row = InvoiceRow(**row_dict)
                    invoice_rows.append(invoice_row)
                except ValidationError as e:
                    # Extract field-level errors
                    field_errors = {}
                    for error in e.errors():
                        field = ".".join(str(loc) for loc in error["loc"])
                        field_errors[field] = error["msg"]
                    validation_errors.append((row_num, field_errors))
        
        # If any validation errors occurred, raise exception
        if validation_errors:
            raise CSVValidationError(validation_errors)
        
        return invoice_rows
        
    except FileNotFoundError:
        raise
    except ValueError:
        raise
    except CSVValidationError:
        raise
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {str(e)}") from e
