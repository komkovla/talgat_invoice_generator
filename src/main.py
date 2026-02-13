"""CLI entry point for invoice generator."""

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from .models import SellerInfo
from .csv_parser import parse_csv, CSVValidationError
from .renderer import render_invoice
from .pdf_generator import html_to_pdf


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate PDF invoices from CSV file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Required arguments
    parser.add_argument(
        "--csv",
        required=True,
        help="Path to the input CSV file",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Seller's full name",
    )
    parser.add_argument(
        "--address",
        required=True,
        help="Seller's address",
    )
    parser.add_argument(
        "--ico",
        required=True,
        help="Seller's IČO (identification number)",
    )
    
    # Optional arguments
    parser.add_argument(
        "--output",
        default="./output",
        help="Output directory for generated PDFs (default: ./output)",
    )
    parser.add_argument(
        "--template",
        default=None,
        help="Path to custom HTML template (default: built-in template)",
    )
    
    args = parser.parse_args()
    
    try:
        # Validate template path if provided
        if args.template:
            template_path = Path(args.template)
            if not template_path.exists():
                raise FileNotFoundError(
                    f"Template file not found: {args.template}"
                )
        
        # Validate seller info
        seller_info = SellerInfo(
            full_name=args.name,
            address=args.address,
            ico=args.ico,
        )
        
        # Parse CSV
        invoice_rows = parse_csv(args.csv)
        
        if not invoice_rows:
            print("Warning: No invoices found in CSV file", file=sys.stderr)
            return 0
        
        # Create output directory if it doesn't exist
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate PDF invoices
        total_invoices = len(invoice_rows)
        print(f"Generating PDF invoices... ({total_invoices} total)")
        
        successful = []
        failed = []
        
        for idx, invoice in enumerate(invoice_rows, start=1):
            try:
                # Render HTML
                html_content = render_invoice(
                    seller_info, 
                    invoice, 
                    template_path=args.template
                )
                
                # Sanitize filename (remove invalid filesystem characters)
                safe_filename = "".join(
                    c for c in invoice.transaction_id 
                    if c.isalnum() or c in ('-', '_', '.')
                )
                pdf_file = output_dir / f"{safe_filename}.pdf"
                
                # Convert HTML to PDF
                html_to_pdf(html_content, pdf_file)
                print(f"Generated {pdf_file.name} ({idx}/{total_invoices})")
                successful.append(pdf_file.name)
                
            except Exception as e:
                error_msg = f"Error generating {invoice.transaction_id}.pdf: {str(e)}"
                print(error_msg, file=sys.stderr)
                failed.append((invoice.transaction_id, str(e)))
        
        # Print summary
        print()
        if failed:
            print(
                f"Generated {len(successful)} PDF invoices successfully",
                file=sys.stdout
            )
            print(f"{len(failed)} invoice(s) failed:", file=sys.stderr)
            for transaction_id, error in failed:
                print(f"  {transaction_id}.pdf: {error}", file=sys.stderr)
            return 1
        else:
            print(f"Generated {len(successful)} PDF invoices in {output_dir}")
            return 0
        
    except ValidationError as e:
        print("Error: Invalid seller information", file=sys.stderr)
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            print(f"  {field}: {error['msg']}", file=sys.stderr)
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
