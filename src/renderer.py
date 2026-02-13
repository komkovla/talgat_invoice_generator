"""HTML rendering module using Jinja2 templates."""

from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, TemplateSyntaxError

from .models import SellerInfo, InvoiceRow


def add_days(date_str: str, days: int) -> str:
    """
    Add days to a date string in YYYY-MM-DD format.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        days: Number of days to add (can be negative)
        
    Returns:
        Date string in YYYY-MM-DD format
    """
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    new_date = date_obj + timedelta(days=days)
    return new_date.strftime("%Y-%m-%d")


def render_invoice(
    seller: SellerInfo,
    invoice: InvoiceRow,
    template_path: Optional[str] = None
) -> str:
    """
    Render invoice HTML using Jinja2 template.
    
    Args:
        seller: SellerInfo object containing seller information
        invoice: InvoiceRow object containing invoice data
        template_path: Optional custom path to template file.
                      If None, uses default templates/invoice.html
        
    Returns:
        Rendered HTML string
        
    Raises:
        FileNotFoundError: If template file is not found
        ValueError: If template has syntax errors or rendering fails
    """
    # Determine template directory and filename
    if template_path:
        template_file = Path(template_path)
        template_dir = template_file.parent
        template_name = template_file.name
    else:
        # Default: use templates/invoice.html relative to project root
        project_root = Path(__file__).parent.parent
        template_dir = project_root / "templates"
        template_name = "invoice.html"
    
    if not template_dir.exists():
        raise FileNotFoundError(
            f"Template directory not found: {template_dir}"
        )
    
    try:
        # Create Jinja2 environment
        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True,  # Security: escape HTML in data
            trim_blocks=True,  # Remove first newline after block
            lstrip_blocks=True,  # Strip whitespace from start of blocks
        )
        
        # Register custom filter for date arithmetic
        env.filters['add_days'] = add_days
        
        # Load template
        template = env.get_template(template_name)
        
        # Render template with data
        html = template.render(
            seller=seller,
            invoice=invoice
        )
        
        return html
        
    except TemplateNotFound as e:
        raise FileNotFoundError(
            f"Template not found: {template_name} in {template_dir}"
        ) from e
        
    except TemplateSyntaxError as e:
        raise ValueError(
            f"Template syntax error in {template_name}: {str(e)}"
        ) from e
        
    except Exception as e:
        raise ValueError(
            f"Error rendering template: {str(e)}"
        ) from e
