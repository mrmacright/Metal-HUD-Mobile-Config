# Metal Hud Mobile Config

<img width="125" height="125" alt="Icon" src="https://github.com/user-attachments/assets/9504691b-983a-40b5-94fd-2569c4967da0" />

### A handy tool to operate the Metal Performance HUD on iPhone & iPad, without tinkering with Terminal

- Lists connected devices and shows only running games (hides system apps)

- Instantly launch Metal HUD for selected games, with HUD presets, location and scale options!

- Save frequently used games and view previously launched games for easy re-use

- View logs directly from the interface for better debugging and tracking

## Requirements 

✅ Mac (macOS 15.3 or later) 

❌ Windows is not supported (needs macOS tools like xcrun devicectl)

❌ System-wide HUD support is not available, Metal HUD works per app on iPhone & iPad!

### Supported devices for Metal HUD

✅ iOS/iPadOS 26 (best experience)

✅ iOS/iPadOS 16+

✅ Apple TV HD (2015+) – see Apple TV section

## Launching The App
<img width="561" height="471" alt="UI_Screenshot" src="https://github.com/user-attachments/assets/0c7ebf6c-58b4-46d5-a336-03c86da38386" />

### iPhone/iPad

1. Connect iPhone/iPad to Mac via USB

- You may need to tap "Trust This Computer" on iPhone/iPad and "Allow accessory" on Mac

2. Download Xcode if prompted

3. Re-open app; may need to install Apple files (takes time)

### Apple TV

1. Xcode → Window → Devices and Simulators → Discovered

2. Pair Apple TV → enter verification code → Connect

3. Open Metal HUD Mobile Config → List Devices
- You might need to re-pair after tvOS/macOS updates

## Using The App

1. Click List Devices (wireless operation after pairing)

2. Open the game on your iPhone or iPad before pressing "Show Running Games" 

3. Click "Show Running Games" to see games running on your device. 

- If Developer Mode is disabled, you’ll see an error. Enable dev mode following the instructions

4. Click the game you want HUD enabled for and then click Launch App with Metal HUD
- Try HUD Presets, HUD Locations, and HUD Scale (iOS/iPadOS 26 required)
- Close and retry app if HUD doesn’t appear

## Troubleshooting 

### Device not appearing?

1. Close the app

2. Unplug, restart Mac & device, reconnect
- Turning Wi-Fi off and back on may help

4. Re-open the app

### Still not working? Run the following in Terminal:

Install Command Line Tools
```
xcode-select --install
```
Check if XCODE is installed:
```
xcode-select -p
```
Set Xcode Path 
```
sudo xcode-select -s /Applications/Xcode.app
```
Agree to Xcode License
```
sudo xcodebuild -license
```
Reset Xcode Path (if things break)
```
sudo xcode-select -r
```

## Known Issues

- Game names may differ from App Store names

- Metal HUD does not work with OpenGL-based games

## Manual commands in terminal

List devices:
```
xcrun devicectl list devices
```

Find running apps:
```
xcrun devicectl device info processes --device <DEVICE_UDID> | grep 'Bundle/Application'
```

Launch with Default HUD:
```
xcrun devicectl device process launch \
  -e '{"MTL_HUD_ENABLED": "1"}' \
  --console \
  --device <DEVICE_UDID> \
  "/private/var/containers/Bundle/Application/UUID/AppName.app/"
```

Custom HUD location:
```
xcrun devicectl device process launch \
    --device <device-udid> \
    -e 'MTL_HUD_ENABLED=1' \
    -e 'MTL_HUD_ALIGNMENT=top-right' \
    "/private/var/containers/Bundle/Application/UUID/AppName.app/AppExecutable"
```

Full HUD customization:
```
xcrun devicectl device process launch \
  -e '{"MTL_HUD_ENABLED": "1", "MTL_HUD_ELEMENTS": "device,layersize,layerscale,gamemode,memory,refreshrate,fps,frameinterval,gputime,thermal,frameintervalgraph,presentdelay,metalcpu,shaders", "MTL_HUD_ALIGNMENT": "<alignment>", "MTL_HUD_SCALE": "<scale>"}' \
  --console \
  --device <device-udid> \
  "/private/var/containers/Bundle/Application/<app-uuid>/<app-name>.app"
```

## Other

Join my Discord server for support: https://discord.gg/RaXugyqp63

Support my work: https://buymeacoffee.com/mrmacright
