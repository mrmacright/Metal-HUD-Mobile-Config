![MyIcon](https://github.com/user-attachments/assets/0fbc1c8f-7eb9-4602-8104-0c767aacae81)

# Metal Hud Mobile Config

### Enable Metal Performance HUD on iPhone and iPad without using Terminal or relying on jailbreaks or exploits

- Quickly list connected devices and display only relevant running apps (hides system/background apps)

- Instantly launch the Metal HUD for selected apps, with customizable HUD alignment

- Save frequently used app paths and view command history for easy re-use

- View logs directly from the interface for better debugging and tracking

## Requirements 

### You need a Mac 
✅ Requires macOS 15.2 or later (Only tested on Apple silicon Macs)

✅ Requires Xcode app

❌ Windows is not supported, do not make requests for it! macOS exclusive tools like xcrun devicectl are required that are not available on Windows

### Supported devices for Metal HUD
✅ iOS 16 or later / iPadOS 16 or later. Yes it works with iOS 18+ / iPadOS 18+

✅ Apple TV HD (2015) and newer. The setup process is more involved; please refer to the # Apple TV section below.



## Launching & Using The App


<img width="605" alt="UI Screenshot" src="https://github.com/user-attachments/assets/1b70bd55-e84f-47a3-801f-42473f3ecb9f" />

1. Connect iPhone or iPad to Mac via USB

2. You may be promoted to "Trust This Computer" on your iPhone / iPad and "Allow accessory to connect" on Mac

3. On the first run, macOS may block the app. To allow it:

- Go to System Settings > Privacy & Security > Security, then click “Open Anyway” next to "Metal HUD Mobile Config was blocked…"

4. Open App (Metal HUD Mobile Config). You’ll be promoted to download Xcode 

- If you have Xcode installed, this prompt won’t appear

5. Re-open App. You’ll be promoted to install Apple files. This can take quite a while, be patient

- If you have Xcode installed, this may not appear

6. Click "List Devices" to view connected devices 

- For errors see # Troubleshooting
- Once device is paired successfully you can do all this wirelessly! 

7. Click a device in the list to automatically fill in the “Device Identifier.”

8. Open the game you want the HUD enabled for before pressing "Show Running Apps"

9. Click "Show Running Apps" to see which apps are running. It might take some time if you have a lot of apps on your device! 

- If developer mode is not enabled on your device you will receive "Operation failed because Developer Mode is disabled on your iPhone or iPad". Follow instructions to enable dev mode! 
- Click an App in the list to automatically fill in the “App Path”
- You can click "Save App Path" to save the path for future use

10. Close App on iPhone / iPad

11. Click "Launch App with Metal Performance HUD" to enable Metal HUD for App 

- Sometimes you may need to close the app and try again for the HUD to appear
- Use "HUD Alignment" to change the HUD’s position on the screen by applying a custom number — note it can be a bit finicky!
- "Previous Commands" displays the last 10 commands you entered

## Troubleshooting 

### If your device is not appearing under List Devices, try the following:

1. Close the Metal HUD Mobile Config

2. Agree to "Xcode and Apple SDKs Agreement" by opening file "setup_xcode.sh" and press "Agree". Close XCODE after pressing "Agree", don't continue with other installs

3. Unplug iPhone / iPad from Mac > Restart Mac > Reconnect iPhone / iPad to Mac

4. Re-open the App and hopefully your device will appear! 

### Still not working? Open Terminal and run the following commands to fix common issues.

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

- If you already have Xcode installed in a different location (e.g., Downloads or Desktop), the app might not detect it. Please move Xcode to the Applications folder. This will be fixed in a future version!

- Metal HUD does not work with OpenGL-based games. You may see a warning in the logs

- Compatibility issues may occur with games using MoltenVK, such as Wreckfest. You may see a warning in the logs

- Some games with anti-cheat (e.g., Warzone Mobile) may not launch with HUD. I’ve used Metal HUD since 2023 without bans in games like PUBG or Fortnite, but use at your own risk

## Apple TV

Enabling Metal HUD on Apple TV is a little more involved compared to iPhone or iPad—you’ll need to connect the device using the Xcode app.

Steps: 

1. Open Xcode and go to “Window” and find “Devices and Simulators”

2. Go to “Discovered”, find your Apple TV.
- If you don’t see it make sure your Apple TV is on the same Wi-Fi Network.

3. Click “Pair”

4. Enter verification code displayed on Apple TV to finish pairing. Click “Connect”

5. It should now appear as “Connected”

6. Open "Metal HUD Mobile Config" and Click "List Devices" and it should appear.

- After updating to a new version of tvOS, re-pairing your Apple TV device might be required 


## Other

Join my Discord server for support: https://discord.gg/RaXugyqp63

I'm not a developer... I used ChatGPT to help with development, so issues are likely to occur! 

