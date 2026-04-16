# ==========================================================
#  METAL HUD MOBILE CONFIG 
#  Author: Stewie (MrMacRight)
#  Purpose: Metal HUD iOS launcher GUI & iOS device management 
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
import tkinter.font as tkfont
import webbrowser
from PIL import Image, ImageTk

process = None
current_launch_process = None

MAX_LOG_LINES = 5000  

def trim_log_widget(widget):
    try:
        lines = int(widget.index("end-1c").split(".")[0])
        if lines > MAX_LOG_LINES + 200:
            widget.delete("1.0", f"{lines - MAX_LOG_LINES}.0")
    except Exception:
        pass

# === MACOS VERSION CHECK ===
def check_macos_version(min_version="26.2"):
    if sys.platform != "darwin":
        return  

    ver_tuple = tuple(int(x) for x in platform.mac_ver()[0].split("."))
    min_tuple = tuple(int(x) for x in min_version.split("."))

    if ver_tuple < min_tuple:
        messagebox.showerror(
            "Unsupported macOS Version",
            f"This app requires macOS Tahoe 26.2 or later.\n"
            f"You are running {platform.mac_ver()[0]}"
        )
        sys.exit(1)

check_macos_version()

# === ENVIRONMENT VARIABLES AND GLOBAL FLAGS ===
os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ["LANG"] = "en_US.UTF-8"

DEVICE_INFO_CACHE = {}
DEVICE_STATE_CACHE = {}
APP_DISPLAY_SUFFIX = {}

DEVICE_ICON_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "assets",
    "Devices"
)

CONNECTION_ICON_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "assets",
    "Connection"
)

DEVICE_ICON_CACHE = {}
CONNECTION_ICON_CACHE = {}

DEVICE_NAME_MAX_PX = 170
DEVICE_STATE_MAX_PX = 180

DEVICE_NAME_TAB_X = 50
DEVICE_STATE_TAB_X = 230
DEVICE_STATUS_ICON_TAB_X = 440
DEVICE_MODEL_TAB_X = 390

DEVICE_ICON_SLOT_WIDTH = 48
DEVICE_ICON_SLOT_HEIGHT = 34

CONNECTION_ICON_SLOT_WIDTH = 26
CONNECTION_ICON_SLOT_HEIGHT = 23

STATE_ICON_NAME_MAP = {
    "available": "available",
    "available (paired)": "available (paired)",
    "unavailable": "unavailable",
    "connected": "connected",
    "connected (no ddi)": "connected (no DDI)",
}

OPEN_GAME_WARNING_SHOWN = False
WARZONE_WARNING_SHOWN = False
FARLIGHT_WARNING_SHOWN = False
DEVICE_PREPARING_WARNING_SHOWN = False
RESTORING_FROM_PROFILE = False
OPENGL_WARNING_SHOWN = False
WUTHERING_WAVES_WARNING_SHOWN = False
XCODE_VERSION_WARNING_SHOWN = False
FIRST_DEVICE_SCAN_WARNING_SHOWN = False

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

def detect_wuthering_waves_issue(output: str) -> bool:
    """
    Detect Wuthering Waves Metal HUD startup conflict.
    Identified by Client process + perfsight + apm_postCallGraph errors.
    """
    if not output:
        return False

    text = output.lower()

    return (
        "client[" in text
        and "perfsight" in text
        and "apm_postcallgraph" in text
    )

APP_DISPLAY_RENAME = {
    "ShadowTrackerExtra": "PUBG MOBILE",
    "scimitar": "Assassin's Creed Mirage",
    "SolarlandClient": "Farlight 84",
    "hkrpg": "Honkai: Star Rail",
    "bh3oversea": "Honkai Impact 3",
    "X6Game": "Infinity Nikki",
    "ExtremeGame": "PUBG: New State",
    "librdr_1.50.60293175_ios-netflix_ww": "Red Dead Redemption Netflix",
    "librdr_1.50.60293175_ios_ww": "Red Dead Redemption",
    "WWE2K_Apple": "WWE 2K25: Netflix Edition",
    "narutoNext1": "NARUTO: Ultimate Ninja STORM",
    "Civ6_iOS64_Metal_FinalRelease": "CIV 6",
    "cobalt-tv": "Beach Buggy Racing 2",
    "OH2-IOS-Shipping": "Oceanhorn 3",
    "OH2-TVOS-Shipping": "Oceanhorn 3",
    "PrinceofPersiaTheLostCrown": "Prince of Persia The Lost Crown",
    "EasyDeliveryCo.": "Easy Delivery Co.",
    "SubwaySurf": "Subway Surfers",
    "FortniteClient-IOS-Shipping": "Fortnite",
    "GenshinImpact": "Genshin Impact",
    "GRIDLegends": "GRID Legends",
    "TheDivision": "The Division Resurgence",
    "HacPro-IOS-Shipping": "Borderlands Mobile"
}

# === APP DISPLAY AND DEVICE INFO HELPERS ===
def add_display_name(app_name: str) -> str:
    return APP_DISPLAY_RENAME.get(app_name, app_name)

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

def get_device_state(udid: str) -> str:
    if not udid:
        return ""
    return DEVICE_STATE_CACHE.get(udid, "")

def normalize_model_for_icon(model: str) -> str:
    if not model:
        return ""

    text = model.replace("?", "'").strip()

    text = re.sub(r"\s+\((?:iPhone|iPad|AppleTV)\d+,\d+\)$", "", text)

    text = text.replace("″", '"').replace("”", '"').replace("“", '"')
    text = re.sub(r'(\d+(?:\.\d+)?)"', r'\1-inch', text)

    text = re.sub(
        r"^(iPad Pro) \(([\d\.]+-inch)\) \((.+)\)$",
        r"\1 \2 (\3)",
        text
    )

    if text.startswith("Apple TV"):
        return "Apple TV"

    return text

def get_device_icon_path(model: str) -> str | None:
    normalized = normalize_model_for_icon(model)
    if not normalized:
        return None

    if normalized.startswith("Apple Vision"):
        path = os.path.join(DEVICE_ICON_ROOT, "Apple Vision Pro.png")
        return path if os.path.exists(path) else None

    if normalized.startswith("Apple TV"):
        path = os.path.join(DEVICE_ICON_ROOT, "Apple TV.png")
        return path if os.path.exists(path) else None

    if normalized.startswith("Apple Watch"):
        path = os.path.join(DEVICE_ICON_ROOT, "Apple Watch.png")
        return path if os.path.exists(path) else None

    if normalized.startswith("iPhone"):
        exact_path = os.path.join(
            DEVICE_ICON_ROOT,
            "iPhone",
            f"{normalized}.png"
        )
        if os.path.exists(exact_path):
            return exact_path

        generic_path = os.path.join(
            DEVICE_ICON_ROOT,
            "iPhone",
            "Generic iPhone.png"
        )
        return generic_path if os.path.exists(generic_path) else None

    if normalized.startswith("iPad"):
        exact_path = os.path.join(
            DEVICE_ICON_ROOT,
            "iPad",
            f"{normalized}.png"
        )
        if os.path.exists(exact_path):
            return exact_path

        generic_path = os.path.join(
            DEVICE_ICON_ROOT,
            "iPad",
            "Generic iPad.png"
        )
        return generic_path if os.path.exists(generic_path) else None

    return None

def get_device_icon(model: str):
    path = get_device_icon_path(model)
    if not path:
        return None

    if path in DEVICE_ICON_CACHE:
        return DEVICE_ICON_CACHE[path]

    try:
        image = tk.PhotoImage(file=path)

        if "Apple TV.png" in path:
            image = image.subsample(7, 7)
        else:
            image = image.subsample(8, 8)

        DEVICE_ICON_CACHE[path] = image
        return image
    except Exception as e:
        print(f"Could not load icon from {path}: {e}")
        return None

