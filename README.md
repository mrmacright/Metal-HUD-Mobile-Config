![MyIcon](https://github.com/user-attachments/assets/0fbc1c8f-7eb9-4602-8104-0c767aacae81)

# Metal Hud Mobile Config

### A handy tool to operate the Metal Performance HUD on iPhone & iPad, without tinkering with Terminal

- Quickly list connected devices and display only relevant running apps (hides system/background apps)

- Instantly launch the Metal HUD for selected apps, with customizable HUD alignment

- Save frequently used app paths and view command history for easy re-use

- View logs directly from the interface for better debugging and tracking

## Requirements 
✅ macOS 15.2 or later (Only tested on Apple silicon Macs)

✅ Xcode 

✅ iOS 16 or later / iPadOS 16 or later. Yes it works with iOS 18+ / iPadOS 18+

❌ Windows is not supported, do not make requests for it! macOS exclusive tools like xcrun devicectl are required that are not available on Windows

## Launching & Using The App


<img width="605" alt="UI Screenshot" src="https://github.com/user-attachments/assets/1b70bd55-e84f-47a3-801f-42473f3ecb9f" />

1. Connect iPhone or iPad to Mac via USB. You may be promoted to "Trust This Computer" on your device and "Allow accessory to connect" on Mac. "Trust"!

2. On 1st run, macOS will block the app. Go to: System Settings > Privacy & Security > Security and click “Open Anyway” next to "Metal HUD Mobile Config was blocked…"

3. Open App (Metal HUD Mobile Config). You’ll be promoted to download Xcode. Install Xcode! 

- If you have Xcode installed, this prompt won’t appear

4. Re-open App. You’ll be promoted to install Apple files. This can take quite a while, be patient.

- If you have Xcode installed, this may not appear

5. Click "List Devices" to view connected devices. 

- For errors see # TROUBLESHOOTING
- Once device is paired successfully you can do all this wirelessly! 

6. Click your device in the list and it will automatically fill in "Device Identifier" 

7. Click "Show Running Apps" to view running Apps. Open desired game before pressing "Show Running Apps"! 

- If developer mode is not enabled on your device you will receive "Operation failed because Developer Mode is disabled on your iPhone or iPad". Follow instructions to enable dev mode! 
- You can also click an App in the list and it will automatically fill in App Path
- You can click "Save App Path" and save path for future use

8. Close App on iPhone / iPad

9. Click "Launch App with Metal Performance HUD" to enable Metal HUD for App 

- Sometimes you need to close app and re-try for HUD to appear
- You can also use "HUD Alignment" to change HUD position on screen. Apply a custom number. It's very finicky! 
- "Previous Commands" will show last 10 commands entered

## Troubleshooting 

1. If you're seeing "No Devices", or "The Device must be paired before it can be connected"... close the App

2. You might need to Agree to "Xcode and Apple SDKs Agreement" for the App to work. Open "setup_xcode.sh" and press Agree. Close XCODE after pressing "Agree"

3. Unplug iPhone / iPad from Mac > Restart Mac > Reconnect iPhone / iPad to Mac

4. Re-open the App and hopefully your device will appear! 

- You can also try running in terminal
```
  sudo xcode-select -s /Applications/Xcode.app" .
```

This might fix Xcode installation issues. Then try running "xcrun devicectl list devices" in terminal to see if devices show. If they do, then the App should work! 

- If you're using an iOS / iPadOS beta, you'll likely need to install the corresponding Xcode Beta and Command Line Tools: https://developer.apple.com/xcode/resources/ 

## Known Issues

- You can't enable the HUD system-wide on iOS / iPadOS. Unlike macOS, which supports a global HUD via MTL_HUD_ENABLED=1, Apple limits the mobile HUD to individual apps launched through tools like xcrun devicectl

- Game paths often use internal bundle names that differ from the App Store title

- Metal HUD does not work with OpenGL-based games. You may see a warning in the logs

- Compatibility issues may occur with games using MoltenVK, such as Wreckfest. You may see a warning in the logs

- Some games with anti-cheat (e.g., Warzone Mobile) may not launch with HUD. I’ve used Metal HUD since 2023 without bans in games like PUBG or Fortnite, but use at your own risk

## Other

Join my Discord server for support: https://discord.gg/RaXugyqp63

I'm not a developer... I used ChatGPT to help with development, so issues are likely to occur! 
