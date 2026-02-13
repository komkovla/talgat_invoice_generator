# Invoice Generator

A command-line tool that reads a CSV file and generates individual PDF invoices for each row. Built with Python, Jinja2 templating, and WeasyPrint for HTML-to-PDF conversion.

---

## Stack

| Component        | Technology    | Why                                                        |
| ---------------- | ------------- | ---------------------------------------------------------- |
| Language          | Python 3.10+  | Built-in CSV, rich PDF ecosystem, clean scripting          |
| HTML templating   | Jinja2        | Industry-standard, powerful template inheritance           |
| HTML → PDF       | WeasyPrint    | Pure Python, no external binaries (unlike wkhtmltopdf)     |
| CLI interface     | argparse      | Standard library, no extra dependency for a simple CLI     |
| Data validation   | pydantic      | Strict schema enforcement for CSV rows and seller info     |
| Project tooling   | pip + venv    | Simple, universal Python packaging                         |

## Project Structure

```
talgat_invoice_generator/
├── README.md
├── requirements.txt
├── sample.csv                  # Example input file
├── templates/
│   └── invoice.html            # Jinja2 HTML template
├── output/                     # Generated PDFs (gitignored)
├── src/
│   ├── __init__.py
│   ├── main.py                 # CLI entry point
│   ├── models.py               # Pydantic data models
│   ├── csv_parser.py           # CSV reading and validation
│   ├── renderer.py             # Jinja2 HTML rendering
│   └── pdf_generator.py        # WeasyPrint PDF conversion
└── tests/
    ├── __init__.py
    ├── test_csv_parser.py
    ├── test_renderer.py
    └── test_pdf_generator.py
```

## Data Fields

### Per-Invoice (from CSV)

| Field            | CSV Column       | Description                          |
| ---------------- | ---------------- | ------------------------------------ |
| Transaction ID   | `transaction_id` | Unique identifier for the invoice    |
| Customer Name    | `customer_name`  | Name of the customer being invoiced  |
| Date             | `date`           | Invoice / transaction date           |
| Purchase Item    | `item`           | Description of the purchased item    |
| Amount           | `amount`         | Total amount (numeric)               |

### Seller Info (CLI parameters, same on every invoice)

| Field               | CLI Flag     | Description                       |
| ------------------- | ------------ | --------------------------------- |
| Full Name           | `--name`     | Seller's full name                |
| Address             | `--address`  | Seller's address                  |
| IČO (ID number)     | `--ico`      | Seller's identification number    |

## Features

- **CSV Validation**: Automatic validation of invoice data with clear error messages
- **Custom Templates**: Use your own HTML templates with `--template` option
- **Progress Indicators**: Real-time progress showing "Generated X/Y invoices"
- **Robust Error Handling**: Continues processing even if individual invoices fail
- **Professional Output**: Clean, print-ready PDF invoices with modern styling

## CLI Interface

**Basic Usage:**
```bash
python -m src.main \
  --csv sample.csv \
  --name "Talgat Doe" \
  --address "123 Main St, Prague" \
  --ico "12345678" \
  --output ./output
```

**With Custom Template:**
```bash
python -m src.main \
  --csv invoices.csv \
  --name "John Doe" \
  --address "123 St" \
  --ico "12345" \
  --template custom_template.html \
  --output ./output
```

### Arguments

| Argument        | Required | Default      | Description                        |
| --------------- | -------- | ------------ | ---------------------------------- |
| `--csv`         | Yes      | —            | Path to the input CSV file         |
| `--name`        | Yes      | —            | Seller full name                   |
| `--address`     | Yes      | —            | Seller address                     |
| `--ico`         | Yes      | —            | Seller IČO (identification number) |
| `--output`      | No       | `./output`   | Directory for generated PDFs       |
| `--template`    | No       | built-in     | Path to custom HTML template       |

### Output

Each invoice is saved as a separate PDF file named:

```
<transaction_id>.pdf
```

Example: `TXN-2026-001.pdf`

### Error Handling

The tool includes robust error handling:

- **Per-Invoice Errors**: If one invoice fails to generate, processing continues for remaining invoices
- **Error Summary**: At the end, a summary shows successful and failed invoices
- **Clear Messages**: Error messages include context (which invoice, what went wrong)
- **Exit Codes**: Returns 0 on success, 1 if any invoices failed

**Example Error Output:**
```
Generating PDF invoices... (3 total)
Generated TXN-2026-001.pdf (1/3)
Error generating TXN-2026-002.pdf: Template syntax error
Generated TXN-2026-003.pdf (3/3)

Generated 2 PDF invoices successfully
1 invoice(s) failed:
  TXN-2026-002.pdf: Template syntax error
```

## CSV Format

```csv
transaction_id,customer_name,date,item,amount
TXN-2026-001,Acme Corp,2026-01-15,Consulting Services,1500.00
TXN-2026-002,Globex Inc,2026-01-20,Software License,3200.00
TXN-2026-003,Initech Ltd,2026-02-01,Training Workshop,800.00
TXN-2026-004,John Smith,2026-02-10,Website Development,5500.00
TXN-2026-005,Tech Solutions s.r.o.,2026-02-28,Monthly Maintenance,1200.00
TXN-2026-006,StartupXYZ,2026-03-05,Product Design Consultation,2500.00
```

See `sample.csv` for a complete example with realistic invoice data.

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd talgat_invoice_generator

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Development Plan

Incremental milestones — each step produces a working, testable artifact.

### Phase 1: Foundation ✅

**Goal:** Parse CSV, validate data, print structured output to terminal.

- [x] Set up project structure (`src/`, `tests/`, `requirements.txt`)
- [x] Define Pydantic models for `InvoiceRow` and `SellerInfo`
- [x] Implement CSV parser with validation and clear error messages
- [x] Wire up CLI with argparse
- [x] Add unit tests for CSV parsing and model validation

**Deliverable:** Running `python -m src.main --csv sample.csv --name ... --address ... --ico ...` prints parsed invoice data to stdout.

### Phase 2: HTML Rendering ✅

**Goal:** Render each invoice row into a standalone HTML file using Jinja2.

- [x] Create the `invoice.html` Jinja2 template with clean, professional styling
- [x] Implement the renderer module (load template, inject data, return HTML string)
- [x] Integrate renderer into the main pipeline
- [x] Add unit tests for HTML rendering (verify key fields appear in output)

**Deliverable:** The tool generates one `.html` file per invoice row in the output directory.

### Phase 3: PDF Generation ✅

**Goal:** Convert rendered HTML into PDF files.

- [x] Implement WeasyPrint PDF conversion module
- [x] Integrate into the main pipeline (CSV → HTML → PDF)
- [x] Handle output directory creation and file naming
- [x] Add integration test (generate PDF, verify file exists and is valid)

**Deliverable:** The tool generates one `.pdf` file per invoice row. Core functionality is complete.

### Phase 4: Polish ✅

**Goal:** Production-ready error handling, logging, and UX.

- [x] Add progress output (e.g., "Generated 3/10 invoices...")
- [x] Graceful error handling for missing files, malformed CSV, bad data
- [x] Support custom template path (`--template`)
- [x] Add `sample.csv` with realistic example data
- [x] Final README review

**Deliverable:** Robust, user-friendly tool ready for daily use.

## License

MIT
