#!/bin/bash
set -e

# --------------------------
# Config
# --------------------------
APP_NAME="Metal HUD Mobile Config"
APP_VERSION="2.0.2"
BUNDLE_ID="com.example.metalhud"

BUILD_DIR="build"
DIST_DIR="dist"
APP_PATH="$DIST_DIR/$APP_NAME.app"
ZIP_PATH="$DIST_DIR/$APP_NAME.app.zip"
DMG_PATH="$DIST_DIR/MetalHUDMobileConfig-$APP_VERSION.dmg"

APPLE_ID="${APPLE_ID:?Set APPLE_ID env variable}"
APP_SPECIFIC_PASSWORD="${APP_SPECIFIC_PASSWORD:?Set APP_SPECIFIC_PASSWORD env variable}"
TEAM_ID="${TEAM_ID:?Set TEAM_ID env variable}"
DEVELOPER_ID="${DEVELOPER_ID:?Set DEVELOPER_ID env variable}"
# --------------------------

# Step 0: Clean build
rm -rf "$BUILD_DIR" "$DIST_DIR"

# Step 1: Rebuild with py2app 
python3 setup.py py2app

# Step 1.5: Sign all binaries inside Resources
find "$APP_PATH" -type f \( -name "*.so" -o -name "*.dylib" -o -perm +111 \) | while read -r file; do
  echo "   Signing $file"
  codesign --force --options runtime --timestamp --sign "$DEVELOPER_ID" --verbose "$file" || true
done

# Step 2: Codesign
codesign --deep --force --options runtime --timestamp \
  --sign "$DEVELOPER_ID" "$APP_PATH"

# Step 3: Verify codesign
codesign --verify --deep --strict --verbose=2 "$APP_PATH"

# Step 4: Zip for notarization
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"

# Step 5: Submit for notarization
xcrun notarytool submit "$ZIP_PATH" \
  --apple-id "$APPLE_ID" \
  --password "$APP_SPECIFIC_PASSWORD" \
  --team-id "$TEAM_ID" \
  --wait

# Step 6: Staple ticket
xcrun stapler staple "$APP_PATH"

# Step 7: Final verification
spctl --assess --verbose=4 --type execute "$APP_PATH"

# Step 8: Create DMG
create-dmg \
  "$APP_PATH" \
  "$(dirname "$DMG_PATH")" \
  --volname "$APP_NAME" \
  --window-size 600 400 \
  --icon-size 128 \
  --app-drop-link 500 200 \
  --overwrite \
  --dmg-title "$(basename "$DMG_PATH")"

# Step 9: Staple DMG 
xcrun stapler staple "$DMG_PATH"

echo "✅ Done! DMG created at $DMG_PATH"