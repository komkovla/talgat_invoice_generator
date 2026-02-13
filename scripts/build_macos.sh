#!/usr/bin/env bash
#
# Build macOS .app bundle and .dmg for Invoice Generator.
#
# Usage:
#   ./scripts/build_macos.sh          # builds .app + .dmg
#   ./scripts/build_macos.sh --app    # builds .app only
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_NAME="Invoice Generator"
DMG_NAME="InvoiceGenerator"

cd "$PROJECT_ROOT"

# ── Check prerequisites ──────────────────────────────────────────────────────

echo "==> Checking prerequisites..."

if ! command -v brew &>/dev/null; then
    echo "Error: Homebrew is required. Install from https://brew.sh" >&2
    exit 1
fi

for pkg in pango gdk-pixbuf libffi cairo; do
    if ! brew list "$pkg" &>/dev/null; then
        echo "==> Installing $pkg via Homebrew..."
        brew install "$pkg"
    fi
done

if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is required." >&2
    exit 1
fi

# ── Set up virtual environment ───────────────────────────────────────────────

echo "==> Setting up Python environment..."

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt
pip install -q pyinstaller

# ── Build .app ───────────────────────────────────────────────────────────────

echo "==> Building macOS .app bundle..."
pyinstaller invoice_generator.spec --noconfirm --clean

APP_PATH="dist/${APP_NAME}.app"

if [ ! -d "$APP_PATH" ]; then
    echo "Error: Build failed -- $APP_PATH not found." >&2
    exit 1
fi

echo "==> Built $APP_PATH"

# ── Create .dmg (unless --app flag) ─────────────────────────────────────────

if [ "${1:-}" = "--app" ]; then
    echo "==> Done (skipping .dmg)."
    exit 0
fi

echo "==> Creating .dmg disk image..."

DMG_DIR="dist/dmg"
DMG_OUTPUT="dist/${DMG_NAME}.dmg"

rm -rf "$DMG_DIR" "$DMG_OUTPUT"
mkdir -p "$DMG_DIR"
cp -R "$APP_PATH" "$DMG_DIR/"

# Create a symlink to Applications for drag-to-install
ln -s /Applications "$DMG_DIR/Applications"

hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$DMG_DIR" \
    -ov \
    -format UDZO \
    "$DMG_OUTPUT"

rm -rf "$DMG_DIR"

echo "==> Done: $DMG_OUTPUT"