def normalize_connection_state_for_icon(state: str) -> str:
    return (state or "").strip().lower()

def get_connection_icon_path(state: str) -> str | None:
    normalized = normalize_connection_state_for_icon(state)

    filename = STATE_ICON_NAME_MAP.get(normalized)

    if not filename:
        if "available (pairing)" in normalized:
            filename = "available (pairing)"
        elif normalized == "available":
            filename = "available"
        elif "available (paired)" in normalized:
            filename = "available (paired)"
        elif normalized.startswith("connected"):
            filename = "connected"
        elif normalized.startswith("unavailable"):
            filename = "unavailable"
        else:
            filename = "connected"

    path = os.path.join(CONNECTION_ICON_ROOT, f"{filename}.png")
    return path if os.path.exists(path) else None

def get_connection_icon(state: str):
    path = get_connection_icon_path(state)
    if not path:
        return None

    if path in CONNECTION_ICON_CACHE:
        return CONNECTION_ICON_CACHE[path]

    try:
        img = Image.open(path)

        img = img.resize((20, 14), Image.LANCZOS)

        from PIL import ImageEnhance
        img = ImageEnhance.Sharpness(img).enhance(1.2)

        image = ImageTk.PhotoImage(img)
        CONNECTION_ICON_CACHE[path] = image
        return image

    except Exception as e:
        print(f"Could not load connection icon from {path}: {e}")
        return None

def get_display_state_text(state: str) -> str:
    original_state = (state or "").replace("?", "'")
    normalized_state = original_state.lower()

    if normalized_state in ("available", "available (pairing)"):
        return "available (pairing required)"

    if normalized_state == "available (paired)":
        return "available (paired + wireless)"

    if "no ddi" in normalized_state:
        return "Connected (Xcode beta required)"

    if normalized_state.startswith("connected"):
        return "Connected"

    if normalized_state.startswith("unavailable"):
        return "unavailable (device offline)"

    return original_state

def get_connection_hint(state: str) -> str:
    normalized_state = (state or "").lower()

    if normalized_state in ("available", "available (pairing)"):
        return "Complete pairing on the device (check for Trust prompt)"

    if "no ddi" in normalized_state:
        return "Device requires Xcode beta"

    if normalized_state.startswith("unavailable"):
        return "Device is likely turned off or not connected to Wi-Fi"

    return ""

def truncate_text_to_px(text: str, max_px: int, font) -> str:
    text = (text or "").replace("?", "'")
    ellipsis = "…"

    if font.measure(text) <= max_px:
        return text

    while text and font.measure(text + ellipsis) > max_px:
        text = text[:-1]

    return text.rstrip() + ellipsis

def build_device_row_left_text(widget, device: dict) -> str:
    row_font = tkfont.Font(font=widget.cget("font"))

    name = truncate_text_to_px(device["name"], DEVICE_NAME_MAX_PX, row_font)
    state = truncate_text_to_px(
        get_display_state_text(device["state"]),
        DEVICE_STATE_MAX_PX,
        row_font
    )

    return f"\t{name}\t{state}\t"

def build_device_row_right_text(device: dict) -> str:
    return f"\t{device['model']}".replace("?", "'")

def highlight_device_row(widget, line_num):
    selected_bg = "#ffcc66"
    normal_bg = widget.cget("background")

    widget.config(state='normal')
    widget.tag_remove("selected_device", "1.0", tk.END)
    widget.tag_add("selected_device", f"{line_num}.0", f"{line_num}.end")
    widget.config(state='disabled')

    if hasattr(widget, "_device_rows") and 1 <= line_num <= len(widget._device_rows):
        state = widget._device_rows[line_num - 1]["state"]
        connection_hint_label.config(text=get_connection_hint(state))
    else:
        connection_hint_label.config(text="")

    if hasattr(widget, "_row_icon_slots"):
        for i, row_slots in enumerate(widget._row_icon_slots, start=1):
            row_bg = selected_bg if i == line_num else normal_bg

            for slot in row_slots:
                try:
                    slot.config(bg=row_bg)
                except Exception:
                    pass

                icon_label = getattr(slot, "_icon_label", None)
                if icon_label is not None:
                    try:
                        icon_label.config(bg=row_bg)
                    except Exception:
                        pass

def render_devices_with_icons(widget, devices):
    widget.config(state='normal')
    widget.delete("1.0", tk.END)

    widget._icon_refs = []
    widget._row_icon_slots = []
    widget._device_rows = list(devices)

    bg = widget.cget("background")

    for i, d in enumerate(devices):
        device_icon = get_device_icon(d["model"])
        connection_icon = get_connection_icon(d["state"])

        row_slots = []

        # Left device icon
        device_icon_slot = tk.Frame(
            widget,
            width=DEVICE_ICON_SLOT_WIDTH,
            height=DEVICE_ICON_SLOT_HEIGHT,
            bg=bg,
            bd=0,
            highlightthickness=0
        )
        device_icon_slot.pack_propagate(False)
        device_icon_slot._icon_label = None

        if device_icon:
            widget._icon_refs.append(device_icon)

            icon_label = tk.Label(
                device_icon_slot,
                image=device_icon,
                bg=bg,
                bd=0,
                highlightthickness=0
            )
            icon_label.image = device_icon
            device_icon_slot._icon_label = icon_label
            icon_label.place(relx=1.0, rely=0.5, x=-4, anchor="e")

        row_slots.append(device_icon_slot)
        widget.window_create(tk.END, window=device_icon_slot, align="center")

        # Fixed columns: name, state, icon column
        widget.insert(tk.END, build_device_row_left_text(widget, d))

        connection_icon_slot = tk.Frame(
            widget,
            width=CONNECTION_ICON_SLOT_WIDTH,
            height=CONNECTION_ICON_SLOT_HEIGHT,
            bg=bg,
            bd=0,
            highlightthickness=0
        )
        connection_icon_slot.pack_propagate(False)
        connection_icon_slot._icon_label = None

        if connection_icon:
            widget._icon_refs.append(connection_icon)

            connection_label = tk.Label(
                connection_icon_slot,
                image=connection_icon,
                bg=bg,
                bd=0,
                highlightthickness=0
            )
            connection_label.image = connection_icon
            connection_icon_slot._icon_label = connection_label
            connection_label.place(relx=0.5, rely=0.5, anchor="center")

        row_slots.append(connection_icon_slot)
        widget.window_create(tk.END, window=connection_icon_slot, align="center")

        # Fixed model column
        widget.insert(tk.END, build_device_row_right_text(d))

        widget._row_icon_slots.append(row_slots)

        if i < len(devices) - 1:
            widget.insert(tk.END, "\n")

    widget.config(state='disabled')

def get_xcode_version():
    try:
        out = subprocess.check_output(
            ["xcodebuild", "-version"],
            text=True
        )
        match = re.search(r"Xcode\s+([0-9]+(?:\.[0-9]+)*)", out)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None


def version_tuple(v):
    return tuple(int(x) for x in v.split("."))


