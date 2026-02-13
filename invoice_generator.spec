# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Invoice Generator macOS .app bundle."""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# Collect WeasyPrint and its heavy native dependencies
weasyprint_datas, weasyprint_binaries, weasyprint_hiddenimports = collect_all("weasyprint")
cffi_datas, cffi_binaries, cffi_hiddenimports = collect_all("cffi")
ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all("customtkinter")

all_datas = weasyprint_datas + cffi_datas + ctk_datas + [
    ("templates", "templates"),
    ("src", "src"),  # Include entire src package
]

all_binaries = weasyprint_binaries + cffi_binaries + ctk_binaries

all_hiddenimports = (
    weasyprint_hiddenimports
    + cffi_hiddenimports
    + ctk_hiddenimports
    + collect_submodules("pydantic")
    + [
        "cssselect2",
        "tinycss2",
        "pango",
        "cairocffi",
    ]
)

# -- Locate Homebrew shared libraries (Pango, Cairo, GDK-Pixbuf, etc.) --------
homebrew_lib = Path("/opt/homebrew/lib")
if homebrew_lib.exists():
    for dylib in homebrew_lib.glob("*.dylib"):
        all_binaries.append((str(dylib), "."))

homebrew_gdk_loaders = Path("/opt/homebrew/lib/gdk-pixbuf-2.0")
if homebrew_gdk_loaders.exists():
    for f in homebrew_gdk_loaders.rglob("*"):
        if f.is_file():
            rel = f.relative_to(Path("/opt/homebrew/lib"))
            all_datas.append((str(f), str(rel.parent)))

a = Analysis(
    ["gui_launcher.py"],
    pathex=["."],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hiddenimports + ["src.main", "src.gui", "src.csv_parser", "src.renderer", "src.pdf_generator", "src.models"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="InvoiceGenerator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    target_arch="arm64",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="InvoiceGenerator",
)

app = BUNDLE(
    coll,
    name="Invoice Generator.app",
    icon=None,
    bundle_identifier="com.talgat.invoicegenerator",
    info_plist={
        "CFBundleShortVersionString": "1.0.0",
        "NSHighResolutionCapable": True,
    },
)
