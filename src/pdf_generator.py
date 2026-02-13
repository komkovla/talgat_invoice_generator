"""PDF generation module using WeasyPrint."""

from pathlib import Path
from typing import Union
from weasyprint import HTML


def html_to_pdf(html_content: str, output_path: Union[str, Path]) -> None:
    """
    Convert HTML string to PDF file using WeasyPrint.
    
    Args:
        html_content: HTML string to convert to PDF
        output_path: Path where PDF file will be written (str or Path)
        
    Raises:
        FileNotFoundError: If parent directory cannot be created
        PermissionError: If file cannot be written due to permissions
        ValueError: If HTML/CSS has errors or PDF generation fails
    """
    # Convert to Path if string provided
    pdf_path = Path(output_path)
    
    # Ensure parent directory exists
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create HTML object from string
        html_doc = HTML(string=html_content)
        
        # Generate PDF
        html_doc.write_pdf(pdf_path)
        
    except (OSError, IOError) as e:
        # File system errors
        if "Permission denied" in str(e) or "denied" in str(e).lower():
            raise PermissionError(
                f"Cannot write PDF file: {pdf_path}. Permission denied."
            ) from e
        elif "No such file" in str(e) or "not found" in str(e).lower():
            raise FileNotFoundError(
                f"Cannot create PDF file: {pdf_path}. Directory not found."
            ) from e
        else:
            raise FileNotFoundError(
                f"Error writing PDF file: {pdf_path}. {str(e)}"
            ) from e
            
    except Exception as e:
        # Other WeasyPrint errors (HTML parsing, etc.)
        error_type = type(e).__name__
        raise ValueError(
            f"Error generating PDF: {error_type}: {str(e)}"
        ) from e
