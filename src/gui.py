"""GUI application for invoice generator using customtkinter."""

import sys
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

# Handle imports for both development and PyInstaller bundle
try:
    from .main import generate_invoices, GenerationResult
except ImportError:
    # Fallback for PyInstaller when package structure isn't preserved
    from src.main import generate_invoices, GenerationResult


def get_templates_dir() -> Path:
    """Resolve the templates directory for both development and packaged builds."""
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller bundle
        base = Path(sys._MEIPASS)
    else:
        # Running from source
        base = Path(__file__).parent.parent
    return base / "templates"


TEMPLATES = {
    "English": "invoice.html",
    "Czech": "invoice_cz.html",
}

PADDING = {"padx": 16, "pady": (4, 4)}
SECTION_PADDING = {"padx": 16, "pady": (16, 4)}


class InvoiceGeneratorApp(ctk.CTk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()

        self.title("Invoice Generator")
        self.geometry("520x520")
        self.minsize(480, 480)
        self.resizable(True, True)

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self._build_csv_section()
        self._build_seller_section()
        self._build_options_section()
        self._build_generate_section()
        self._build_status_section()

    # ── CSV file picker ──────────────────────────────────────────────

    def _build_csv_section(self) -> None:
        label = ctk.CTkLabel(self, text="CSV File", font=ctk.CTkFont(size=13, weight="bold"))
        label.pack(anchor="w", **SECTION_PADDING)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", **PADDING)
        frame.columnconfigure(0, weight=1)

        self.csv_entry = ctk.CTkEntry(frame, placeholder_text="Select a CSV file...")
        self.csv_entry.grid(row=0, column=0, sticky="ew")

        browse_btn = ctk.CTkButton(frame, text="Browse", width=80, command=self._browse_csv)
        browse_btn.grid(row=0, column=1, padx=(8, 0))

    def _browse_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.csv_entry.delete(0, "end")
            self.csv_entry.insert(0, path)

    # ── Seller information ───────────────────────────────────────────

    def _build_seller_section(self) -> None:
        label = ctk.CTkLabel(self, text="Seller Information", font=ctk.CTkFont(size=13, weight="bold"))
        label.pack(anchor="w", **SECTION_PADDING)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", **PADDING)
        frame.columnconfigure(1, weight=1)

        fields = [
            ("Name", "Seller's full name"),
            ("Address", "Seller's address"),
            ("ICO", "Identification number"),
        ]

        self.seller_entries: dict[str, ctk.CTkEntry] = {}

        for row, (name, placeholder) in enumerate(fields):
            lbl = ctk.CTkLabel(frame, text=f"{name}:")
            lbl.grid(row=row, column=0, sticky="w", pady=4)

            entry = ctk.CTkEntry(frame, placeholder_text=placeholder)
            entry.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=4)
            self.seller_entries[name.lower()] = entry

    # ── Options (template + output dir) ──────────────────────────────

    def _build_options_section(self) -> None:
        label = ctk.CTkLabel(self, text="Options", font=ctk.CTkFont(size=13, weight="bold"))
        label.pack(anchor="w", **SECTION_PADDING)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", **PADDING)
        frame.columnconfigure(1, weight=1)

        # Template selector
        lbl_tpl = ctk.CTkLabel(frame, text="Template:")
        lbl_tpl.grid(row=0, column=0, sticky="w", pady=4)

        self.template_var = ctk.StringVar(value="English")
        self.template_selector = ctk.CTkSegmentedButton(
            frame, values=list(TEMPLATES.keys()), variable=self.template_var
        )
        self.template_selector.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)

        # Output directory
        lbl_out = ctk.CTkLabel(frame, text="Output:")
        lbl_out.grid(row=1, column=0, sticky="w", pady=4)

        out_frame = ctk.CTkFrame(frame, fg_color="transparent")
        out_frame.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)
        out_frame.columnconfigure(0, weight=1)

        self.output_entry = ctk.CTkEntry(out_frame, placeholder_text="./output")
        self.output_entry.grid(row=0, column=0, sticky="ew")

        browse_out_btn = ctk.CTkButton(out_frame, text="Browse", width=80, command=self._browse_output)
        browse_out_btn.grid(row=0, column=1, padx=(8, 0))

    def _browse_output(self) -> None:
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, path)

    # ── Generate button ──────────────────────────────────────────────

    def _build_generate_section(self) -> None:
        self.generate_btn = ctk.CTkButton(
            self,
            text="Generate Invoices",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_generate,
        )
        self.generate_btn.pack(fill="x", **SECTION_PADDING)

    # ── Status / progress ────────────────────────────────────────────

    def _build_status_section(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", **PADDING)

        self.progress_bar = ctk.CTkProgressBar(frame)
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(frame, text="Ready", font=ctk.CTkFont(size=12))
        self.status_label.pack(anchor="w", pady=(6, 0))

    # ── Validation & generation ──────────────────────────────────────

    def _collect_inputs(self) -> dict | None:
        """Collect and validate form inputs. Returns dict or None on error."""
        csv_path = self.csv_entry.get().strip()
        name = self.seller_entries["name"].get().strip()
        address = self.seller_entries["address"].get().strip()
        ico = self.seller_entries["ico"].get().strip()
        output_dir = self.output_entry.get().strip() or "./output"

        missing = []
        if not csv_path:
            missing.append("CSV File")
        elif not Path(csv_path).exists():
            self._set_status(f"CSV file not found: {csv_path}", error=True)
            return None
        if not name:
            missing.append("Name")
        if not address:
            missing.append("Address")
        if not ico:
            missing.append("ICO")

        if missing:
            self._set_status(f"Missing required fields: {', '.join(missing)}", error=True)
            return None

        template_name = TEMPLATES[self.template_var.get()]
        template_path = str(get_templates_dir() / template_name)

        return {
            "csv_path": csv_path,
            "seller_name": name,
            "seller_address": address,
            "seller_ico": ico,
            "output_dir": output_dir,
            "template_path": template_path,
        }

    def _on_generate(self) -> None:
        inputs = self._collect_inputs()
        if inputs is None:
            return

        self.generate_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self._set_status("Starting...")

        thread = threading.Thread(target=self._run_generation, args=(inputs,), daemon=True)
        thread.start()

    def _run_generation(self, inputs: dict) -> None:
        """Run invoice generation in a background thread."""

        def on_progress(current: int, total: int, filename: str) -> None:
            self.after(0, self._update_progress, current, total, filename)

        try:
            result = generate_invoices(**inputs, on_progress=on_progress)
            self.after(0, self._on_complete, result)
        except Exception as e:
            self.after(0, self._set_status, str(e), True)
            self.after(0, self.generate_btn.configure, {"state": "normal"})

    def _update_progress(self, current: int, total: int, filename: str) -> None:
        self.progress_bar.set(current / total)
        self._set_status(f"Generating {filename}  ({current}/{total})")

    def _on_complete(self, result: GenerationResult) -> None:
        self.generate_btn.configure(state="normal")
        self.progress_bar.set(1)

        if result.all_succeeded:
            self._set_status(f"Done -- generated {len(result.successful)} invoices")
        else:
            failed_names = ", ".join(name for name, _ in result.failed)
            self._set_status(
                f"Generated {len(result.successful)}, failed {len(result.failed)}: {failed_names}",
                error=True,
            )

    def _set_status(self, text: str, error: bool = False) -> None:
        self.status_label.configure(text=text, text_color="red" if error else ("gray70", "gray30"))


def run_gui() -> None:
    """Launch the GUI application."""
    app = InvoiceGeneratorApp()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
