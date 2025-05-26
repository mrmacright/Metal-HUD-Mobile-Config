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

1. Connect iPhone or iPad to Mac via USB

2. You may be promoted to "Trust This Computer" on your iPhone / iPad and "Allow accessory to connect" on Mac

3. On 1st run, macOS will block the app. Go to: System Settings > Privacy & Security > Security and click “Open Anyway” next to "Metal HUD Mobile Config was blocked…"

4. Open App (Metal HUD Mobile Config). You’ll be promoted to download Xcode 

- If you have Xcode installed, this prompt won’t appear

5. Re-open App. You’ll be promoted to install Apple files. This can take quite a while, be patient

- If you have Xcode installed, this may not appear

6. Click "List Devices" to view connected devices 

- For errors see # TROUBLESHOOTING
- Once device is paired successfully you can do all this wirelessly! 

7. Click your device in the list and it will automatically fill in "Device Identifier"

8. Open the game you want the HUD enabled for before pressing "Show Running Apps". 

9. Click "Show Running Apps" to view running Apps. 

- If developer mode is not enabled on your device you will receive "Operation failed because Developer Mode is disabled on your iPhone or iPad". Follow instructions to enable dev mode! 
- You can also click an App in the list and it will automatically fill in App Path
- You can click "Save App Path" and save path for future use

10. Close App on iPhone / iPad

11. Click "Launch App with Metal Performance HUD" to enable Metal HUD for App 

- Sometimes you may need to close the app and try again for the HUD to appear.
- Use "HUD Alignment" to change the HUD’s position on the screen by applying a custom number — note it can be a bit finicky!
- "Previous Commands" displays the last 10 commands you entered.

## Troubleshooting 

### If you're seeing "No Devices", or "The Device must be paired before it can be connected"... 

Try the following:

1. Close the Metal HUD Mobile Config

2. Agree to "Xcode and Apple SDKs Agreement" by opening file "setup_xcode.sh" and press "Agree". Close XCODE after pressing "Agree", don't continue with other installs

3. Unplug iPhone / iPad from Mac > Restart Mac > Reconnect iPhone / iPad to Mac

4. Re-open the App and hopefully your device will appear! 

Still not working? Execute the following commands in order to fix common issues.

Install Command Line Tools 
```
sudo xcode-select -s /Applications/Xcode.app" .
```

Set Xcode Path 
```
sudo xcode-select -s /Applications/Xcode.app
```

Agree to Xcode License
```
sudo xcodebuild -license
```

Run this in terminal to see if devices show. If they do, then the App should work! 
```
xcrun devicectl list devices
```


If you're using an iOS / iPadOS beta, you'll likely need to install the corresponding Xcode Beta and Command Line Tools: https://developer.apple.com/xcode/resources/ 

## Known Issues

- You can't enable the HUD system-wide on iOS / iPadOS. Unlike macOS, which supports a global HUD via MTL_HUD_ENABLED=1, Apple limits the mobile HUD to individual apps launched through tools like xcrun devicectl

- Game paths often use internal bundle names that differ from the App Store title

- Metal HUD does not work with OpenGL-based games. You may see a warning in the logs

- Compatibility issues may occur with games using MoltenVK, such as Wreckfest. You may see a warning in the logs

- Some games with anti-cheat (e.g., Warzone Mobile) may not launch with HUD. I’ve used Metal HUD since 2023 without bans in games like PUBG or Fortnite, but use at your own risk

## Other

Join my Discord server for support: https://discord.gg/RaXugyqp63

I'm not a developer... I used ChatGPT to help with development, so issues are likely to occur! 
