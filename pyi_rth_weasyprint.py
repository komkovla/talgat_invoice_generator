"""
PyInstaller runtime hook for WeasyPrint.
Sets up library paths so WeasyPrint can find its native dependencies.
"""
import os
import sys
import ctypes
from pathlib import Path

# Get the base directory where PyInstaller extracted files
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    base_path = Path(sys._MEIPASS)
else:
    # Running as a script
    base_path = Path(__file__).parent

# Add lib directory to library search paths
lib_path = base_path / "lib"
if lib_path.exists():
    lib_path_str = str(lib_path)
    
    # On macOS, we need to help ctypes find libraries
    # WeasyPrint's cffi uses ctypes.util.find_library which may not find bundled libs
    # Monkey-patch ctypes.util.find_library to search our lib directory
    import ctypes.util
    
    _original_find_library = ctypes.util.find_library
    
    def patched_find_library(name):
        # Try original method first
        result = _original_find_library(name)
        if result:
            return result
        
        # Try to find in our bundled lib directory
        # Handle different library name formats
        patterns = [
            f"lib{name}.dylib",
            f"{name}.dylib",
            f"lib{name}.0.dylib",
            f"{name}.0.dylib",
        ]
        
        # Also try with version numbers
        for version in ["2.0", "1.0", "0"]:
            patterns.extend([
                f"lib{name}-{version}.dylib",
                f"{name}-{version}.dylib",
                f"lib{name}-{version}.0.dylib",
            ])
        
        for pattern in patterns:
            candidate = lib_path / pattern
            if candidate.exists():
                return str(candidate)
        
        return None
    
    ctypes.util.find_library = patched_find_library
    
    # Set DYLD_LIBRARY_PATH as fallback (may be restricted on macOS)
    current_lib_path = os.environ.get("DYLD_LIBRARY_PATH", "")
    if lib_path_str not in current_lib_path:
        if current_lib_path:
            os.environ["DYLD_LIBRARY_PATH"] = f"{lib_path_str}:{current_lib_path}"
        else:
            os.environ["DYLD_LIBRARY_PATH"] = lib_path_str

# Set GDK_PIXBUF_MODULEDIR for GDK-Pixbuf loaders
gdk_pixbuf_dir = base_path / "gdk-pixbuf-2.0"
if gdk_pixbuf_dir.exists():
    os.environ["GDK_PIXBUF_MODULEDIR"] = str(gdk_pixbuf_dir)
else:
    # Try alternative location
    alt_gdk_dir = base_path.parent / "gdk-pixbuf-2.0"
    if alt_gdk_dir.exists():
        os.environ["GDK_PIXBUF_MODULEDIR"] = str(alt_gdk_dir)
