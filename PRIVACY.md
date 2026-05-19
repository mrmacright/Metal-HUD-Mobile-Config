# Privacy Policy for Metal HUD Mobile Config

*Last updated: May 19, 2026*

## Overview

Metal HUD Mobile Config ("the App") is a macOS developer tool created by Stewie (MrMacRight). This privacy policy explains how the App handles data.

## Data Collected

### Crash Reporting
Crash logs and performance diagnostics are collected via Apple's built-in crash reporting system.

### Analytics (Opt-In)
If you opt in to analytics, the following data is sent to a private Google Sheets endpoint each time you test an app with the HUD:

- Timestamp
- Device model (e.g. iPhone18,2) and display name (e.g. iPhone 17 Pro Max)
- Device connection state (e.g. USB / Wi-Fi)
- App name and bundle identifier of the app being tested
- App icon URL (fetched from Apple's iTunes Search API)

Analytics collection is opt-in and can be disabled at any time in the App's settings.

### App Reports (Optional, User-Initiated)
When you submit a report via "Report Wrong Icon/Name" or similar menu options, the following data is sent to the same private Google Sheets endpoint:

- Report type (e.g. Wrong Icon, Wrong Name, Not a Game, HUD Supported/Unsupported)
- App name and bundle identifier
- App icon URL

These reports are submitted only when you explicitly choose to send one.

### Local Storage
The following data is stored locally on your Mac in `~/Library/Application Support/com.stewie.metalhud/data.json` and is never transmitted:

- Connected device identifiers, names, and models
- Command history (including HUD settings used per session)
- Custom app name mappings
- App preferences (hidden/pinned apps, window geometry, etc.)

App icons are cached locally in `~/Library/Caches/com.stewie.metalhud/icons/`.

## Data Not Collected

The App does not collect:

- Personal information (name, email, phone number, or account data)
- Location data
- Advertising or tracking data

## Network Usage

The App makes network requests solely to:

- Fetch app icons from Apple's iTunes Search API
- Check for app updates via the GitHub API
- Transmit analytics data (opt-in only) and user-submitted app reports to a private Google Sheets endpoint

No data is shared with third-party advertisers or data brokers.

## Contact

For privacy questions: business@mrmacright.com
