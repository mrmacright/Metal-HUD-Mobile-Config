# Enable Metal HUD on iPhone, iPad & Apple TV!

Launch Metal HUD instantly for games, view connected devices, customize HUD presets

<img width="300" alt="MetalHUDVideo" src="https://github.com/user-attachments/assets/affeb269-0c07-4c13-90bd-3e12c754ed25" />

- For support email: business@mrmacright.com

- [Support my work on Buy Me a Coffee](https://buymeacoffee.com/mrmacright)

## Requirements 

▶ macOS Tahoe 26.2 or later and [M1 or later](https://support.apple.com/en-au/116943)

▶ Xcode 26.5 (13GB+ free space required)

▶ [Version 2.9.2](https://github.com/mrmacright/Metal-HUD-Mobile-Config/releases/tag/2.9.2) and earlier supports Intel Macs, but future compatibility is not guaranteed

> [!NOTE]
> **Windows is not supported — This app requires Xcode and Terminal and they only run on macOS**

## Supported platforms for Metal HUD

▶ [iOS 17 or later](https://support.apple.com/en-au/guide/iphone/iphe3fa5df43/17.0/ios/17.0)

▶ [iPadOS 17 or later](https://support.apple.com/en-au/guide/ipad/ipad213a25b2/17.0/ipados/17.0)

▶ Apple TV 4K (1st gen, 2017) or later

> [!IMPORTANT]
> - System-wide HUD support is not possible — Metal HUD works per app by design on iOS, iPadOS, & tvOS  
> - Can I use this app on iPhone or iPad without a Mac? No — Metal HUD requires Xcode and Terminal, which cannot run on iOS  
> - iOS 16 or earlier is not supported as `devicectl` is unavailable

## CONNECTION HELP

### How to launch a game with Metal HUD

Apps are only detectable when already open and in the foreground.

1. Launch the game on your device
2. Keep it open in the foreground
3. Click **Show Running Games**
4. Choose your game → Launch App with Metal HUD

### Device not connecting?

If you can't connect to a device, it's likely not paired correctly. Try the following steps:

1. Connect your iPhone or iPad via USB
2. Unlock the device
3. Tap **Trust This Computer** if prompted
4. On the Mac, click **Allow** if asked to connect the accessory

> [!IMPORTANT]
> If you previously dismissed the trust prompt, reset it on the device and try again:
> - Settings → General → Transfer or Reset iPhone → Reset → Reset Location & Privacy

### How to connect to Apple TV
1. On Apple TV go to Settings > Remotes and Devices > Remote App and Devices
2. Open Xcode → Window → Devices and Simulators → Discovered
3. Pair Apple TV → enter verification code → Connect
4. Open FPS Logger → List Devices

> [!IMPORTANT]
> Apple TV HD (2015) is not supported

### Custom HUD metrics not working?

Custom metrics, position, and scale require iOS 26, iPadOS 26, or tvOS 26 or later.

iOS 17–18 only support the Default preset.

### Connection states

**Available (paired + wireless)**  
Paired and reachable over Wi-Fi — no USB cable needed.

▶ Connected

Device connected and ready.

▶ Available (preparing) 

Device is visible, but Xcode may still be preparing it or requires pairing. Metal HUD may still work.

▶ Available (pairing required)

Device is visible but may need pairing or trust confirmation. Connect via USB and tap Trust if prompted.

▶ Connected (limited support)

Xcode may still be preparing the device. If you can't connect, install the latest Xcode beta and switch to it:
```bash
sudo xcode-select -s /Applications/Xcode-beta.app/Contents/Developer
```

▶ Unavailable

Device is offline, turned off, or not reachable on the same Wi-Fi network.

▶ Unsupported

This device does not support Metal HUD.

### Why isn't Game Mode turning on?

Game Mode turns on automatically for supported games. If it isn't turning on, the game likely doesn't support Game Mode yet. This can only be enabled by the game developer in Xcode — external tools cannot force it on.

### Is it safe to use with online games?

Metal Performance HUD has been widely used in games like PUBG MOBILE, COD: Mobile, and Genshin Impact. However, some anti-cheat systems may detect it and block the game from launching.

Use at your own risk, especially in competitive online games.

### Why isn't Metal HUD showing?

If the game launches but the Metal HUD does not appear, the game is likely not using Metal graphics (for example, it may use OpenGL instead). Metal HUD only works with games powered by Metal.

### Why is a game called something different than its actual name?

This app detects the game's internal app name from the App Store package. Some developers do not use the official game title internally, so certain games may appear with generic names like “Game”.

### Xcode license

Normally the Xcode license is accepted automatically on first launch. If it possibly failed, run this once in Terminal:

```bash
sudo xcodebuild -license
```

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

## Special thanks

<a href="https://www.elverils.com">
  <img src="https://github.com/user-attachments/assets/03bb3fe6-1b72-4cfb-99ef-c25b0bf147c9" alt="Elverils logo" width="450" />
</a>

[Nat Brown](https://x.com/natbro?lang=en)

[LordOfTheUnicorn](https://github.com/LordOfTheUnicorn)

and to many others who have helped! Thanks

## AI Support
Built with the help of AI Tools