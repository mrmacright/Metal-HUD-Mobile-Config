# Easily enable Metal HUD on iPhone, iPad & Apple TV!

<p float="left">
  <img src="https://github.com/user-attachments/assets/75d1ed77-c9cc-4134-9268-21aea8c16fe6" width="700" height="700" />

- Lists connected devices & shows only running games (hides system apps)
- Instantly launch Metal HUD for selected games
- Choose HUD presets, locations, & scale **(Requires iOS 26 / iPadOS 26 / tvOS 26)**
- Save & quickly relaunch your favorite games with Metal HUD
- View logs directly from the interface for better debugging and tracking

## PLATFORM SUPPORT 

✅ Mac [(macOS Sequoia 15.6 or later) ](https://support.apple.com/en-au/120282) | 20-30 GB free space recommended

❌ Windows support is impossible — Xcode is required & only runs on macOS

❌ System-wide HUD support is not possible — Metal HUD works per app by design on iOS, iPadOS & tvOS

❌ Can I use this app on iPhone or iPad without a Mac? No — Metal HUD requires Xcode and Terminal, which can’t run on iOS

### SUPPORTED DEVICES FOR METAL HUD

✅ iOS / iPadOS 16+ (iPhone 8 or later / iPads from 2016 or later)

✅ Apple TV HD (2015) or later

## LAUNCHING THE APP 
<img width="561" height="471" alt="UI_Screenshot" src="https://github.com/user-attachments/assets/048fe425-97ef-482f-a2b6-1c3dd23f7d77" />

1. Click List Devices (wireless operation after pairing)
2. Open the game on your device before pressing "Show Running Games" 
3. Click "Show Running Games" to see games running on your device. 
4. Click the game you want HUD enabled for and then click Launch App with Metal HUD
- Try HUD Presets, HUD Locations, and HUD Scale **(Requires iOS 26 / iPadOS 26 / tvOS 26)**

## CONNECTION HELP

### DEVICE NOT APPEARING?

If you see **NO DEVICES WERE FOUND**, follow the steps below in order.

---

### STEP 1 — CHECK USB & TRUST (MOST CASES)

In most cases, the device is simply not trusted or not fully connected.

Do the following:

- Connect your iPhone or iPad via USB  
- Unlock the device  
- On the device, tap **Trust This Computer** if prompted  
- On the Mac, click **Allow** if asked to connect the accessory  

If you previously dismissed the trust prompt, reset it on the device:

Settings → General → Transfer or Reset iPhone → Reset → Reset Location & Privacy

After doing this, quit and relaunch **Metal HUD Mobile Config** and check again.

If the device still does not appear, continue to Step 2.

---

### STEP 2 — FORCE DEVICE PREP USING XCODE (FALLBACK)

Sometimes macOS has not finished preparing the device, especially on first connection or after iOS/macOS updates.

1. Open **Xcode → Window → Devices and Simulators**  
2. Confirm your device appears as connected  

<img src="https://github.com/user-attachments/assets/d02a60b0-dec7-4852-94e4-aeb9b9989004" width="350" />

If Xcode shows **Connecting to device** or **Copying shared cache symbols**, wait until this process completes.

<img src="https://github.com/user-attachments/assets/ad1995ef-1b16-473d-b827-9eeedff3255c" width="600" />
<img src="https://github.com/user-attachments/assets/29480f4c-2b41-4773-a27b-c02eb8f77286" width="600" />

Once finished, return to **Metal HUD Mobile Config** — the device should now appear.

---

### STEP 3 - XCODE LICENSE (RARE)

Normally the Xcode license is accepted automatically on first launch. If it possibly failed, run this once in Terminal:

```bash
sudo xcodebuild -license
```

### NO GAMES DETECTED?

If you see **NO GAMES DETECTED** or **NO USER APPS RUNNING**, this means:

- The device is connected and responding correctly
- No user games are currently running

**Fix:**
1. Launch a game on the device
2. Ensure the game is in the foreground
3. Click **Show Running Games** again
   
---

### DEVICE VISIBLE BUT NOT PAIRED?

If you see **DEVICE NOT PAIRED**, try the following:

- Unlock the device
- Unplug and reconnect the USB cable
- Tap **Trust This Computer** if prompted
- Click **Show Running Games** again

---

### How to connect to Apple TV

1. On Apple TV go to Settings > Remotes and Devices > Remote App and Devices
2. Download Xcode
3. Open Xcode → Window → Devices and Simulators → Discovered
4. Pair Apple TV → enter verification code → Connect
5. Open Metal HUD Mobile Config → List Devices
- You might need to re-pair after tvOS/macOS updates

---

### New iPhone or iPad isn't connecting?

If your new iPhone or iPad isn’t appearing or showing any games, it’s usually because very new Apple devices (like upcoming iPhones or iPads) require a newer version of Xcode and Command Line Tools than what’s currently available from App Store. 

You need to install the latest XCODE beta and Command Line tools here: https://developer.apple.com/download/ 

Switch to the latest Xcode Beta and its Command Line Tools in Terminal:
```
sudo xcode-select -s /Applications/Xcode-beta.app/Contents/Developer
```
Then verify your setup:
```
xcode-select -p
xcodebuild -version
```
You should see a path ending in `Xcode-beta.app/Contents/Developer` and a recent build version (for example, `Xcode 26.x (or newer)`

## Known Issues

- Game names may differ from App Store names

- Metal HUD does not work with OpenGL-based games
  
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





