# ==========================================================
#  METAL HUD MOBILE CONFIG 
#  Author: Stewie (MrMacRight)
#  Purpose: iOS device management & Metal HUD launcher GUI
#  Platform: macOS Sequoia 15.6+
# ==========================================================

# === IMPORTS AND INITIAL SETUP ===
import tkinter as tk
from tkinter import Tk, ttk, scrolledtext, messagebox, simpledialog
import subprocess
import re
import os
import sys
import threading
import json
import locale   
import platform
import time
import signal
from tkinter.ttk import Progressbar

process = None

# === MACOS VERSION CHECK ===
def check_macos_version(min_version="15.6"):
    if sys.platform != "darwin":
        return  
    
    ver_tuple = tuple(int(x) for x in platform.mac_ver()[0].split("."))
    min_tuple = tuple(int(x) for x in min_version.split("."))

    if ver_tuple < min_tuple:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Unsupported macOS Version",
            f"This app requires macOS Sequoia 15.6 or later.\n"
            f"You are running {platform.mac_ver()[0]}"
        )
        sys.exit(1)

check_macos_version()

# === ENVIRONMENT VARIABLES AND GLOBAL FLAGS ===
os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ["LANG"] = "en_US.UTF-8"

DEVICE_INFO_CACHE = {}  

WARNING_SHOWN = False  
OPEN_GAME_WARNING_SHOWN = False
WARZONE_WARNING_SHOWN = False
FARLIGHT_WARNING_SHOWN = False

# === LOG AND DEVICE DETECTION HELPERS ===
WARZONE_LOG_INDICATORS = [
    "telemetry.codefusion.technology",
    "codefusion.technology",
    "telemetry.codefusion",
    "app terminated due to signal 10",
    "acquired tunnel connection to device",
]

def detect_warzone_anti_cheat(output: str) -> bool:
    """
    Return True only if the output matches known Warzone anti-cheat patterns:
    1. Connection to telemetry.codefusion.technology
    2. App terminated due to signal 10
    """
    if not output:
        return False

    text = output.lower()
    if "telemetry.codefusion.technology" in text and "app terminated due to signal 10" in text:
        return True

    return False

FARLIGHT_LOG_INDICATORS = [
    "device anomaly detected",                
    "temporarily unable to access the game",  
    "0-3-2048",                                
    "accesskeyid not found",                  
    "solarlandclient",                         
    "farlight"                                
]

def detect_farlight_issue(output: str) -> bool:
    """
    Return True if any known Farlight/SolarlandClient log indicator appears.
    Called per-line as logs stream in.
    """
    if not output:
        return False
    text = output.lower()
    for indicator in FARLIGHT_LOG_INDICATORS:
        if indicator in text:
            return True
    return False

APP_DISPLAY_SUFFIX = {
    "ShadowTrackerExtra": "(PUBG MOBILE)",
    "scimitar": "(Assassin's Creed Mirage)",
    "SolarlandClient": "(Farlight 84)",
    "hkrpg": "(Honkai: Star Rail)",
    "bh3oversea": "(Honkai Impact 3)",
    "X6Game": "(Infinity Nikki)",
   "ExtremeGame": "(PUBG: New State)"
}

# === MISSING DDI DETECTION ===
MISSING_DDI_WARNING_SHOWN = False

DDI_ERROR_KEYWORDS = [
    "developer disk image could not be mounted",
    "missing the requested variant for this device",
    "kamdmobileimagemounterpersonalizedbundlemissingvarianterror",
    "unable to find a valid ddi for the ios platform",
    "unable to find a developer disk image to use for the ios platform",
    "ddi not found",
    "0xe800010f",
    "com.apple.mobiledevice error -402652913",
    "com.apple.dt.coredeviceerror error 12001",
    "com.apple.dt.coredeviceerror error 12007",
]

def get_current_device_model() -> str:
    """
    Returns the Model string for the currently selected UDID, e.g. 'iPad (iPad17,1)'.
    Falls back to UDID or '' if unknown.
    """
    udid = device_udid_combo.get().strip()
    if not udid:
        return ""
    return DEVICE_INFO_CACHE.get(udid, udid)

def detect_missing_ddi_issue(model: str, output: str) -> bool:
    """
    True if the connected device is the new M5 iPad Pro (iPad17,1)
    AND the output contains any of the known DDI mount failure indicators.
    """
    if not model or not output:
        return False

    model_l = model.lower()
    out_l = output.lower()

    if "ipad17,1" not in model_l:
        return False

    for key in DDI_ERROR_KEYWORDS:
        if key in out_l:
            return True

    return False

def prompt_update_for_missing_ddi():
    """
    Show a single-shot warning and open Apple's Developer downloads page.
    """
    global MISSING_DDI_WARNING_SHOWN
    if MISSING_DDI_WARNING_SHOWN:
        return

    MISSING_DDI_WARNING_SHOWN = True

def _do():
    import webbrowser
    try:
        xcode_ver = subprocess.check_output(
            ["xcodebuild", "-version"], text=True
        ).splitlines()[0]
    except Exception:
        xcode_ver = "Xcode (version unknown)"

    result = messagebox.showwarning(
        "Update Required",
        f"{xcode_ver}\n\n"
        "⚠️ Your version of Xcode or Command Line Tools doesn't include the "
        "Developer Disk Image required for this iPad Pro (iPad17,1).\n\n"
        "👉 Click OK to open Apple's Developer Downloads page and install the latest beta tools."
    )

    if result == "ok":
        webbrowser.open("https://developer.apple.com/download/all/")
        root.destroy()
        os._exit(0)

    root.after(0, _do)

# === APP DISPLAY AND DEVICE INFO HELPERS ===
def add_suffix(app_name: str) -> str:
    """Return a display name with suffix if one exists for this app."""
    if not app_name:
        return app_name
    suffix = APP_DISPLAY_SUFFIX.get(app_name)
    return f"{app_name}{suffix}" if suffix else app_name

