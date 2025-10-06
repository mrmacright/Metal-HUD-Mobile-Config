#!/bin/bash
set -e

# --------------------------
# Config
# --------------------------
APP_NAME="Metal HUD Mobile Config"
APP_VERSION="2.4.0"
BUNDLE_ID="com.example.metalhud"   # Replace with your actual bundle ID

BUILD_DIR="build"
DIST_DIR="dist"
APP_PATH="$DIST_DIR/$APP_NAME.app"
ZIP_PATH="$DIST_DIR/$APP_NAME.app.zip"
DMG_PATH="$DIST_DIR/MetalHUDMobileConfig-$APP_VERSION.dmg"

# Apple Developer Credentials (set as environment variables before running)
# Example:
# export APPLE_ID="your@appleid.com"
# export APP_SPECIFIC_PASSWORD="xxxx-xxxx-xxxx-xxxx"
# export TEAM_ID="XXXXXXXXXX"
# export DEVELOPER_ID="Developer ID Application: Your Name (XXXXXXXXXX)"
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

# Step 2: Codesign the app bundle
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

# Step 8: Create DMG with drag-to-Applications using hdiutil
TMP_DIR=$(mktemp -d)

# Copy app into temp dir
cp -R "$APP_PATH" "$TMP_DIR/"

# Create Applications shortcut
ln -s /Applications "$TMP_DIR/Applications"

# Create compressed DMG
hdiutil create -volname "$APP_NAME" \
  -srcfolder "$TMP_DIR" \
  -ov -format UDZO "$DMG_PATH"

# Clean up temp folder
rm -rf "$TMP_DIR"

# Step 9: Staple DMG 
xcrun stapler staple "$DMG_PATH"

echo "✅ Done! DMG created at $DMG_PATH"
