#!/bin/zsh
set -euo pipefail

cd "$(dirname "$0")"
export COPYFILE_DISABLE=1

PROJECT="DockCatApp/DockCat.xcodeproj"
SCHEME="DockCat"
CONFIGURATION="Release"
DERIVED_DATA="DockCatApp/DerivedDataRelease"
APP_PATH="$DERIVED_DATA/Build/Products/$CONFIGURATION/DockCat.app"
EXECUTABLE_PATH="$APP_PATH/Contents/MacOS/DockCat"
README_PATH="README.md"
README_EN_PATH="README.en.md"
LICENSE_PATH="LICENSE.txt"
CUSTOMIZATION_GUIDE_PATH="CustomizationGuide"
ZIP_PATH="DockCat.zip"

echo "Clean building DockCat for packaging..."
xcodebuild \
  -project "$PROJECT" \
  -scheme "$SCHEME" \
  -configuration "$CONFIGURATION" \
  -derivedDataPath "$DERIVED_DATA" \
  ONLY_ACTIVE_ARCH=NO \
  ARCHS="arm64 x86_64" \
  clean build

if [[ ! -d "$APP_PATH" ]]; then
  echo "DockCat.app was not found after build:"
  echo "$APP_PATH"
  exit 1
fi

if [[ ! -f "$EXECUTABLE_PATH" ]]; then
  echo "DockCat executable was not found after build:"
  echo "$EXECUTABLE_PATH"
  exit 1
fi

ARCHS_OUTPUT="$(lipo -archs "$EXECUTABLE_PATH")"
if [[ " $ARCHS_OUTPUT " != *" arm64 "* || " $ARCHS_OUTPUT " != *" x86_64 "* ]]; then
  echo "DockCat executable is not universal. Found architectures: $ARCHS_OUTPUT"
  exit 1
fi

if [[ ! -f "$README_PATH" ]]; then
  echo "README.md was not found."
  exit 1
fi

if [[ ! -f "$README_EN_PATH" ]]; then
  echo "README.en.md was not found."
  exit 1
fi

if [[ ! -f "$LICENSE_PATH" ]]; then
  echo "LICENSE.txt was not found."
  exit 1
fi

if [[ ! -d "$CUSTOMIZATION_GUIDE_PATH" ]]; then
  echo "CustomizationGuide folder was not found."
  exit 1
fi

PACKAGE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/dockcat-package.XXXXXX")"
trap 'rm -rf "$PACKAGE_DIR"' EXIT

echo "Preparing release package..."
ditto --norsrc "$APP_PATH" "$PACKAGE_DIR/DockCat.app"
cp "$README_PATH" "$PACKAGE_DIR/README.md"
cp "$README_EN_PATH" "$PACKAGE_DIR/README.en.md"
cp "$LICENSE_PATH" "$PACKAGE_DIR/LICENSE.txt"
mkdir -p "$PACKAGE_DIR/CustomizationGuide"
cp -R "$CUSTOMIZATION_GUIDE_PATH"/. "$PACKAGE_DIR/CustomizationGuide/"

echo "Checking packaged app contents..."
if find "$PACKAGE_DIR/DockCat.app" \
  \( -name '.DS_Store' \
     -o -name 'DockCatTests.xctest' \
     -o -name '*.debug.dylib' \
     -o -name '__preview.dylib' \
     -o -name 'XCTest*.framework' \
     -o -name 'XCT*.framework' \
     -o -name 'Testing.framework' \) \
  -print -quit | grep -q .; then
  echo "Packaged app contains debug, test, preview, or local metadata artifacts. Aborting."
  find "$PACKAGE_DIR/DockCat.app" \
    \( -name '.DS_Store' \
       -o -name 'DockCatTests.xctest' \
       -o -name '*.debug.dylib' \
       -o -name '__preview.dylib' \
       -o -name 'XCTest*.framework' \
       -o -name 'XCT*.framework' \
       -o -name 'Testing.framework' \) \
    -print
  exit 1
fi

echo "Packing DockCat.app, CustomizationGuide, README.md, README.en.md, and LICENSE.txt..."
rm -f "$ZIP_PATH"
ditto -c -k --norsrc "$PACKAGE_DIR" "$ZIP_PATH"

echo "Checking archive contents..."
if unzip -l "$ZIP_PATH" | grep -E '(__MACOSX|\.DS_Store|DockCatTests\.xctest|\.debug\.dylib|__preview\.dylib|XCTest[^/]*\.framework|XCT[^/]*\.framework|Testing\.framework|DerivedData)' >/dev/null; then
  echo "Archive contains debug, test, preview, or local metadata artifacts. Aborting."
  unzip -l "$ZIP_PATH" | grep -E '(__MACOSX|\.DS_Store|DockCatTests\.xctest|\.debug\.dylib|__preview\.dylib|XCTest[^/]*\.framework|XCT[^/]*\.framework|Testing\.framework|DerivedData)'
  exit 1
fi

echo "Created $(pwd)/$ZIP_PATH with architectures: $ARCHS_OUTPUT"
