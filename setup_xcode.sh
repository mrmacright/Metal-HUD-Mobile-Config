#!/bin/bash

echo "Running Xcode setup..."

# Install Xcode command line tools if not installed
if ! xcode-select -p &>/dev/null; then
  echo "Installing Xcode Command Line Tools..."
  xcode-select --install
  echo "Please complete installation and rerun the app."
  exit 1
fi

# Accept license if needed
if ! xcrun clang &>/dev/null; then
  echo "Accepting Xcode license..."
  sudo xcodebuild -license accept
fi

# Find Xcode.app anywhere using mdfind
xcode_path=$(mdfind "kMDItemCFBundleIdentifier == 'com.apple.dt.Xcode'" | head -n 1)

if [ -z "$xcode_path" ]; then
  echo "Xcode.app not found in system search."
  # Optional: fallback to /Applications
  if [ -d "/Applications/Xcode.app" ]; then
    echo "Using default /Applications/Xcode.app"
    sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
  else
    echo "Xcode not found. Please install Xcode."
    exit 1
  fi
else
  echo "Found Xcode at: $xcode_path"
  sudo xcode-select -s "$xcode_path/Contents/Developer"
fi

echo "Xcode setup complete."