def check_xcode_version_or_exit(min_version="26.4"):
    current = get_xcode_version()

    if not current:
        messagebox.showerror(
            "Xcode Version Unknown",
            "Could not determine the installed Xcode version.\n\n"
            "This app requires Xcode "
            + min_version +
            " or later.\n"
            "Please install/update Xcode and try again."
        )
        sys.exit(1)

    try:
        current_tuple = version_tuple(current)
        min_tuple = version_tuple(min_version)
    except Exception:
        messagebox.showerror(
            "Xcode Version Error",
            f"Could not parse Xcode version: {current}\n\n"
            f"This app requires Xcode {min_version} or later."
        )
        sys.exit(1)

    if current_tuple < min_tuple:
        messagebox.showerror(
            "Xcode Required",
            f"Detected: Xcode {current}\n\n"
            f"This app requires Xcode {min_version} or later.\n"
            "Please update Xcode, then relaunch Metal HUD Mobile Config."
        )
        sys.exit(1)

locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

# === XCODE AND COMMAND LINE TOOL SETUP ===
def is_using_command_line_tools_only() -> bool:
    try:
        path = subprocess.check_output(["xcode-select", "-p"], text=True).strip()
        return "CommandLineTools" in path
    except Exception:
        return False

def ensure_xcode_ready_or_exit():
    if not os.path.exists("/Applications/Xcode.app"):
        messagebox.showwarning(
            "Xcode Missing",
            "Xcode not found in Applications.\nPlease install it from the App Store."
        )
        subprocess.Popen(["open", "macappstore://itunes.apple.com/app/id497799835"])
        sys.exit(1)

    try:
        current = subprocess.check_output(["xcode-select", "-p"], text=True).strip()
    except Exception:
        current = ""

    if "CommandLineTools" in current or not current:
        subprocess.run(
            [
                "osascript", "-e",
                'do shell script "xcode-select -s /Applications/Xcode.app/Contents/Developer" '
                'with administrator privileges'
            ],
            check=True
        )

    license_ok = False
    try:
        subprocess.run(
            ["xcodebuild", "-checkFirstLaunchStatus"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        license_ok = True
    except subprocess.CalledProcessError:
        license_ok = False

    if not license_ok:
        subprocess.run(
            [
                "osascript", "-e",
                'do shell script "xcodebuild -license accept" '
                'with administrator privileges'
            ],
            check=True
        )

    subprocess.run(
        ["xcrun", "--find", "devicectl"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False
    )

# === GUI ROOT AND STARTUP CHECKS ===
root = tk.Tk()

# FORCE LIGHT MODE (temporary fix for icons)
try:
    root.tk.call("tk::unsupported::MacWindowStyle", "appearance", root._w, "aqua")
except Exception:
    pass

root.withdraw()

default_font = tkfont.nametofont("TkDefaultFont")
default_font.config(family="SF Pro Text", size=13)

root.option_add("*Font", default_font)

def startup_checks():
    try:
        ensure_xcode_ready_or_exit()
        check_xcode_version_or_exit("26.4")
    finally:
        root.deiconify()

root.after(100, startup_checks)

# === DATA LOADING AND SAVING ===
DATA_FILE = os.path.expanduser("~/ios_device_controller_data.json")

saved_paths = {}  
command_history = []
hud_settings_saved = {}
analytics_opt_in = None
first_device_scan_notice_shown = False
window_geometry_saved = None

def load_data():
    global saved_paths, command_history, hud_settings_saved, analytics_opt_in, first_device_scan_notice_shown, custom_app_names, window_geometry_saved
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                saved_paths = data.get("saved_paths", {})
                command_history = data.get("command_history", [])
                hud_settings_saved = data.get("hud_settings", {})
                analytics_opt_in = data.get("analytics_opt_in", None)
                first_device_scan_notice_shown = data.get("first_device_scan_notice_shown", False)
                window_geometry_saved = data.get("window_geometry", None)
        except Exception as e:
            print("Error loading saved data:", e)
            saved_paths = {}
            command_history = []
            hud_settings_saved = {}
            analytics_opt_in = None
            first_device_scan_notice_shown = False
    else:
        saved_paths = {}
        command_history = []
        hud_settings_saved = {}
        analytics_opt_in = None
        first_device_scan_notice_shown = False

def save_data():
    try:
        hud_settings = {
            "preset": hud_preset_var.get(),
            "alignment": hud_alignment_var.get(),
            "scale": hud_scale_var.get(),
            "advanced_open": hud_advanced_open.get(),
            "custom_elements": {
                key: var.get()
                for key, var in hud_elements_vars.items()
            }
        }

    except Exception:
        hud_settings = {}

    data = {
        "saved_paths": saved_paths,
        "command_history": command_history,
        "hud_settings": hud_settings,
        "analytics_opt_in": analytics_opt_in,
        "first_device_scan_notice_shown": first_device_scan_notice_shown,
        "window_geometry": root.geometry(),
    }
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Data saved to {DATA_FILE}")
        print(f"Saved data content:\n{json.dumps(data, indent=2)}")
    except Exception as e:
        print("Error saving data:", e)

# === GENERAL GUI HELPERS ===

def ask_analytics_permission():
    global analytics_opt_in

    if analytics_opt_in is not None:
        return

    result = messagebox.askyesno(
        "Help Improve Metal HUD",
        "Would you like to share compatibility data to help improve Metal HUD?\n\n"
        "This includes:\n"
        "• Device model (iPhone/iPad/Apple TV)\n"
        "• App/game name being tested\n\n"
        "No personal information or device identifiers are collected."
    )

    analytics_opt_in = result
    save_data()

def on_close():
    print("on_close called")
    save_data()
    root.destroy()

def disable_text_selection(widget):
    widget.bind("<B1-Motion>", lambda e: "break")
    widget.bind("<Double-Button-1>", lambda e: "break")
    widget.bind("<Triple-Button-1>", lambda e: "break")

    widget.bind("<Shift-Left>", lambda e: "break")
    widget.bind("<Shift-Right>", lambda e: "break")
    widget.bind("<Shift-Up>", lambda e: "break")
    widget.bind("<Shift-Down>", lambda e: "break")

    widget.bind("<Command-a>", lambda e: "break")
    widget.bind("<Control-a>", lambda e: "break")

    widget.configure(takefocus=0)

def show_device_checklist():
    webbrowser.open(
        "https://github.com/mrmacright/Metal-HUD-Mobile-Config#connection-help"
    )

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

def looks_like_xcode_preparing(raw_output: str) -> bool:
    if not raw_output:
        return True

    text = raw_output.lower()

    if "identifier" in text and "state" in text and "model" in text:
        return False

    return any(s in text for s in (
        "waiting for device",
        "connecting",
        "acquired tunnel connection",
    ))

def is_pairing_error(output: str) -> bool:
    if not output:
        return False

    text = output.lower()
    return (
        "must be paired" in text or
        "remotepairingerror" in text or
        "coredeviceerror error 2" in text
    )

def is_device_not_discoverable_error(output: str) -> bool:
    if not output:
        return False

    text = output.lower()
    return (
        "coredeviceservice was unable to locate a device matching the requested device identifier" in text
        or "coredeviceerror error 1011" in text
    )

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

def append_log(text):
    if not launch_output_text.winfo_exists():
        return
    launch_output_text.config(state='normal')
    launch_output_text.insert(tk.END, text)
    trim_log_widget(launch_output_text)
    launch_output_text.see(tk.END)
    launch_output_text.config(state='disabled')

def open_xcode_download():
    subprocess.Popen(["open", "macappstore://itunes.apple.com/app/id497799835"])

# === DEVICE MANAGEMENT ===
def list_devices():
    global FIRST_DEVICE_SCAN_WARNING_SHOWN, first_device_scan_notice_shown, status_clear_time

    if is_using_command_line_tools_only():
        messagebox.showwarning(
            "Xcode Setup Required",
            "Metal HUD needs the full Xcode selected.\n\n"
            "macOS will now ask for administrator approval."
        )
        ensure_xcode_ready_or_exit()

    should_show_first_scan_notice = (
        not first_device_scan_notice_shown
        or is_using_command_line_tools_only()
    )

    if should_show_first_scan_notice and not FIRST_DEVICE_SCAN_WARNING_SHOWN:
        if is_using_command_line_tools_only():
            message = (
                "The first device scan can take a while.\n\n"
                "Metal HUD may need to wait while Apple software finishes installing "
                "because the full Xcode app is being selected.\n\n"
                "Please wait for the loading bar to finish."
            )
        else:
            message = (
                "The first device scan can take a while.\n\n"
                "Xcode may still be preparing the device.\n\n"
                "Please wait for the loading bar to finish."
            )

        messagebox.showinfo("Checking for Devices", message)
        FIRST_DEVICE_SCAN_WARNING_SHOWN = True
        first_device_scan_notice_shown = True
        save_data()

    list_devices_button.config(state="disabled")
    device_progress_bar.pack(fill=tk.X, pady=(0, 10))
    device_progress_bar.start(10)
    status_label.config(
        text="Checking for devices…"
    )
    status_clear_time = time.time() + 2.5

    def background_task():
        attempts = 3
        raw_output = ""

        try:
            for attempt in range(attempts):
                raw_output = run_command("xcrun devicectl list devices")

                if looks_like_xcode_preparing(raw_output):
                    root.after(0, lambda: status_label.config(
                        text="Preparing device / installing Apple software… please wait."
                    ))

                if raw_output and not looks_like_xcode_preparing(raw_output):
                    break

                time.sleep(2)

            lines = raw_output.splitlines()

            content_lines = []
            for line in lines:
                stripped = line.strip()

                if not stripped:
                    continue

                if stripped.startswith("Failed to load provisioning"):
                    continue
                if stripped.startswith("`devicectl manage create`"):
                    continue

                if stripped.startswith("Name") and "Identifier" in stripped:
                    continue
                if set(stripped) <= {"-", " "}:
                    continue

                content_lines.append(line)

            devices = []
            device_ids = {}
            device_info = {}
            device_states = {}

            uuid_like = re.compile(r"^[A-F0-9-]{8,}$", re.I)

            for line in content_lines:
                parts = re.split(r"\s{2,}", line.strip())
                if len(parts) < 5:
                    continue

                name = parts[0].strip()
                identifier = parts[2].strip()
                state = parts[3].strip()
                model = parts[4].strip()

                if not uuid_like.match(identifier):
                    continue

                devices.append({
                    "name": name,
                    "identifier": identifier,
                    "state": state,
                    "model": model
                })

            def device_sort_key(d):
                state = get_display_state_text(d["state"]).lower()

                if state.startswith("available (paired)"):
                    priority = 0
                elif state.startswith("available"):
                    priority = 1
                elif state.startswith("connected"):
                    priority = 2
                elif state.startswith("unavailable"):
                    priority = 3
                else:
                    priority = 99

                return (priority, d["name"].lower())

            devices.sort(key=device_sort_key)

            device_ids.clear()
            device_info.clear()

            for d in devices:
                device_ids[d["name"]] = d["identifier"]
                device_info[d["identifier"]] = d["model"]
                device_states[d["identifier"]] = d["state"]

            def update_ui():
                global DEVICE_INFO_CACHE, DEVICE_STATE_CACHE
                DEVICE_INFO_CACHE = device_info.copy()
                DEVICE_STATE_CACHE = device_states.copy()

                device_lines = []

                if devices:
                    device_lines[:] = [
                        f"{d['name']:<40}  {d['state']:<40}  {d['model']}"
                        for d in devices
                    ]
                    formatted = "\n".join(device_lines).replace("?", "'")
                else:
                    formatted = "No devices found."

            if not devices:
                set_text_widget(
                    device_text,
                    "NO DEVICES WERE FOUND\n\n"
                    "MOST COMMON REASONS:\n"
                    "• Device is not connected via USB\n"
                    "• macOS accessory permission was not allowed\n"
                    "• Device is locked or \"Trust This Computer\" was not accepted\n"
                    "• Xcode is still preparing the device (first connection or after updates)\n\n"
                    "FIX:\n"
                    "1) Connect your iPhone or iPad via USB and unlock it\n"
                    "2) On your Mac, click \"Allow\" if asked to connect the accessory\n"
                    "3) On your device, tap \"Trust This Computer\" if prompted\n"
                    "4) Open Xcode → Window → Devices and Simulators\n"
                    "5) Wait until preparation finishes\n\n"
                    "Then click:\n"
                    "List Devices (Cmd+R)"
                )
                device_udid_combo['values'] = []
                device_udid_var.set("")
                unpair_button.config(state="disabled")
            else:
                render_devices_with_icons(device_text, devices)

                device_text.device_info = device_info

                udids = [d["identifier"] for d in devices]
                device_udid_combo['values'] = udids
                device_udid_var.set(udids[0] if udids else "")

                unpair_button.config(state="normal" if device_ids else "disabled")

                refresh_command_history_combo()

                if devices:
                    highlight_device_row(device_text, 1)
                    device_text.mark_set("insert", "1.0")
                    device_text.see("insert")
                    device_udid_combo.set(devices[0]["identifier"])

                device_text.focus_set()
                device_text.bind("<Up>", lambda e: move_selection(device_text, "up"))
                device_text.bind("<Down>", lambda e: move_selection(device_text, "down"))
                device_text.bind("<Return>", lambda e: show_apps())

            root.after(0, update_ui)

        finally:
            def finish_ui():
                device_progress_bar.stop()
                device_progress_bar.pack_forget()
                list_devices_button.config(state="normal")

                remaining = status_clear_time - time.time()
                if remaining > 0:
                    root.after(int(remaining * 1000), lambda: status_label.config(text=""))
                else:
                    status_label.config(text="")

            root.after(0, finish_ui)

    threading.Thread(target=background_task, daemon=True).start()

def unpair_device():
    """Unpair the selected/highlighted device."""
    udid = device_udid_var.get().strip()
    if not udid:
        messagebox.showwarning("No Device Selected", "Please select a device to unpair.")
        return

    device_display = get_device_display(udid)  
    confirm = messagebox.askyesno("Confirm Unpair", f"Are you sure you want to unpair device {device_display}?")
    if not confirm:
        return

    command = f"xcrun devicectl manage unpair --device {udid}"
    output = run_command(command)

    append_log(output + "\n")

    list_devices()

def refresh_command_history_combo():
    global appname_to_command
    appname_to_command.clear()

    display_entries = []

    for entry in command_history:
        if not isinstance(entry, dict):
            continue

        if "command" not in entry:
            continue

        full_path = entry.get("app_path", "")
        if full_path:
            app_basename = os.path.basename(full_path)
            app_name = app_basename[:-4] if app_basename.endswith(".app") else app_basename
            display_app_name = add_display_name(app_name)
        else:
            display_app_name = "Unknown App"

        device_display = entry.get("device_display") or entry.get("udid") or "Unknown Device"

        display_str = f"{device_display} - {display_app_name}"
        display_entries.append(display_str)
        appname_to_command[display_str] = entry

    command_history_combo["values"] = display_entries

def update_command_history(cmd, udid, app_path):
    entry = {
        "command": cmd,
        "udid": udid,
        "device_display": get_device_display(udid),  
        "app_path": app_path,
        "hud": {
            "preset": hud_preset_var.get(),
            "alignment": hud_alignment_var.get(),
            "scale": hud_scale_var.get(),
            "custom_elements": {
                key: var.get()
                for key, var in hud_elements_vars.items()
            }
        }
    }

    command_history.insert(0, entry)
    command_history[:] = command_history[:10]

    refresh_command_history_combo()
    save_data()

def show_apps():
    global OPEN_GAME_WARNING_SHOWN

    udid = device_udid_combo.get().strip()
    if not udid:
        return

    device_state = get_device_state(udid).lower()

    if device_state == "unavailable":
        set_text_widget(
            apps_text,
            "DEVICE NOT DISCOVERABLE"
        )
        return

# Progress bar and threaded process scan
    progress_bar.pack(fill=tk.X, pady=(0, 10))
    progress_bar.start(10)
    games_status_label.config(text="Searching for games...")

    def background_task():
        try:
            command = f"xcrun devicectl device info processes --device {udid} 2>&1"
            output = run_command(command)
            root.after(0, lambda: process_apps_output(output))
        finally:
            root.after(0, lambda: (
                progress_bar.stop(),
                progress_bar.pack_forget(),
                games_status_label.config(text="")
            ))

    threading.Thread(target=background_task, daemon=True).start()

# === Select game with keyboard ===
last_letter_pressed = None
last_letter_index = -1

def jump_to_app_starting_with(letter):
    global last_letter_pressed, last_letter_index

    apps_text.config(state='normal')
    lines = apps_text.get("1.0", "end-1c").splitlines()

    matches = []
    for i, line in enumerate(lines, start=1):
        if line.lower().startswith(letter.lower()):
            matches.append((i, line))

    if not matches:
        apps_text.config(state='disabled')
        return

    if last_letter_pressed == letter:
        last_letter_index = (last_letter_index + 1) % len(matches)
    else:
        last_letter_pressed = letter
        last_letter_index = 0

    target_line_num, target_line_text = matches[last_letter_index]

    apps_text.tag_remove("selected_app", "1.0", tk.END)
    start = f"{target_line_num}.0"
    end = f"{target_line_num}.end"
    apps_text.tag_add("selected_app", start, end)
    apps_text.see(start)

    full_path = apps_text.full_path_map.get(target_line_text)
    if full_path:
        app_path_combo.set(target_line_text)
        app_path_combo.full_path = full_path
        update_launch_button_text(target_line_text)

    apps_text.config(state='disabled')

def on_apps_keypress(event):
    if not event.char or not event.char.isalpha():
        return
    jump_to_app_starting_with(event.char)

# === FILTER AND UPDATE RUNNING APP LIST ===
def process_apps_output(output):
    global DEVICE_PREPARING_WARNING_SHOWN

    # 1) Pairing error (DEVICE NOT PAIRED)
    if is_pairing_error(output):
        set_text_widget(
            apps_text,
            "DEVICE NOT PAIRED\n\n"
            "This device is visible but not paired.\n\n"
            "FIX:\n"
            "• Unlock the device\n"
            "• Unplug the USB cable\n"
            "• Reconnect the USB cable\n"
            "• Tap “Trust This Computer” if prompted\n\n"
            "Then click:\n"
            "Show Running Games"
        )
        return

    # 2) No processes returned yet (Xcode preparing)
    if not output or not output.strip():
        set_text_widget(
            apps_text,
            "DEVICE PREPARING\n\n"
            "No running games were found yet.\n\n"
            "This is normal the first time a device is connected\n"
            "or after iOS / Xcode updates.\n\n"
            "FIX:\n"
            "• Open Xcode\n"
            "• Window → Devices and Simulators\n"
            "• Wait until preparation finishes\n\n"
            "Then click:\n"
            "Show Running Games"
        )
        return
    
    # 3) Device is ready but no obvious user apps are running
    has_user_app = (
        "Bundle/Application" in output or
        ".app" in output
    )

    if not has_user_app:
        set_text_widget(
            apps_text,
            "NO GAMES DETECTED\n\n"
            "The device is connected and responding,\n"
            "but no user games are currently running.\n\n"
            "FIX:\n"
            "• Launch a game on the device\n"
            "• Ensure it is in the foreground\n"
            "• Click: Show Running Games"
        )
        return

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
        "RedditApp.app", "BlackmagicCam.app", "Cash.app", "Chase.app", "Helix.app", "com.roborock.smart.app", "MintMobile.app", "GooglePhotos.app",
        "Geekbench 6.app", "WeatherViewer.app", "Twitter.app", "narwhal2.app", "OneDrive.app", "To Do.app", "Todoist.app", "CapCut.app", "HelloTalk_Binary.app",
        "Threads.app", "Truecaller.app", "Viber.app", "WeChat.app", "1Password.app", "Microsoft Authenticator.app", "GrokApp.app", "DMSS-GSA.app", "MyDictionary.app",
        "Strava.app", "dictionary-ios.app", "cpkamerasmart.app", "Flo.app", "HikConnect.app", "LegoApp.app", "ReelShort.app", "ReelShort.app", "LegoBuilder.app", "Meesho.app",
        "Paytm.app", "TimeTree.app", "YouTubeMusic.app", "WeatherPlus.app", "Canva.app", "Starbucks WatchKit App.app", "NanoHealthBalance.app", "HeartRate.app.app", "NanoWeather.app"
        "ActivityMonitorApp.app", "CommBankProd.app",
    ]

    unique_apps = {}
    for line in output.splitlines():
        cleaned_line = re.sub(r"^\s*\d+\s+", "", line.strip())
        if cleaned_line:
            match = re.search(r'(/private/var/containers/.+?\.app)', cleaned_line)
            if match:
                full_path = match.group(1)
                app_name = os.path.basename(full_path)
                if app_name in filter_out:
                    continue
                if full_path not in unique_apps:
                    unique_apps[full_path] = app_name

    # === NO USER APPS RUNNING (ONLY SYSTEM PROCESSES FOUND) ===
    if not unique_apps:
        append_log("\n[DEBUG] devicectl output:\n" + output + "\n")
        
        set_text_widget(
            apps_text,
            "NO GAMES DETECTED\n\n"
            "The device is connected and responding,\n"
            "but no user games are currently running.\n\n"
            "FIX:\n"
            "• Launch a game on the device\n"
            "• Ensure it is in the foreground\n"
            "• Click: Show Running Games"
        )
        return

    if unique_apps:
        DEVICE_PREPARING_WARNING_SHOWN = False

    sorted_apps = sorted(unique_apps.items(), key=lambda x: x[1].lower())

    APP_DISPLAY_RENAME = {
        "ShadowTrackerExtra": "PUBG MOBILE",
        "scimitar": "Assassin's Creed Mirage",
        "SolarlandClient": "Farlight 84",
        "hkrpg": "Honkai: Star Rail",
        "bh3oversea": "Honkai Impact 3",
        "X6Game": "Infinity Nikki",
        "ExtremeGame": "PUBG: New State",
        "librdr_1.50.60293175_ios-netflix_ww": "Red Dead Redemption Netflix",
        "librdr_1.50.60293175_ios_ww": "Red Dead Redemption",
        "WWE2K_Apple": "WWE 2K25: Netflix Edition",
        "narutoNext1": "NARUTO: Ultimate Ninja STORM",
        "Civ6_iOS64_Metal_FinalRelease": "CIV 6",
        "cobalt-tv": "Beach Buggy Racing 2",
        "OH2-IOS-Shipping": "Oceanhorn 3",
        "OH2-TVOS-Shipping": "Oceanhorn 3",
        "PrinceofPersiaTheLostCrown": "Prince of Persia The Lost Crown",
        "EasyDeliveryCo.": "Easy Delivery Co.",
        "SubwaySurf": "Subway Surfers",
        "FortniteClient-IOS-Shipping": "Fortnite",
        "GenshinImpact": "Genshin Impact",
        "GRIDLegends": "GRID Legends",
        "TheDivision": "The Division Resurgence",
        "HacPro-IOS-Shipping": "Borderlands Mobile"
    }

    def add_suffix(app_name: str) -> str:
        return f"{app_name}{APP_DISPLAY_SUFFIX[app_name]}" if app_name in APP_DISPLAY_SUFFIX else app_name

    display_names = []
    app_name_to_full_path = {}

    for full_path, app_name in sorted_apps:
        base_name = app_name[:-4] if app_name.endswith(".app") else app_name
        display_name = add_display_name(base_name)
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
    apps_text.bind("<Key>", on_apps_keypress)

# === OUTPUT PROCESSING AND WARNINGS ===
def update_launch_output(output):
    append_log(output + "\n")

    global OPENGL_WARNING_SHOWN
    if not OPENGL_WARNING_SHOWN and "OpenGL" in output:
        OPENGL_WARNING_SHOWN = True
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

    global WUTHERING_WAVES_WARNING_SHOWN
    if (
        not WUTHERING_WAVES_WARNING_SHOWN
        and detect_wuthering_waves_issue(output)
    ):
        WUTHERING_WAVES_WARNING_SHOWN = True
        root.after(0, lambda: messagebox.showwarning(
            "Wuthering Waves – Known Metal HUD Startup Issue",
            "Metal HUD detected a known startup issue with Wuthering Waves.\n\n"
            "When launched with Metal HUD enabled and network access active, "
            "the game may appear frozen on the loading screen and stop responding.\n\n"
            "Workaround (follow carefully):\n"
            "• Launch the game with Metal HUD enabled\n"
            "• If the game appears frozen, temporarily disable Wi-Fi or cellular data\n"
            "• Return to the game without closing it\n"
            "• Wait — the game may look stuck for a long time\n"
            "• When the “No network connection” message appears, re-enable Wi-Fi or cellular data\n"
            "• Return to the game and wait or tap the screen until it connects\n\n"
            "This process can be slow and unreliable, but the game will eventually load "
            "successfully with Metal HUD active."
        ))

# === ANALYTICS, SAVED GAMES, AND HUD CONFIG HELPERS ===

def send_analytics(device_model, app_name, connection_state):
    if not analytics_opt_in:
        return

    def worker():
        try:
            import urllib.request
            import urllib.error

            url = "https://script.google.com/macros/s/AKfycbzfA2LfPx2jyjH5zCFOkcVCkIfVy0PjflU69DA6gYkJXy5spRfA3g9m3Nz-aA7s55Nr/exec"

            payload = json.dumps({
                "device_model": device_model,
                "app_name": app_name,
                "connection_state": connection_state   # ← ADD THIS
            }).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=2) as response:
                response.read()

        except Exception as e:
            print("Analytics send failed:", e)

    threading.Thread(target=worker, daemon=True).start()

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

    saved_paths[name] = {
        'udid': udid,
        'app_path': app_path,
        'hud': {
            'preset': hud_preset_var.get(),
            'alignment': hud_alignment_var.get(),
            'scale': hud_scale_var.get(),
            'custom_elements': {
                key: var.get()
                for key, var in hud_elements_vars.items()
            }
        }
    }

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

# Restore saved game
def on_saved_path_select(event):
    global RESTORING_FROM_PROFILE
    RESTORING_FROM_PROFILE = True

    name = saved_paths_combo.get()
    if name not in saved_paths:
        RESTORING_FROM_PROFILE = False
        return

    entry = saved_paths[name]

    device_udid_combo.set(entry['udid'])

    full_path = entry['app_path']
    app_basename = os.path.basename(full_path)
    app_name = app_basename[:-4] if app_basename.endswith(".app") else app_basename
    display_name = add_display_name(app_name)

    app_path_combo.set(display_name)
    app_path_combo.full_path = full_path
    update_launch_button_text(display_name)

    hud = entry.get('hud')
    if hud:
        hud_preset_var.set(hud.get('preset', 'Default'))
        hud_alignment_var.set(hud.get('alignment', 'Top-Right'))
        hud_scale_var.set(hud.get('scale', 'Default'))

        saved_custom = hud.get('custom_elements', {})
        for key, var in hud_elements_vars.items():
            var.set(saved_custom.get(key, 0))

        on_preset_change()

    RESTORING_FROM_PROFILE = False

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
    elif preset == "Compiled Shaders":
        return {
            "MTL_HUD_ENABLED": "1",
            "MTL_HUD_ELEMENTS": "device,layersize,memory,thermal,fps,gputime,frameinterval,frameintervalgraph,shaders,metalfx"
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
    global current_launch_process

    udid = device_udid_combo.get().strip()
    app_path = getattr(app_path_combo, "full_path", None)

    if not udid or not app_path:
        messagebox.showwarning("Missing Info", "Please select Device and Game")
        return
    
    device_model = get_device_display(udid)

    app_basename = os.path.basename(app_path)
    raw_app_name = app_basename[:-4] if app_basename.endswith(".app") else app_basename
    app_name = add_display_name(raw_app_name)
    connection_state = get_display_state_text(get_device_state(udid))

    alignment = get_alignment_internal()
    preset = hud_preset_var.get()

    env_vars = get_hud_env_vars(preset)
    env_vars["MTL_HUD_ALIGNMENT"] = alignment
    env_vars["MTL_HUD_SCALE"] = hud_scale_map.get(hud_scale_var.get(), "0.4")
    env_json = json.dumps(env_vars)

    base_command = (
        f"xcrun devicectl device process launch "
        f"-e '{env_json}' "
        f"--console --device {udid} \"{app_path}\""
    )

    update_command_history(base_command, udid, app_path)

    send_analytics(device_model, app_name, connection_state)

    try:
        if current_launch_process and current_launch_process.poll() is None:
            current_launch_process.terminate()
            current_launch_process = None
    except Exception:
        pass

    def launch_close_relaunch():
        global current_launch_process

        show_temporary_status_message("Launching app with Metal HUD…")

        first_proc = subprocess.Popen(
            base_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        current_launch_process = first_proc

        time.sleep(1.0)

        show_temporary_status_message("Restarting app with Metal HUD…")

        try:
            first_proc.terminate()
            first_proc.wait(timeout=5)
        except Exception:
            first_proc.kill()

        time.sleep(0.3)

        second_proc = subprocess.Popen(
            base_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        current_launch_process = second_proc

        for line in second_proc.stdout:
            launch_output_text.after(0, lambda l=line: update_launch_output(l))

        try:
            second_proc.stdout.close()
        except Exception:
            pass

        second_proc.wait()
        show_temporary_status_message("App relaunched with Metal HUD.")

    threading.Thread(target=launch_close_relaunch, daemon=True).start()

# === DEVICE AND APP SELECTION HANDLERS ===
def on_device_text_click(event):
    device_text.config(state='normal')

    index = device_text.index(f"@{event.x},{event.y}")
    line_num = int(index.split('.')[0])

    if not hasattr(device_text, "_device_rows"):
        device_text.config(state='disabled')
        return

    if line_num < 1 or line_num > len(device_text._device_rows):
        device_text.config(state='disabled')
        return

    highlight_device_row(device_text, line_num)
    device_udid_combo.set(device_text._device_rows[line_num - 1]["identifier"])

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

    line_start = f"{new_line}.0"
    line_end = f"{new_line}.end"

    if widget == device_text:
        highlight_device_row(widget, new_line)
    else:
        widget.tag_remove("selected_app", "1.0", tk.END)
        widget.tag_add("selected_app", line_start, line_end)

    widget.see(line_start)

    line_text = widget.get(line_start, line_end).strip()

    if widget == device_text and hasattr(widget, "_device_rows"):
        if 1 <= new_line <= len(widget._device_rows):
            device_udid_combo.set(widget._device_rows[new_line - 1]["identifier"])
    elif widget == apps_text and hasattr(widget, "full_path_map"):
        app_name = line_text.strip()
        full_path = widget.full_path_map.get(app_name)
        if full_path:
            app_path_combo.set(app_name)
            app_path_combo.full_path = full_path
            update_launch_button_text(app_name)
    widget.config(state='disabled')

# === Export logs to desktop ===
def export_logs_to_desktop():
    try:
        launch_output_text.config(state='normal')
        log_text = launch_output_text.get("1.0", tk.END).strip()
        launch_output_text.config(state='disabled')

        if not log_text:
            messagebox.showwarning("No Logs", "There are no logs to export.")
            return

        desktop_path = os.path.join(os.path.expanduser("~/Desktop"), "MetalHUD_Logs.txt")

        with open(desktop_path, "w", encoding="utf-8") as f:
            f.write(log_text)

        subprocess.Popen(["open", desktop_path])

        messagebox.showinfo("Logs Exported", f"Saved to Desktop:\nMetalHUD_Logs.txt")

    except Exception as e:
        messagebox.showerror("Export Failed", f"Could not export logs:\n{e}")

# === GUI INITIALIZATION ===

root.title("Metal HUD Mobile Config")
load_data()

root.update_idletasks()

default_width = 1120

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Leave space for menu bar + dock
max_height = screen_height - 120
default_height = min(1000, max_height)

x = (screen_width - default_width) // 2
y = max(20, (screen_height - default_height) // 2)

default_geometry = f"{default_width}x{default_height}+{x}+{y}"

root.geometry(window_geometry_saved or default_geometry)

# Allow proper resizing
root.minsize(1000, 700)
root.resizable(True, True)

resize_save_job = None

def on_window_resize(event):
    global resize_save_job

    if event.widget != root:
        return

    if resize_save_job is not None:
        root.after_cancel(resize_save_job)

    resize_save_job = root.after(500, save_data)

root.bind("<Configure>", on_window_resize)

padx_side = 30

from PIL import Image, ImageTk

connection_icon_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "assets",
    "Connection.png"
)
img = Image.open(connection_icon_path)

base_height = 28
w, h = img.size
new_width = int((base_height / h) * w)

img = img.resize((new_width, base_height), Image.LANCZOS)

list_devices_icon = ImageTk.PhotoImage(img)

# === Scrollable Layout ===

canvas = tk.Canvas(root, highlightthickness=0)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

canvas.configure(yscrollcommand=scrollbar.set)

scrollable_frame = ttk.Frame(canvas)

canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

def on_frame_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

scrollable_frame.bind("<Configure>", on_frame_configure)

def on_canvas_configure(event):
    canvas.itemconfig(canvas_window, width=event.width)

canvas.bind("<Configure>", on_canvas_configure)

# === DEVICES HEADER (label left, help right) ===

# === LIST DEVICES BUTTON + PROGRESS BAR ===
list_devices_frame = ttk.Frame(scrollable_frame)
list_devices_frame.pack(anchor="w", fill="x", padx=padx_side, pady=(25, 0))

list_devices_top_row = ttk.Frame(list_devices_frame)
list_devices_top_row.pack(fill="x")

list_devices_button = tk.Button(
    list_devices_top_row,
    text="List Devices (Cmd+R)",
    command=list_devices,
    image=list_devices_icon,
    compound="left",
    font=default_font,
    padx=12,
    pady=8,
    bd=1,
    relief="raised",
    highlightthickness=0
)
list_devices_button.pack(side="left")

ttk.Button(
    list_devices_top_row,
    text="Connection help",
    command=show_device_checklist
).pack(side="left", padx=(10, 0))

device_progress_bar = ttk.Progressbar(list_devices_frame, mode='indeterminate')
device_progress_bar.pack(fill=tk.X, pady=(8, 0))
device_progress_bar.pack_forget()

status_label = ttk.Label(list_devices_frame, text="", foreground="red")
status_label.pack(anchor="w", pady=(5, 0))

device_text = scrolledtext.ScrolledText(
    scrollable_frame,
    height=10,
    state='disabled',
    padx=2,
    pady=4,
    font=default_font,
    spacing1=2,
    spacing2=2,
    spacing3=2
)
device_text.configure(
    tabs=(
        DEVICE_NAME_TAB_X,
        DEVICE_STATE_TAB_X,
        DEVICE_STATUS_ICON_TAB_X,
        DEVICE_MODEL_TAB_X
    )
)
device_text.tag_configure("selected_device", background="#ffcc66", foreground="black")
device_text.tag_configure("device_row", spacing1=1, spacing3=3)
device_text.pack(fill=tk.BOTH, padx=padx_side, pady=5, expand=True)
device_text.bind("<Button-1>", on_device_text_click)

connection_hint_label = ttk.Label(
    scrollable_frame,
    text="",
    foreground="red",
    anchor="w",
    justify="left",
    wraplength=800
)
connection_hint_label.pack(anchor="w", fill="x", padx=padx_side, pady=(0, 8))

def update_wrap(event):
    connection_hint_label.config(wraplength=event.width - 60)

scrollable_frame.bind("<Configure>", update_wrap)

disable_text_selection(device_text)

device_udid_var = tk.StringVar(value="")

device_udid_combo = ttk.Combobox(
    scrollable_frame,
    textvariable=device_udid_var,
    values=[],
    state="readonly"
)

unpair_button = ttk.Button(scrollable_frame, text="Unpair", command=unpair_device)
unpair_button.pack(anchor="w", padx=padx_side, pady=(0, 10))
unpair_button.config(state="disabled")

# === SHOW RUNNING GAMES UI ===
show_games_frame = ttk.Frame(scrollable_frame)
show_games_frame.pack(anchor="w", fill="x", padx=padx_side, pady=(0, 2))

show_games_button = ttk.Button(
    show_games_frame,
    text="Show Running Games (Cmd+S)",
    command=show_apps
)
show_games_button.pack(anchor="w")

progress_bar = ttk.Progressbar(show_games_frame, mode='indeterminate')
progress_bar.pack(fill=tk.X, pady=(0, 10))
progress_bar.pack_forget()

games_status_label = ttk.Label(show_games_frame, text="", foreground="red")
games_status_label.pack(anchor="w", pady=(5, 0))

# === RUNNING GAMES LIST UI ===
apps_text = scrolledtext.ScrolledText(scrollable_frame, height=7, state='disabled')
apps_text.tag_configure("selected_app", background="#ffcc66", foreground="black")
apps_text.pack(fill=tk.BOTH, padx=padx_side, pady=15, expand=True)
apps_text.bind("<Button-1>", on_apps_text_click)

disable_text_selection(apps_text)

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

ttk.Label(scrollable_frame, text="Saved Games").pack(anchor="w", padx=padx_side)
saved_paths_combo = ttk.Combobox(scrollable_frame, values=sorted(saved_paths.keys()))
saved_paths_combo.pack(fill=tk.X, padx=padx_side, pady=5)
saved_paths_combo.bind("<<ComboboxSelected>>", on_saved_path_select)

ttk.Button(scrollable_frame, text="Delete Saved Game", command=delete_saved_path).pack(anchor="w", padx=padx_side, pady=(0, 10))

def extract_device_and_app_from_command(cmd):
    udid_match = re.search(r"--device\s+([^\s]+)", cmd)
    udid = udid_match.group(1) if udid_match else None

    device_display = udid if udid else "Unknown Device"

    app_match = re.search(r'"([^"]+)"$', cmd)
    if app_match:
        full_path = app_match.group(1)
        app_basename = os.path.basename(full_path)
        app_name = app_basename[:-4] if app_basename.endswith(".app") else app_basename
        display_app_name = add_display_name(app_name)
    else:
        display_app_name = "Unknown App"

    return f"{device_display} - {display_app_name}", cmd

history_display_entries = []
appname_to_command = {}

ttk.Label(scrollable_frame, text="Previous Games").pack(anchor="w", padx=padx_side)
command_history_combo = ttk.Combobox(scrollable_frame, values=[], state="readonly")
command_history_combo.pack(fill=tk.X, padx=padx_side, pady=(0, 10))

refresh_command_history_combo()

def on_command_history_select(event):
    global RESTORING_FROM_PROFILE
    RESTORING_FROM_PROFILE = True

    entry = appname_to_command.get(command_history_combo.get())
    if not entry:
        RESTORING_FROM_PROFILE = False
        return

    device_udid_combo.set(entry["udid"])

    full_path = entry["app_path"]
    app_basename = os.path.basename(full_path)
    app_name = app_basename[:-4] if app_basename.endswith(".app") else app_basename
    display_name = add_display_name(app_name)

    app_path_combo.set(display_name)
    app_path_combo.full_path = full_path
    update_launch_button_text(display_name)

    hud = entry.get("hud", {})
    hud_preset_var.set(hud.get("preset", "Default"))
    hud_alignment_var.set(hud.get("alignment", "Top-Right"))
    hud_scale_var.set(hud.get("scale", "Default"))

    saved_custom = hud.get("custom_elements", {})
    for key, var in hud_elements_vars.items():
        var.set(saved_custom.get(key, 0))

    on_preset_change()

    RESTORING_FROM_PROFILE = False

command_history_combo.bind("<<ComboboxSelected>>", on_command_history_select)

# === HUD STATE VARIABLES (MUST EXIST BEFORE UI) ===
hud_preset_var = tk.StringVar(value="Default")

# === HUD ADVANCED OPTIONS (COLLAPSIBLE) ===

hud_arrow_font = tkfont.Font(size=18, weight="bold")

hud_advanced_open = tk.BooleanVar(value=False)

hud_advanced_header = ttk.Frame(scrollable_frame)
hud_advanced_header.pack(fill="x", padx=padx_side, pady=(10, 5))

hud_arrow_label = ttk.Label(
    hud_advanced_header,
    text="▸",
    font=hud_arrow_font
)
hud_arrow_label.pack(side="left")

hud_advanced_title = ttk.Label(hud_advanced_header, text="HUD Advanced Options")
hud_advanced_title.pack(side="left", padx=(5, 0))

hud_advanced_frame = ttk.Frame(scrollable_frame)

def toggle_hud_advanced(force_state=None, save=True):
    if force_state is None:
        new_state = not hud_advanced_open.get()
    else:
        new_state = force_state

    hud_advanced_open.set(new_state)

    if new_state:
        hud_advanced_frame.pack(fill=tk.X, padx=padx_side)
        hud_arrow_label.config(text="▾")
    else:
        hud_advanced_frame.pack_forget()
        hud_arrow_label.config(text="▸")

    root.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

    if save:
        save_data()

hud_advanced_header.bind("<Button-1>", lambda e: toggle_hud_advanced())
hud_arrow_label.bind("<Button-1>", lambda e: toggle_hud_advanced())
hud_advanced_title.bind("<Button-1>", lambda e: toggle_hud_advanced())

# === HUD PRESETS ===

ttk.Label(hud_advanced_frame, text="HUD Preset").pack(anchor="w")

preset_dropdown = ttk.OptionMenu(
    hud_advanced_frame,
    hud_preset_var,
    "Default",
    "Default",
    "Simple",
    "FPS Only",
    "Thermals",
    "Compiled Shaders",
    "Rich",
    "Full",
    "Custom"
)
preset_dropdown.pack(fill=tk.X, pady=(0, 10))

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

custom_elements_frame = ttk.Frame(hud_advanced_frame)

def clear_hud_elements():
    for var in hud_elements_vars.values():
        var.set(0)

clear_button = ttk.Button(
    hud_advanced_frame,
    text="Clear List",
    command=clear_hud_elements
)

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
    if RESTORING_FROM_PROFILE:
        return

    if hud_preset_var.get() == "Custom":
        custom_elements_frame.pack(fill=tk.X, padx=padx_side, pady=(0,10))
        clear_button.pack(anchor="w", padx=padx_side, pady=(0,10))
    else:
        custom_elements_frame.pack_forget()
        clear_button.pack_forget()

hud_preset_var.trace_add("write", on_preset_change)
on_preset_change()  

# === HUD ALIGNMENT OPTIONS ===

ttk.Label(hud_advanced_frame, text="Set HUD Location").pack(anchor="w", pady=(5, 0))

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
    hud_advanced_frame,
    textvariable=hud_alignment_var,
    values=list(hud_alignment_display_map.keys()),
    state="readonly"
)
hud_alignment_combo.pack(fill=tk.X, pady=(0, 10))

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

ttk.Label(hud_advanced_frame, text="Set HUD Scale").pack(anchor="w")

hud_scale_var = tk.StringVar(value="Default")

hud_scale_options = list(hud_scale_map.keys())

hud_scale_optionmenu = ttk.OptionMenu(
    hud_advanced_frame,
    hud_scale_var,
    hud_scale_var.get(),
    *hud_scale_options
)
hud_scale_optionmenu.pack(fill=tk.X, pady=(0, 10))

# === RESTORE SAVED HUD STATE ===

saved_custom = hud_settings_saved.get("custom_elements", {})
for key, var in hud_elements_vars.items():
    if key in saved_custom:
        var.set(saved_custom[key])

    saved_open = hud_settings_saved.get("advanced_open", False)
    hud_advanced_open.set(saved_open)
    hud_arrow_label.config(text="▾" if saved_open else "▸")

    saved_alignment = hud_settings_saved.get("alignment", "Top-Right")
    saved_alignment_display = hud_alignment_internal_to_display.get(
        saved_alignment,
        saved_alignment
    )
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

# === LOG PANEL CONTROLS ===
def toggle_logs():
    if launch_output_text.winfo_ismapped():
        launch_output_text.pack_forget()
        toggle_log_button.config(text="Show Logs")
    else:
        launch_output_text.pack(fill=tk.BOTH, padx=padx_side, pady=10, expand=True)
        toggle_log_button.config(text="Hide Logs")

toggle_log_button = ttk.Button(scrollable_frame, text="Show Logs", command=toggle_logs)
toggle_log_button.pack(anchor="w", padx=padx_side, pady=(0, 5))
export_logs_button = ttk.Button(scrollable_frame, text="Export Logs", command=export_logs_to_desktop)
export_logs_button.pack(anchor="w", padx=padx_side, pady=(0, 10))

launch_output_text = scrolledtext.ScrolledText(scrollable_frame, height=12, state='disabled')
launch_output_text.pack_forget()

root.bind("<Command-r>", lambda event: list_devices())
root.bind("<Command-s>", lambda event: show_apps())

root.protocol("WM_DELETE_WINDOW", on_close)

root.after(0, lambda: toggle_hud_advanced(
    force_state=hud_settings_saved.get("advanced_open", False),
    save=False
))

root.after(500, ask_analytics_permission)

# === MAINLOOP ===
root.mainloop()