def strip_suffix(display_name: str) -> str:
    """
    Reverse the add_suffix transformation when possible.
    If no match found, returns the input (assumes it is already original).
    """
    if not display_name:
        return display_name
    for orig, suffix in APP_DISPLAY_SUFFIX.items():
        if display_name == f"{orig}{suffix}":
            return orig
    for suffix in set(APP_DISPLAY_SUFFIX.values()):
        if display_name.endswith(suffix):
            return display_name[: -len(suffix)]
    return display_name

def _fetch_device_info_map():
    """Query devicectl once and build a udid -> 'Model' map."""
    output = run_command("xcrun devicectl list devices")
    lines = output.splitlines()[2:]  
    cache = {}
    for line in lines:
        m = re.match(r"^(.*?)\s{2,}.*?\s{2,}(.*?)\s{2,}(.*?)\s{2,}(.*)$", line)
        if m:
            udid = m.group(2).strip()
            model = m.group(4).strip()  
            cache[udid] = model        
    return cache

def get_device_display(udid: str) -> str:
    """Return 'Model' for a UDID, refreshing cache if needed."""
    global DEVICE_INFO_CACHE
    if not udid:
        return "Unknown Device"
    if udid not in DEVICE_INFO_CACHE:
        try:
            DEVICE_INFO_CACHE = _fetch_device_info_map()
        except Exception:
            pass
    return DEVICE_INFO_CACHE.get(udid, udid)

locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

