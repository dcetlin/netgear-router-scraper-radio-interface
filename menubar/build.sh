#!/bin/bash
# Builds "Router Radio.app" (menu bar app) and installs it to /Applications. No Xcode needed.
set -euo pipefail
cd "$(dirname "$0")"
APP="build/Router Radio.app"
rm -rf build && mkdir -p "$APP/Contents/MacOS"
swiftc -O -parse-as-library RouterRadio.swift -o "$APP/Contents/MacOS/RouterRadio"
cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Router Radio</string>
  <key>CFBundleIdentifier</key><string>com.dzc.routerradio</string>
  <key>CFBundleExecutable</key><string>RouterRadio</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>LSMinimumSystemVersion</key><string>13.0</string>
  <key>LSUIElement</key><true/>
</dict></plist>
PLIST
codesign --force -s - "$APP"
rm -rf "/Applications/Router Radio.app" && cp -R "$APP" /Applications/
echo "Installed /Applications/Router Radio.app"
