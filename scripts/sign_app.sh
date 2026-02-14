#!/bin/bash
set -euo pipefail

# Sign macOS .app bundle for notarization.
# Usage: sign_app.sh <app_path> <signing_identity> [entitlements_file]
#
# Signing order (inside-out):
#   1. .dylib / .so libraries  (hardened runtime + timestamp)
#   2. Other Mach-O binaries   (timestamp only — e.g. embedded Python interpreter)
#   3. Main executable          (hardened runtime + timestamp + entitlements)
#   4. .app bundle              (hardened runtime + timestamp + entitlements)

APP_PATH="$1"
IDENTITY="$2"
ENTITLEMENTS="${3:-entitlements.plist}"

if [ ! -d "$APP_PATH" ]; then
    echo "Error: App bundle not found: $APP_PATH" >&2
    exit 1
fi

if [ ! -f "$ENTITLEMENTS" ]; then
    echo "Error: Entitlements file not found: $ENTITLEMENTS" >&2
    exit 1
fi

echo "Signing app bundle: $APP_PATH"
echo "Using identity: $IDENTITY"
echo "Using entitlements: $ENTITLEMENTS"

EXECUTABLE="$APP_PATH/Contents/MacOS/InvoiceGenerator"
if [ ! -f "$EXECUTABLE" ]; then
    echo "Error: Main executable not found: $EXECUTABLE" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Collect every Mach-O binary inside the bundle into a temp file.
# Using a temp file avoids pipefail/set-e failures that occur when the last
# file in a pipeline isn't Mach-O (grep returns 1 → pipeline returns 1).
# ---------------------------------------------------------------------------
MACHO_LIST=$(mktemp)
trap 'rm -f "$MACHO_LIST"' EXIT

echo "Scanning for Mach-O binaries..."
find "$APP_PATH" -type f -print0 | while IFS= read -r -d '' f; do
    # `if/fi` always returns 0 when the condition is false, keeping the
    # pipeline exit code clean regardless of which file is processed last.
    if file -b "$f" 2>/dev/null | grep -q "Mach-O"; then
        printf '%s\n' "$f"
    fi
done > "$MACHO_LIST" || true

# Sort deepest paths first (inside-out signing order).
SORTED_LIST=$(awk '{print length($0), $0}' "$MACHO_LIST" | sort -rn | cut -d' ' -f2-)
TOTAL=$(wc -l < "$MACHO_LIST" | tr -d ' ')
echo "Found $TOTAL Mach-O binaries"

# ---------------------------------------------------------------------------
# Step 1 — Sign .dylib and .so with hardened runtime
# ---------------------------------------------------------------------------
echo "Signing .dylib / .so libraries..."
while IFS= read -r lib; do
    [ -z "$lib" ] && continue
    case "$lib" in
        *.dylib|*.so) ;;
        *) continue ;;
    esac
    echo "  Signing: $lib"
    codesign --force --options runtime --timestamp \
        --sign "$IDENTITY" \
        "$lib"
done <<< "$SORTED_LIST"

# ---------------------------------------------------------------------------
# Step 2 — Sign remaining Mach-O binaries (e.g. Python.framework/Python)
#   • timestamp is required for notarization
#   • hardened runtime is omitted — embedded interpreters may allocate
#     executable memory, which conflicts with the runtime flag
# ---------------------------------------------------------------------------
echo "Signing other Mach-O binaries..."
while IFS= read -r binpath; do
    [ -z "$binpath" ] && continue
    [ "$binpath" = "$EXECUTABLE" ] && continue
    case "$binpath" in *.dylib|*.so) continue ;; esac

    echo "  Signing: $binpath"
    codesign --remove-signature "$binpath" 2>/dev/null || true
    codesign --force --timestamp \
        --sign "$IDENTITY" \
        "$binpath"
done <<< "$SORTED_LIST"

# ---------------------------------------------------------------------------
# Step 3 — Sign the main executable (hardened runtime + entitlements)
# ---------------------------------------------------------------------------
echo "Signing main executable: $EXECUTABLE"
codesign --force --options runtime --timestamp \
    --sign "$IDENTITY" \
    --entitlements "$ENTITLEMENTS" \
    "$EXECUTABLE"

# ---------------------------------------------------------------------------
# Step 4 — Sign the .app bundle itself (hardened runtime + entitlements)
# ---------------------------------------------------------------------------
echo "Signing .app bundle: $APP_PATH"
codesign --force --options runtime --timestamp \
    --sign "$IDENTITY" \
    --entitlements "$ENTITLEMENTS" \
    "$APP_PATH"

# ---------------------------------------------------------------------------
# Step 5 — Verify
# ---------------------------------------------------------------------------
echo "Verifying signature..."
codesign --verify --deep --strict --verbose=2 "$APP_PATH"

echo "Code signing completed successfully"
