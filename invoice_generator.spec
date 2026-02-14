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
# WeasyPrint requires these specific libraries and their dependencies
import subprocess

def collect_dylib_dependencies(dylib_path):
    """Recursively collect all dependencies of a dylib."""
    collected = set()
    to_process = [dylib_path]
    
    while to_process:
        current = to_process.pop()
        if current in collected or not Path(current).exists():
            continue
        collected.add(current)
        
        try:
            # Use otool to find dependencies
            result = subprocess.run(
                ["otool", "-L", current],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.split('\n')[1:]:  # Skip first line (the dylib itself)
                line = line.strip()
                if not line or ':' in line:
                    continue
                # Extract library path (before the first space)
                dep_path = line.split()[0]
                # Only process Homebrew libraries
                if '/opt/homebrew/' in dep_path or '/usr/local/' in dep_path:
                    # Resolve @rpath and @loader_path
                    if dep_path.startswith('@rpath/') or dep_path.startswith('@loader_path/'):
                        # Try to resolve relative to homebrew lib
                        lib_name = dep_path.split('/')[-1]
                        for search_path in ['/opt/homebrew/lib', '/usr/local/lib']:
                            candidate = Path(search_path) / lib_name
                            if candidate.exists():
                                dep_path = str(candidate)
                                break
                    if Path(dep_path).exists() and dep_path not in collected:
                        to_process.append(dep_path)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    return collected

# Required WeasyPrint libraries (core dependencies)
# Map library names to their actual filenames on macOS
required_libs = {
    'libgobject-2.0': ['libgobject-2.0.0.dylib', 'libgobject-2.0.dylib'],
    'libglib-2.0': ['libglib-2.0.0.dylib', 'libglib-2.0.dylib'],
    'libpango-1.0': ['libpango-1.0.0.dylib', 'libpango-1.0.dylib'],
    'libpangocairo-1.0': ['libpangocairo-1.0.0.dylib', 'libpangocairo-1.0.dylib'],
    'libpangoft2-1.0': ['libpangoft2-1.0.0.dylib', 'libpangoft2-1.0.dylib'],
    'libcairo': ['libcairo.2.dylib', 'libcairo.dylib'],
    'libcairo-gobject': ['libcairo-gobject.2.dylib', 'libcairo-gobject.dylib'],
    'libgdk_pixbuf-2.0': ['libgdk_pixbuf-2.0.0.dylib', 'libgdk_pixbuf-2.0.dylib'],
    'libffi': ['libffi.8.dylib', 'libffi.dylib'],
    'libintl': ['libintl.8.dylib', 'libintl.dylib'],
    'libgio-2.0': ['libgio-2.0.0.dylib', 'libgio-2.0.dylib'],
    'libgmodule-2.0': ['libgmodule-2.0.0.dylib', 'libgmodule-2.0.dylib'],
    'libgthread-2.0': ['libgthread-2.0.0.dylib', 'libgthread-2.0.dylib'],
}

homebrew_lib = Path("/opt/homebrew/lib")
homebrew_local = Path("/usr/local/lib")

# Collect all required libraries and their dependencies
all_collected_dylibs = set()

for lib_name, patterns in required_libs.items():
    for search_path in [homebrew_lib, homebrew_local]:
        if not search_path.exists():
            continue
        
        # Try each pattern for this library
        for pattern in patterns:
            candidate = search_path / pattern
            if candidate.exists() and candidate.is_file():
                # Collect this library and all its dependencies
                deps = collect_dylib_dependencies(str(candidate))
                all_collected_dylibs.update(deps)
                break
        else:
            # If exact match failed, try glob pattern
            base_name = lib_name.replace('lib', '')
            glob_pattern = f"{lib_name}*.dylib"
            matches = list(search_path.glob(glob_pattern))
            if matches:
                for dylib in matches:
                    if dylib.is_file():
                        deps = collect_dylib_dependencies(str(dylib))
                        all_collected_dylibs.update(deps)
                        break
                break

# Add collected libraries to binaries
for dylib_path in all_collected_dylibs:
    dylib = Path(dylib_path)
    if dylib.exists() and dylib.is_file():
        # Place in lib/ subdirectory to avoid conflicts
        all_binaries.append((str(dylib), "lib"))

# Collect GDK-Pixbuf loaders
for loader_dir in [homebrew_lib / "gdk-pixbuf-2.0", homebrew_local / "gdk-pixbuf-2.0"]:
    if loader_dir.exists():
        for f in loader_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(loader_dir.parent)
                all_datas.append((str(f), str(rel.parent)))

a = Analysis(
    ["gui_launcher.py"],
    pathex=["."],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hiddenimports + ["src.main", "src.gui", "src.csv_parser", "src.renderer", "src.pdf_generator", "src.models"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["pyi_rth_weasyprint.py"],
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
