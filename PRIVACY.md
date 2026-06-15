# Privacy Policy for FPS Logger

*Last updated: May 31, 2026*

## Overview

FPS Logger ("the App") is a macOS developer tool created by Stewie (MrMacRight). This privacy policy explains how the App handles data.

FPS Logger is available in two versions:

- **App Store build** — sandboxed, distributed via the Mac App Store
- **GitHub build** — unsandboxed, distributed directly from GitHub

Differences between builds are noted where relevant below.

## Data Collected

### Analytics (Opt-In)

If you opt in to analytics, the following data is sent to a private Google Sheets endpoint each time you test an app with the HUD:

- Timestamp
- App version
- Device model (display name and terminal format)
- Wireless state (display name and terminal format)
- App name tested (display name and terminal format)
- App icon URL (fetched from Apple's iTunes Search API)

Analytics collection is opt-in and can be disabled at any time in the App's settings. Both builds include analytics.

### App Reports (Optional, User-Initiated — App Store build only)

When you submit a report via the right-click context menu, the following data is sent to the same private Google Sheets endpoint:

- Report type (one of: Report Wrong Icon, Report Wrong Name, Report: Not a Game, Report: Metal HUD Supported, Report: Metal HUD Unsupported)
- App name (display name and terminal format)
- App icon URL

These reports are submitted only when you explicitly choose to send one. The right-click report menu is not present in the GitHub build.

### Local Storage

The following data is stored locally on your Mac in `~/Library/Application Support/com.stewie.metalhud/data.json` and is never transmitted:

- Connected device identifiers, names, and models
- Command history (including HUD settings used per session)
- Custom app name mappings
- App preferences (hidden/pinned apps, window geometry, etc.)
- Mac hardware information (model name, chip, memory, macOS version) logged once at launch

App icons are cached locally in `~/Library/Caches/com.stewie.metalhud/icons/`.

## Data Not Collected

The App does not collect:

- Personal information (name, email, phone number, or account data)
- Location data
- Advertising or tracking data

## Network Usage

The App makes network requests solely to:

- Fetch app icons from Apple's iTunes Search API
- Transmit analytics data (opt-in only) to a private Google Sheets endpoint
- Transmit user-submitted app reports to a private Google Sheets endpoint (App Store build only)
- Check for app updates via the GitHub Releases API (GitHub build only — App Store build receives updates through the Mac App Store)

No data is shared with third-party advertisers or data brokers.

## Contact

For privacy questions: business@mrmacright.com