# === XCODE AND COMMAND LINE TOOL SETUP ===
def is_xcode_installed():
    """Check if Xcode Command Line Tools are installed."""
    try:
        subprocess.run(
            ["xcode-select", "-p"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False

# === LICENSE ACCEPTANCE AND VALIDATION ===
def has_agreed_to_license():
    """Check if the Xcode license has been agreed to."""
    try:
        subprocess.run(
            ["xcrun", "devicectl", "list", "devices"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False

def accept_xcode_license_gui():
    """
    Ensure the system is pointing to the full Xcode developer directory,
    then attempt to accept the Xcode license automatically using AppleScript.
    """
    import subprocess

    try:
        current_path = subprocess.check_output(
            ["xcode-select", "-p"], text=True
        ).strip()

        if "CommandLineTools" in current_path:
            subprocess.run(
                ["sudo", "xcode-select", "-s", "/Applications/Xcode.app/Contents/Developer"],
                check=True
            )

        applescript = '''
        do shell script "xcodebuild -license accept" with administrator privileges
        '''
        subprocess.run(["osascript", "-e", applescript], check=True)

        return True

    except subprocess.CalledProcessError as e:
        messagebox.showwarning(
            "Xcode License",
            "Failed to automatically accept the Xcode license.\n\n"
            "Please run the following command manually in Terminal:\n\n"
            "sudo xcode-select -s /Applications/Xcode.app/Contents/Developer\n"
            "sudo xcodebuild -license accept\n\n"
            f"Error details:\n{e}"
        )
        return False

def ensure_xcode_beta_selected(model: str = None):
    """
    Automatically switches to Xcode Beta if the connected device requires it.
    Uses AppleScript to perform the switch with admin privileges (no sudo prompt).
    Silently skips if Beta isn't needed or already selected.
    """
    import subprocess
    import os
    import webbrowser
    from tkinter import messagebox

    try:
        current_path = subprocess.check_output(
            ["xcode-select", "-p"], text=True
        ).strip()

        if "Xcode-beta.app" in current_path:
            return True

        needs_beta = False
        if model:
            lower_model = model.lower()
            # Only these specific models currently require Xcode Beta
            BETA_REQUIRED_MODELS = ["ipad17,1", "ipad17,2"]
            needs_beta = any(m in lower_model for m in BETA_REQUIRED_MODELS)

        if not needs_beta:
            return True

        beta_path = "/Applications/Xcode-beta.app/Contents/Developer"
        if os.path.exists(beta_path):
            applescript = f'''
            do shell script "xcode-select -s {beta_path}" with administrator privileges
            '''
            subprocess.run(["osascript", "-e", applescript], check=True)
            return True

        messagebox.showwarning(
            "Xcode Beta Required",
            (
                f"Your connected device ({model or 'new device'}) requires Xcode Beta and Command Line Tools Beta "
                "to work properly.\n\nClick OK to open Apple's Developer Downloads page."
            ),
        )
        webbrowser.open("https://developer.apple.com/download/all/")
        root.destroy()
        os._exit(0)

    except subprocess.CalledProcessError as e:
        messagebox.showwarning(
            "Xcode Switch Failed",
            f"Unable to switch to Xcode Beta.\n\nError details:\n{e}"
        )
        return False

    except Exception as e:
        messagebox.showwarning(
            "Unexpected Error",
            f"An unexpected error occurred while switching Xcode:\n\n{e}"
        )
        return False

def run_setup_xcode():
    """Ensure Xcode is installed and the license is accepted."""
    if not os.path.exists("/Applications/Xcode.app"):
        messagebox.showwarning(
            "Xcode Missing",
            "Xcode not found in Applications.\nPlease install it from the App Store. No need to open it after install."
        )
        subprocess.Popen(["open", "macappstore://itunes.apple.com/app/id497799835"])
        root.destroy()
        os._exit(0)

    if not has_agreed_to_license():
        success = accept_xcode_license_gui()
        if not success:
            root.destroy()
            os._exit(0)

def prompt_update_for_missing_ddi():
    """
    Show a single-shot warning and open Apple's Developer Downloads page.
    Then exit the app completely after OK is clicked.
    """
    global MISSING_DDI_WARNING_SHOWN
    if MISSING_DDI_WARNING_SHOWN:
        return
    MISSING_DDI_WARNING_SHOWN = True

    try:
        xcode_ver = subprocess.check_output(
            ["xcodebuild", "-version"], text=True
        ).splitlines()[0]
    except Exception:
        xcode_ver = "Unknown Xcode version"

    def _do():
        import webbrowser
        result = messagebox.showwarning(
            "Update Required",
            f"{xcode_ver}\n\n"
            "Your version of Xcode or Command Line Tools doesn't include the "
            "Developer Disk Image required for this iPad Pro (iPad17,1).\n\n"
            "Click OK to open Apple's Developer Downloads page."
        )
        if result == "ok":
            webbrowser.open("https://developer.apple.com/download/all/")
            root.destroy()
            os._exit(0)  

    root.after(0, _do)

# === GUI root ===
root = tk.Tk()
root.withdraw()  

root.deiconify()  

# === DATA LOADING AND SAVING ===
DATA_FILE = os.path.expanduser("~/ios_device_controller_data.json")

saved_paths = {}  
command_history = []
hud_settings_saved = {} 

def load_data():
    global saved_paths, command_history, hud_settings_saved
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                saved_paths = data.get("saved_paths", {})
                command_history = data.get("command_history", [])
                hud_settings_saved = data.get("hud_settings", {})
        except Exception as e:
            print("Error loading saved data:", e)
            saved_paths = {}
            command_history = []
            hud_settings_saved = {}
    else:
        saved_paths = {}
        command_history = []
        hud_settings_saved = {}

def save_data():
    try:
        hud_settings = {
            "preset": hud_preset_var.get(),
            "alignment": hud_alignment_var.get(),
            "scale": hud_scale_var.get(),
            "custom_elements": {
            key: var.get() for key, var in hud_elements_vars.items()
        }
    }
    except Exception:
        hud_settings = {}

    data = {
        "saved_paths": saved_paths,
        "command_history": command_history,
        "hud_settings": hud_settings
    }
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Data saved to {DATA_FILE}")
        print(f"Saved data content:\n{json.dumps(data, indent=2)}")
    except Exception as e:
        print("Error saving data:", e)

# === GUI UTILITIES AND EVENT HANDLERS ===
def on_close():
    print("on_close called")
    save_data()
    root.destroy()

# === COMMAND EXECUTION AND LOGGING ===
def run_command(command):
    """
    Run a shell command, capture both success and error output,
    and always display it in the launch_output_text log window.
    """
    try:
        output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output = e.output if e.output else str(e)

    print(f"Command Output:\n{output}")
    root.after(0, lambda: update_launch_output(output))  

    if output and "Developer Mode is disabled" in output:
        root.after(0, lambda: messagebox.showwarning(
            "Developer Mode Disabled",
            "Operation failed because Developer Mode is disabled on your iPhone or iPad.\n\n"
            "Go to Settings > Privacy & Security > Developer Mode on your device to enable it."
        ))

    return output.strip()

def set_text_widget(widget, text):
    """
    Safely replace the contents of a Text/ScrolledText widget and keep it read-only.
    Use this instead of widget.delete(...); widget.insert(...).
    """
    widget.config(state='normal')
    widget.delete("1.0", tk.END)
    if text:
        widget.insert(tk.END, text)
    widget.config(state='disabled')

def is_xcode_installed():
    return os.path.exists("/Applications/Xcode.app")

def open_xcode_download():
    subprocess.Popen(["open", "macappstore://itunes.apple.com/app/id497799835"])

# === DEVICE MANAGEMENT ===
def list_devices():
    global WARNING_SHOWN  

    if not WARNING_SHOWN:
        messagebox.showwarning(
            "Connect Device",
            "Please connect your device via USB. Wireless works after pairing."
        )
        WARNING_SHOWN = True  

    raw_output = run_command("xcrun devicectl list devices")
    lines = raw_output.splitlines()
    content_lines = lines[2:]  

    device_lines = []
    device_ids = {}
    device_info = {}

    for line in content_lines:
        match = re.match(r"^(.*?)\s{2,}.*?\s{2,}(.*?)\s{2,}(.*?)\s{2,}(.*)$", line)
        if match:
            name = match.group(1).strip()
            identifier = match.group(2).strip()  
            state = match.group(3).strip()
            model = match.group(4).strip()

            device_ids[name] = identifier  
            device_info[identifier] = model  

            device_lines.append(f"{name:<40}  {state:<40}  {model}")

    global DEVICE_INFO_CACHE
    DEVICE_INFO_CACHE = device_info.copy()

    if device_lines:
        formatted = "\n".join(device_lines)
        formatted = formatted.replace("?", "'")
    else:
        formatted = "No devices found."

    set_text_widget(device_text, formatted)

    device_text.name_to_udid = device_ids
    device_text.device_info = device_info 

    if device_ids:
        device_udid_combo['values'] = list(device_ids.values())
        device_udid_combo.set(list(device_ids.values())[0])
    else:
        device_udid_combo.set('')

    refresh_command_history_combo()

    device_text.config(state='normal')
    lines = device_text.get("1.0", "end-1c").splitlines()
    if lines:
        device_text.tag_remove("selected_device", "1.0", tk.END)
        device_text.tag_add("selected_device", "1.0", "1.end")
        device_text.mark_set("insert", "1.0")
        device_text.see("insert")
        first_name = lines[0].split("  ")[0].strip()
        if hasattr(device_text, "name_to_udid") and first_name in device_text.name_to_udid:
            device_udid_combo.set(device_text.name_to_udid[first_name])
    device_text.config(state='disabled')

    device_text.focus_set()
    device_text.bind("<Up>", lambda e: move_selection(device_text, "up"))
    device_text.bind("<Down>", lambda e: move_selection(device_text, "down"))
    device_text.bind("<Return>", lambda e: show_apps())

def unpair_device():
    """Unpair the selected/highlighted device."""
    udid = device_udid_combo.get().strip()
    if not udid:
        messagebox.showwarning("No Device Selected", "Please select a device to unpair.")
        return

    device_display = get_device_display(udid)  
    confirm = messagebox.askyesno("Confirm Unpair", f"Are you sure you want to unpair device {device_display}?")
    if not confirm:
        return

    command = f"xcrun devicectl manage unpair --device {udid}"
    output = run_command(command)

    set_text_widget(launch_output_text, output)

    list_devices()

def refresh_command_history_combo():
    global appname_to_command
    history_display_entries = []
    appname_to_command.clear()
    for cmd in command_history:
        display_str, full_cmd = extract_device_and_app_from_command(cmd)
        history_display_entries.append(display_str)
        appname_to_command[display_str] = full_cmd
    command_history_combo['values'] = history_display_entries

def update_command_history(cmd):
    if cmd not in command_history:
        command_history.insert(0, cmd)
        if len(command_history) > 10:
            command_history.pop()
        refresh_command_history_combo()
        display_str, _ = extract_device_and_app_from_command(cmd)
        command_history_combo.set(display_str)
        save_data()

def show_apps():
    global OPEN_GAME_WARNING_SHOWN

    udid = device_udid_combo.get().strip()
    if not udid:
        return

    model = get_device_display(udid)
    ensure_xcode_beta_selected(model)

    if not OPEN_GAME_WARNING_SHOWN:
        messagebox.showwarning(
            "Open Game Reminder",
            "Make sure your selected game is open and all other apps are closed before clicking Show Running Games"
        )
        OPEN_GAME_WARNING_SHOWN = True

# === Auto repair wireless mount for M5 iPads ===
    model = get_current_device_model().lower()
    if "ipad17" in model:
        try:
            connection_info = subprocess.check_output(
                ["xcrun", "devicectl", "list", "devices"],
                text=True
            )

            if "wireless" in connection_info.lower():
                print("🔄 Detected wireless M5 iPad — trying auto repair...")
                
                subprocess.run("xcrun devicectl discover start", shell=True, check=False)
                time.sleep(2)
                subprocess.run("xcrun devicectl discover stop", shell=True, check=False)

                subprocess.run(f"xcrun devicectl device pair --device {udid}", shell=True, check=False)
                subprocess.run(f"xcrun devicectl device info --device {udid}", shell=True, check=False)

        except Exception as e:
            print(f"⚠️ Wireless auto-mount check failed: {e}")

# === Progress bar and threaded process scan ===
    progress_bar.pack(fill=tk.X, pady=(0, 10))
    progress_bar.start(10)
    show_temporary_status_message("Searching for games...")

    def background_task():
        try:
            command = f"xcrun devicectl device info processes --device {udid} | grep 'Bundle/Application'"
            output = run_command(command)
            root.after(0, lambda: process_apps_output(output))
        finally:
            root.after(0, lambda: (
                progress_bar.stop(),
                progress_bar.pack_forget(),
                status_label.config(text="")
            ))

    threading.Thread(target=background_task, daemon=True).start()

def process_apps_output(output):
    filter_out = [
        "Photos.app", "Weather.app", "VoiceMemos.app", "News.app", "Tips.app",
        "Reminders.app", "Music.app", "Maps.app", "Stocks.app", "AppStore.app",
        "Measure.app", "Magnifier.app", "Books.app", "Shortcuts.app", "Podcasts.app",
        "Calculator.app", "Health.app", "FindMy.app", "Freeform.app", "Camera.app",
        "AppleTV.app", "YouTube.app", "TestFlight.app", "MobileCal.app", "MobileMail.app",
        "MobileSafari.app", "SequoiaTranslator.app", "MobileNotes.app", "MobileTimer.app",
        "Home.app", "Journal.app", "Files.app", "Fitness.app", "Passbook.app",
        "MobileSMS.app", "Bridge.app", "Messenger.app", "ChatGPT.app", "WhatsApp.app",
        "Drive.app", "Spotify.app", "Discord.app", "Bumble.app", "Meetup.app",
        "ProtonNative.app", "YouTubeCreator.app", "Tinder.app", "Hinge.app", "TikTok.app",
        "Google.app", "maps.app", "Docs.app", "Gmail.app", "Twitch.app", "Instagram.app",
        "Snapchat.app", "Authenticator.app", "Preview.app", "Games.app", "Final Cut Camera.app", 
        "MobilePhone.app", "Max-iOS.app", "Facebook.app", "Argo.app", "Compass.app", "Dominguez.app", 
        "Evernote.app", "FaceBook.app", "LinkedIn.app", "Notion.app", "Outlook-iOS.app", "PrimeVideo.app", 
        "Slack.app", "TeamSpaceApp.app", "Telegram.app", "YouTubeKids.app", "Zoom.app", "Signal.app", "Sheets.app", 
        "Netflix.app", "DisneyPlus.app", "OneNote.app", "Tachyon.app", "Word.app", "RunestoneEditor.app", "Contacts.app", 
        "FaceTime.app", "Image Playground.app", "MobileStore.app", "Amazon.app", "Apple Store.app", "Control Center.app", "Passwords.app",
        "RedditApp.app", "BlackmagicCam.app", "Cash.app", "Chase.app", "Helix.app", "com.roborock.smart.app", "MintMobile.app", "GooglePhotos",
        "Geekbench 6",
    ]

    unique_apps = {}
    for line in output.splitlines():
        cleaned_line = re.sub(r"^\s*\d+\s+", "", line.strip())
        if cleaned_line:
            match = re.search(r'(/private/var/containers/Bundle/Application/[A-F0-9\-]+/.+?\.app)', cleaned_line)
            if match:
                full_path = match.group(1)
                app_name = os.path.basename(full_path)
                if app_name in filter_out:
                    continue
                if full_path not in unique_apps:
                    unique_apps[full_path] = app_name

    sorted_apps = sorted(unique_apps.items(), key=lambda x: x[1].lower())

    APP_DISPLAY_SUFFIX = {
        "ShadowTrackerExtra": "(PUBG MOBILE)",
        "scimitar": "(Assassin's Creed Mirage)",
        "SolarlandClient": "(Farlight 84)",
        "hkrpg": "(Honkai: Star Rail)",
        "bh3oversea": "(Honkai Impact 3)",
        "X6Game": "(Infinity Nikki)",
        "ExtremeGame": "(PUBG: New State)"
    }

    def add_suffix(app_name: str) -> str:
        return f"{app_name}{APP_DISPLAY_SUFFIX[app_name]}" if app_name in APP_DISPLAY_SUFFIX else app_name

    display_names = []
    app_name_to_full_path = {}

    for full_path, app_name in sorted_apps:
        base_name = app_name[:-4] if app_name.endswith(".app") else app_name
        display_name = add_suffix(base_name)
        if display_name not in app_name_to_full_path:  
            app_name_to_full_path[display_name] = full_path
            display_names.append(display_name)

    set_text_widget(apps_text, "\n".join(display_names))

    apps_text.full_path_map = app_name_to_full_path

    app_names = sorted(app_name_to_full_path.keys())
    app_path_combo['values'] = app_names

    if app_names:
        app_path_combo.set(app_names[0])
        app_path_combo.full_path = app_name_to_full_path[app_names[0]]
    else:
        app_path_combo.set('')
        app_path_combo.full_path = None

    if not sorted_apps:
        update_launch_button_text(None)

    apps_text.config(state='normal')
    lines = apps_text.get("1.0", "end-1c").splitlines()
    if lines:
        apps_text.tag_remove("selected_app", "1.0", tk.END)
        apps_text.tag_add("selected_app", "1.0", "1.end")
        apps_text.mark_set("insert", "1.0")
        apps_text.see("insert")
        first_app = lines[0].strip()
        if first_app in app_name_to_full_path:
            app_path_combo.set(first_app)
            app_path_combo.full_path = app_name_to_full_path[first_app]
            update_launch_button_text(first_app)
    apps_text.config(state='disabled')

    apps_text.focus_set()
    apps_text.bind("<Up>", lambda e: move_selection(apps_text, "up"))
    apps_text.bind("<Down>", lambda e: move_selection(apps_text, "down"))
    apps_text.bind("<Return>", lambda e: launch_app())

# === OUTPUT PROCESSING AND WARNINGS ===
def update_launch_output(output):
    set_text_widget(launch_output_text, output)

    if "OpenGL" in output:
        root.after(0, lambda: messagebox.showwarning(
            "OpenGL Detected",
            "Warning: OpenGL detected in the logs. Metal HUD may not work!"
        ))

    global WARZONE_WARNING_SHOWN, FARLIGHT_WARNING_SHOWN
    if not WARZONE_WARNING_SHOWN and detect_warzone_anti_cheat(output):
        WARZONE_WARNING_SHOWN = True
        root.after(0, lambda: messagebox.showwarning(
            "Warzone Not Supported",
            "Note! Metal HUD doesn’t work with COD Warzone due to anti-cheat. The game may crash if you try to use it"
        ))

    if not FARLIGHT_WARNING_SHOWN and detect_farlight_issue(output):
        FARLIGHT_WARNING_SHOWN = True
        root.after(0, lambda: messagebox.showwarning(
            "Farlight 84 Not Supported",
            "Note! Metal HUD does not work with Farlight 84 (SolarlandClient.app).\n\n"
            "The game detects the HUD as a device anomaly and will refuse to run. "
            "In-game you may see: \"Device anomaly detected. Temporarily unable to access the game. (0-3-2048)\".\n\n"
            "Launch the game without the HUD (disable the HUD preset or launch normally) to play."
        ))

    try:
        model = get_current_device_model() 
    except Exception:
        model = ""

    if detect_missing_ddi_issue(model, output):
        prompt_update_for_missing_ddi()

# === THREADING AND BACKGROUND TASKS ===
def run_command_in_thread(command):
    try:
        global process
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            launch_output_text.after(0, lambda l=line: update_launch_output(l))
        process.wait()
    except Exception as e:
        launch_output_text.after(0, lambda: update_launch_output(f"Error: {e}"))

def show_temporary_status_message(message, duration=3000):
    status_label.config(text=message)
    status_label.after(duration, lambda: status_label.config(text=""))

def save_app_path():
    udid = device_udid_combo.get().strip()
    app_path = getattr(app_path_combo, "full_path", None)

    if not udid or not app_path:
        messagebox.showwarning("Missing Info", "Please select both Device and Game before saving.")
        return

    name = simpledialog.askstring("Save Path", "Enter a name for this Game/Device combo:")
    if not name:
        return

    saved_paths[name] = {'udid': udid, 'app_path': app_path}
    refresh_saved_paths_combo()
    saved_paths_combo.set(name)
    save_data() 

def refresh_saved_paths_combo():
    names = sorted(saved_paths.keys())
    saved_paths_combo['values'] = names
    if names:
        if saved_paths_combo.get() not in names:
            saved_paths_combo.set(names[0])
    else:
        saved_paths_combo.set('')

def delete_saved_path():
    name = saved_paths_combo.get()
    if name in saved_paths:
        del saved_paths[name]
        refresh_saved_paths_combo()
        if saved_paths_combo.get() == '':
            device_udid_combo.set('')
            app_path_combo.set('')
        save_data()  

def on_saved_path_select(event):
    name = saved_paths_combo.get()
    if name in saved_paths:
        device_udid_combo.set(saved_paths[name]['udid'])
        app_path_combo.set(saved_paths[name]['app_path'])

def get_hud_env_vars(preset):
    if preset == "Default":
        return {"MTL_HUD_ENABLED": "1"}
    elif preset == "Simple":
        return {
            "MTL_HUD_ENABLED": "1",
            "MTL_HUD_ELEMENTS": "device,layersize,fps"
        }
    elif preset == "FPS Only":
        return {
            "MTL_HUD_ENABLED": "1",
            "MTL_HUD_ELEMENTS": "fps"
        }
    elif preset == "Thermals":
        return {
            "MTL_HUD_ENABLED": "1",
            "MTL_HUD_ELEMENTS": "device,layersize,memory,fps,frameinterval,gputime,thermal,frameintervalgraph,metalfx"
        }
    elif preset == "Rich":
        return {
            "MTL_HUD_ENABLED": "1",
            "MTL_HUD_ELEMENTS": "device,layersize,layerscale,gamemode,memory,refreshrate,fps,frameinterval,gputime,thermal,frameintervalgraph,presentdelay,metalcpu,shaders,metalfx"
        }
    elif preset == "Full":
        return {
            "MTL_HUD_ENABLED": "1",
            "MTL_HUD_ELEMENTS": "device,layersize,layerscale,memory,refreshrate,thermal,gamemode,fps,fpsgraph,framenumber,gputime,frameinterval,frameintervalgraph,frameintervalhistogram,presentdelay,metalcpu,gputimeline,shaders,metalfx"
        }
    elif preset == "Custom":
        selected_elements = [elem for elem, var in hud_elements_vars.items() if var.get() == 1]
        elements_str = ",".join(selected_elements)
        return {
            "MTL_HUD_ENABLED": "1",
            "MTL_HUD_ELEMENTS": elements_str
        }
    else:
        return {"MTL_HUD_ENABLED": "1"}

def is_app_running(udid, bundle_id):
    result = subprocess.run(
        f"xcrun devicectl device process list --device {udid}",
        shell=True, capture_output=True, text=True
    )
    return bundle_id in result.stdout

# === APP LAUNCH AND METAL HUD EXECUTION ===
def launch_app():
    udid = device_udid_combo.get().strip()
    app_path = getattr(app_path_combo, "full_path", None)

    if not udid or not app_path:
        messagebox.showwarning("Missing Info", "Please select Device and Game")
        return

    app_path_clean = app_path.rstrip("/")
    app_basename = os.path.basename(app_path_clean)
    app_name = app_basename[:-4] if app_basename.lower().endswith(".app") else app_basename
    bundle_id = app_name  

    alignment = get_alignment_internal()
    preset = hud_preset_var.get()
    env_vars = get_hud_env_vars(preset)
    env_vars["MTL_HUD_ALIGNMENT"] = alignment
    selected_label = hud_scale_var.get()
    env_vars["MTL_HUD_SCALE"] = hud_scale_map.get(selected_label, "0.4")
    env_json = json.dumps(env_vars)

    base_command = (
        f"xcrun devicectl device process launch "
        f"-e '{env_json}' "
        f"--console --device {udid} \"{app_path}\""
    )

    update_command_history(base_command)

    def launch_with_restart():
        show_temporary_status_message("Launching app with Metal HUD...")

        process = subprocess.Popen(base_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        time.sleep(1)

        try:
            show_temporary_status_message("Restarting app with Metal HUD...")
            process.terminate()
            process.wait(timeout=5)
        except Exception:
            process.kill()

        time.sleep(0.2)
        show_temporary_status_message(
        "If the Metal HUD doesn’t appear, please close and reopen the app on your device."
        )
        relaunch_process = subprocess.Popen(base_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        for line in relaunch_process.stdout:
            launch_output_text.after(0, lambda l=line: update_launch_output(l))
        relaunch_process.stdout.close()
        relaunch_process.wait()

        show_temporary_status_message("App relaunched with Metal HUD.")

    threading.Thread(target=launch_with_restart, daemon=True).start()

# === DEVICE AND APP SELECTION HANDLERS ===
def on_device_text_click(event):
    device_text.config(state='normal')

    index = device_text.index(f"@{event.x},{event.y}")
    line_num = index.split('.')[0]
    line_start = f"{line_num}.0"
    line_end = f"{line_num}.end"
    line_text = device_text.get(line_start, line_end).strip()

    if not line_text:
        device_text.config(state='disabled')
        return

    device_text.tag_remove("selected_device", "1.0", tk.END)
    device_text.tag_add("selected_device", line_start, line_end)

    name = line_text.split("  ")[0].strip()

    if hasattr(device_text, "name_to_udid") and name in device_text.name_to_udid:
        device_udid_combo.set(device_text.name_to_udid[name])

    device_text.config(state='disabled')

    device_text.bind("<Up>", lambda e: move_selection(device_text, "up"))
    device_text.bind("<Down>", lambda e: move_selection(device_text, "down"))
    device_text.focus_set()  
    device_text.bind("<Return>", lambda e: show_apps())

def device_enter(event):
    show_apps()
    return "break"  

    device_text.bind("<Return>", device_enter)

def on_apps_text_click(event):
    apps_text.config(state='normal')

    index = apps_text.index(f"@{event.x},{event.y}")
    line_num = index.split('.')[0]
    line_start = f"{line_num}.0"
    line_end = f"{line_num}.end"
    app_name = apps_text.get(line_start, line_end).strip()

    if not app_name or not hasattr(apps_text, "full_path_map"):
        apps_text.config(state='disabled')
        return

    apps_text.tag_remove("selected_app", "1.0", tk.END)
    apps_text.tag_add("selected_app", line_start, line_end)

    full_path = apps_text.full_path_map.get(app_name)
    if full_path:
        app_path_combo.set(app_name)
        app_path_combo.full_path = full_path
        update_launch_button_text(app_name)
        apps_text.selected_app_name = app_name
    else:
        app_path_combo.set('')
        app_path_combo.full_path = None
        update_launch_button_text(None)
        apps_text.selected_app_name = None

    apps_text.config(state='disabled')

    apps_text.bind("<Up>", lambda e: move_selection(apps_text, "up"))
    apps_text.bind("<Down>", lambda e: move_selection(apps_text, "down"))

def move_selection(widget, direction="down"):
    """
    Move the selection in a scrolledtext widget up or down by one line.
    direction: "up" or "down"
    """
    widget.config(state='normal')
    ranges = widget.tag_ranges("selected_device") if widget == device_text else widget.tag_ranges("selected_app")
    if ranges:
        line_start = widget.index(ranges[0])
        line_num = int(line_start.split('.')[0])
    else:
        line_num = 1  

    if direction == "down":
        new_line = line_num + 1
        if new_line > int(widget.index(tk.END).split('.')[0]) - 1:
            new_line = line_num  
    else:
        new_line = line_num - 1
        if new_line < 1:
            new_line = 1  

    widget.tag_remove("selected_device" if widget == device_text else "selected_app", "1.0", tk.END)

    line_start = f"{new_line}.0"
    line_end = f"{new_line}.end"
    widget.tag_add("selected_device" if widget == device_text else "selected_app", line_start, line_end)
    widget.see(line_start) 

    line_text = widget.get(line_start, line_end).strip()
    if widget == device_text and hasattr(widget, "name_to_udid"):
        name = line_text.split("  ")[0].strip()
        if name in widget.name_to_udid:
            device_udid_combo.set(widget.name_to_udid[name])
    elif widget == apps_text and hasattr(widget, "full_path_map"):
        app_name = line_text.strip()
        full_path = widget.full_path_map.get(app_name)
        if full_path:
            app_path_combo.set(app_name)
            app_path_combo.full_path = full_path
            update_launch_button_text(app_name)
    widget.config(state='disabled')

# === GUI INITIALIZATION ===
root.title("Metal HUD Mobile Config")

root.update_idletasks()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}+0+0")

padx_side = 30

load_data()

canvas = tk.Canvas(root)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

def resize_scrollable_frame(event):
    canvas.itemconfig(canvas_window, width=event.width)

canvas.bind("<Configure>", resize_scrollable_frame)

canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# === XCODE INSTALLATION PROMPT ===
def prompt_install_xcode():
    messagebox.showwarning(
        "Xcode Missing",
        "Xcode not found in Applications.\nPlease install it from the App Store. No need to open it after install"
    )

    subprocess.Popen(["open", "macappstore://itunes.apple.com/app/id497799835"])
    
    root.destroy()
    os._exit(0)

if not is_xcode_installed():
    prompt_install_xcode()

ttk.Label(scrollable_frame, text="Devices").pack(anchor="w", padx=padx_side)
ttk.Button(scrollable_frame, text="List Devices (Cmd+R)", command=list_devices).pack(anchor="w", padx=padx_side)

device_text = scrolledtext.ScrolledText(scrollable_frame, height=10, state='disabled')
device_text.tag_configure("selected_device", background="#ffcc66", foreground="black")
device_text.pack(fill=tk.BOTH, padx=padx_side, pady=5, expand=True)
device_text.bind("<Button-1>", on_device_text_click)

device_udid_combo = ttk.Combobox(scrollable_frame, values=[])

ttk.Button(scrollable_frame, text="Unpair", command=unpair_device).pack(anchor="w", padx=padx_side, pady=(0, 10))

# === SHOW RUNNING GAMES SECTION (button + status + progress bar) ===
show_games_frame = ttk.Frame(scrollable_frame)
show_games_frame.pack(anchor="w", fill="x", padx=padx_side, pady=(0, 2))

show_games_button = ttk.Button(show_games_frame, text="Show Running Games", command=show_apps)
show_games_button.pack(anchor="w")

status_label = ttk.Label(show_games_frame, text="", foreground="red")
status_label.pack(anchor="w", pady=(5, 2))

progress_bar = ttk.Progressbar(show_games_frame, mode='indeterminate')
progress_bar.pack(fill=tk.X, pady=(0, 10))
progress_bar.pack_forget()

# === APPS LIST ===
apps_text = scrolledtext.ScrolledText(scrollable_frame, height=7, state='disabled')
apps_text.tag_configure("selected_app", background="#ffcc66", foreground="black")
apps_text.pack(fill=tk.BOTH, padx=padx_side, pady=15, expand=True)
apps_text.bind("<Button-1>", on_apps_text_click)

app_path_combo = ttk.Combobox(scrollable_frame, values=[])

def on_app_path_select(event):
    selected_app_name = app_path_combo.get()
    full_path = getattr(scrollable_frame, "app_name_to_full_path", {}).get(selected_app_name)
    if full_path:
        app_path_combo.full_path = full_path
        update_launch_button_text(selected_app_name)  
    else:
        app_path_combo.full_path = None
        update_launch_button_text(None)  

app_path_combo.bind("<<ComboboxSelected>>", on_app_path_select)

ttk.Button(scrollable_frame, text="Save Game", command=save_app_path).pack(anchor="w", padx=padx_side, pady=(0, 5))

ttk.Label(scrollable_frame, text="Saved Games").pack(anchor="w", padx=padx_side)
saved_paths_combo = ttk.Combobox(scrollable_frame, values=sorted(saved_paths.keys()))
saved_paths_combo.pack(fill=tk.X, padx=padx_side, pady=5)
saved_paths_combo.bind("<<ComboboxSelected>>", on_saved_path_select)

ttk.Button(scrollable_frame, text="Delete Saved Game", command=delete_saved_path).pack(anchor="w", padx=padx_side, pady=(0, 10))

def extract_device_and_app_from_command(cmd):
    udid_match = re.search(r"--device\s+([^\s]+)", cmd)
    udid = udid_match.group(1) if udid_match else None

    device_display = get_device_display(udid)

    app_match = re.search(r'"([^"]+)"$', cmd)
    if app_match:
        full_path = app_match.group(1)
        app_basename = os.path.basename(full_path)
        app_name = app_basename[:-4] if app_basename.endswith(".app") else app_basename
        display_app_name = add_suffix(app_name)
    else:
        display_app_name = "Unknown App"

    return f"{device_display} - {display_app_name}", cmd

history_display_entries = []
appname_to_command = {}

for cmd in command_history:
    display_str, full_cmd = extract_device_and_app_from_command(cmd)
    history_display_entries.append(display_str)
    appname_to_command[display_str] = full_cmd

ttk.Label(scrollable_frame, text="Previous Games").pack(anchor="w", padx=padx_side)
command_history_combo = ttk.Combobox(scrollable_frame, values=[], state="readonly")
command_history_combo.pack(fill=tk.X, padx=padx_side, pady=(0, 10))

refresh_command_history_combo()

def on_command_history_select(event):
    selected_appname = command_history_combo.get()
    full_command = appname_to_command.get(selected_appname)

    if full_command:
        udid_match = re.search(r"--device\s+([^\s]+)", full_command)
        if udid_match:
            device_udid_combo.set(udid_match.group(1))

        app_path_match = re.search(r'"([^"]+)"$', full_command)
        if app_path_match:
            full_path = app_path_match.group(1)
            app_basename = os.path.basename(full_path)
            app_name = app_basename[:-4] if app_basename.endswith(".app") else app_basename
            display_name = add_suffix(app_name)

            app_path_combo.set(display_name)
            app_path_combo.full_path = full_path


    alignment_match = re.search(r'"MTL_HUD_ALIGNMENT"\s*:\s*"(\w+)"', full_command)
    if alignment_match:
        internal = alignment_match.group(1)
        display_alignment = hud_alignment_internal_to_display.get(internal, internal)
        hud_alignment_var.set(display_alignment)
    else:
        hud_alignment_var.set("")

    update_launch_button_text(app_name)
command_history_combo.bind("<<ComboboxSelected>>", on_command_history_select)

# === HUD PRESETS ===

ttk.Label(scrollable_frame, text="HUD Preset").pack(anchor="w", padx=padx_side)

hud_preset_var = tk.StringVar(value="Default")
preset_dropdown = ttk.OptionMenu(
    scrollable_frame,
    hud_preset_var,
    "Default",
    "Default",
    "Simple",
    "FPS Only",
    "Thermals",
    "Rich",
    "Full",
    "Custom"
)
preset_dropdown.pack(fill=tk.X, padx=padx_side, pady=(0, 10))

hud_elements_display_map = {
    "Metal Device": "device",
    "Layer Size & Present Mode": "layersize",
    "Layer Scale & Pixel Format": "layerscale",
    "Memory": "memory",
    "Refresh Rate": "refreshrate",
    "Thermal State": "thermal",
    "Game Mode": "gamemode",
    "FPS": "fps",
    "FPS Graph": "fpsgraph",
    "Frame Number": "framenumber",
    "GPU Time": "gputime",
    "Frame Interval": "frameinterval",
    "Frame Interval Graph": "frameintervalgraph",
    "Frame Interval Histogram": "frameintervalhistogram",
    "Present Delay": "presentdelay",
    "Command Buffer & Encoder Count": "metalcpu",
    "Encoder Time & GPU Timeline": "gputimeline",
    "Shader Compiler": "shaders",
    "MetalFX": "metalfx"
}

hud_elements_vars = {}
custom_elements_frame = ttk.Frame(scrollable_frame)

row = 0
col = 0
max_cols = 4  

for display_name, internal_name in hud_elements_display_map.items():
    var = tk.IntVar(value=0)
    cb = ttk.Checkbutton(custom_elements_frame, text=display_name, variable=var)
    cb.grid(row=row, column=col, padx=5, pady=5, sticky="w")
    hud_elements_vars[internal_name] = var

    col += 1
    if col >= max_cols:
        col = 0
        row += 1

custom_elements_frame.pack_forget()

def on_preset_change(*args):
    if hud_preset_var.get() == "Custom":
        custom_elements_frame.pack(fill=tk.X, padx=padx_side, pady=(0,10))
    else:
        custom_elements_frame.pack_forget()

hud_preset_var.trace_add("write", on_preset_change)
on_preset_change()  

# === HUD ALIGNMENT OPTIONS ===

ttk.Label(scrollable_frame, text="Set HUD Location").pack(anchor="w", padx=padx_side)

hud_alignment_var = tk.StringVar(value="Top-Right")

hud_alignment_display_map = {
    "Top-Left": "topleft",
    "Top-Center": "topcenter",
    "Top-Right": "topright",
    "Center-Left": "centerleft",
    "Centered": "centered",
    "Center-Right": "centerright",
    "Bottom-Right": "bottomright",
    "Bottom-Center": "bottomcenter",
    "Bottom-Left": "bottomleft"
}

hud_alignment_internal_to_display = {v: k for k, v in hud_alignment_display_map.items()}

hud_alignment_combo = ttk.Combobox(
    scrollable_frame,
    textvariable=hud_alignment_var,
    values=list(hud_alignment_display_map.keys()),
    state="readonly"
)
hud_alignment_combo.pack(fill=tk.X, padx=padx_side, pady=5)

def get_alignment_internal():
    """Return the internal string used by HUD (e.g., 'topleft')."""
    display_value = hud_alignment_var.get()
    return hud_alignment_display_map.get(display_value, "topright")

# === HUD SCALE OPTIONS ===

hud_scale_map = {
    "Small": "0.15",
    "Default": "0.2",
    "Large": "0.3",
    "Larger": "0.4",
    "Max": "1.0"
}

ttk.Label(scrollable_frame, text="Set HUD Scale").pack(anchor="w", padx=padx_side)

hud_scale_var = tk.StringVar(value="Default")  

hud_scale_options = list(hud_scale_map.keys())

hud_scale_optionmenu = ttk.OptionMenu(scrollable_frame, hud_scale_var, hud_scale_var.get(), *hud_scale_options)
hud_scale_optionmenu.pack(fill=tk.X, padx=padx_side, pady=5)

saved_custom = hud_settings_saved.get("custom_elements", {})
for key, var in hud_elements_vars.items():
    if key in saved_custom:
        var.set(saved_custom[key])

if hud_settings_saved:
    saved_preset = hud_settings_saved.get("preset", "Default")
    hud_preset_var.set(saved_preset)
    try:
        on_preset_change()
    except Exception:
        pass

    saved_alignment = hud_settings_saved.get("alignment", "Top-Right")
    saved_alignment_display = hud_alignment_internal_to_display.get(saved_alignment, saved_alignment)
    hud_alignment_var.set(saved_alignment_display)

    saved_scale = hud_settings_saved.get("scale", "Default")
    hud_scale_var.set(saved_scale)

# === LAUNCH METAL HUD ===

launch_button = ttk.Button(scrollable_frame, text="Launch App with Metal Performance HUD", command=launch_app)
launch_button.pack(anchor="w", padx=padx_side, pady=(0, 10))

def update_launch_button_text(app_name):
    """
    Update the Launch button text to include the selected app name,
    or reset to default if None or empty string is given.
    """
    if app_name:
        launch_button.config(text=f"Launch {app_name} with Metal Performance HUD")
    else:
        launch_button.config(text="Launch App with Metal Performance HUD")

# === GUI UTILITIES AND EVENT HANDLERS ===
def toggle_logs():
    if launch_output_text.winfo_ismapped():
        launch_output_text.pack_forget()
        toggle_log_button.config(text="Show Logs")
    else:
        launch_output_text.pack(fill=tk.BOTH, padx=padx_side, pady=10, expand=True)
        toggle_log_button.config(text="Hide Logs")

toggle_log_button = ttk.Button(scrollable_frame, text="Show Logs", command=toggle_logs)
toggle_log_button.pack(anchor="w", padx=padx_side, pady=(0, 5))

launch_output_text = scrolledtext.ScrolledText(scrollable_frame, height=12, state='disabled')
launch_output_text.pack_forget()

root.bind("<Command-r>", lambda event: list_devices())

root.protocol("WM_DELETE_WINDOW", on_close)

# === MAINLOOP AND EXIT HANDLERS ===
root.mainloop()