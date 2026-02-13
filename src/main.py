"""CLI entry point for invoice generator."""

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from pydantic import ValidationError

from .models import SellerInfo
from .csv_parser import parse_csv, CSVValidationError
from .renderer import render_invoice
from .pdf_generator import html_to_pdf


@dataclass
class GenerationResult:
    """Result of an invoice generation run."""

    successful: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.successful) + len(self.failed)

    @property
    def all_succeeded(self) -> bool:
        return len(self.failed) == 0


def generate_invoices(
    csv_path: str,
    seller_name: str,
    seller_address: str,
    seller_ico: str,
    output_dir: str = "./output",
    template_path: Optional[str] = None,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
) -> GenerationResult:
    """
    Generate PDF invoices from a CSV file.

    Args:
        csv_path: Path to the input CSV file.
        seller_name: Seller's full name.
        seller_address: Seller's address.
        seller_ico: Seller's ICO (identification number).
        output_dir: Directory for generated PDFs.
        template_path: Optional path to a custom HTML template.
        on_progress: Optional callback(current, total, filename) for progress updates.

    Returns:
        GenerationResult with lists of successful and failed filenames.

    Raises:
        FileNotFoundError: If CSV or template file is missing.
        ValidationError: If seller info is invalid.
        CSVValidationError: If CSV data fails validation.
        ValueError: If CSV is empty or unreadable.
    """
    if template_path:
        if not Path(template_path).exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

    seller_info = SellerInfo(
        full_name=seller_name,
        address=seller_address,
        ico=seller_ico,
    )

    invoice_rows = parse_csv(csv_path)

    if not invoice_rows:
        raise ValueError("No invoices found in CSV file")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    result = GenerationResult()
    total = len(invoice_rows)

    for idx, invoice in enumerate(invoice_rows, start=1):
        safe_filename = "".join(
            c for c in invoice.transaction_id
            if c.isalnum() or c in ("-", "_", ".")
        )
        pdf_name = f"{safe_filename}.pdf"

        try:
            html_content = render_invoice(
                seller_info,
                invoice,
                template_path=template_path,
            )
            pdf_file = output / pdf_name
            html_to_pdf(html_content, pdf_file)
            result.successful.append(pdf_name)
        except Exception as e:
            result.failed.append((pdf_name, str(e)))

        if on_progress:
            on_progress(idx, total, pdf_name)

    return result


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate PDF invoices from CSV file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--csv", required=True,
        help="Path to the input CSV file",
    )
    parser.add_argument(
        "--name", required=True,
        help="Seller's full name",
    )
    parser.add_argument(
        "--address", required=True,
        help="Seller's address",
    )
    parser.add_argument(
        "--ico", required=True,
        help="Seller's IČO (identification number)",
    )
    parser.add_argument(
        "--output", default="./output",
        help="Output directory for generated PDFs (default: ./output)",
    )
    parser.add_argument(
        "--template", default=None,
        help="Path to custom HTML template (default: built-in template)",
    )

    args = parser.parse_args()

    def cli_progress(current: int, total: int, filename: str) -> None:
        print(f"Generated {filename} ({current}/{total})")

    try:
        result = generate_invoices(
            csv_path=args.csv,
            seller_name=args.name,
            seller_address=args.address,
            seller_ico=args.ico,
            output_dir=args.output,
            template_path=args.template,
            on_progress=cli_progress,
        )

        print()
        if result.all_succeeded:
            print(f"Generated {len(result.successful)} PDF invoices in {args.output}")
            return 0
        else:
            print(f"Generated {len(result.successful)} PDF invoices successfully")
            print(f"{len(result.failed)} invoice(s) failed:", file=sys.stderr)
            for filename, error in result.failed:
                print(f"  {filename}: {error}", file=sys.stderr)
            return 1

    except ValidationError as e:
        print("Error: Invalid seller information", file=sys.stderr)
        for error in e.errors():
            loc = ".".join(str(loc) for loc in error["loc"])
            print(f"  {loc}: {error['msg']}", file=sys.stderr)
        return 1

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except PermissionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except CSVValidationError as e:
        print("Error: CSV validation failed", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 1

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
