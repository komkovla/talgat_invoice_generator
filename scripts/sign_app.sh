#!/bin/bash
set -euo pipefail

# Sign macOS .app bundle with code signing
# Usage: sign_app.sh <app_path> <signing_identity>
#
# The signing identity should be the full name of the certificate,
# e.g., "Developer ID Application: Your Name (TEAM_ID)"

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

# Find the main executable (should be InvoiceGenerator)
EXECUTABLE="$APP_PATH/Contents/MacOS/InvoiceGenerator"
if [ ! -f "$EXECUTABLE" ]; then
    echo "Error: Main executable not found: $EXECUTABLE" >&2
    exit 1
fi

# Step 1: Sign all .dylib and .so files recursively (inside-out order)
# We need to sign deepest files first, so we sort by path depth (longer paths first)
echo "Signing all .dylib and .so files..."

find "$APP_PATH" -type f \( -name "*.dylib" -o -name "*.so" \) | \
    awk '{print length($0), $0}' | \
    sort -rn | \
    cut -d' ' -f2- | \
    while read -r lib; do
        echo "  Signing: $lib"
        codesign --force --options runtime --timestamp \
            --sign "$IDENTITY" \
            "$lib" || {
            echo "Error: Failed to sign $lib" >&2
            exit 1
        }
    done

# Step 1b: Sign any other Mach-O binaries (e.g. embedded Python.framework/Versions/3.12/Python)
# Notarization requires every executable to be signed with Developer ID + timestamp.
# Build list (deepest first) then iterate in main shell so failures show codesign output.
echo "Signing other Mach-O binaries (e.g. embedded Python)..."
macho_list=$(find "$APP_PATH" -type f -print0 | while IFS= read -r -d '' f; do
    file -b "$f" | grep -q "Mach-O" && echo "$f"
done | awk '{print length($0), $0}' | sort -rn | cut -d' ' -f2-)
while read -r binpath; do
    [ -z "$binpath" ] && continue
    # Skip main executable (signed with entitlements in Step 2)
    [ "$binpath" = "$EXECUTABLE" ] && continue
    # Skip .dylib and .so (already signed in Step 1)
    case "$binpath" in *.dylib|*.so) continue ;; esac
    echo "  Signing: $binpath"
    codesign --remove-signature "$binpath" 2>/dev/null || true
    # Sign without hardened runtime for embedded interpreter (Python); avoids codesign failure
    # while still satisfying notarization (main app has runtime + entitlements).
    if ! codesign --force --timestamp --sign "$IDENTITY" "$binpath" 2>&1; then
        echo "Error: Failed to sign $binpath" >&2
        exit 1
    fi
done <<< "$macho_list"

# Step 2: Sign the main executable with hardened runtime + entitlements
echo "Signing main executable: $EXECUTABLE"
codesign --force --options runtime --timestamp \
    --sign "$IDENTITY" \
    --entitlements "$ENTITLEMENTS" \
    "$EXECUTABLE" || {
    echo "Error: Failed to sign main executable" >&2
    exit 1
}

# Step 3: Sign the .app bundle itself with hardened runtime + entitlements
echo "Signing .app bundle: $APP_PATH"
codesign --force --options runtime --timestamp \
    --sign "$IDENTITY" \
    --entitlements "$ENTITLEMENTS" \
    "$APP_PATH" || {
    echo "Error: Failed to sign .app bundle" >&2
    exit 1
}

# Step 4: Verify the signature
echo "Verifying signature..."
codesign --verify --deep --strict --verbose=2 "$APP_PATH" || {
    echo "Error: Signature verification failed" >&2
    exit 1
}

echo "✓ Code signing completed successfully"
