# Enable Metal HUD on iPhone, iPad & Apple TV!

Launch Metal HUD instantly for games, view connected devices, customize HUD presets

<img width="300" alt="MetalHUDVideo" src="https://github.com/user-attachments/assets/affeb269-0c07-4c13-90bd-3e12c754ed25" />

## Requirements 

▶ macOS Tahoe 26.2 or later and [M1 or later](https://support.apple.com/en-au/116943)

▶ Xcode 26.4.1 (20–30 GB free space recommended)

▶ [Version 2.9.2](https://github.com/mrmacright/Metal-HUD-Mobile-Config/releases/tag/2.9.2) and earlier supports Intel Macs, but future compatibility is not guaranteed

> [!NOTE]
> **Windows is not supported — This app requires Xcode and Terminal and they only run on macOS**

## Supported platforms for Metal HUD

▶ [iOS 17 or later](https://support.apple.com/en-au/guide/iphone/iphe3fa5df43/17.0/ios/17.0)

▶ [iPadOS 17 or later](https://support.apple.com/en-au/guide/ipad/ipad213a25b2/17.0/ipados/17.0)

▶ Apple TV HD (2015) or later

> [!IMPORTANT]
> - System-wide HUD support is not possible — Metal HUD works per app by design on iOS, iPadOS, & tvOS  
> - Can I use this app on iPhone or iPad without a Mac? No — Metal HUD requires Xcode and Terminal, which cannot run on iOS  
> - iOS 16 or earlier is not supported as `devicectl` is unavailable

### How to connect to Apple TV
1. On Apple TV go to Settings > Remotes and Devices > Remote App and Devices
2. Open Xcode → Window → Devices and Simulators → Discovered
3. Pair Apple TV → enter verification code → Connect
4. Open Metal HUD Mobile Config → List Devices

> [!IMPORTANT]
> You might need to re-pair after tvOS/macOS updates

## CONNECTION HELP

### No games detected?
Apps are only detectable when already open and in the foreground: 
1. Launch the game on your device  
2. Keep it open in the foreground  
3. Click **Show Running Games** again  

### Device not connecting?

If you can't connect to a device, it's likely not paired correctly. Try the following steps:

1. Connect your iPhone or iPad via USB  
2. Unlock the device  
3. On the device, tap **Trust This Computer** if prompted  
4. On the Mac, click **Allow** if asked to connect the accessory  

> [!IMPORTANT]
> If you previously dismissed the trust prompt, reset it on the device and try again:
> - Settings → General → Transfer or Reset iPhone → Reset → Reset Location & Privacy

### Check connection in Xcode

Sometimes macOS has not finished preparing the device, especially on first connection or after iOS/macOS updates.

1. Open Xcode → Window → Devices and Simulators

2. Wait for Xcode to finish preparing the device

<img src="https://github.com/user-attachments/assets/ad1995ef-1b16-473d-b827-9eeedff3255c" width="600" />

<img src="https://github.com/user-attachments/assets/29480f4c-2b41-4773-a27b-c02eb8f77286" width="600" />

3. Confirm your device is connected, then return to Metal HUD Mobile Config

<img src="https://github.com/user-attachments/assets/d02a60b0-dec7-4852-94e4-aeb9b9989004" width="350" />

### Xcode license

Normally the Xcode license is accepted automatically on first launch. If it possibly failed, run this once in Terminal:

```bash
sudo xcodebuild -license
```

### Device shows “Connected (limited support)”

If your device shows **Connected (limited support)**, Xcode may still be preparing the device or you may need a newer Xcode and command-line tools version (common with beta or very new iOS versions).

1. Install the latest Xcode beta and command-line tools: https://developer.apple.com/download/ 

2. Switch to Xcode Beta in Terminal:
```
sudo xcode-select -s /Applications/Xcode-beta.app/Contents/Developer
```
3. Verify your setup:
```
xcode-select -p
xcodebuild -version
```

> [!IMPORTANT]
> You should see a path ending in `Xcode-beta.app/Contents/Developer` and a recent build version (for example, `Xcode 26.x` or newer)

## Known issues

- Game names may differ from App Store names

- Metal HUD does not work with games not powered by Metal, for example OpenGL-based games
  
- Some games anti-cheat might not work with Metal HUD or could possibly ban you
  
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

**Custom HUD location**: 

Available options are:
`topleft`, `topcenter`, `topright`, `centerleft`, `centered`, `centerright`, `bottomright`, `bottomcenter`, `bottomleft`
```
xcrun devicectl device process launch \
    --device <device-udid> \
    -e 'MTL_HUD_ENABLED=1' \
    -e 'MTL_HUD_ALIGNMENT=<position>' \
    "/private/var/containers/Bundle/Application/UUID/AppName.app/
```

**Custom HUD scale**:

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

## ChatGPT
Built with the help of ChatGPT
