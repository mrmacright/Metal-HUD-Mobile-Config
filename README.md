# Metal HUD Mobile Config
### Manage Metal Performance HUD on iPhone, iPad & Apple TV—no Terminal needed

<p float="left">
  <img src="https://github.com/user-attachments/assets/75d1ed77-c9cc-4134-9268-21aea8c16fe6" width="700" height="700" />

- Lists connected devices and shows only running games (hides system apps)
- Instantly launch Metal HUD for selected games
- Choose HUD presets, locations, and scale **(Requires iOS 26 / iPadOS 26 / tvOS 26)**
- Save and quickly relaunch your favorite games with Metal HUD
- View logs directly from the interface for better debugging and tracking

## Requires 

✅ Mac (macOS 15.3 or later) 

❌ Windows is not supported (needs macOS tools like xcrun devicectl)

❌ System-wide HUD support is not available, Metal HUD works per app on iPhone, iPad and Apple TV!

### Supported devices for Metal HUD

✅ iOS / iPadOS 16+ (iPhone 8 or later / iPads from 2016 or later)

✅ Apple TV HD (2015) or later

## Launching The App 
<img width="561" height="471" alt="UI_Screenshot" src="https://github.com/user-attachments/assets/d004be79-9351-4314-a1a1-f15206364d56" />

### iPhone / iPad

1. Connect iPhone or iPad to Mac via USB
- You may need to tap "Trust This Computer" on iPhone/iPad and "Allow accessory" on Mac
2. Launch Metal HUD Mobile Config
- If prompted, download Xcode and reopen (Apple files may take a while).

### Apple TV

1. Download Xcode
2. Open Xcode → Window → Devices and Simulators → Discovered
3. Pair Apple TV → enter verification code → Connect
4. Open Metal HUD Mobile Config → List Devices
- You might need to re-pair after tvOS/macOS updates

## Using The App

1. Click List Devices (wireless operation after pairing)
2. Open the game on your device before pressing "Show Running Games" 
3. Click "Show Running Games" to see games running on your device. 
- If Developer Mode is disabled, you’ll see an error. Enable dev mode following the instructions
4. Click the game you want HUD enabled for and then click Launch App with Metal HUD
- Try HUD Presets, HUD Locations, and HUD Scale **(Requires iOS 26 / iPadOS 26 / tvOS 26)**
- Close and retry app if HUD doesn’t appear

## Troubleshooting 

### Device not appearing?

1. Close Metal HUD Mobile Config
2. Unplug iPhone or iPad from Mac and reconnect
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
  
- If you’ve manually adjusted Metal HUD Metrics on your iPhone/iPad under Developer → Graphics HUD (iOS 26 / iPadOS 26 / tvOS 26), the Default Metal HUD preset will launch using your custom metrics. Press **Reset** on your device to revert to the default metrics

## Manual commands in terminal

**List devices**:
```
xcrun devicectl list devices
```

**Find running apps**:
```
xcrun devicectl device info processes --device <DEVICE_UDID> | grep 'Bundle/Application'
```

**Launch with Default HUD**:
```
xcrun devicectl device process launch \
  -e '{"MTL_HUD_ENABLED": "1"}' \
  --console \
  --device <DEVICE_UDID> \
  "/private/var/containers/Bundle/Application/UUID/AppName.app/"
```

**Custom HUD Location**: 

Available options are:
`topleft`, `topcenter`, `topright`, `centerleft`, `centered`, `centerright`, `bottomright`, `bottomcenter`, `bottomleft`
```
xcrun devicectl device process launch \
    --device <device-udid> \
    -e 'MTL_HUD_ENABLED=1' \
    -e 'MTL_HUD_ALIGNMENT=<position>' \
    "/private/var/containers/Bundle/Application/UUID/AppName.app/
```

**Custom HUD Scale**:

0.0–1.0. Default: 0.2
```
xcrun devicectl device process launch \
  -e '{"MTL_HUD_ENABLED": "1", "MTL_HUD_SCALE": "<scale>"}' \
  --console \
  --device <device-udid> \
  "/private/var/containers/Bundle/Application/UUID/AppName.app/"
```
**Full HUD customization**:
```
xcrun devicectl device process launch \
  -e '{"MTL_HUD_ENABLED": "1", "MTL_HUD_ELEMENTS": "device,layersize,layerscale,memory,refreshrate,thermal,gamemode,fps,fpsgraph,framenumber,gputime,frameinterval,frameintervalgraph,frameintervalhistogram,presentdelay,metalcpu,gputimeline,shaders,metalfx", "MTL_HUD_ALIGNMENT": "<position>", "MTL_HUD_SCALE": "<scale>"}' \
  --console \
  --device <device-udid> \
  "/private/var/containers/Bundle/Application/UUID/AppName.app/"
```
**Unpair device**:
```
xcrun devicectl manage unpair --device <DEVICE-UDID>
```

## Other

[Join my Discord server for support](https://discord.gg/RaXugyqp63)

[Support my work on Buy Me a Coffee](https://buymeacoffee.com/mrmacright)

## Special thanks

<a href="https://www.elverils.com">
  <img src="https://github.com/user-attachments/assets/03bb3fe6-1b72-4cfb-99ef-c25b0bf147c9" alt="Elverils logo" width="450" />
</a>

[Nat Brown](https://x.com/natbro?lang=en)

[LordOfTheUnicorn](https://github.com/LordOfTheUnicorn)

and to many others who have helped! Thanks





