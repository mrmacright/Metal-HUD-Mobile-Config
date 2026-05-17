# ==========================================================
#  METAL HUD MOBILE CONFIG
#  Author: Stewie (MrMacRight)
#  Purpose: Metal HUD iOS launcher GUI & iOS device management
#  Copyright © 2025 Stewie (MrMacRight). All rights reserved.
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
from PIL import Image, ImageTk, ImageEnhance, ImageDraw
import glob
import urllib.request
import urllib.parse
import io
from app_data import (
    APP_DISPLAY_RENAME, METAL_HUD_SUPPORTED, METAL_HUD_UNSUPPORTED, APP_FILTER_OUT,
    APP_STORE_IDS, BUNDLE_IDS, SKIP_ICON_LOOKUP, APP_ICON_SEARCH_NAME, VERSIONED_APP_DISPLAY_NAMES,
    STALE_ICON_CACHE,
)

process = None
current_launch_process = None

CURRENT_VERSION = "4.1.0"
GITHUB_RELEASES_API = "https://api.github.com/repos/mrmacright/Metal-HUD-Mobile-Config/releases/latest"
GITHUB_RELEASES_PAGE = "https://github.com/mrmacright/Metal-HUD-Mobile-Config/releases/latest"

MAX_LOG_LINES = 50000

LOG_FILE_PATH = None
APP_LOG_BUFFER = []

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

# === UPDATE CHECK ===
def check_for_updates():
    def _fetch():
        try:
            req = urllib.request.Request(
                GITHUB_RELEASES_API,
                headers={"User-Agent": "Metal-HUD-Mobile-Config"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            latest = data.get("tag_name", "").lstrip("v")
            current = CURRENT_VERSION.lstrip("v")
            if latest and tuple(int(x) for x in latest.split(".")) > tuple(int(x) for x in current.split(".")):
                root.after(0, lambda: _prompt_update(latest))
        except Exception:
            pass

    def _prompt_update(latest):
        answer = messagebox.askyesno(
            "Update Available",
            f"A new version of Metal HUD Mobile Config is available.\n\n"
            f"Current version:  {CURRENT_VERSION}\n"
            f"Latest version:    {latest}\n\n"
            f"Would you like to download the update?",
            icon="info"
        )
        if answer:
            webbrowser.open(GITHUB_RELEASES_PAGE)

    threading.Thread(target=_fetch, daemon=True).start()

# === DEVICE MODEL CODE → FRIENDLY NAME MAP ===
DEVICE_MODEL_FRIENDLY_NAMES = {
    # iPhone XS / XR
    "iPhone11,2": "iPhone XS",
    "iPhone11,4": "iPhone XS Max",
    "iPhone11,6": "iPhone XS Max Global",
    "iPhone11,8": "iPhone XR",
    # iPhone 11
    "iPhone12,1": "iPhone 11",
    "iPhone12,3": "iPhone 11 Pro",
    "iPhone12,5": "iPhone 11 Pro Max",
    # iPhone 12
    "iPhone13,1": "iPhone 12 Mini",
    "iPhone13,2": "iPhone 12",
    "iPhone13,3": "iPhone 12 Pro",
    "iPhone13,4": "iPhone 12 Pro Max",
    # iPhone 13
    "iPhone14,2": "iPhone 13 Pro",
    "iPhone14,3": "iPhone 13 Pro Max",
    "iPhone14,4": "iPhone 13 Mini",
    "iPhone14,5": "iPhone 13",
    # iPhone SE
    "iPhone12,8": "iPhone SE (2nd generation)",
    "iPhone14,6": "iPhone SE (3rd generation)",
    # iPhone 14
    "iPhone14,7": "iPhone 14",
    "iPhone14,8": "iPhone 14 Plus",
    "iPhone15,2": "iPhone 14 Pro",
    "iPhone15,3": "iPhone 14 Pro Max",
    # iPhone 15
    "iPhone15,4": "iPhone 15",
    "iPhone15,5": "iPhone 15 Plus",
    "iPhone16,1": "iPhone 15 Pro",
    "iPhone16,2": "iPhone 15 Pro Max",
    # iPhone 16
    "iPhone17,1": "iPhone 16 Pro",
    "iPhone17,2": "iPhone 16 Pro Max",
    "iPhone17,3": "iPhone 16",
    "iPhone17,4": "iPhone 16 Plus",
    "iPhone17,5": "iPhone 16e",
    # iPhone 17
    "iPhone18,1": "iPhone 17 Pro",
    "iPhone18,2": "iPhone 17 Pro Max",
    "iPhone18,3": "iPhone 17",
    # iPhone Air
    "iPhone18,4": "iPhone Air",
    # iPad
    "iPad7,5":   "iPad (6th generation)",
    "iPad7,6":   "iPad (6th generation)",
    "iPad7,11":  "iPad (7th generation)",
    "iPad7,12":  "iPad (7th generation)",
    "iPad11,6":  "iPad (8th generation)",
    "iPad11,7":  "iPad (8th generation)",
    "iPad12,1":  "iPad (9th generation)",
    "iPad12,2":  "iPad (9th generation)",
    "iPad13,18": "iPad (10th generation)",
    "iPad13,19": "iPad (10th generation)",
    "iPad15,7":  "iPad (A16)",
    "iPad15,8":  "iPad (A16)",
    # iPad mini
    "iPad11,1": "iPad mini (5th generation)",
    "iPad11,2": "iPad mini (5th generation)",
    "iPad14,1": "iPad mini (6th generation)",
    "iPad14,2": "iPad mini (6th generation)",
    "iPad16,1": "iPad mini (A17 Pro)",
    "iPad16,2": "iPad mini (A17 Pro)",
    # iPad Air
    "iPad11,3":  "iPad Air (3rd generation)",
    "iPad11,4":  "iPad Air (3rd generation)",
    "iPad13,1":  "iPad Air (4th generation)",
    "iPad13,2":  "iPad Air (4th generation)",
    "iPad13,16": "iPad Air (5th generation)",
    "iPad13,17": "iPad Air (5th generation)",
    "iPad14,8":  "iPad Air 11-inch (M2)",
    "iPad14,9":  "iPad Air 11-inch (M2)",
    "iPad14,10": "iPad Air 13-inch (M2)",
    "iPad14,11": "iPad Air 13-inch (M2)",
    "iPad15,3":  "iPad Air 11-inch (M3)",
    "iPad15,4":  "iPad Air 11-inch (M3)",
    "iPad15,5":  "iPad Air 13-inch (M3)",
    "iPad15,6":  "iPad Air 13-inch (M3)",
    "iPad16,7":  "iPad Air 11-inch (M4)",
    "iPad16,8":  "iPad Air 11-inch (M4)",
    # iPad Pro
    "iPad7,1":  "iPad Pro (12.9-inch) (2nd generation)",
    "iPad7,2":  "iPad Pro (12.9-inch) (2nd generation)",
    "iPad7,3":  "iPad Pro (10.5-inch)",
    "iPad7,4":  "iPad Pro (10.5-inch)",
    "iPad8,1":  "iPad Pro (11-inch) (1st generation)",
    "iPad8,2":  "iPad Pro (11-inch) (1st generation)",
    "iPad8,3":  "iPad Pro (11-inch) (1st generation)",
    "iPad8,4":  "iPad Pro (11-inch) (1st generation)",
    "iPad8,5":  "iPad Pro (12.9-inch) (3rd generation)",
    "iPad8,6":  "iPad Pro (12.9-inch) (3rd generation)",
    "iPad8,7":  "iPad Pro (12.9-inch) (3rd generation)",
    "iPad8,8":  "iPad Pro (12.9-inch) (3rd generation)",
    "iPad8,9":  "iPad Pro (11-inch) (2nd generation)",
    "iPad8,10": "iPad Pro (11-inch) (2nd generation)",
    "iPad8,11": "iPad Pro (12.9-inch) (4th generation)",
    "iPad8,12": "iPad Pro (12.9-inch) (4th generation)",
    "iPad13,4": "iPad Pro (11-inch) (3rd generation)",
    "iPad13,5": "iPad Pro (11-inch) (3rd generation)",
    "iPad13,6": "iPad Pro (11-inch) (3rd generation)",
    "iPad13,7": "iPad Pro (11-inch) (3rd generation)",
    "iPad13,8":  "iPad Pro (12.9-inch) (5th generation)",
    "iPad13,9":  "iPad Pro (12.9-inch) (5th generation)",
    "iPad13,10": "iPad Pro (12.9-inch) (5th generation)",
    "iPad13,11": "iPad Pro (12.9-inch) (5th generation)",
    "iPad14,3": "iPad Pro (11-inch) (4th generation)",
    "iPad14,4": "iPad Pro (11-inch) (4th generation)",
    "iPad14,5": "iPad Pro (12.9-inch) (6th generation)",
    "iPad14,6": "iPad Pro (12.9-inch) (6th generation)",
    "iPad16,3": "iPad Pro 11-inch (M4)",
    "iPad16,4": "iPad Pro 11-inch (M4)",
    "iPad16,5": "iPad Pro 13-inch (M4)",
    "iPad16,6": "iPad Pro 13-inch (M4)",
    "iPad17,1": "iPad Pro 11-inch (M5)",
    "iPad17,2": "iPad Pro 11-inch (M5)",
    "iPad17,3": "iPad Pro 13-inch (M5)",
    "iPad17,4": "iPad Pro 13-inch (M5)",
    # Apple TV
    "AppleTV5,3":  "Apple TV (4th generation)",
    "AppleTV6,2":  "Apple TV 4K",
    "AppleTV11,1": "Apple TV 4K (2nd generation)",
    "AppleTV14,1": "Apple TV 4K (3rd generation)",
}

def resolve_model_display(model: str) -> str:
    """If model is a raw code in DEVICE_MODEL_FRIENDLY_NAMES, return 'Friendly Name (ModelCode)'; otherwise return model unchanged."""
    friendly = DEVICE_MODEL_FRIENDLY_NAMES.get(model)
    if friendly:
        return f"{friendly} ({model})"
    return model

# === ENVIRONMENT VARIABLES AND GLOBAL FLAGS ===
os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ["LANG"] = "en_US.UTF-8"

DEVICE_INFO_CACHE = {}
DEVICE_STATE_CACHE = {}
APP_DISPLAY_SUFFIX = {}
LAST_DEVICE_SCAN = []

DEVICE_ICON_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "assets",
    "UI",
    "Devices"
)

CONNECTION_ICON_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "assets",
    "UI",
    "Wireless State"
)

DEVICE_ICON_CACHE = {}
CONNECTION_ICON_CACHE = {}

ICON_CACHE_DIR = os.path.expanduser("~/.cache/metal-hud-icons")
GAME_ICON_PIL_CACHE   = {}   
GAME_ICON_PHOTO_CACHE = {}   
GAME_ICON_URL_MAP     = {}   
GAME_LIST_GENERATION  = [0]  
LIVE_BUNDLE_ID_MAP    = {}  
LIVE_DISPLAY_NAME_MAP = {}   

DEVICE_NAME_MAX_PX = 150
DEVICE_STATE_MAX_PX = 260

DEVICE_NAME_TAB_X = 50
DEVICE_STATE_TAB_X = 230
DEVICE_STATUS_ICON_TAB_X = 454
DEVICE_MODEL_TAB_X = 390

DEVICE_ICON_SLOT_WIDTH = 48
DEVICE_ICON_SLOT_HEIGHT = 34

CONNECTION_ICON_SLOT_WIDTH = 26
CONNECTION_ICON_SLOT_HEIGHT = 23

STATE_ICON_NAME_MAP = {
    "available": "Available (preparing)",
    "available (paired)": "available (paired + wireless)",
    "unavailable": "Unavailable",
    "connected": "Connected",
    "connected (no ddi)": "Connected (limited support)",
    "unsupported": "Unsupported",
}

APP_LAST_DETECTED = {}  
_current_apps_data = []  
hidden_apps = set()
pinned_apps = set()
_apps_search_var = None  
_apps_sort_var = None    

OPEN_GAME_WARNING_SHOWN = False
DEVICE_PREPARING_WARNING_SHOWN = False
RESTORING_FROM_PROFILE = False
OPENGL_WARNING_SHOWN = False
XCODE_VERSION_WARNING_SHOWN = False
FIRST_DEVICE_SCAN_WARNING_SHOWN = False
PAIRING_ATTEMPTS = 0

REQUIRED_XCODE_VERSION = "26.5"

xcode_overlay = None
xcode_overlay_icon = None
xcode_poll_job = None
xcode_status_var = None
startup_finished = False

# === LOG AND DEVICE DETECTION HELPERS ===
_GREEN = "#34C759"

def _metal_hud_status(internal, display):
    if internal in METAL_HUD_SUPPORTED or display in METAL_HUD_SUPPORTED:
        return ("Supports Metal HUD", _GREEN)
    if internal in METAL_HUD_UNSUPPORTED or display in METAL_HUD_UNSUPPORTED:
        return ("Metal HUD Unsupported", _RED)
    return None

for _bn in STALE_ICON_CACHE:
    try:
        os.remove(os.path.join(ICON_CACHE_DIR, f"{_bn}.png"))
    except Exception:
        pass

for _f in glob.glob(os.path.join(ICON_CACHE_DIR, "librdr_*.png")):
    try:
        os.remove(_f)
    except Exception:
        pass

# === APP DISPLAY AND DEVICE INFO HELPERS ===
def add_display_name(app_name: str) -> str:
    if app_name in APP_DISPLAY_RENAME:
        return APP_DISPLAY_RENAME[app_name]
    return LIVE_DISPLAY_NAME_MAP.get(app_name, app_name)

def make_unique_app_names(app_list):
    display_list = []

    for app in app_list:
        display_list.append(add_display_name(app))

    return display_list, app_list

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
            model = resolve_model_display(m.group(4).strip())
            cache[udid] = model
    return cache

def get_device_display(udid: str) -> str:
    """Return 'Model' for a UDID, refreshing cache if needed."""
    global DEVICE_INFO_CACHE
    if not udid:
        return "Unknown Device"
    if udid not in DEVICE_INFO_CACHE:
        try:
            new_cache = _fetch_device_info_map()
            if new_cache:
                DEVICE_INFO_CACHE = new_cache
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

    if text.startswith("Apple Vision"):
        return "Apple Vision"

    if text.startswith("Apple TV") or text.startswith("AppleTV"):
        return "Apple TV"

    if text.startswith("Watch") or text.startswith("Apple Watch"):
        return "Apple Watch"

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
            filename = "available (pairing required)"
        elif normalized == "available":
            filename = "Available (preparing)"
        elif "available (paired)" in normalized:
            filename = "available (paired + wireless)"
        elif normalized == "unsupported":
            filename = "Unsupported"
        elif normalized.startswith("connected"):
            filename = "Connected"
        elif normalized.startswith("unavailable"):
            filename = "Unavailable"
        else:
            filename = "Connected"

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

        img = ImageEnhance.Sharpness(img).enhance(1.2)

        image = ImageTk.PhotoImage(img)
        CONNECTION_ICON_CACHE[path] = image
        return image

    except Exception as e:
        print(f"Could not load connection icon from {path}: {e}")
        return None

def _disk_icon_path(internal_name):
    return os.path.join(ICON_CACHE_DIR, f"{internal_name}.png")

def _disk_icon_url_path(internal_name):
    return os.path.join(ICON_CACHE_DIR, f"{internal_name}.url")

def _shorten_mzstatic_url(url):
    """Normalise Apple CDN URL to 100x100 — keeps the filename segment (required by CDN)."""
    if not url or "mzstatic.com" not in url:
        return url
    return re.sub(r'/\d+x\d+bb\.jpg$', '/100x100bb.jpg', url)

def _itunes_lookup(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Metal-HUD-Mobile-Config"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
        results = data.get("results", [])
        if results:
            raw = results[0].get("artworkUrl512") or results[0].get("artworkUrl100")
            return _shorten_mzstatic_url(raw)
    except Exception:
        pass
    return None

def _backfill_icon_urls():
    """Background thread: generate missing .url sidecars for already-cached icons."""
    if not os.path.isdir(ICON_CACHE_DIR):
        return
    for fname in os.listdir(ICON_CACHE_DIR):
        if not fname.endswith(".png"):
            continue
        internal = fname[:-4]
        url_path = _disk_icon_url_path(internal)
        if os.path.exists(url_path):
            continue
        artwork_url = None
        app_id = APP_STORE_IDS.get(internal)
        if app_id:
            artwork_url = _itunes_lookup(f"https://itunes.apple.com/lookup?id={app_id}")
        if not artwork_url:
            bundle_id = BUNDLE_IDS.get(internal)
            if bundle_id:
                artwork_url = _itunes_lookup(
                    f"https://itunes.apple.com/lookup?bundleId={urllib.parse.quote(bundle_id)}"
                )
        if not artwork_url:
            search_name = APP_ICON_SEARCH_NAME.get(internal) or APP_DISPLAY_RENAME.get(internal)
            if not search_name and internal not in SKIP_ICON_LOOKUP:
                search_name = internal
            if search_name:
                safe = urllib.parse.quote(search_name)
                artwork_url = _itunes_lookup(
                    f"https://itunes.apple.com/search?term={safe}&entity=software&limit=1"
                )
        if artwork_url:
            try:
                with open(url_path, "w") as _uf:
                    _uf.write(artwork_url)
                GAME_ICON_URL_MAP[internal] = artwork_url
            except Exception:
                pass

def _fetch_bundle_id_map(udid):
    """Query devicectl for installed apps; return (bundle_map, name_map). Background-safe."""
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "metal-hud-apps.json")
    try:
        result = subprocess.run(
            ["xcrun", "devicectl", "device", "info", "apps",
             "--device", udid, "--include-removable-apps", "-j", tmp],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        if result.returncode != 0:
            err = result.stderr.decode(errors="replace").strip()
            append_log(f"[BundleMap] devicectl apps failed (code {result.returncode}): {err}\n")
            return {}, {}
        with open(tmp) as f:
            data = json.load(f)
        bundle_map = {}
        name_map = {}
        for app in data.get("result", {}).get("apps", []):
            url = app.get("url", "")
            bundle_id = app.get("bundleIdentifier", "")
            display_name = app.get("name", "")
            if url and bundle_id:
                basename = os.path.basename(url.rstrip("/"))
                if basename.endswith(".app"):
                    internal = basename[:-4]
                    bundle_map[internal] = bundle_id
                    if display_name:
                        name_map[internal] = display_name
        append_log(f"[BundleMap] loaded {len(bundle_map)} apps from device\n")
        for _k in sorted(bundle_map.keys()):
            append_log(f"[BundleMap]   {_k}: {bundle_map[_k]}\n")
        return bundle_map, name_map
    except subprocess.TimeoutExpired:
        append_log("[BundleMap] devicectl apps timed out (>30s)\n")
        return {}, {}
    except Exception as e:
        append_log(f"[BundleMap] error: {e}\n")
        return {}, {}
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass

def _round_icon(img, radius_pct=0.27):
    """Apply smooth rounded-corner mask (supersampled for anti-aliased edges)."""
    size = img.size
    scale = 4
    big = (size[0] * scale, size[1] * scale)
    radius = int(size[0] * radius_pct * scale)
    mask = Image.new("L", big, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, big[0] - 1, big[1] - 1), radius=radius, fill=255)
    mask = mask.resize(size, Image.LANCZOS)
    result = img.copy()
    result.putalpha(mask)
    return result

def _fetch_game_icon_pil(internal_name, display_name=None):
    """Background-safe. Returns a 26×26 PIL.Image or None on failure."""
    live_bundle_id = LIVE_BUNDLE_ID_MAP.get(internal_name)
    live_display_name = LIVE_DISPLAY_NAME_MAP.get(internal_name)

    if not live_display_name:
        for _prefix, _known in VERSIONED_APP_DISPLAY_NAMES.items():
            if internal_name.startswith(_prefix):
                live_display_name = _known
                break
    if internal_name in SKIP_ICON_LOOKUP and not live_bundle_id and not live_display_name:
        return None

    if internal_name in GAME_ICON_PIL_CACHE:
        return GAME_ICON_PIL_CACHE[internal_name]

    disk_path = _disk_icon_path(internal_name)
    if os.path.exists(disk_path):
        try:
            img = _round_icon(Image.open(disk_path).convert("RGBA").resize((40, 40), Image.LANCZOS))
            GAME_ICON_PIL_CACHE[internal_name] = img
            url_path = _disk_icon_url_path(internal_name)
            if os.path.exists(url_path):
                try:
                    with open(url_path) as _uf:
                        GAME_ICON_URL_MAP[internal_name] = _shorten_mzstatic_url(_uf.read().strip())
                except Exception:
                    pass
            append_log(f"[Icon] {internal_name}: loaded from disk cache\n")
            return img
        except Exception:
            pass

    artwork_url = None
    icon_source = None

    app_id = APP_STORE_IDS.get(internal_name)
    if app_id:
        artwork_url = _itunes_lookup(f"https://itunes.apple.com/lookup?id={app_id}")
        if artwork_url:
            icon_source = f"App Store ID {app_id}"

    if not artwork_url:
        bundle_id = BUNDLE_IDS.get(internal_name)
        if bundle_id:
            artwork_url = _itunes_lookup(
                f"https://itunes.apple.com/lookup?bundleId={urllib.parse.quote(bundle_id)}"
            )
            if artwork_url:
                icon_source = f"bundle ID {bundle_id}"

    if not artwork_url and live_display_name and internal_name not in SKIP_ICON_LOOKUP:
        safe = urllib.parse.quote(live_display_name)
        artwork_url = _itunes_lookup(
            f"https://itunes.apple.com/search?term={safe}&entity=software&limit=1"
        )
        if artwork_url:
            icon_source = f"live display name search \"{live_display_name}\""

    if not artwork_url and live_bundle_id:
        artwork_url = _itunes_lookup(
            f"https://itunes.apple.com/lookup?bundleId={urllib.parse.quote(live_bundle_id)}"
        )
        if artwork_url:
            icon_source = f"bundle ID {live_bundle_id}"

    if not artwork_url:
        if internal_name in SKIP_ICON_LOOKUP:
            search_term = live_display_name  
        else:
            search_term = APP_ICON_SEARCH_NAME.get(internal_name, display_name)
            if search_term == live_display_name:
                search_term = None 
        if search_term:
            safe = urllib.parse.quote(search_term)
            artwork_url = _itunes_lookup(
                f"https://itunes.apple.com/search?term={safe}&entity=software&limit=1"
            )
            if artwork_url:
                icon_source = f"name search \"{search_term}\""

    if not artwork_url:
        append_log(f"[Icon] {internal_name}: no icon found, using generic\n")
        return None

    try:
        with urllib.request.urlopen(artwork_url, timeout=5) as img_resp:
            img_data = img_resp.read()
        os.makedirs(ICON_CACHE_DIR, exist_ok=True)
        with open(disk_path, "wb") as f:
            f.write(img_data)
        try:
            with open(_disk_icon_url_path(internal_name), "w") as _uf:
                _uf.write(artwork_url)
        except Exception:
            pass
        GAME_ICON_URL_MAP[internal_name] = artwork_url
        img = _round_icon(Image.open(io.BytesIO(img_data)).convert("RGBA").resize((40, 40), Image.LANCZOS))
        GAME_ICON_PIL_CACHE[internal_name] = img
        append_log(f"[Icon] {internal_name}: fetched via {icon_source}\n")
        return img
    except Exception:
        return None

def _get_game_icon_photo(internal_name):
    """Main-thread only. Converts cached PIL image to PhotoImage, or returns None."""
    if internal_name in GAME_ICON_PHOTO_CACHE:
        return GAME_ICON_PHOTO_CACHE[internal_name]
    pil = GAME_ICON_PIL_CACHE.get(internal_name)
    if pil:
        photo = ImageTk.PhotoImage(pil)
        GAME_ICON_PHOTO_CACHE[internal_name] = photo
        return photo
    return None

def get_display_state_text(state: str) -> str:
    original_state = (state or "").replace("?", "'")
    normalized_state = original_state.lower()

    if normalized_state == "available":
        return "available (preparing)"

    if normalized_state == "available (pairing)":
        return "available (pairing required)"

    if normalized_state == "available (paired)":
        return "available (paired + wireless)"

    if "no ddi" in normalized_state:
        return "Connected (limited support)"

    if normalized_state.startswith("connected"):
        return "Connected"

    if normalized_state.startswith("unavailable"):
        return "unavailable (device offline)"

    if normalized_state == "unsupported":
        return "Device Unsupported"

    return original_state

def truncate_text_to_px(text: str, max_px: int, font) -> str:
    text = (text or "").replace("?", "'")
    ellipsis = "…"

    if font.measure(text) <= max_px:
        return text

    while text and font.measure(text + ellipsis) > max_px:
        text = text[:-1]

    return text.rstrip() + ellipsis

def update_show_games_button_text(device):
    if not device:
        show_games_button.config(text="Show Running Games (Cmd+S)")
        return

    model = device["model"].replace("?", "'")
    show_games_button.config(text=f"Show games on {model}")



def highlight_device_row(widget, line_num):
    selected_bg = _SELECTION
    normal_bg = widget.cget("background")

    widget.config(state='normal')
    widget.tag_remove("selected_device", "1.0", tk.END)
    widget.tag_add("selected_device", f"{line_num}.0", f"{line_num}.end")
    widget.config(state='disabled')

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

def build_device_row_right_text(device: dict) -> str:
    return f"\t{device['model']}".replace("?", "'")


def render_devices_with_icons(widget, devices):
    render_device_headers(widget)

    widget._selected_device_index = 0
    widget._device_select_callbacks = []
    widget._device_rows = list(devices)

    NAME_COL_WIDTH = 220
    STATE_COL_WIDTH = 180
    WIFI_COL_WIDTH = 60
    MODEL_COL_WIDTH = 300
    MORE_COL_WIDTH = 32
    NAME_TEXT_MAX_PX = 170

    row_font = tkfont.Font(font=_FONT_BODY)

    for i, d in enumerate(devices):
        row = tk.Frame(widget, bg=_SURFACE, height=44)
        row.pack(fill="x")
        row.pack_propagate(False)

        device_icon = get_device_icon(d["model"])
        connection_icon = get_connection_icon(d["state"])

        name_cell = tk.Frame(row, bg=_SURFACE, width=NAME_COL_WIDTH, height=46)
        name_cell.grid(row=0, column=0, sticky="w")
        name_cell.grid_propagate(False)

        ICON_SLOT_WIDTH = 40  

        icon_slot = tk.Frame(name_cell, width=ICON_SLOT_WIDTH, height=46, bg=_SURFACE)
        icon_slot.pack(side="left")
        icon_slot.pack_propagate(False)

        if device_icon:
            icon_label = tk.Label(icon_slot, image=device_icon, bg=_SURFACE, bd=0)
            icon_label.image = device_icon
            icon_label.place(relx=0.5, rely=0.5, anchor="center")
            icon_spacer = tk.Frame(name_cell, width=12, bg=_SURFACE)
            icon_spacer.pack(side="left")

        name_text = truncate_text_to_px(
            d["name"].replace("?", "'"),
            NAME_TEXT_MAX_PX,
            row_font
        )

        tk.Label(
            name_cell,
            text=name_text,
            bg=_SURFACE,
            fg=_ACCENT,
            font=_FONT_BODY
        ).pack(side="left")

        state_cell = tk.Frame(row, bg=_SURFACE, width=STATE_COL_WIDTH, height=46)
        state_cell.grid(row=0, column=1, sticky="w")
        state_cell.grid_propagate(False)

        tk.Label(
            state_cell,
            text=get_display_state_text(d["state"]),
            bg=_SURFACE,
            fg=_FG_PRIMARY,
            font=_FONT_BODY
        ).pack(side="left")

        wifi_cell = tk.Frame(row, bg=_SURFACE, width=WIFI_COL_WIDTH, height=46)
        wifi_cell.grid(row=0, column=2, sticky="w")
        wifi_cell.grid_propagate(False)

        if connection_icon:
            wifi_label = tk.Label(wifi_cell, image=connection_icon, bg=_SURFACE, bd=0)
            wifi_label.image = connection_icon
            wifi_label.pack(side="left")

        model_cell = tk.Frame(row, bg=_SURFACE, width=MODEL_COL_WIDTH, height=46)
        model_cell.grid(row=0, column=3, sticky="w")
        model_cell.grid_propagate(False)

        tk.Label(
            model_cell,
            text=d["model"].replace("?", "'"),
            bg=_SURFACE,
            fg=_FG_PRIMARY,
            font=_FONT_BODY
        ).pack(side="left")

        more_btn = tk.Label(
            row,
            text="⋮",
            bg=_SURFACE,
            fg=_FG_SECONDARY,
            font=("SF Pro Text", 18),
            bd=0
        )
        more_btn.grid(row=0, column=4, sticky="e", padx=(8, 4))

        def make_more_menu(device, btn):
            def show_menu(event):
                menu = tk.Menu(widget, tearoff=0)
                menu.add_command(
                    label="Check Connection",
                    command=lambda: show_connection_help(scroll_to="sec_connstates")
                )
                menu.add_separator()
                menu.add_command(
                    label=f"Unpair {device['name']}",
                    foreground=_RED,
                    command=lambda: (device_udid_var.set(device["identifier"]), unpair_device())
                )
                menu.tk_popup(event.x_root, event.y_root)

            btn.bind("<Button-1>", show_menu)

        def select_row(event=None, device=d, selected_row=row, index=i):
            widget._selected_device_index = index
            device_udid_var.set(device["identifier"])
            device_udid_combo.set(device["identifier"])
            update_show_games_button_text(device)

            def set_bg_recursive(w, color):
                try:
                    w.config(bg=color)
                except Exception:
                    pass

                for child in w.winfo_children():
                    set_bg_recursive(child, color)

            for child_row in widget.winfo_children():
                if isinstance(child_row, tk.Frame) and not getattr(child_row, "_is_separator", False):
                    set_bg_recursive(child_row, _SURFACE)

            set_bg_recursive(selected_row, _SELECTION)

            connection_hint_label.config(text="")

            widget.focus_set()
            return "break"

        def bind_row_click(widget_to_bind):
            if widget_to_bind is more_btn:
                return

            widget_to_bind.bind("<Button-1>", select_row)

            for child in widget_to_bind.winfo_children():
                bind_row_click(child)

        bind_row_click(row)

        make_more_menu(d, more_btn)

        for col, size in [(0, NAME_COL_WIDTH), (1, STATE_COL_WIDTH), (2, WIFI_COL_WIDTH), (3, MODEL_COL_WIDTH), (4, MORE_COL_WIDTH)]:
            row.grid_columnconfigure(col, minsize=size)

        widget._device_select_callbacks.append(select_row)

        if i < len(devices) - 1:
            sep = tk.Frame(widget, bg=_BORDER, height=1)
            sep._is_separator = True
            sep.pack(fill="x")

    def select_device_by_index(index):
        if not widget._device_select_callbacks:
            return "break"

        index = max(0, min(index, len(widget._device_select_callbacks) - 1))
        widget._selected_device_index = index
        widget._device_select_callbacks[index]()

        return "break"

    def device_key_up(event):
        return select_device_by_index(widget._selected_device_index - 1)

    def device_key_down(event):
        return select_device_by_index(widget._selected_device_index + 1)

    widget.bind("<Up>", device_key_up)
    widget.bind("<Down>", device_key_down)
    widget.bind("<Button-1>", lambda e: widget.focus_set())
    widget.configure(takefocus=1)
    widget.after(50, lambda: widget.focus_set())

def get_xcode_version():
    xcode_app = find_xcode_app()
    if not xcode_app:
        return None

    xcodebuild_path = os.path.join(
        xcode_app,
        "Contents",
        "Developer",
        "usr",
        "bin",
        "xcodebuild"
    )

    if not os.path.exists(xcodebuild_path):
        return None

    try:
        out = subprocess.check_output(
            [xcodebuild_path, "-version"],
            text=True,
            stderr=subprocess.DEVNULL
        )
        match = re.search(r"Xcode\s+([0-9]+(?:\.[0-9]+)*)", out)
        if match:
            return match.group(1)
    except Exception:
        pass

    return None

def version_tuple(v):
    return tuple(int(x) for x in v.split("."))


def check_xcode_version_or_exit():
    xcode_app = find_xcode_app()
    if not xcode_app:
        show_xcode_overlay(
            title="Xcode Required",
            message=f"This app requires Xcode {REQUIRED_XCODE_VERSION} or later.",
            button_text="Open App Store",
            status_text="Please install Xcode to continue."
        )
        return False

    current = get_xcode_version()

    if not current:
        show_xcode_overlay(
            title="Xcode Version Unknown",
            message=(
                "Could not determine the installed Xcode version.\n\n"
                f"This app requires Xcode {REQUIRED_XCODE_VERSION} or later."
            ),
            button_text="Open App Store",
            status_text="Please install or update Xcode to continue."
        )
        return False

    try:
        current_tuple = version_tuple(current)
        min_tuple = version_tuple(REQUIRED_XCODE_VERSION)
    except Exception:
        show_xcode_overlay(
            title="Xcode Version Error",
            message=(
                f"Could not parse Xcode version: {current}\n\n"
                f"This app requires Xcode {REQUIRED_XCODE_VERSION} or later."
            ),
            button_text="Open App Store",
            status_text="Please install or update Xcode to continue."
        )
        return False

    if current_tuple < min_tuple:
        show_xcode_overlay(
            title=f"Detected: Xcode {current}",
            message=f"This app requires Xcode {REQUIRED_XCODE_VERSION} or later.",
            button_text="Update Xcode",
            status_text="Waiting for Xcode to be updated…"
        )
        return False

    return True

locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

def resource_path(*parts):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), *parts)


def find_xcode_app():
    for app_path in sorted(glob.glob("/Applications/Xcode*.app")):
        xcodebuild_path = os.path.join(
            app_path,
            "Contents",
            "Developer",
            "usr",
            "bin",
            "xcodebuild"
        )
        if os.path.exists(xcodebuild_path):
            return app_path
    return None


def is_xcode_installed():
    return find_xcode_app() is not None

def open_xcode_app_store():
    global xcode_poll_job

    subprocess.Popen(["open", "macappstore://itunes.apple.com/app/id497799835"])

    if xcode_status_var is not None:
        xcode_status_var.set("Waiting for Xcode to be installed or updated...")

    if xcode_poll_job is None:
        start_xcode_install_poll()

def show_xcode_overlay(
    title="This app requires Xcode.",
    message="",
    button_text="Download Xcode",
    status_text="This screen will close automatically once Xcode is installed."
):
    global xcode_overlay, xcode_overlay_icon, xcode_status_var

    if xcode_overlay and xcode_overlay.winfo_exists():
        xcode_overlay.destroy()

    xcode_overlay = tk.Frame(root, bg=_SURFACE)
    xcode_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
    xcode_overlay.lift()

    panel = tk.Frame(
        xcode_overlay,
        bg=_SURFACE,
        bd=0,
        highlightthickness=0,
    )
    panel.place(relx=0.5, rely=0.5, anchor="center", width=700, height=360)

    icon_path = resource_path("assets", "UI", "Xcode.png")
    if os.path.exists(icon_path):
        img = Image.open(icon_path).convert("RGBA")
        img.thumbnail((120, 120), Image.LANCZOS)
        xcode_overlay_icon = ImageTk.PhotoImage(img)

        tk.Label(
            panel,
            image=xcode_overlay_icon,
            bg=_SURFACE
        ).pack(pady=(35, 16))

    tk.Label(
        panel,
        text=title,
        bg=_SURFACE,
        fg=_FG_PRIMARY,
        justify="center",
        font=("SF Pro Display", 22, "bold")
    ).pack(pady=(0, 10))

    tk.Label(
        panel,
        text=message,
        bg=_SURFACE,
        fg=_FG_SECONDARY,
        justify="center",
        wraplength=560,
        font=("SF Pro Text", 14)
    ).pack(pady=(0, 12))

    xcode_status_var = tk.StringVar(value=status_text)

    tk.Label(
        panel,
        textvariable=xcode_status_var,
        bg=_SURFACE,
        fg=_FG_TERTIARY,
        justify="center",
        wraplength=560,
        font=("SF Pro Text", 12)
    ).pack(pady=(0, 18))

    ttk.Button(
        panel,
        text=button_text,
        command=open_xcode_app_store,
        style="Accent.TButton",
    ).pack()

    start_xcode_install_poll()

def hide_xcode_overlay():
    global xcode_overlay, xcode_poll_job

    if xcode_poll_job is not None:
        root.after_cancel(xcode_poll_job)
        xcode_poll_job = None

    if xcode_overlay and xcode_overlay.winfo_exists():
        xcode_overlay.destroy()

    xcode_overlay = None

def start_xcode_install_poll():
    poll_for_xcode_install()

def poll_for_xcode_install():
    global xcode_poll_job

    if is_xcode_installed():
        current = get_xcode_version()
        if current:
            try:
                if version_tuple(current) >= version_tuple(REQUIRED_XCODE_VERSION):
                    hide_xcode_overlay()
                    finish_startup_after_xcode()
                    return
                else:
                    if xcode_status_var is not None:
                        xcode_status_var.set(
                            f"Waiting for Xcode {REQUIRED_XCODE_VERSION} or later..."
                        )
            except Exception:
                pass

    xcode_poll_job = root.after(3000, poll_for_xcode_install)

def finish_startup_after_xcode():
    global startup_finished

    if startup_finished:
        return

    ensure_xcode_ready_or_exit()

    if not check_xcode_version_or_exit():
        return

    startup_finished = True

    if first_device_scan_notice_shown:
        root.after(200, restore_device_preview)

# === XCODE AND COMMAND LINE TOOL SETUP ===
def is_using_command_line_tools_only() -> bool:
    try:
        path = subprocess.check_output(["xcode-select", "-p"], text=True).strip()
        return "CommandLineTools" in path
    except Exception:
        return False

def ensure_xcode_ready_or_exit():
    xcode_app = find_xcode_app()
    if not xcode_app:
        return

    developer_dir = os.path.join(xcode_app, "Contents", "Developer")

    if os.path.exists(developer_dir):
        try:
            subprocess.run(
                ["xcode-select", "-s", developer_dir],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
        except Exception:
            pass

    try:
        subprocess.run(
            [os.path.join(developer_dir, "usr", "bin", "xcodebuild"), "-checkFirstLaunchStatus"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
    except Exception:
        pass

    try:
        subprocess.run(
            [os.path.join(developer_dir, "usr", "bin", "xcrun"), "--find", "devicectl"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
    except Exception:
        pass

# === GUI ROOT AND STARTUP CHECKS ===
root = tk.Tk()

root.configure(cursor="")

menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

hud_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Metal HUD", menu=hud_menu)

help_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Help", menu=help_menu)

# FORCE LIGHT MODE (temporary fix for icons)
try:
    root.tk.call("tk::unsupported::MacWindowStyle", "appearance", root._w, "aqua")
except Exception:
    pass

_titlebar_retry_count = 0

def _apply_macos_titlebar_color(hex_color=None):
    """Make the macOS title bar transparent, match the given background color, and remove the separator line."""
    global _titlebar_retry_count
    if sys.platform != "darwin":
        return
    if hex_color is None:
        hex_color = _BG
    try:
        import ctypes, ctypes.util
        libobjc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))

        libobjc.objc_getClass.restype = ctypes.c_void_p
        libobjc.objc_getClass.argtypes = [ctypes.c_char_p]
        libobjc.sel_registerName.restype = ctypes.c_void_p
        libobjc.sel_registerName.argtypes = [ctypes.c_char_p]
        libobjc.objc_msgSend.restype = ctypes.c_void_p
        libobjc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        def sel(name): return libobjc.sel_registerName(name.encode())
        def cls(name): return libobjc.objc_getClass(name.encode())
        def msg(obj, s): return libobjc.objc_msgSend(obj, sel(s))

        NSApp = msg(cls("NSApplication"), "sharedApplication")
        win = msg(NSApp, "keyWindow") or msg(NSApp, "mainWindow")
        if not win:
            if _titlebar_retry_count < 10:
                _titlebar_retry_count += 1
                root.after(200, lambda: _apply_macos_titlebar_color(hex_color))
            return
        _titlebar_retry_count = 0

        f_bool = ctypes.cast(libobjc.objc_msgSend, ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool))
        f_bool(win, sel("setTitlebarAppearsTransparent:"), True)

        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0
        f_color = ctypes.cast(libobjc.objc_msgSend, ctypes.CFUNCTYPE(
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double))
        color = f_color(cls("NSColor"), sel("colorWithSRGBRed:green:blue:alpha:"), r, g, b, 1.0)

        f_obj = ctypes.cast(libobjc.objc_msgSend, ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p))
        f_obj(win, sel("setBackgroundColor:"), color)

        f_int = ctypes.cast(libobjc.objc_msgSend, ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int64))
        f_int(win, sel("setTitlebarSeparatorStyle:"), 1)
    except Exception:
        pass

def _style_toplevel_titlebar(tk_win, hex_color):
    """Apply macOS title bar styling to the key window (call after focus_force on tk_win)."""
    if sys.platform != "darwin":
        return
    try:
        import ctypes, ctypes.util
        libobjc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
        libobjc.objc_msgSend.restype = ctypes.c_void_p
        libobjc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        libobjc.sel_registerName.restype = ctypes.c_void_p
        libobjc.sel_registerName.argtypes = [ctypes.c_char_p]
        libobjc.objc_getClass.restype = ctypes.c_void_p
        libobjc.objc_getClass.argtypes = [ctypes.c_char_p]

        def sel(name): return libobjc.sel_registerName(name.encode())
        def cls(name): return libobjc.objc_getClass(name.encode())
        def msg(obj, s): return libobjc.objc_msgSend(obj, sel(s))

        tk_win.focus_force()
        tk_win.update_idletasks()
        NSApp = msg(cls("NSApplication"), "sharedApplication")
        ns_win = msg(NSApp, "keyWindow")
        if not ns_win:
            return

        f_bool = ctypes.cast(libobjc.objc_msgSend, ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool))
        f_bool(ns_win, sel("setTitlebarAppearsTransparent:"), True)

        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0
        f_color = ctypes.cast(libobjc.objc_msgSend, ctypes.CFUNCTYPE(
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double))
        color = f_color(cls("NSColor"), sel("colorWithSRGBRed:green:blue:alpha:"), r, g, b, 1.0)

        f_obj = ctypes.cast(libobjc.objc_msgSend, ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p))
        f_obj(ns_win, sel("setBackgroundColor:"), color)

        f_int = ctypes.cast(libobjc.objc_msgSend, ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int64))
        f_int(ns_win, sel("setTitlebarSeparatorStyle:"), 1)
    except Exception:
        pass

def _remove_app_menu_items():
    """Keep only Quit in the macOS application menu."""
    if sys.platform != "darwin":
        return
    try:
        import ctypes, ctypes.util
        libobjc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
        libobjc.objc_getClass.restype = ctypes.c_void_p
        libobjc.objc_getClass.argtypes = [ctypes.c_char_p]
        libobjc.sel_registerName.restype = ctypes.c_void_p
        libobjc.sel_registerName.argtypes = [ctypes.c_char_p]
        libobjc.sel_getName.restype = ctypes.c_char_p
        libobjc.sel_getName.argtypes = [ctypes.c_void_p]
        libobjc.objc_msgSend.restype = ctypes.c_void_p
        libobjc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        def sel(name): return libobjc.sel_registerName(name.encode())
        def cls(name): return libobjc.objc_getClass(name.encode())

        f_at = ctypes.cast(libobjc.objc_msgSend, ctypes.CFUNCTYPE(
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long))
        f_count = ctypes.cast(libobjc.objc_msgSend, ctypes.CFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p))
        f_remove = ctypes.cast(libobjc.objc_msgSend, ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p))
        f_bool = ctypes.cast(libobjc.objc_msgSend, ctypes.CFUNCTYPE(
            ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p))

        NSApp = libobjc.objc_msgSend(cls("NSApplication"), sel("sharedApplication"))
        main_menu = libobjc.objc_msgSend(NSApp, sel("mainMenu"))
        app_item = f_at(main_menu, sel("itemAtIndex:"), 0)
        app_menu = libobjc.objc_msgSend(app_item, sel("submenu"))

        count = f_count(app_menu, sel("numberOfItems"))
        to_remove = []
        for i in range(count):
            item = f_at(app_menu, sel("itemAtIndex:"), i)
            if f_bool(item, sel("isSeparatorItem")):
                to_remove.append(item)
                continue
            action = libobjc.objc_msgSend(item, sel("action"))
            action_name = libobjc.sel_getName(action) if action else b""
            if action_name != b"terminate:":
                to_remove.append(item)
        for item in to_remove:
            f_remove(app_menu, sel("removeItem:"), item)
    except Exception:
        pass

default_font = tkfont.nametofont("TkDefaultFont")
default_font.config(family="SF Pro Text", size=13)

root.option_add("*Font", default_font)

_BG            = "#F2F2F7"
_SURFACE       = "#FFFFFF"
_SURFACE_ALT   = "#F2F2F7"
_BORDER        = "#E0E0E5"
_ACCENT        = "#007AFF"  
_ACCENT_HOVER  = "#0071EE"
_ACCENT_PRESS  = "#0062D4"
_ACCENT_FG     = "#FFFFFF"
_FG_PRIMARY    = "#1C1C1E"   
_FG_SECONDARY  = "#3A3A3C"  
_FG_TERTIARY   = "#636366"  
_FG_PLACEHOLDER= "#AEAEB2"
_RED           = "#FF3B30"   
_SELECTION     = "#CCE4FF"

_FONT_BODY     = ("SF Pro Text", 13)
_FONT_BODY_MED = ("SF Pro Text", 13, "bold")
_FONT_HEADLINE = ("SF Pro Display", 15, "bold")

root.configure(background=_BG)

_style = ttk.Style(root)
_style.theme_use("clam")   


_style.configure("TFrame",
    background=_BG,
    borderwidth=0,
    relief="flat"
)

_style.configure("TLabel",
    background=_BG,
    foreground=_FG_PRIMARY,
    font=_FONT_BODY,
    padding=0
)

_style.configure("Section.TLabel",
    background=_BG,
    foreground=_FG_TERTIARY,
    font=("SF Pro Text", 11),
    padding=(0, 0, 0, 2)
)

_style.configure("TButton",
    background=_SURFACE,
    foreground=_FG_PRIMARY,
    font=_FONT_BODY,
    relief="flat",
    borderwidth=1,
    focusthickness=0,
    padding=(14, 6)
)
_style.map("TButton",
    background=[
        ("pressed",  "#D1D1D6"),
        ("active",   "#E8E8ED"),
        ("disabled", _SURFACE_ALT),
    ],
    foreground=[
        ("disabled", _FG_PLACEHOLDER),
    ],
    relief=[("pressed", "flat"), ("active", "flat")]
)

_style.configure("Accent.TButton",
    background=_ACCENT,
    foreground=_ACCENT_FG,
    font=("SF Pro Text", 13, "bold"),
    relief="flat",
    borderwidth=0,
    focusthickness=0,
    padding=(22, 9)
)
_style.map("Accent.TButton",
    background=[
        ("pressed",  _ACCENT_PRESS),
        ("active",   _ACCENT_HOVER),
        ("disabled", "#AEAEB2"),
    ],
    foreground=[("disabled", "#FFFFFF")],
    relief=[("pressed", "flat"), ("active", "flat")]
)

_style.configure("Destructive.TButton",
    background=_SURFACE,
    foreground=_RED,
    font=_FONT_BODY,
    relief="flat",
    borderwidth=1,
    focusthickness=0,
    padding=(14, 6)
)
_style.map("Destructive.TButton",
    background=[
        ("pressed",  "#FFE5E3"),
        ("active",   "#FFF1F0"),
    ],
    relief=[("pressed", "flat"), ("active", "flat")]
)

_style.configure("Grey.TButton",
    background=_SURFACE_ALT,
    foreground=_FG_SECONDARY,
    font=_FONT_BODY,
    relief="flat",
    borderwidth=0,
    focusthickness=0,
    padding=(14, 6)
)
_style.map("Grey.TButton",
    background=[
        ("pressed",  "#D1D1D6"),
        ("active",   "#E5E5EA"),
    ],
    relief=[("pressed", "flat"), ("active", "flat")]
)

_style.configure("Launch.TButton",
    background=_ACCENT,
    foreground=_ACCENT_FG,
    font=("SF Pro Display", 14, "bold"),
    relief="flat",
    borderwidth=0,
    focusthickness=0,
    padding=(32, 12)
)
_style.map("Launch.TButton",
    background=[
        ("pressed",  _ACCENT_PRESS),
        ("active",   _ACCENT_HOVER),
        ("disabled", "#AEAEB2"),
    ],
    relief=[("pressed", "flat"), ("active", "flat")]
)

_cb_asset_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "UI", "Checkbox")
_CB_SIZE = 13
_cb_uncheck_img = ImageTk.PhotoImage(Image.open(os.path.join(_cb_asset_root, "Uncheck.png")).resize((_CB_SIZE, _CB_SIZE), Image.LANCZOS))
_cb_check_img   = ImageTk.PhotoImage(Image.open(os.path.join(_cb_asset_root, "Check.png")).resize((_CB_SIZE, _CB_SIZE), Image.LANCZOS))

# === GENERIC GAME ICON ===
_generic_game_icon = ImageTk.PhotoImage(
    Image.open(resource_path("assets", "App Icons", "Generic Icon.png"))
    .resize((40, 40), Image.LANCZOS)
)

# === LOADING SPINNER ===
_SPINNER_FRAME_COUNT = 12
_raw_spinner = Image.open(resource_path("assets", "UI", "loading.png")).convert("RGBA").resize((24, 24), Image.LANCZOS)
_spinner_frames = [
    ImageTk.PhotoImage(_raw_spinner.rotate(-i * (360 // _SPINNER_FRAME_COUNT), resample=Image.BICUBIC))
    for i in range(_SPINNER_FRAME_COUNT)
]

class SpinningIcon:
    def __init__(self, parent):
        self._label = tk.Label(parent, image=_spinner_frames[0], bg=_BG, bd=0, highlightthickness=0)
        self._after_id = None
        self._frame_idx = 0
        self._running = False

    def start(self):
        if self._running:
            return
        self._running = True
        self._frame_idx = 0
        self._label.pack(side="left", padx=(6, 0))
        self._tick()

    def _tick(self):
        if not self._running:
            return
        self._frame_idx = (self._frame_idx + 1) % _SPINNER_FRAME_COUNT
        self._label.config(image=_spinner_frames[self._frame_idx])
        self._after_id = root.after(80, self._tick)

    def stop(self):
        self._running = False
        if self._after_id:
            root.after_cancel(self._after_id)
            self._after_id = None
        self._label.pack_forget()

_style.element_create("Custom.Checkbutton.indicator", "image", _cb_uncheck_img,
    ("selected", _cb_check_img),
    sticky="", padding=(0, 2, 6, 2)
)

_cb_layout = [
    ("Checkbutton.padding", {"sticky": "nswe", "children": [
        ("Custom.Checkbutton.indicator", {"side": "left", "sticky": ""}),
        ("Checkbutton.label",            {"side": "left", "sticky": ""}),
    ]})
]

_style.configure("TCheckbutton",
    background=_BG,
    foreground=_FG_PRIMARY,
    font=_FONT_BODY,
    focusthickness=0,
)
_style.map("TCheckbutton",
    background=[("active", _BG)],
)
_style.layout("TCheckbutton", _cb_layout)

_style.configure("White.TCheckbutton",
    background=_SURFACE,
    foreground=_FG_PRIMARY,
    font=_FONT_BODY,
    focusthickness=0,
)
_style.map("White.TCheckbutton",
    background=[("active", _SURFACE)],
)
_style.layout("White.TCheckbutton", _cb_layout)

_style.configure("TCombobox",
    fieldbackground=_SURFACE,
    background=_SURFACE,
    foreground=_FG_PRIMARY,
    arrowcolor=_FG_SECONDARY,
    bordercolor=_BORDER,
    lightcolor=_SURFACE,
    darkcolor=_SURFACE,
    relief="flat",
    font=_FONT_BODY,
    padding=(8, 5)
)
_style.map("TCombobox",
    fieldbackground=[("readonly", _SURFACE), ("disabled", _SURFACE_ALT)],
    foreground=[("disabled", _FG_PLACEHOLDER)],
    background=[("active", _SURFACE)]
)

_style.configure("Thin.Vertical.TScrollbar",
    gripcount=0,
    background="#A0A0A0",
    troughcolor=_SURFACE,
    bordercolor=_SURFACE,
    arrowcolor=_SURFACE,
    relief="flat",
    width=6
)

_style.map("Thin.Vertical.TScrollbar",
    background=[
        ("active", "#8A8A8A"),
        ("pressed", "#6E6E6E")
    ]
)

_style.configure("TProgressbar",
    troughcolor=_SURFACE_ALT,
    background=_ACCENT,
    bordercolor=_BG,
    lightcolor=_ACCENT,
    darkcolor=_ACCENT_HOVER,
    thickness=4,
    relief="flat"
)

_style.configure("TSeparator",
    background=_BORDER
)

root.option_add("*Text.background",    _SURFACE)
root.option_add("*Text.foreground",    _FG_PRIMARY)
root.option_add("*Text.font",          "\"SF Pro Text\" 13")
root.option_add("*Text.relief",        "flat")
root.option_add("*Text.borderWidth",   "0")
root.option_add("*Text.highlightThickness", "1")
root.option_add("*Text.highlightBackground", _BORDER)
root.option_add("*Text.highlightColor",      _ACCENT)
root.option_add("*Canvas.background",  _BG)

root.option_add("*Listbox.background",    _SURFACE)
root.option_add("*Listbox.foreground",    _FG_PRIMARY)
root.option_add("*Listbox.selectBackground", _SELECTION)
root.option_add("*Listbox.selectForeground", _FG_PRIMARY)
root.option_add("*Listbox.font",          "\"SF Pro Text\" 13")
root.option_add("*Listbox.relief",        "flat")
root.option_add("*Listbox.borderWidth",   "0")

DATA_FILE = os.path.expanduser("~/ios_device_controller_data.json")

saved_paths = {}  
command_history = []
hud_settings_saved = {}
analytics_opt_in = None
analytics_prompt_launch_count = 0
first_device_scan_notice_shown = False
window_geometry_saved = None
selected_library = ""
library_panel_open = False

def load_data():
    global saved_paths, command_history, hud_settings_saved, analytics_opt_in, analytics_prompt_launch_count, first_device_scan_notice_shown, custom_app_names, window_geometry_saved, LAST_DEVICE_SCAN, selected_library, library_panel_open, hidden_apps, pinned_apps
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                saved_paths = data.get("saved_paths", {})
                command_history = data.get("command_history", [])
                hud_settings_saved = data.get("hud_settings", {})
                analytics_opt_in = data.get("analytics_opt_in", None)
                analytics_prompt_launch_count = data.get("analytics_prompt_launch_count", 0)
                first_device_scan_notice_shown = data.get("first_device_scan_notice_shown", False)
                window_geometry_saved = data.get("window_geometry", None)
                LAST_DEVICE_SCAN = [
                    {**d, "model": resolve_model_display(d["model"])} if "model" in d else d
                    for d in data.get("last_device_scan", [])
                ]
                selected_library = data.get("selected_library", "")
                library_panel_open = data.get("library_panel_open", False)
                hidden_apps = set(data.get("hidden_apps", []))
                pinned_apps = set(data.get("pinned_apps", []))
        except Exception as e:
            print("Error loading saved data:", e)
            saved_paths = {}
            command_history = []
            hud_settings_saved = {}
            analytics_opt_in = None
            analytics_prompt_launch_count = 0
            first_device_scan_notice_shown = False
            LAST_DEVICE_SCAN = []

    else:
        saved_paths = {}
        command_history = []
        hud_settings_saved = {}
        analytics_opt_in = None
        analytics_prompt_launch_count = 0
        first_device_scan_notice_shown = False
        LAST_DEVICE_SCAN = []

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
        "analytics_opt_in": analytics_opt_in_var.get() if "analytics_opt_in_var" in globals() else analytics_opt_in,
        "analytics_prompt_launch_count": analytics_prompt_launch_count,
        "first_device_scan_notice_shown": first_device_scan_notice_shown,
        "window_geometry": root.geometry(),
        "last_device_scan": LAST_DEVICE_SCAN,
        "selected_library": saved_paths_combo.get() if "saved_paths_combo" in globals() else selected_library,
        "library_panel_open": library_panel_open,
        "hidden_apps": list(hidden_apps),
        "pinned_apps": list(pinned_apps),
    }
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("Error saving data:", e)

# === GENERAL GUI HELPERS ===
def ask_analytics_permission(force=False):
    global analytics_opt_in

    if analytics_opt_in is not None:
        return

    if not force and analytics_prompt_launch_count < 3:
        return

    result = messagebox.askyesno(
        "Help Improve Metal HUD",
        "Would you like to share compatibility data to help improve Metal HUD?\n\n"
        "This includes:\n"
        "• Device model\n"
        "• Connection type (USB / Wi-Fi)\n"
        "• App name & icon\n\n"
        "No personal information or device identifiers are collected."
    )

    analytics_opt_in = result
    save_data()

def maybe_prompt_analytics_after_launch():
    global analytics_prompt_launch_count, analytics_opt_in

    if analytics_opt_in is not None:
        return

    analytics_prompt_launch_count += 1
    save_data()

    if analytics_prompt_launch_count >= 3:
        root.after(800, ask_analytics_permission)

def on_close():
    save_data()
    os._exit(0)

def make_rounded_box(parent, radius=20, height=None):
    kw = {"height": height} if height else {}
    outer = tk.Canvas(parent, bg=_BG, highlightthickness=0, bd=0, **kw)
    inner = tk.Frame(outer, bg=_SURFACE, bd=0, highlightthickness=0)
    win = outer.create_window(1, 1, window=inner, anchor="nw")

    def _redraw(_event=None):
        w, h = outer.winfo_width(), outer.winfo_height()
        if w < 4 or h < 4:
            return
        outer.delete("rr")
        r = radius
        pts = [
            r, 0,  w-r, 0,
            w, 0,  w, r,
            w, h-r, w, h,
            w-r, h, r, h,
            0, h,  0, h-r,
            0, r,  0, 0,
        ]
        outer.create_polygon(pts, smooth=True, fill=_SURFACE, outline=_BORDER, tags="rr")
        outer.tag_lower("rr")
        outer.itemconfig(win, width=w-2, height=h-2)

    outer.bind("<Configure>", _redraw)
    return outer, inner

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

def open_support_email():
    webbrowser.open("mailto:business@mrmacright.com?subject=Metal HUD Mobile Config Support")

def show_help_window(title, content):
    help_window = tk.Toplevel(root)
    help_window.title(title)
    help_window.geometry("760x560")

    text_box = scrolledtext.ScrolledText(
        help_window,
        wrap="word",
        font=("SF Pro Text", 13),
        padx=14,
        pady=14
    )
    text_box.pack(fill="both", expand=True)

    text_box.insert("1.0", content)
    text_box.config(state="disabled")


_connection_help_win = [None]

_chelp_img_cache = {
    "icon": None,
    "ngd": None,
    "trust": None,
    "xcode_conn": None,
    "hud": None,
}

def _preload_connection_help_images():
    import tempfile, subprocess as _sp

    try:
        _icns = resource_path("assets", "App Icons", "MyIcon.icns")
        _fd, _tmp = tempfile.mkstemp(suffix=".png")
        os.close(_fd)
        _sp.run(["sips", "-s", "format", "png", "--resampleHeightWidth", "104", "104",
                 _icns, "--out", _tmp], capture_output=True)
        _chelp_img_cache["_icon_path"] = _tmp
    except Exception:
        _chelp_img_cache["_icon_path"] = None

    try:
        _p = resource_path("assets", "Connection Help", "iPhone 17 Pro Max", "iPhone 17 Pro Max_Metal HUD OFF.png")
        _r = Image.open(_p).convert("RGBA")
        _w = 380
        _r = _r.resize((_w, int(_w * _r.height / _r.width)), Image.LANCZOS)
        _chelp_img_cache["ngd_pil"] = _r
    except Exception:
        _chelp_img_cache["ngd_pil"] = None

    try:
        _r = Image.open(resource_path("assets", "Connection Help", "Trust This Computer.png")).convert("RGBA")
        _w = 300
        _r = _r.resize((_w, int(_w * _r.height / _r.width)), Image.LANCZOS)
        _chelp_img_cache["trust_pil"] = _r
    except Exception:
        _chelp_img_cache["trust_pil"] = None


    try:
        _r = Image.open(resource_path("assets", "Connection Help", "Metal HUD_iOS 26.png")).convert("RGBA")
        _w = 320
        _r = _r.resize((_w, int(_w * _r.height / _r.width)), Image.LANCZOS)
        _chelp_img_cache["hud_pil"] = _r
    except Exception:
        _chelp_img_cache["hud_pil"] = None

    try:
        _r = Image.open(resource_path("assets", "Connection Help", "Game Mode.png")).convert("RGBA")
        _gm_w = 420
        _r = _r.resize((_gm_w, int(_gm_w * _r.height / _r.width)), Image.LANCZOS)
        _chelp_img_cache["gamemode_pil"] = _r
    except Exception:
        _chelp_img_cache["gamemode_pil"] = None

    try:
        _r = Image.open(resource_path("assets", "Connection Help", "PUBG Mobile with Metal HUD.png")).convert("RGBA")
        _w = 500
        _r = _r.resize((_w, int(_w * _r.height / _r.width)), Image.LANCZOS)
        _chelp_img_cache["pubg_pil"] = _r
    except Exception:
        _chelp_img_cache["pubg_pil"] = None

def show_connection_help(scroll_to=None):
    if _connection_help_win[0] is not None and _connection_help_win[0].winfo_exists():
        _connection_help_win[0].deiconify()
        _connection_help_win[0].lift()
        _connection_help_win[0].focus_force()
        if scroll_to:
            _connection_help_win[0]._scroll_to_section(scroll_to)
        return

    if not _chelp_img_cache.get("_loaded"):
        _preload_connection_help_images()
        _chelp_img_cache["_loaded"] = True

    win = tk.Toplevel(root)
    _connection_help_win[0] = win
    win.title("Connection Help")
    _screen_h = root.winfo_screenheight()
    _win_h = min(710, _screen_h - 120)
    win.geometry(f"1200x{_win_h}")
    win.minsize(1200, _win_h)
    win.configure(bg=_SURFACE)

    def _hide_connection_help():
        win.withdraw()

    win.protocol("WM_DELETE_WINDOW", _hide_connection_help)

    win.after(100, lambda: _style_toplevel_titlebar(win, _SURFACE))

    win.grid_rowconfigure(0, weight=1)
    win.grid_columnconfigure(0, weight=0, minsize=192)
    win.grid_columnconfigure(1, weight=0)
    win.grid_columnconfigure(2, weight=1)
    win.grid_columnconfigure(3, weight=0)

    _sidebar_sections = [
        ("How to launch a game", "sec_launch"),
        ("Requirements", "sec_requirements"),
        ("Supported platforms", "sec_platforms"),
        ("Device not connecting?", "sec_device"),
        ("How to connect to Apple TV", "sec_appletv"),
        ("Custom HUD metrics", "sec_customhud"),
        ("Connection states", "sec_connstates"),
        ("Why isn't Game Mode turning on?", "sec_gamemode"),
        ("Is it safe to use with online games?", "sec_onlinegames"),
        ("Why isn't Metal HUD showing?", "sec_metalnotshowing"),
        ("Why is a game called something different?", "sec_gamename"),
    ]

    _active_mark = [None]
    _sidebar_item_widgets = {}
    _sec_fractions = {}
    _scroll_cb = [None]

    def _set_sidebar_active(mark_name):
        _active_mark[0] = mark_name
        for mn, (lbl, frm) in _sidebar_item_widgets.items():
            if mn == mark_name:
                frm.configure(bg=_ACCENT)
                lbl.configure(bg=_ACCENT, fg="white")
            else:
                frm.configure(bg=_BG)
                lbl.configure(bg=_BG, fg=_FG_PRIMARY)

    def _update_sidebar_from_scroll(first_frac):
        if not _sec_fractions:
            return
        active = None
        for _, mark in _sidebar_sections:
            if _sec_fractions.get(mark, 1.0) <= first_frac + 0.01:
                active = mark
        if active and active != _active_mark[0]:
            _set_sidebar_active(active)

    _scroll_cb[0] = _update_sidebar_from_scroll

    def _make_click(m):
        def _click(e):
            txt.yview(m)
            _set_sidebar_active(m)
            _show_sb()
            return "break"
        return _click

    def _make_hover(m, sf_ref, sl_ref):
        def _enter(e):
            if _active_mark[0] != m:
                sf_ref.configure(bg=_SURFACE)
                sl_ref.configure(bg=_SURFACE)
        def _leave(e):
            if _active_mark[0] != m:
                sf_ref.configure(bg=_BG)
                sl_ref.configure(bg=_BG)
        return _enter, _leave

    _sidebar = tk.Frame(win, bg=_BG, width=192)
    _sidebar.grid(row=0, column=0, sticky="nsew")
    _sidebar.grid_propagate(False)

    _sidebar_divider = tk.Frame(win, bg=_BORDER, width=1)
    _sidebar_divider.grid(row=0, column=1, sticky="nsew")

    tk.Label(
        _sidebar,
        text="On This Page",
        font=("SF Pro Text", 11),
        fg=_FG_TERTIARY,
        bg=_BG,
        anchor="w",
        padx=16,
    ).pack(anchor="w", pady=(16, 4))

    for _slabel, _smark in _sidebar_sections:
        _sf = tk.Frame(_sidebar, bg=_BG, cursor="pointinghand")
        _sf.pack(fill="x", padx=8, pady=1)
        _sl = tk.Label(
            _sf,
            text=_slabel,
            font=("SF Pro Text", 12),
            fg=_FG_PRIMARY,
            bg=_BG,
            anchor="w",
            padx=8,
            pady=4,
            justify="left",
            wraplength=160,
        )
        _sl.pack(fill="x")
        _sidebar_item_widgets[_smark] = (_sl, _sf)
        _sf.bind("<Button-1>", _make_click(_smark))
        _sl.bind("<Button-1>", _make_click(_smark))
        _eh, _lh = _make_hover(_smark, _sf, _sl)
        _sf.bind("<Enter>", _eh)
        _sl.bind("<Enter>", _eh)
        _sf.bind("<Leave>", _lh)
        _sl.bind("<Leave>", _lh)

    txt = tk.Text(
        win,
        wrap="word",
        bg=_SURFACE,
        fg=_FG_PRIMARY,
        font=("SF Pro Text", 13),
        padx=64,
        pady=52,
        relief="flat",
        borderwidth=0,
        highlightthickness=0,
        spacing1=1,
        spacing3=3,
        cursor="arrow",
    )
    sb = tk.Canvas(win, width=8, bg=_SURFACE, highlightthickness=0, bd=0)
    txt.grid(row=0, column=2, sticky="nsew")
    sb.grid(row=0, column=3, sticky="ns")
    sb.grid_remove()

    _sb_hide_job = [None]
    _sb_pos = [0.0, 1.0]

    def _draw_thumb():
        sb.delete("all")
        h = sb.winfo_height()
        if h < 4:
            return
        first, last = _sb_pos
        mg = 2
        y0 = int(first * h) + mg
        y1 = int(last * h) - mg
        if y1 - y0 < 16:
            y1 = y0 + 16
        if y1 > h - mg:
            y0 = max(mg, h - mg - (y1 - y0))
            y1 = h - mg
        r, x0, x1 = 3, 1, 7
        sb.create_oval(x0, y0, x1, y0 + 2 * r, fill="#6E6E6E", outline="")
        sb.create_oval(x0, y1 - 2 * r, x1, y1, fill="#6E6E6E", outline="")
        sb.create_rectangle(x0, y0 + r, x1, y1 - r, fill="#6E6E6E", outline="")

    def _show_sb(*_):
        if not sb.winfo_ismapped():
            sb.grid(row=0, column=3, sticky="ns")
            win.after(10, _draw_thumb)
        else:
            _draw_thumb()
        if _sb_hide_job[0]:
            win.after_cancel(_sb_hide_job[0])
        _sb_hide_job[0] = win.after(1200, lambda: sb.grid_remove())

    def _on_yscroll(first, last):
        _sb_pos[0], _sb_pos[1] = float(first), float(last)
        _show_sb()
        if _scroll_cb[0]:
            _scroll_cb[0](float(first))

    txt.configure(yscrollcommand=_on_yscroll)

    _drag_start = [None]

    def _sb_click(e):
        h = sb.winfo_height()
        if h <= 0:
            return
        first, last = _sb_pos
        thumb_y0 = first * h
        thumb_y1 = last * h
        if thumb_y0 <= e.y <= thumb_y1:
            _drag_start[0] = e.y - thumb_y0
        else:
            _drag_start[0] = (thumb_y1 - thumb_y0) / 2
            txt.yview_moveto((e.y - _drag_start[0]) / h)

    def _sb_drag(e):
        h = sb.winfo_height()
        if h <= 0 or _drag_start[0] is None:
            return
        new_first = (e.y - _drag_start[0]) / h
        txt.yview_moveto(max(0.0, min(1.0, new_first)))
        _show_sb()

    sb.bind("<Button-1>", _sb_click)
    sb.bind("<B1-Motion>", _sb_drag)

    def _on_mousewheel(e):
        top, _ = txt.yview()
        delta_fraction = -e.delta / 120 * 0.05
        txt.yview_moveto(max(0.0, min(1.0, top + delta_fraction)))
        _show_sb()

    txt.bind("<Enter>", lambda e: txt.bind_all("<MouseWheel>", _on_mousewheel))
    txt.bind("<Leave>", lambda e: txt.unbind_all("<MouseWheel>"))

    txt.tag_configure("h1",
        font=("SF Pro Display", 17, "bold"),
        foreground=_FG_PRIMARY,
        spacing1=6,
        spacing3=6,
    )
    txt.tag_configure("body",  font=("SF Pro Text", 13), foreground=_FG_PRIMARY, spacing3=2)
    txt.tag_configure("dim",   font=("SF Pro Text", 13), foreground=_FG_TERTIARY, spacing3=2)
    txt.tag_configure("mono",  font=("SF Pro Mono", 12), foreground=_FG_SECONDARY,
                      background=_BG, lmargin1=4, lmargin2=4, spacing1=2, spacing3=2)

    _sep_frames = []

    txt.tag_configure(
        "anchor",
        font=("SF Pro Text", 1),
        foreground=_SURFACE,
        spacing1=0,
        spacing3=0,
    )

    def _anchor(mark_name):
        txt.insert(tk.END, "\n", "anchor")
        txt.mark_set(mark_name, "end-1c")
        txt.mark_gravity(mark_name, "left")

    def _h(text):
        txt.insert(tk.END, text + "\n", "h1")

    def _p(text, tag="body"):
        txt.insert(tk.END, text + "\n", tag)

    def _cmd(command):
        frame = tk.Frame(txt, bg=_BG, padx=8, pady=6)
        lbl = tk.Label(
            frame,
            text=command,
            font=("SF Pro Mono", 12),
            fg=_FG_SECONDARY,
            bg=_BG,
            justify="left",
            anchor="w",
        )
        lbl.pack(side="left", fill="x", expand=True)

        btn = tk.Label(
            frame,
            text="Copy",
            font=("SF Pro Text", 11),
            fg=_ACCENT,
            bg=_BG,
            cursor="pointinghand",
            padx=4,
        )
        btn.pack(side="right", anchor="center")

        def _do_copy(_e=None, _cmd=command, _btn=btn):
            win.clipboard_clear()
            win.clipboard_append(_cmd)
            _btn.config(text="Copied!")
            win.after(1500, lambda: _btn.config(text="Copy"))

        btn.bind("<Button-1>", _do_copy)
        txt.window_create(tk.END, window=frame, stretch=True)
        txt.insert(tk.END, "\n")

    _hdr_ref = [None]

    def _update_sep_widths(_event=None):
        w = txt.winfo_width() - 128
        if w > 0:
            for c in _sep_frames:
                c.configure(width=w)
            if _hdr_ref[0] is not None:
                _hdr_ref[0].configure(width=w)

    def _sep():
        txt.insert(tk.END, "\n")
        c = tk.Canvas(txt, height=1, width=1, bd=0, highlightthickness=0, bg=_BORDER)
        _sep_frames.append(c)
        txt.window_create(tk.END, window=c, stretch=True, pady=12)
        txt.insert(tk.END, "\n")

    txt.bind("<Configure>", _update_sep_widths)

    _icon_img = [None]
    try:
        _icon_path = _chelp_img_cache.get("_icon_path")
        if _icon_path and os.path.exists(_icon_path):
            _icon_img[0] = tk.PhotoImage(file=_icon_path)
    except Exception:
        pass

    # Header
    _hdr = tk.Frame(txt, bg=_SURFACE, height=114)
    _hdr.pack_propagate(False)
    _title_col = tk.Frame(_hdr, bg=_SURFACE)
    _title_col.pack(side="left", anchor="nw")
    tk.Label(
        _title_col,
        text="Metal HUD Mobile Config",
        font=("SF Pro Display", 34, "bold"),
        fg=_FG_PRIMARY,
        bg=_SURFACE,
        justify="left",
        anchor="w",
    ).pack(anchor="w")
    tk.Label(
        _title_col,
        text="Connection Help",
        font=("SF Pro Text", 16),
        fg=_FG_SECONDARY,
        bg=_SURFACE,
        justify="left",
        anchor="w",
    ).pack(anchor="w", pady=(4, 0))
    if _icon_img[0]:
        _il = tk.Label(_hdr, image=_icon_img[0], bg=_SURFACE, bd=0)
        _il.image = _icon_img[0]
        _il.place(relx=1.0, y=0, anchor="ne")
    _hdr_ref[0] = _hdr
    txt.window_create(tk.END, window=_hdr, stretch=True)
    txt.insert(tk.END, "\n")

    #how to launch a game with Metal HUD
    _anchor("sec_launch")
    _sep()

    _ngd_img_ref = [None]
    try:
        _pil = _chelp_img_cache.get("ngd_pil")
        if _pil:
            _ngd_img_ref[0] = ImageTk.PhotoImage(_pil)
    except Exception:
        pass

    _ngd_frame = tk.Frame(txt, bg=_SURFACE)

    if _ngd_img_ref[0]:
        _ngd_img_lbl = tk.Label(_ngd_frame, image=_ngd_img_ref[0], bg=_SURFACE, bd=0)
        _ngd_img_lbl.image = _ngd_img_ref[0]
        _ngd_img_lbl.pack(side="left", anchor="nw", padx=(0, 70))

    _ngd_text = tk.Frame(_ngd_frame, bg=_SURFACE)
    _ngd_text.pack(side="left", anchor="w", fill="x", expand=True)

    tk.Label(
        _ngd_text,
        text="How to launch a game with Metal HUD",
        font=("SF Pro Display", 17, "bold"),
        fg=_FG_PRIMARY,
        bg=_SURFACE,
        justify="left",
        anchor="w",
    ).pack(anchor="w", pady=(0, 8))

    tk.Label(
        _ngd_text,
        text="Apps are only detectable when already open and in the foreground.",
        font=("SF Pro Text", 13),
        fg=_FG_PRIMARY,
        bg=_SURFACE,
        justify="left",
        anchor="w",
        wraplength=420,
    ).pack(anchor="w", pady=(0, 8))

    for _step in [
        "1. Launch the game on your device",
        "2. Keep it open in the foreground",
        "3. Click Show Running Games",
        "4. Choose your game → Launch App with Metal HUD"
    ]:
        tk.Label(
            _ngd_text,
            text=_step,
            font=("SF Pro Text", 13),
            fg=_FG_PRIMARY,
            bg=_SURFACE,
            justify="left",
            anchor="w",
        ).pack(anchor="w")

    txt.window_create(tk.END, window=_ngd_frame, stretch=True)
    txt.insert(tk.END, "\n")

    #Supported platforms for Metal HUD
    _anchor("sec_platforms")

    _sep()

    _plat_frame = tk.Frame(txt, bg=_SURFACE)
    _plat_text = tk.Frame(_plat_frame, bg=_SURFACE)
    _plat_text.pack(side="left", anchor="nw", fill="both", expand=True)

    tk.Label(
        _plat_text,
        text="Supported platforms for Metal HUD",
        font=("SF Pro Display", 17, "bold"),
        fg=_FG_PRIMARY,
        bg=_SURFACE,
        justify="left",
        anchor="w",
    ).pack(anchor="w", pady=(0, 8))

    _plat_ios_row = tk.Frame(_plat_text, bg=_SURFACE)
    tk.Label(
        _plat_ios_row,
        text="▶  ",
        font=("SF Pro Text", 13),
        fg=_FG_PRIMARY,
        bg=_SURFACE,
    ).pack(side="left")
    _plat_ios_lbl = tk.Label(
        _plat_ios_row,
        text="iOS 17 or later",
        font=("SF Pro Text", 13),
        fg=_ACCENT,
        bg=_SURFACE,
        cursor="pointinghand",
    )
    _plat_ios_lbl.pack(side="left")
    _plat_ios_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://support.apple.com/en-au/guide/iphone/iphe3fa5df43/17.0/ios/17.0"))
    _plat_ios_row.pack(anchor="w")

    _plat_ipados_row = tk.Frame(_plat_text, bg=_SURFACE)
    tk.Label(
        _plat_ipados_row,
        text="▶  ",
        font=("SF Pro Text", 13),
        fg=_FG_PRIMARY,
        bg=_SURFACE,
    ).pack(side="left")
    _plat_ipados_lbl = tk.Label(
        _plat_ipados_row,
        text="iPadOS 17 or later",
        font=("SF Pro Text", 13),
        fg=_ACCENT,
        bg=_SURFACE,
        cursor="pointinghand",
    )
    _plat_ipados_lbl.pack(side="left")
    _plat_ipados_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://support.apple.com/en-au/guide/ipad/ipad213a25b2/17.0/ipados/17.0"))
    _plat_ipados_row.pack(anchor="w")

    tk.Label(
        _plat_text,
        text="▶    Apple TV 4K (1st gen, 2017) or later",
        font=("SF Pro Text", 13),
        fg=_FG_PRIMARY,
        bg=_SURFACE,
        justify="left",
        anchor="w",
    ).pack(anchor="w")

    _plat_imp_frame = tk.Frame(_plat_text, bg=_BG, padx=14, pady=8)
    tk.Label(
        _plat_imp_frame,
        text="System-wide HUD support is not possible",
        font=("SF Pro Text", 13),
        fg=_FG_PRIMARY,
        bg=_BG,
        justify="left",
        anchor="w",
        wraplength=500,
    ).pack(anchor="w", pady=(0, 4))
    _plat_imp_frame.pack(anchor="w", pady=(12, 0), fill="x")

    txt.window_create(tk.END, window=_plat_frame, stretch=True)
    txt.insert(tk.END, "\n")

    #Device not connecting?
    _anchor("sec_device")

    _sep()

    _xcode_conn_img_ref = [None]
    try:
        _pil = _chelp_img_cache.get("trust_pil")
        if _pil:
            _xcode_conn_img_ref[0] = ImageTk.PhotoImage(_pil)
    except Exception:
        pass

    _device_conn_frame = tk.Frame(txt, bg=_SURFACE)

    _device_conn_text = tk.Frame(_device_conn_frame, bg=_SURFACE)
    _device_conn_text.pack(side="left", anchor="nw", fill="both", expand=True)

    tk.Label(
        _device_conn_text,
        text="Device not connecting?",
        font=("SF Pro Display", 17, "bold"),
        fg=_FG_PRIMARY,
        bg=_SURFACE,
        justify="left",
        anchor="w",
    ).pack(anchor="w", pady=(0, 22))

    for _line in [
        "1. Connect your iPhone or iPad via USB",
        "2. Unlock the device",
        "3. Tap Trust This Computer if prompted",
        "4. On Mac, click Allow if asked to connect the accessory",
    ]:
        tk.Label(
            _device_conn_text,
            text=_line,
            font=("SF Pro Text", 13),
            fg=_FG_PRIMARY,
            bg=_SURFACE,
            justify="left",
            anchor="w",
        ).pack(anchor="w")

    tk.Label(
        _device_conn_text,
        text="If the trust prompt was dismissed:",
        font=("SF Pro Text", 13),
        fg=_FG_PRIMARY,
        bg=_SURFACE,
        justify="left",
        anchor="w",
    ).pack(anchor="w", pady=(34, 8))

    _reset_path_frame = tk.Frame(_device_conn_text, bg=_BG, padx=14, pady=4)

    tk.Label(
        _reset_path_frame,
        text="Settings → General → Transfer or Reset iPhone → Reset → Reset Location & Privacy",
        font=("SF Pro Mono", 12),
        fg=_FG_SECONDARY,
        bg=_BG,
        justify="left",
        anchor="w",
    ).pack(side="left")

    _reset_path_frame.pack(anchor="w", pady=(0, 0))

    if _xcode_conn_img_ref[0]:
        _xcode_conn_img_lbl = tk.Label(
            _device_conn_frame,
            image=_xcode_conn_img_ref[0],
            bg=_SURFACE,
            bd=0
        )
        _xcode_conn_img_lbl.image = _xcode_conn_img_ref[0]
        _xcode_conn_img_lbl.pack(side="right", anchor="center", padx=(55, 20), pady=(35, 0))

    txt.window_create(tk.END, window=_device_conn_frame, stretch=True)
    txt.insert(tk.END, "\n")

    #How to connect to Apple TV
    _anchor("sec_appletv")

    _sep()

    _atv_frame = tk.Frame(txt, bg=_SURFACE)
    _atv_text = tk.Frame(_atv_frame, bg=_SURFACE)
    _atv_text.pack(anchor="w", fill="both", expand=True)

    tk.Label(
        _atv_text,
        text="How to connect to Apple TV",
        font=("SF Pro Display", 17, "bold"),
        fg=_FG_PRIMARY,
        bg=_SURFACE,
        justify="left",
        anchor="w",
    ).pack(anchor="w", pady=(0, 8))

    for _atv_step in [
        "1. On Apple TV go to Settings > Remotes and Devices > Remote App and Devices",
        "2. Open Xcode → Window → Devices and Simulators → Discovered",
        "3. Pair Apple TV → enter verification code → Connect",
        "4. Open Metal HUD Mobile Config → List Devices",
    ]:
        tk.Label(
            _atv_text,
            text=_atv_step,
            font=("SF Pro Text", 13),
            fg=_FG_PRIMARY,
            bg=_SURFACE,
            justify="left",
            anchor="w",
            wraplength=520,
        ).pack(anchor="w")

    _plat_repair_frame = tk.Frame(_atv_text, bg=_BG, padx=14, pady=8)
    tk.Label(
        _plat_repair_frame,
        text="You might need to re-pair after tvOS/macOS updates",
        font=("SF Pro Text", 13),
        fg=_FG_PRIMARY,
        bg=_BG,
        justify="left",
        anchor="w",
    ).pack(anchor="w")
    _plat_repair_frame.pack(anchor="w", pady=(12, 0), fill="x")

    _atv_unsupported_frame = tk.Frame(_atv_text, bg=_BG, padx=14, pady=8)
    tk.Label(
        _atv_unsupported_frame,
        text="Apple TV HD is not supported",
        font=("SF Pro Text", 13),
        fg=_FG_PRIMARY,
        bg=_BG,
        justify="left",
        anchor="w",
    ).pack(anchor="w")
    _atv_unsupported_frame.pack(anchor="w", pady=(8, 0), fill="x")

    txt.window_create(tk.END, window=_atv_frame, stretch=True)
    txt.insert(tk.END, "\n")

    #Custom HUD metrics not working?
    _anchor("sec_customhud")

    _sep()

    _hud_img_ref = [None]
    try:
        _pil = _chelp_img_cache.get("hud_pil")
        if _pil:
            _hud_img_ref[0] = ImageTk.PhotoImage(_pil)
    except Exception:
        pass

    _hud_frame = tk.Frame(txt, bg=_SURFACE)

    if _hud_img_ref[0]:
        _hud_img_lbl = tk.Label(_hud_frame, image=_hud_img_ref[0], bg=_SURFACE, bd=0)
        _hud_img_lbl.image = _hud_img_ref[0]
        _hud_img_lbl.pack(side="left", anchor="center", padx=(0, 250))

    _hud_text = tk.Frame(_hud_frame, bg=_SURFACE)
    _hud_text.pack(side="left", anchor="center", fill="x", expand=True)

    tk.Label(
        _hud_text,
        text="Custom HUD metrics not working?",
        font=("SF Pro Display", 17, "bold"),
        fg=_FG_PRIMARY,
        bg=_SURFACE,
        justify="left",
        anchor="w",
    ).pack(anchor="w", pady=(0, 8))

    for _hud_line in [
        "Custom metrics, position, and scale require",
        "iOS 26, iPadOS 26, or tvOS 26 or later.",
        "",
        "iOS 17–18 only support the Default preset.",
    ]:
        tk.Label(
            _hud_text,
            text=_hud_line,
            font=("SF Pro Text", 13),
            fg=_FG_PRIMARY if _hud_line else _FG_SECONDARY,
            bg=_SURFACE,
            justify="left",
            anchor="w",
        ).pack(anchor="w")

    txt.window_create(tk.END, window=_hud_frame, stretch=True)
    txt.insert(tk.END, "\n")

    #Connection states
    _anchor("sec_connstates")

    _sep()

    _h("Connection states")
    txt.insert(tk.END, "\n")

    def _load_conn_icon_lg(state_key):
        path = get_connection_icon_path(state_key)
        if not path:
            return None
        try:
            img = Image.open(path).convert("RGBA")
            img = img.resize((30, 21), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    _state_icon_refs = []

    for _sk, _slabel, _sdesc in [
        (
            "available (paired)",
            "Available (paired + wireless)",
            "Paired and reachable over Wi-Fi — no USB cable needed."
        ),
        (
            "connected",
            "Connected",
            "Device connected and ready."
        ),
        (
            "available",
            "Available (preparing)",
            "Device is visible, but Xcode may still be preparing it or requires pairing. Metal HUD may still work."
        ),
        (
            "available (pairing)",
            "Available (pairing required)",
            "Device is visible but may need pairing or trust confirmation. Connect via USB and tap Trust if prompted."
        ),
        (
            "connected (no ddi)",
            "Connected (limited support)",
            "Xcode may still be preparing the device. If you can't connect, install the latest Xcode beta and switch to it using the command below."
        ),
        (
            "unavailable",
            "Unavailable",
            "Device is offline, turned off, or not reachable on the same Wi-Fi network."
        ),
        (
            "unsupported",
            "Unsupported",
            "This device does not support Metal HUD."
        ),
    ]:
        _sf = tk.Frame(txt, bg=_SURFACE)

        _icon_col = tk.Frame(_sf, bg=_SURFACE, width=42, height=48)
        _icon_col.pack(side="left", anchor="n", padx=(0, 14))
        _icon_col.pack_propagate(False)

        _sicon = _load_conn_icon_lg(_sk)
        if _sicon:
            _state_icon_refs.append(_sicon)
            _sil = tk.Label(_icon_col, image=_sicon, bg=_SURFACE, bd=0)
            _sil.image = _sicon
            _sil.place(relx=0.5, y=24, anchor="center")

        _stc = tk.Frame(_sf, bg=_SURFACE)
        _stc.pack(side="left", anchor="w", fill="x", expand=True)

        tk.Label(
            _stc,
            text=_slabel,
            font=("SF Pro Text", 13, "bold"),
            fg=_FG_PRIMARY,
            bg=_SURFACE,
            justify="left",
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            _stc,
            text=_sdesc,
            font=("SF Pro Text", 12),
            fg=_FG_SECONDARY,
            bg=_SURFACE,
            justify="left",
            anchor="w",
            wraplength=560,
        ).pack(anchor="w")

        if _sk == "available":
            tk.Label(
                _stc,
                text="If device isn't ready:",
                font=("SF Pro Text", 13),
                fg=_FG_PRIMARY,
                bg=_SURFACE,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=(10, 5))

            _xcode_steps_box = tk.Frame(_stc, bg=_BG, padx=14, pady=7)

            for _xcode_conn_step in [
                "1. Open Xcode → Window → Devices and Simulators",
                "2. Wait for device preparation to complete.",
            ]:
                tk.Label(
                    _xcode_steps_box,
                    text=_xcode_conn_step,
                    font=("SF Pro Text", 13),
                    fg=_FG_SECONDARY,
                    bg=_BG,
                    justify="left",
                    anchor="w",
                ).pack(anchor="w")

            _xcode_steps_box.pack(anchor="w", fill="x", pady=(0, 2))

        elif _sk == "connected (no ddi)":
            _ddi_cmd_box = tk.Frame(_stc, bg=_BG, padx=8, pady=6)

            _ddi_cmd_lbl = tk.Label(
                _ddi_cmd_box,
                text="sudo xcode-select -s /Applications/Xcode-beta.app/Contents/Developer",
                font=("SF Pro Mono", 12),
                fg=_FG_SECONDARY,
                bg=_BG,
                justify="left",
                anchor="w",
            )
            _ddi_cmd_lbl.pack(side="left", fill="x", expand=True)

            _ddi_btn = tk.Label(
                _ddi_cmd_box,
                text="Copy",
                font=("SF Pro Text", 11),
                fg=_ACCENT,
                bg=_BG,
                cursor="pointinghand",
                padx=8,
            )
            _ddi_btn.pack(side="right", anchor="center")

            def _do_ddi_copy(_, _btn=_ddi_btn):
                win.clipboard_clear()
                win.clipboard_append("sudo xcode-select -s /Applications/Xcode-beta.app/Contents/Developer")
                _btn.config(text="Copied!")
                win.after(1500, lambda: _btn.config(text="Copy"))

            _ddi_btn.bind("<Button-1>", _do_ddi_copy)
            _ddi_cmd_box.pack(anchor="w", fill="x", pady=(6, 0))

        txt.window_create(tk.END, window=_sf, stretch=True)

        _gap = tk.Frame(txt, bg=_SURFACE, height=22)
        txt.window_create(tk.END, window=_gap, stretch=True)
        txt.insert(tk.END, "\n")

    _p("")

    #Game Mode
    _anchor("sec_gamemode")

    _sep()

    _gamemode_img_ref = [None]
    try:
        _pil = _chelp_img_cache.get("gamemode_pil")
        if _pil:
            _gamemode_img_ref[0] = ImageTk.PhotoImage(_pil)
    except Exception:
        pass

    _gm_frame = tk.Frame(txt, bg=_SURFACE)

    _gm_text = tk.Frame(_gm_frame, bg=_SURFACE)
    _gm_text.pack(side="left", anchor="nw", fill="both", expand=True)

    tk.Label(
        _gm_text,
        text="Why isn't Game Mode turning on?",
        font=("SF Pro Display", 17, "bold"),
        fg=_FG_PRIMARY,
        bg=_SURFACE,
        justify="left",
        anchor="w",
    ).pack(anchor="w", pady=(0, 8))

    for _line in [
        "Game Mode turns on automatically for supported games.",
        "If it isn't turning on, the game likely doesn't support Game Mode yet. This can only be enabled by the game developer in Xcode — external tools cannot force it on.",
    ]:
        tk.Label(
            _gm_text,
            text=_line,
            font=("SF Pro Text", 13),
            fg=_FG_PRIMARY,
            bg=_SURFACE,
            justify="left",
            anchor="w",
            wraplength=380,
        ).pack(anchor="w", pady=(0, 4))

    if _gamemode_img_ref[0]:
        _gm_img_lbl = tk.Label(_gm_frame, image=_gamemode_img_ref[0], bg=_SURFACE, bd=0)
        _gm_img_lbl.image = _gamemode_img_ref[0]
        _gm_img_lbl.pack(side="right", anchor="center", padx=(75, 0))

    txt.window_create(tk.END, window=_gm_frame, stretch=True)
    txt.insert(tk.END, "\n")

    #Is it safe to use with online games?
    _anchor("sec_onlinegames")

    _sep()

    _pubg_img_ref = [None]
    try:
        _pil = _chelp_img_cache.get("pubg_pil")
        if _pil:
            _pubg_img_ref[0] = ImageTk.PhotoImage(_pil)
    except Exception:
        pass

    _og_frame = tk.Frame(txt, bg=_SURFACE)

    if _pubg_img_ref[0]:
        _pubg_img_lbl = tk.Label(_og_frame, image=_pubg_img_ref[0], bg=_SURFACE, bd=0)
        _pubg_img_lbl.image = _pubg_img_ref[0]
        _pubg_img_lbl.pack(side="left", anchor="center", padx=(0, 16))

    _og_text = tk.Frame(_og_frame, bg=_SURFACE)
    _og_text.pack(side="left", anchor="nw", fill="both", expand=True, padx=(60, 0))

    tk.Label(
        _og_text,
        text="Is it safe to use with online games?",
        font=("SF Pro Display", 17, "bold"),
        fg=_FG_PRIMARY,
        bg=_SURFACE,
        justify="left",
        anchor="w",
    ).pack(anchor="w", pady=(0, 8))

    for _line in [
        "Metal Performance HUD has been widely used in games like PUBG MOBILE, COD: Mobile, and Genshin Impact.",
        "However, some anti-cheat systems may detect it and block the game from launching.",
        "",
        "Use at your own risk, especially in competitive online games.",
    ]:
        tk.Label(
            _og_text,
            text=_line,
            font=("SF Pro Text", 13),
            fg=_FG_PRIMARY,
            bg=_SURFACE,
            justify="left",
            anchor="w",
            wraplength=260,
        ).pack(anchor="w", pady=(0, 4))

    txt.window_create(tk.END, window=_og_frame, stretch=True)
    txt.insert(tk.END, "\n")

    #Why isn't Metal HUD showing?
    _anchor("sec_metalnotshowing")

    _sep()

    _h("Why isn't Metal HUD showing?")
    _p("")
    _p("If the game launches but the Metal HUD does not appear, the game is likely not using Metal graphics (for example, it may use OpenGL instead).")
    _p("")
    _p("Metal HUD only works with games powered by Metal.")

    _sep()

    _anchor("sec_gamename")
    _p("")
    _h("Why is a game called something different than its actual name?")
    _p("")
    _p("This app detects the game's internal app name from the App Store package. Some developers do not use the official game title internally, so certain games may appear with generic names like \"Game\".")

    txt.config(state="disabled")

    def _scroll_to_section(mark_name):
        txt.yview(mark_name)
        _set_sidebar_active(mark_name)

    win._scroll_to_section = _scroll_to_section

    if scroll_to:
        win.after(80, lambda: _scroll_to_section(scroll_to))
    elif _sidebar_sections:
        _set_sidebar_active(_sidebar_sections[0][1])

help_menu.add_command(label="Connection Help", command=show_connection_help)

help_menu.add_separator()

help_menu.add_command(label="Contact Support", command=open_support_email)

help_menu.add_separator()

help_menu.add_command(label="Support Me", command=lambda: webbrowser.open("https://buymeacoffee.com/mrmacright"))

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

    root.after(0, lambda: update_launch_output(output))

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
    global APP_LOG_BUFFER

    if not text:
        return

    APP_LOG_BUFFER.append(text)

    if len(APP_LOG_BUFFER) > MAX_LOG_LINES:
        APP_LOG_BUFFER = APP_LOG_BUFFER[-MAX_LOG_LINES:]

def show_logs():
    log_window = tk.Toplevel(root)
    log_window.title("Logs")
    log_window.geometry("1200x650")

    log_text = scrolledtext.ScrolledText(
        log_window,
        wrap="none",
        font=("SF Pro Text", 12)
    )
    log_text.pack(fill="both", expand=True, padx=10, pady=10)

    last_content = {"text": None}

    def refresh_logs_window():
        if not log_window.winfo_exists():
            return

        content = "".join(APP_LOG_BUFFER).strip()

        if not content:
            content = "No logs yet."

        if content != last_content["text"]:
            last_content["text"] = content

            log_text.config(state="normal")
            log_text.delete("1.0", tk.END)
            log_text.insert("1.0", content)
            log_text.see(tk.END)
            log_text.config(state="disabled")

        log_window.after(1000, refresh_logs_window)

    refresh_logs_window()

def open_xcode_download():
    subprocess.Popen(["open", "macappstore://itunes.apple.com/app/id497799835"])

# === DEVICE MANAGEMENT ===
def device_sort_key(d):
    raw = d["state"]
    state = get_display_state_text(raw).lower()
    if state.startswith("available (paired)"):
        priority = 0
    elif state.startswith("available"):
        priority = 1
    elif state.startswith("connected"):
        priority = 2
    elif raw == "unsupported":
        priority = 3
    elif state.startswith("unavailable"):
        priority = 4
    else:
        priority = 99
    return (priority, d["name"].lower())

def restore_device_preview():
    """Populate the device list from the last saved scan without running devicectl."""
    global DEVICE_INFO_CACHE, DEVICE_STATE_CACHE

    if not LAST_DEVICE_SCAN:
        render_device_headers(device_list_frame)

        empty_box = tk.Frame(device_list_frame, bg=_SURFACE)
        empty_box.pack(fill="both", expand=True, pady=(38, 0))

        tk.Label(
            empty_box,
            text="No devices found",
            bg=_SURFACE,
            fg=_FG_PRIMARY,
            font=("SF Pro Display", 16, "bold")
        ).pack(pady=(0, 6))

        tk.Label(
            empty_box,
            text="Connect an iPhone or iPad via USB, or pair Apple TV in Xcode, then press List Devices again.",
            bg=_SURFACE,
            fg=_FG_SECONDARY,
            font=_FONT_BODY,
            wraplength=700,
            justify="center"
        ).pack()

        return

    device_info = {d["identifier"]: d["model"] for d in LAST_DEVICE_SCAN}
    device_states = {d["identifier"]: d["state"] for d in LAST_DEVICE_SCAN}
    device_ids = {d["name"]: d["identifier"] for d in LAST_DEVICE_SCAN}

    DEVICE_INFO_CACHE = device_info
    DEVICE_STATE_CACHE = device_states

    sorted_devices = sorted(LAST_DEVICE_SCAN, key=device_sort_key)
    render_devices_with_icons(device_list_frame, sorted_devices)
    device_list_frame.device_info = device_info

    udids = [d["identifier"] for d in LAST_DEVICE_SCAN]
    device_udid_combo["values"] = udids
    device_udid_combo.set(udids[0])
    device_udid_var.set(udids[0])

    unpair_button.config(state="normal" if device_ids else "disabled")
    refresh_command_history_combo()
    connection_hint_label.config(text="")

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
        FIRST_DEVICE_SCAN_WARNING_SHOWN = True
        first_device_scan_notice_shown = True
        save_data()

        status_label.config(
            text="First device scan may take a while while Xcode prepares devices…"
        )

    list_devices_button.config(state="disabled")
    device_spinner.start()
    status_label.config(
        text="Checking for devices…"
    )
    status_clear_time = time.time() + 2.5

    root.update_idletasks()

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
                model = resolve_model_display(parts[4].strip())

                if not uuid_like.match(identifier):
                    continue

                if normalize_model_for_icon(model) == "Apple Watch":
                    state = "unsupported"

                if "AppleTV5,3" in model:
                    state = "unsupported"

                devices.append({
                    "name": name,
                    "identifier": identifier,
                    "state": state,
                    "model": model
                })

            devices.sort(key=device_sort_key)

            device_ids.clear()
            device_info.clear()

            for d in devices:
                device_ids[d["name"]] = d["identifier"]
                device_info[d["identifier"]] = d["model"]
                device_states[d["identifier"]] = d["state"]

            def update_ui():
                global DEVICE_INFO_CACHE, DEVICE_STATE_CACHE, LAST_DEVICE_SCAN

                DEVICE_INFO_CACHE = device_info.copy()
                DEVICE_STATE_CACHE = device_states.copy()

                if not devices:
                    render_device_headers(device_list_frame)

                    empty_box = tk.Frame(device_list_frame, bg=_SURFACE)
                    empty_box.pack(fill="both", expand=True, pady=(38, 0))

                    tk.Label(
                        empty_box,
                        text="No devices found",
                        bg=_SURFACE,
                        fg=_FG_PRIMARY,
                        font=("SF Pro Display", 16, "bold")
                    ).pack(pady=(0, 6))

                    tk.Label(
                        empty_box,
                        text="Connect an iPhone or iPad via USB, or pair Apple TV in Xcode, then press List Devices again.",
                        bg=_SURFACE,
                        fg=_FG_SECONDARY,
                        font=_FONT_BODY,
                        wraplength=700,
                        justify="center"
                    ).pack()

                    status_label.config(text="No devices found.")
                    device_udid_combo["values"] = []
                    device_udid_var.set("")
                    device_udid_combo.set("")
                    update_show_games_button_text(None)
                    unpair_button.config(state="disabled")
                    return

                LAST_DEVICE_SCAN = list(devices)
                save_data()

                render_devices_with_icons(device_list_frame, devices)
                device_list_frame.device_info = device_info

                udids = [d["identifier"] for d in devices]
                device_udid_combo["values"] = udids
                device_udid_combo.set(udids[0])
                device_udid_var.set(udids[0])

                unpair_button.config(state="normal" if device_ids else "disabled")
                refresh_command_history_combo()
                connection_hint_label.config(text="")
            root.after(0, update_ui)

        except Exception as e:
            root.after(0, lambda: status_label.config(
                text=f"Device scan failed: {e}"
            ))

            root.after(0, update_ui)

        except Exception as e:
            root.after(0, lambda: status_label.config(
                text=f"Device scan failed: {e}"
            ))

        finally:
            root.after(0, lambda: (
                device_spinner.stop(),
                list_devices_button.config(state="normal"),
                status_label.config(text="Devices loaded."),
                root.after(1500, lambda: status_label.config(text=""))
            ))

    threading.Thread(target=background_task, daemon=True).start()

def unpair_device():
    """Unpair the selected/highlighted device."""
    global LAST_DEVICE_SCAN

    udid = device_udid_var.get().strip()
    if not udid:
        messagebox.showwarning("No Device Selected", "Please select a device to unpair.")
        return

    device_entry = next((d for d in LAST_DEVICE_SCAN if d["identifier"] == udid), None)
    if device_entry:
        device_display = f"{device_entry['name'].replace('?', chr(39))} ({device_entry['model'].replace('?', chr(39))})"
    else:
        device_display = get_device_display(udid)

    confirm = messagebox.askyesno("Confirm Unpair", f"Are you sure you want to unpair {device_display}?")
    if not confirm:
        return

    command = f"xcrun devicectl manage unpair --device {udid}"
    output = run_command(command)

    append_log(output + "\n")

    LAST_DEVICE_SCAN = [d for d in LAST_DEVICE_SCAN if d["identifier"] != udid]
    DEVICE_INFO_CACHE.pop(udid, None)
    DEVICE_STATE_CACHE.pop(udid, None)
    save_data()

    root.after(500, list_devices)

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

        if display_str in appname_to_command:
            continue

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

    games_spinner.start()

    def background_task():
        try:
            bundle_map = {}
            name_map = {}

            def _fetch_bundles():
                nonlocal bundle_map, name_map
                bundle_map, name_map = _fetch_bundle_id_map(udid)

            bundle_thread = threading.Thread(target=_fetch_bundles, daemon=True)
            bundle_thread.start()

            command = f"xcrun devicectl device info processes --device {udid} 2>&1"
            output = run_command(command)

            bundle_thread.join(timeout=32)

            LIVE_BUNDLE_ID_MAP.clear()
            LIVE_BUNDLE_ID_MAP.update(bundle_map)
            LIVE_DISPLAY_NAME_MAP.clear()
            LIVE_DISPLAY_NAME_MAP.update(name_map)

            root.after(0, lambda: process_apps_output(output))
        finally:
            root.after(0, games_spinner.stop)

    threading.Thread(target=background_task, daemon=True).start()

# === Select game with keyboard ===
last_letter_pressed = None
last_letter_index = -1

def _apps_move_selection(direction):
    rf_list = getattr(apps_list_frame, "_row_frames", [])
    if not rf_list:
        return
    current = getattr(apps_list_frame, "_selected_index", -1)
    visible = [i for i, rf in enumerate(rf_list) if rf is not None]
    if not visible:
        return
    if current not in visible:
        target = visible[0]
    else:
        pos = visible.index(current)
        if direction == "down":
            pos = min(pos + 1, len(visible) - 1)
        else:
            pos = max(pos - 1, 0)
        target = visible[pos]

    row = rf_list[target]
    full_path = apps_list_frame.full_path_map[target]
    display = apps_list_frame.display_list[target]

    for rf in rf_list:
        if rf is not None:
            _set_widget_bg(rf, _SURFACE)
    _set_widget_bg(row, _SELECTION)
    apps_list_frame._selected_index = target
    app_path_combo.set(display)
    app_path_combo.full_path = full_path
    update_launch_button_text(display)
    apps_list_frame.selected_app_name = display

    apps_canvas.update_idletasks()
    row.update_idletasks()
    total = apps_list_frame.winfo_height()
    y = row.winfo_y()
    h = apps_canvas.winfo_height()
    if total > 0:
        apps_canvas.yview_moveto(max(0.0, min(1.0, (y - h / 3) / total)))

def jump_to_app_starting_with(letter):
    global last_letter_pressed, last_letter_index

    display_list = getattr(apps_list_frame, "display_list", [])
    rf_list = getattr(apps_list_frame, "_row_frames", [])
    if not display_list:
        return

    matches = [
        i for i, name in enumerate(display_list)
        if name.lower().startswith(letter.lower()) and i < len(rf_list) and rf_list[i] is not None
    ]
    if not matches:
        return

    if last_letter_pressed == letter:
        last_letter_index = (last_letter_index + 1) % len(matches)
    else:
        last_letter_pressed = letter
        last_letter_index = 0

    target = matches[last_letter_index]
    row = rf_list[target]
    full_path = apps_list_frame.full_path_map[target]
    display = display_list[target]

    for rf in rf_list:
        if rf is not None:
            _set_widget_bg(rf, _SURFACE)
    _set_widget_bg(row, _SELECTION)
    apps_list_frame._selected_index = target
    app_path_combo.set(display)
    app_path_combo.full_path = full_path
    update_launch_button_text(display)

def on_apps_keypress(event):
    if not event.char or not event.char.isalpha():
        return
    jump_to_app_starting_with(event.char)

# === FILTER AND UPDATE RUNNING APP LIST ===
def detect_device_locked_issue(output: str) -> bool:
    if not output:
        return False

    text = output.lower()

    return (
        "device is locked" in text or
        "devicelocked" in text or
        "kamdmobileimagemounterdevicelocked" in text
    )

def _set_widget_bg(widget, color):
    try:
        widget.config(bg=color)
    except Exception:
        pass
    for child in widget.winfo_children():
        _set_widget_bg(child, color)


def _show_apps_error(message):
    for child in apps_list_frame.winfo_children():
        child.destroy()
    apps_list_frame.full_path_map = []
    apps_list_frame.display_list = []
    apps_list_frame._internal_names = []
    apps_list_frame._row_frames = []
    apps_list_frame._selected_index = -1
    tk.Label(
        apps_list_frame,
        text=message,
        bg=_SURFACE,
        fg=_FG_SECONDARY,
        font=_FONT_BODY,
        justify="left",
        anchor="nw",
        padx=16,
        pady=16,
    ).pack(anchor="nw", fill="x", padx=16, pady=16)

def _apply_apps_sort(data):
    sort = (_apps_sort_var.get() if _apps_sort_var else "").replace("Sort by: ", "") or "Recently Detected"
    if sort == "Name":
        base = sorted(data, key=lambda x: x[2].lower())
    elif sort == "Previously Launched":
        history_order = {}
        for idx, entry in enumerate(command_history):
            if not isinstance(entry, dict):
                continue
            fp = entry.get("app_path", "")
            if fp and fp not in history_order:
                history_order[fp] = idx
        base = sorted(data, key=lambda x: history_order.get(x[0], 9999))
    else:
        base = sorted(data, key=lambda x: APP_LAST_DETECTED.get(x[1], 0.0), reverse=True)
    pinned = [x for x in base if x[1] in pinned_apps]
    unpinned = [x for x in base if x[1] not in pinned_apps]
    return pinned + unpinned

def _refresh_hidden_games_combo():
    pass 

def _hide_app(internal_name):
    hidden_apps.add(internal_name)
    save_data()
    _do_refilter()
    _refresh_hidden_games_combo()

def _pin_app(internal_name):
    pinned_apps.add(internal_name)
    save_data()
    _do_refilter()

def _unpin_app(internal_name):
    pinned_apps.discard(internal_name)
    save_data()
    _do_refilter()

def _render_apps_rows(data, current_gen):
    for child in apps_list_frame.winfo_children():
        child.destroy()

    apps_list_frame.full_path_map = [d[0] for d in data]
    apps_list_frame._internal_names = [d[1] for d in data]
    apps_list_frame.display_list = [d[2] for d in data]
    apps_list_frame._row_frames = [None] * len(data)
    apps_list_frame._selected_index = -1

    search_term = (_apps_search_var.get() if _apps_search_var else "").strip().lower()

    visible = [
        (i, fp, internal, display)
        for i, (fp, internal, display) in enumerate(data)
        if not search_term or search_term in display.lower() or search_term in internal.lower()
    ]

    for j, (i, full_path, internal, display) in enumerate(visible):
        row = tk.Frame(apps_list_frame, bg=_SURFACE, height=54)
        row.pack(fill="x")
        row.pack_propagate(False)
        row._internal = internal
        apps_list_frame._row_frames[i] = row

        icon_slot = tk.Frame(row, width=54, height=54, bg=_SURFACE)
        icon_slot.pack(side="left")
        icon_slot.pack_propagate(False)

        photo = _get_game_icon_photo(internal) or _generic_game_icon
        icon_lbl = tk.Label(icon_slot, image=photo, bg=_SURFACE, bd=0)
        icon_lbl.image = photo
        icon_lbl.place(relx=0.5, rely=0.5, anchor="center")
        row._icon_label = icon_lbl

        text_area = tk.Frame(row, bg=_SURFACE)
        text_area.pack(side="left", fill="both", expand=True, padx=(4, 12))

        text_center = tk.Frame(text_area, bg=_SURFACE)
        text_center.place(relx=0, rely=0.5, anchor="w", relwidth=1)

        tk.Label(
            text_center, text=display,
            bg=_SURFACE, fg=_FG_PRIMARY, font=_FONT_BODY, anchor="w",
        ).pack(anchor="w")

        if internal in SKIP_ICON_LOOKUP:
            tk.Label(
                text_center, text="Game name not identifiable",
                bg=_SURFACE, fg=_FG_TERTIARY, font=("SF Pro Text", 11), anchor="w",
            ).pack(anchor="w")

        hud_status = _metal_hud_status(internal, display)
        if hud_status:
            tk.Label(
                text_center, text=hud_status[0],
                bg=_SURFACE, fg=hud_status[1], font=("SF Pro Text", 11), anchor="w",
            ).pack(anchor="w")

        def make_select(idx, fp, dn, r):
            def _select(event=None):
                for rf in apps_list_frame._row_frames:
                    if rf is not None:
                        _set_widget_bg(rf, _SURFACE)
                _set_widget_bg(r, _SELECTION)
                apps_list_frame._selected_index = idx
                app_path_combo.set(dn)
                app_path_combo.full_path = fp
                update_launch_button_text(dn)
                apps_list_frame.selected_app_name = dn
                apps_canvas.focus_set()
                return "break"
            return _select

        select_fn = make_select(i, full_path, display, row)

        def make_three_dot_menu(iname, dname):
            def _show(event=None):
                menu = tk.Menu(root, tearoff=0)
                if iname in pinned_apps:
                    menu.add_command(label="Unpin from Top", command=lambda: _unpin_app(iname))
                else:
                    menu.add_command(label="Pin to Top", command=lambda: _pin_app(iname))
                menu.add_separator()
                menu.add_command(
                    label="Hide App",
                    command=lambda: _hide_app(iname)
                )
                menu.add_separator()
                def _make_report(rtype, msg):
                    def _do():
                        icon_url = GAME_ICON_URL_MAP.get(iname, "")
                        send_app_report(iname, dname, icon_url, rtype)
                        messagebox.showinfo("Report Sent", f"{msg}\n\nI'll review and fix it in a future update.")
                    return _do
                menu.add_command(label="Report Wrong Icon",          command=_make_report("Wrong Icon",       f"Thanks! Wrong icon report for \"{dname}\" has been sent."))
                menu.add_command(label="Report Wrong Name",          command=_make_report("Wrong Name",       f"Thanks! Wrong name report for \"{dname}\" has been sent."))
                menu.add_command(label="Report: Not a Game",         command=_make_report("Not a Game",       f"Thanks! \"{dname}\" has been flagged as not a game."))
                menu.add_command(label="Report: Metal HUD Supported",   command=_make_report("HUD Supported",   f"Thanks! \"{dname}\" has been reported as Metal HUD supported."))
                menu.add_command(label="Report: Metal HUD Unsupported", command=_make_report("HUD Unsupported", f"Thanks! \"{dname}\" has been reported as Metal HUD unsupported."))
                try:
                    menu.tk_popup(event.x_root, event.y_root)
                finally:
                    menu.grab_release()
            return _show

        dots_btn = tk.Label(
            row,
            text="⋮",
            bg=_SURFACE,
            fg=_FG_SECONDARY,
            font=("SF Pro Text", 18),
            padx=10,
            pady=0,
        )
        dots_btn.pack(side="right", fill="y")
        dots_btn.bind("<Button-1>", make_three_dot_menu(internal, display))

        def bind_all(w, fn, exclude=None):
            if w is exclude:
                return
            w.bind("<Button-1>", fn)
            for child in w.winfo_children():
                bind_all(child, fn, exclude=exclude)

        bind_all(row, select_fn, exclude=dots_btn)

        if j < len(visible) - 1:
            sep = tk.Frame(apps_list_frame, bg=_BORDER, height=1)
            sep._is_separator = True
            sep.pack(fill="x")

    if visible:
        first_i, first_fp, first_display = visible[0][0], visible[0][1], visible[0][3]
        first_row = apps_list_frame._row_frames[first_i]
        if first_row:
            apps_list_frame._selected_index = first_i
            _set_widget_bg(first_row, _SELECTION)
            app_path_combo.set(first_display)
            app_path_combo.full_path = first_fp
            update_launch_button_text(first_display)

    def _bg_fetch_icons():
        for _, internal, display in data:
            if GAME_LIST_GENERATION[0] != current_gen:
                return
            if internal in GAME_ICON_PHOTO_CACHE:
                continue
            pil = _fetch_game_icon_pil(internal, display_name=display)
            if pil and GAME_LIST_GENERATION[0] == current_gen:
                def _apply(iname=internal):
                    if GAME_LIST_GENERATION[0] != current_gen:
                        return
                    photo = _get_game_icon_photo(iname)
                    if not photo:
                        return
                    for rf in apps_list_frame._row_frames:
                        if rf is not None and getattr(rf, '_internal', None) == iname:
                            try:
                                rf._icon_label.config(image=photo)
                                rf._icon_label.image = photo
                            except Exception:
                                pass
                            break
                root.after(0, _apply)

        for _, internal, display in _current_apps_data:
            if GAME_LIST_GENERATION[0] != current_gen:
                return
            if internal not in hidden_apps:
                continue
            if internal in GAME_ICON_PHOTO_CACHE:
                continue
            _fetch_game_icon_pil(internal, display_name=display)

    threading.Thread(target=_bg_fetch_icons, daemon=True).start()
    _bind_apps_scroll_hover(apps_list_frame)

def _do_refilter():
    if not _current_apps_data:
        return
    visible_data = [d for d in _current_apps_data if d[1] not in hidden_apps]
    sorted_data = _apply_apps_sort(visible_data)
    current_gen = GAME_LIST_GENERATION[0]
    _render_apps_rows(sorted_data, current_gen)

def process_apps_output(output):
    global DEVICE_PREPARING_WARNING_SHOWN, _current_apps_data

    # DEVELOPER MODE DISABLED
    if output and "Developer Mode is disabled" in output:
        _show_apps_error(
            "DEVELOPER MODE DISABLED\n\n"
            "Enable it on your device:\n"
            "Settings → Privacy & Security → Developer Mode"
        )
        return

    # DEVICE LOCKED
    if detect_device_locked_issue(output):
        _show_apps_error(
            "DEVICE LOCKED\n\n"
            "Unlock the device and try again.\n\n"
            "Then click:\n"
            "Show Running Games"
        )
        return

    # Pairing error (DEVICE NOT PAIRED / STILL CONNECTING)
    global PAIRING_ATTEMPTS

    if is_pairing_error(output):
        PAIRING_ATTEMPTS += 1
        message = (
            "STILL CONNECTING\n\n"
            "Unlock → Trust → replug (may take a few tries)\n\n"
            "Then: Show Running Games"
        ) if PAIRING_ATTEMPTS >= 3 else (
            "DEVICE NOT PAIRED\n\n"
            "Unlock → Is USB connected? → Trust → replug\n\n"
            "Then: Show Running Games"
        )
        _show_apps_error(message)
        return

    # No processes returned yet (Xcode preparing)
    if not output or not output.strip():
        _show_apps_error(
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

    has_user_app = (
        "Bundle/Application" in output or
        ".app" in output
    )

    PAIRING_ATTEMPTS = 0

    if not has_user_app:
        _show_apps_error(
            "NO GAMES DETECTED\n\n"
            "Launch a game and try again.\n\n"
            "Then click:\n"
            "Show Running Games"
        )
        return

    filter_out = APP_FILTER_OUT

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

    if not unique_apps:
        append_log("\n[DEBUG] devicectl output:\n" + output + "\n")
        _show_apps_error(
            "NO GAMES DETECTED\n\n"
            "Launch a game and try again.\n\n"
            "Then click:\n"
            "Show Running Games"
        )
        return

    DEVICE_PREPARING_WARNING_SHOWN = False

    now = time.time()
    raw_apps_data = []
    for full_path, app_name in unique_apps.items():
        base_name = app_name[:-4] if app_name.endswith(".app") else app_name
        display_name = add_display_name(base_name)
        APP_LAST_DETECTED[base_name] = now
        raw_apps_data.append((full_path, base_name, display_name))

    _current_apps_data[:] = raw_apps_data

    GAME_LIST_GENERATION[0] += 1
    current_gen = GAME_LIST_GENERATION[0]

    visible_data = [d for d in raw_apps_data if d[1] not in hidden_apps]
    sorted_data = _apply_apps_sort(visible_data)
    _render_apps_rows(sorted_data, current_gen)

    display_names = [d[2] for d in raw_apps_data]
    app_path_combo['values'] = display_names

    apps_canvas.focus_set()

# === OUTPUT PROCESSING AND WARNINGS ===
def update_launch_output(output):
    append_log(output + "\n")

    global OPENGL_WARNING_SHOWN

    text = (output or "").lower()

    opengl_detected = any(marker in text for marker in [
        "opengl es",
        "gles is",
        "sdl gl version",
        "aaplopenglviewcontroller",
    ])

    if opengl_detected and not OPENGL_WARNING_SHOWN:
        OPENGL_WARNING_SHOWN = True

        def _show_opengl_button_warning():
            launch_button.config(
                text="OpenGL detected, Metal HUD may not work"
            )

            root.after(
                10000,
                lambda: update_launch_button_text(
                    app_path_combo.get()
                )
            )

        root.after(0, _show_opengl_button_warning)


# === ANALYTICS, SAVED GAMES, AND HUD CONFIG HELPERS ===
_ANALYTICS_URL = "https://script.google.com/macros/s/AKfycbzlfap_uHHIys-_tRiQSTIw1ZGqgjt-pDNlYDVjIA5_hkw6nujAkWmTeWofAri6B6IJ/exec"

def send_analytics(device_model, app_name, connection_state, icon_url="", raw_app_name=""):
    if "analytics_opt_in_var" in globals():
        if not analytics_opt_in_var.get():
            return
    else:
        if not analytics_opt_in:
            return

    m = re.search(r'\(([^)]+)\)$', device_model or "")
    device_model_real = m.group(1) if m else device_model
    connection_real = get_display_state_text(connection_state)

    def worker():
        try:
            payload = json.dumps({
                "type": "launch",
                "device_model": device_model,
                "device_model_real": device_model_real,
                "connection_state": connection_state,
                "connection_real": connection_real,
                "app_name": app_name,
                "raw_app_name": raw_app_name,
                "app_icon_url": icon_url,
            }).encode("utf-8")

            req = urllib.request.Request(
                _ANALYTICS_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=15) as response:
                body = response.read().decode("utf-8", errors="replace")
                print(f"[Analytics] response: {body}")

        except Exception as e:
            print(f"[Analytics] send failed: {e}")

    threading.Thread(target=worker, daemon=True).start()

def send_app_report(internal_name, display_name, icon_url, report_type):
    def worker():
        try:
            payload = json.dumps({
                "type":         "icon_report",
                "report_type":  report_type,
                "raw_app_name": internal_name,
                "app_name":     display_name,
                "app_icon_url": icon_url,
            }).encode("utf-8")
            req = urllib.request.Request(
                _ANALYTICS_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                print(f"[App report] response: {response.read().decode('utf-8', errors='replace')}")
        except Exception as e:
            print(f"[App report] send failed: {e}")

    threading.Thread(target=worker, daemon=True).start()


def run_command_in_thread(command):
    try:
        global process
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        for line in process.stdout:
            root.after(0, lambda l=line: update_launch_output(l))

        process.wait()

    except Exception as e:
        root.after(0, lambda: update_launch_output(f"Error: {e}"))

def show_temporary_status_message(message, duration=3000):
    launch_status_label.config(text=message)
    launch_status_label.after(duration, lambda: launch_status_label.config(text=""))

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
    save_data()

def get_hud_env_vars(preset):
    selected_elements = [
        elem for elem, var in hud_elements_vars.items()
        if var.get() == 1
    ]

    if selected_elements:
        return {
            "MTL_HUD_ENABLED": "1",
            "MTL_HUD_ELEMENTS": ",".join(selected_elements)
        }

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

    return {"MTL_HUD_ENABLED": "1"}

def is_app_running(udid, bundle_id):
    result = subprocess.run(
        f"xcrun devicectl device process list --device {udid}",
        shell=True, capture_output=True, text=True
    )
    return bundle_id in result.stdout

# === APP LAUNCH AND METAL HUD EXECUTION ===
def launch_app():
    global current_launch_process, OPENGL_WARNING_SHOWN
    OPENGL_WARNING_SHOWN = False

    udid = device_udid_combo.get().strip()

    app_path = getattr(app_path_combo, "full_path", None)

    if not udid or not app_path:
        messagebox.showwarning("Missing Info", "Please select Device and Game")
        return

    device_model = get_device_display(udid)

    app_basename = os.path.basename(app_path)
    raw_app_name = app_basename[:-4] if app_basename.endswith(".app") else app_basename
    app_name = add_display_name(raw_app_name)
    connection_state = get_device_state(udid)

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
    icon_url = GAME_ICON_URL_MAP.get(raw_app_name, "")
    send_analytics(device_model, app_name, connection_state, icon_url=icon_url, raw_app_name=raw_app_name)

    try:
        if current_launch_process and current_launch_process.poll() is None:
            current_launch_process.terminate()
            current_launch_process = None
    except Exception:
        pass

    def launch_close_relaunch():
        global current_launch_process

        root.after(0, lambda: launch_button.config(text=f"Launching {app_name} with Metal HUD…"))

        first_proc = subprocess.Popen(
            base_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        current_launch_process = first_proc

        time.sleep(1.0)

        root.after(0, lambda: launch_button.config(text=f"Restarting {app_name} with Metal HUD…"))

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

        launched_shown = False
        for line in second_proc.stdout:
            root.after(0, lambda l=line: update_launch_output(l))
            if not launched_shown and line.strip().startswith("Launched"):
                launched_shown = True
                root.after(0, lambda: launch_button.config(text=f"{app_name} Launched with Metal HUD"))
                root.after(3000, lambda: update_launch_button_text(app_name))

        try:
            second_proc.stdout.close()
        except Exception:
            pass

        second_proc.wait()

        if second_proc.returncode == 0:
            root.after(0, maybe_prompt_analytics_after_launch)

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
    pass  

def move_selection(widget, direction="down"):
    """Move selection in the device list (up/down by one row)."""
    if widget != device_text:
        return
    widget.config(state='normal')
    ranges = widget.tag_ranges("selected_device")
    line_num = int(widget.index(ranges[0]).split('.')[0]) if ranges else 1

    if direction == "down":
        new_line = min(line_num + 1, int(widget.index(tk.END).split('.')[0]) - 1)
    else:
        new_line = max(line_num - 1, 1)

    highlight_device_row(widget, new_line)
    widget.see(f"{new_line}.0")

    if hasattr(widget, "_device_rows") and 1 <= new_line <= len(widget._device_rows):
        device_udid_combo.set(widget._device_rows[new_line - 1]["identifier"])
    widget.config(state='disabled')

# === Export logs to desktop ===
def export_logs_to_desktop():
    try:
        log_text = "".join(APP_LOG_BUFFER).strip()

        if not log_text:
            messagebox.showwarning("No Logs", "There are no logs to export.")
            return

        desktop_path = os.path.join(
            os.path.expanduser("~/Desktop"),
            "MetalHUD_Logs.txt"
        )

        counter = 2
        base_path = desktop_path

        while os.path.exists(desktop_path):
            desktop_path = os.path.join(
                os.path.expanduser("~/Desktop"),
                f"MetalHUD_Logs_{counter}.txt"
            )
            counter += 1

        with open(desktop_path, "w", encoding="utf-8") as f:
            f.write(log_text)

        subprocess.Popen(["open", desktop_path])

        messagebox.showinfo(
            "Logs Exported",
            f"Saved to Desktop:\n{os.path.basename(desktop_path)}"
        )

    except Exception as e:
        messagebox.showerror("Export Failed", f"Could not export logs:\n{e}")

# === GUI INITIALIZATION ===
root.title("Metal HUD Mobile Config")
load_data()

root.update_idletasks()

default_width = 1300

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

max_height = screen_height - 120
default_height = min(870, max_height)

x = (screen_width - default_width) // 2
y = max(20, (screen_height - default_height) // 2)

default_geometry = f"{default_width}x{default_height}+{x}+{y}"

root.geometry(window_geometry_saved or default_geometry)

locked_width = default_width
locked_height = default_height

root.minsize(locked_width, locked_height)
root.maxsize(locked_width, locked_height)
root.resizable(False, False)

try:
    root.attributes("-fullscreen", False)
    root.tk.call("tk::unsupported::MacWindowStyle", "style", root._w, "document", "closeBox miniaturizeBox")
except Exception:
    pass

resize_save_job = None

def on_window_resize(event):
    global resize_save_job

    if event.widget != root:
        return

    if resize_save_job is not None:
        root.after_cancel(resize_save_job)

    resize_save_job = root.after(500, save_data)

root.bind("<Configure>", on_window_resize)

padx_side = 44

# === Scrollable Layout ===
outer_frame = tk.Frame(root, bg=_BG)
outer_frame.pack(fill="both", expand=True)

side_panel_visible = tk.BooleanVar(value=False)

side_panel = tk.Frame(
    outer_frame,
    bg=_SURFACE,
    width=320,
    bd=0,
    highlightthickness=1,
    highlightbackground=_BORDER
)

# === SIDE PANEL CONTENTS ===
tk.Frame(side_panel, bg=_BORDER, height=1).pack(fill="x")

panel_inner = tk.Frame(side_panel, bg=_SURFACE)
panel_inner.pack(fill="both", expand=True, padx=18, pady=18)

tk.Label(
    panel_inner,
    text="Library",
    bg=_SURFACE,
    fg=_FG_PRIMARY,
    font=("SF Pro Display", 15, "bold"),
    anchor="w"
).pack(anchor="w", pady=(0, 16))

tk.Label(
    panel_inner,
    text="SAVED GAMES",
    bg=_SURFACE,
    fg=_FG_TERTIARY,
    font=("SF Pro Text", 10),
    anchor="w"
).pack(anchor="w")

saved_paths_combo = ttk.Combobox(
    panel_inner,
    values=sorted(saved_paths.keys()),
    state="readonly",
    width=28
)
saved_paths_combo.pack(anchor="w", pady=(4, 8), fill="x")
saved_paths_combo.bind("<FocusIn>", lambda e: saved_paths_combo.selection_clear())
saved_paths_combo.bind("<Button-1>", lambda e: saved_paths_combo.selection_clear())
saved_paths_combo.bind("<<ComboboxSelected>>", on_saved_path_select)

btn_row_saved = tk.Frame(panel_inner, bg=_SURFACE)
btn_row_saved.pack(anchor="w", fill="x", pady=(0, 16))
ttk.Button(btn_row_saved, text="Save", command=save_app_path).pack(side="left", padx=(0, 6))
ttk.Button(btn_row_saved, text="Delete", command=delete_saved_path, style="Destructive.TButton").pack(side="left")

tk.Frame(panel_inner, bg=_BORDER, height=1).pack(fill="x", pady=(0, 16))

tk.Label(
    panel_inner,
    text="PREVIOUS GAMES",
    bg=_SURFACE,
    fg=_FG_TERTIARY,
    font=("SF Pro Text", 10),
    anchor="w"
).pack(anchor="w")

command_history_combo = ttk.Combobox(
    panel_inner,
    values=[],
    state="readonly",
    width=28
)
command_history_combo.pack(anchor="w", pady=(4, 0), fill="x")

tk.Frame(panel_inner, bg=_BORDER, height=1).pack(fill="x", pady=(16, 0))

tk.Label(
    panel_inner,
    text="HIDDEN GAMES",
    bg=_SURFACE,
    fg=_FG_TERTIARY,
    font=("SF Pro Text", 10),
    anchor="w"
).pack(anchor="w", pady=(12, 0))

hidden_games_combo = ttk.Combobox(
    panel_inner,
    values=[],
    state="readonly",
    width=28
)
hidden_games_combo.pack(anchor="w", pady=(4, 8), fill="x")

def _refresh_hidden_games_combo():
    names = sorted(
        add_display_name(n) + f" ({n})" for n in hidden_apps
    )
    hidden_games_combo["values"] = names
    if names:
        hidden_games_combo.set(names[0])
    else:
        hidden_games_combo.set("")

def _unhide_selected():
    sel = hidden_games_combo.get()
    if not sel:
        return
    import re as _re
    m = _re.search(r'\(([^)]+)\)$', sel)
    if not m:
        return
    internal = m.group(1)
    hidden_apps.discard(internal)
    save_data()
    _refresh_hidden_games_combo()
    _do_refilter()

ttk.Button(panel_inner, text="Unhide", command=_unhide_selected).pack(anchor="w")

_refresh_hidden_games_combo()

def open_side_panel_instant():
    side_panel.config(width=320)
    side_panel.pack(side="right", fill="y", before=canvas)
    side_panel.pack_propagate(False)
    side_panel_visible.set(True)


def toggle_side_panel():
    global library_panel_open

    target_width = 320
    delay = 8

    def open_panel(width=0):
        global library_panel_open
        if not side_panel.winfo_ismapped():
            side_panel.config(width=0)
            side_panel.pack(side="right", fill="y", before=canvas)
            side_panel.pack_propagate(False)

        if width < target_width:
            side_panel.config(width=width)
            outer_frame.update_idletasks()
            speed = max(6, int((target_width - width) * 0.2))
            root.after(delay, lambda: open_panel(width + speed))
        else:
            side_panel.config(width=target_width)
            outer_frame.update_idletasks()
            side_panel_visible.set(True)
            library_panel_open = True
            save_data()

    def close_panel(width=None):
        global library_panel_open
        if width is None:
            width = side_panel.winfo_width()

        if width > 0:
            side_panel.config(width=width)
            outer_frame.update_idletasks()
            speed = max(6, int(width * 0.2))
            root.after(delay, lambda: close_panel(width - speed))
        else:
            side_panel.config(width=0)
            side_panel.pack_forget()
            side_panel_visible.set(False)
            library_panel_open = False
            save_data()

    if side_panel_visible.get():
        close_panel()
    else:
        open_panel()

canvas = tk.Canvas(outer_frame, highlightthickness=0, background=_BG)
canvas.pack(side="left", fill="both", expand=True)

scrollable_frame = ttk.Frame(canvas)

canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

def on_frame_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

scrollable_frame.bind("<Configure>", on_frame_configure)

def on_canvas_configure(event):
    canvas.itemconfig(canvas_window, width=event.width)

canvas.bind("<Configure>", on_canvas_configure)

# === LIST DEVICES BUTTON + PROGRESS BAR ===
list_devices_frame = ttk.Frame(scrollable_frame)
list_devices_frame.pack(anchor="w", fill="x", padx=padx_side, pady=(25, 0))

list_devices_top_row = ttk.Frame(list_devices_frame)
list_devices_top_row.pack(fill="x")

list_devices_button = ttk.Button(
    list_devices_top_row,
    text="List Devices (Cmd+R)",
    command=list_devices
)
list_devices_button.pack(side="left")

device_spinner = SpinningIcon(list_devices_top_row)

side_panel_toggle = ttk.Button(
    list_devices_top_row,
    text="☰  Library",
    command=toggle_side_panel
)
side_panel_toggle.pack(side="right")

status_label = ttk.Label(list_devices_frame, text="", foreground="red")

_device_outer, device_frame = make_rounded_box(scrollable_frame, radius=20, height=235)
_device_outer.pack(fill=tk.X, padx=padx_side, pady=(8, 5))

device_canvas = tk.Canvas(
    device_frame,
    bg=_SURFACE,
    height=200,
    bd=0,
    highlightthickness=0
)
device_canvas.pack(side="left", fill="both", expand=True, padx=(14, 6), pady=10)

device_scrollbar = tk.Scrollbar(
    device_frame,
    orient="vertical",
    command=device_canvas.yview,
)
device_scrollbar.pack(side="right", fill="y", pady=10)

device_canvas.configure(yscrollcommand=device_scrollbar.set)

device_list_frame = tk.Frame(device_canvas, bg=_SURFACE)
device_canvas_window = device_canvas.create_window(
    (0, 0),
    window=device_list_frame,
    anchor="nw"
)

def update_device_scrollregion(event=None):
    device_canvas.configure(scrollregion=device_canvas.bbox("all"))

def resize_device_list_width(event):
    device_canvas.itemconfig(device_canvas_window, width=event.width)

device_list_frame.bind("<Configure>", update_device_scrollregion)
device_canvas.bind("<Configure>", resize_device_list_width)

def _on_device_mousewheel(event):
    device_canvas.yview_scroll(int(-1 * event.delta), "units")
    return "break"

def _bind_device_scroll(event):
    device_canvas.bind_all("<MouseWheel>", _on_device_mousewheel)

def _unbind_device_scroll(event):
    device_canvas.unbind_all("<MouseWheel>")

device_canvas.bind("<Enter>", _bind_device_scroll)
device_canvas.bind("<Leave>", _unbind_device_scroll)
device_list_frame.bind("<Enter>", _bind_device_scroll)
device_list_frame.bind("<Leave>", _unbind_device_scroll)

device_text = device_list_frame

def render_device_headers(widget):
    for child in widget.winfo_children():
        child.destroy()

    NAME_COL_WIDTH = 220
    STATE_COL_WIDTH = 180
    WIFI_COL_WIDTH = 60
    MODEL_COL_WIDTH = 300
    MORE_COL_WIDTH = 32

    header = tk.Frame(widget, bg=_SURFACE)
    header.pack(fill="x", pady=(0, 8))

    tk.Label(
        header,
        text="Name",
        bg=_SURFACE,
        fg=_FG_TERTIARY,
        font=("SF Pro Text", 11)
    ).grid(row=0, column=0, sticky="w", padx=(4, 0))

    tk.Label(
        header,
        text="Wireless state",
        bg=_SURFACE,
        fg=_FG_TERTIARY,
        font=("SF Pro Text", 11)
    ).grid(row=0, column=1, sticky="w")

    tk.Label(
        header,
        text="Device model name",
        bg=_SURFACE,
        fg=_FG_TERTIARY,
        font=("SF Pro Text", 11)
    ).grid(row=0, column=3, sticky="w")

    for col, size in [
        (0, NAME_COL_WIDTH),
        (1, STATE_COL_WIDTH),
        (2, WIFI_COL_WIDTH),
        (3, MODEL_COL_WIDTH),
        (4, MORE_COL_WIDTH)
    ]:
        header.grid_columnconfigure(col, minsize=size)


render_device_headers(device_text)

connection_hint_label = ttk.Label(
    scrollable_frame,
    text="",
    foreground="red",
    anchor="w",
    justify="left",
    wraplength=800
)
connection_hint_label.pack(anchor="w", fill="x", padx=padx_side, pady=(0, 2))

def update_wrap(event):
    connection_hint_label.config(wraplength=event.width - 60)

scrollable_frame.bind("<Configure>", update_wrap)

device_udid_var = tk.StringVar(value="")

device_udid_combo = ttk.Combobox(
    scrollable_frame,
    textvariable=device_udid_var,
    values=[],
    state="readonly"
)

unpair_button = ttk.Button(scrollable_frame, text="Unpair", command=unpair_device, style="Destructive.TButton")
unpair_button.pack_forget()

# === SHOW RUNNING GAMES UI ===
show_games_frame = ttk.Frame(scrollable_frame)
show_games_frame.pack(anchor="w", fill="x", padx=padx_side, pady=(0, 5))

show_games_top_row = ttk.Frame(show_games_frame)
show_games_top_row.pack(fill="x")

show_games_button = ttk.Button(
    show_games_top_row,
    text="Show Running Games (Cmd+S)",
    command=show_apps
)
show_games_button.pack(side="left")

games_spinner = SpinningIcon(show_games_top_row)

_apps_sort_var = tk.StringVar(value="Sort by: Name")
_sort_combo = ttk.Combobox(
    show_games_top_row,
    textvariable=_apps_sort_var,
    values=["Sort by: Name", "Sort by: Recently Detected", "Sort by: Previously Launched"],
    state="readonly",
    width=26,
)
_sort_combo.pack(side="right")
_sort_combo.bind("<<ComboboxSelected>>", lambda _: _sort_combo.selection_clear())
_apps_sort_var.trace_add("write", lambda *_: _do_refilter())

_apps_search_var = tk.StringVar()

_search_pill = tk.Frame(show_games_top_row, bg=_SURFACE_ALT, highlightthickness=1,
                        highlightbackground=_BORDER, highlightcolor=_ACCENT)
_search_pill.pack(side="left", padx=(10, 10), ipady=3, ipadx=6)

tk.Label(_search_pill, text="⌕", bg=_SURFACE_ALT, fg=_FG_PLACEHOLDER,
         font=("SF Pro Text", 14)).pack(side="left", padx=(6, 2))

_search_entry = tk.Entry(_search_pill, bd=0, relief="flat", bg=_SURFACE_ALT,
                         fg=_FG_PLACEHOLDER, insertbackground=_FG_PRIMARY,
                         font=_FONT_BODY, width=16, highlightthickness=0)
_search_entry.pack(side="left", padx=(0, 6), pady=1)
_search_entry.insert(0, "Search games")

def _on_search_focus_in(e):
    _search_pill.config(highlightbackground=_ACCENT)
    if _search_entry.get() == "Search games":
        _search_entry.delete(0, tk.END)
        _search_entry.config(fg=_FG_PRIMARY)

def _on_search_focus_out(e):
    _search_pill.config(highlightbackground=_BORDER)
    val = _search_entry.get().strip()
    if not val:
        _search_entry.delete(0, tk.END)
        _search_entry.insert(0, "Search games")
        _search_entry.config(fg=_FG_PLACEHOLDER)
        _apps_search_var.set("")
    else:
        _apps_search_var.set(val)

def _on_search_keyrelease(_e=None):
    val = _search_entry.get()
    _apps_search_var.set("" if val == "Search games" else val)

_search_entry.bind("<FocusIn>", _on_search_focus_in)
_search_entry.bind("<FocusOut>", _on_search_focus_out)
_search_entry.bind("<KeyRelease>", _on_search_keyrelease)
_apps_search_var.trace_add("write", lambda *_: _do_refilter())

# === RUNNING GAMES LIST UI ===
_apps_outer, _apps_inner = make_rounded_box(scrollable_frame, radius=20, height=320)
_apps_outer.pack(fill=tk.X, padx=padx_side, pady=(8, 15))

apps_canvas = tk.Canvas(
    _apps_inner,
    bg=_SURFACE,
    bd=0,
    highlightthickness=0,
)
apps_canvas.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=6)

_apps_scrollbar = tk.Scrollbar(_apps_inner, orient="vertical", command=apps_canvas.yview)
_apps_scrollbar.pack(side="right", fill="y", pady=6)
apps_canvas.configure(yscrollcommand=_apps_scrollbar.set)

apps_list_frame = tk.Frame(apps_canvas, bg=_SURFACE)
_apps_canvas_window = apps_canvas.create_window((0, 0), window=apps_list_frame, anchor="nw")

def _on_apps_list_configure(event=None):
    apps_canvas.configure(scrollregion=apps_canvas.bbox("all"))

def _on_apps_canvas_resize(event):
    apps_canvas.itemconfig(_apps_canvas_window, width=event.width)

apps_list_frame.bind("<Configure>", _on_apps_list_configure)
apps_canvas.bind("<Configure>", _on_apps_canvas_resize)

def _on_apps_mousewheel(event):
    apps_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    return "break"

_apps_mw_timer = [None]

def _enable_apps_scroll(e=None):
    if _apps_mw_timer[0]:
        root.after_cancel(_apps_mw_timer[0])
        _apps_mw_timer[0] = None
    apps_canvas.bind_all("<MouseWheel>", _on_apps_mousewheel)

def _disable_apps_scroll_delayed(e=None):
    if _apps_mw_timer[0]:
        root.after_cancel(_apps_mw_timer[0])
    _apps_mw_timer[0] = root.after(120, lambda: apps_canvas.unbind_all("<MouseWheel>"))

def _bind_apps_scroll_hover(w):
    w.bind("<Enter>", _enable_apps_scroll)
    w.bind("<Leave>", _disable_apps_scroll_delayed)
    for child in w.winfo_children():
        _bind_apps_scroll_hover(child)

apps_canvas.bind("<Enter>", _enable_apps_scroll)
apps_canvas.bind("<Leave>", _disable_apps_scroll_delayed)
apps_list_frame.bind("<Enter>", _enable_apps_scroll)
apps_list_frame.bind("<Leave>", _disable_apps_scroll_delayed)

apps_canvas.bind("<Up>", lambda e: _apps_move_selection("up"))
apps_canvas.bind("<Down>", lambda e: _apps_move_selection("down"))
apps_canvas.bind("<Return>", lambda e: launch_app())
apps_canvas.bind("<Key>", on_apps_keypress)
apps_canvas.configure(takefocus=1)

apps_text = apps_list_frame

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

analytics_opt_in_var = tk.BooleanVar(value=bool(analytics_opt_in))

# === HUD ADVANCED OPTIONS (COLLAPSIBLE) ===
hud_arrow_font = tkfont.Font(size=18, weight="bold")

hud_advanced_open = tk.BooleanVar(value=False)

hud_advanced_header = ttk.Frame(scrollable_frame)

hud_arrow_label = ttk.Label(
    hud_advanced_header,
    text="▸",
    font=hud_arrow_font
)
hud_arrow_label.pack(side="left")

hud_advanced_title = ttk.Label(hud_advanced_header, text="Advanced Options")
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

HUD_CONTROL_WIDTH = 370

# === HUD PRESETS ===
HUD_CONTROL_WIDTH = 380

preset_menu = tk.Menu(hud_menu, tearoff=0)
hud_menu.add_cascade(label="Metric Presets", menu=preset_menu)

for preset_name in [
    "Default",
    "Simple",
    "FPS Only",
    "Thermals",
    "Compiled Shaders",
    "Rich",
    "Full"
]:
    preset_menu.add_radiobutton(
        label=preset_name,
        variable=hud_preset_var,
        value=preset_name,
        command=lambda: (on_preset_change(), save_data())
    )

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

config_window = tk.Toplevel(root)
config_window.title("HUD Configuration Panel")
config_window.geometry("850x260")
config_window.minsize(880, 230)
config_window.maxsize(880, 230)
config_window.resizable(False, False)
config_window.configure(bg=_SURFACE)
config_window.withdraw()

def open_config_panel():
    custom_elements_frame.pack(fill=tk.BOTH, expand=True)
    config_window.deiconify()
    config_window.lift()
    config_window.after(100, lambda: _style_toplevel_titlebar(config_window, _SURFACE))

def close_config_panel():
    config_window.withdraw()

config_window.protocol("WM_DELETE_WINDOW", close_config_panel)

config_frame = tk.Frame(config_window, bg=_SURFACE)
config_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

custom_elements_frame = tk.Frame(config_frame, bg=_SURFACE)

row = 0
col = 0
max_cols = 4  

for display_name, internal_name in hud_elements_display_map.items():
    var = tk.IntVar(value=0)
    cb = ttk.Checkbutton(
        custom_elements_frame,
        text=display_name,
        variable=var,
        command=save_data,
        style="White.TCheckbutton"
    )
    cb.grid(row=row, column=col, padx=5, pady=5, sticky="w")
    hud_elements_vars[internal_name] = var

    col += 1
    if col >= max_cols:
        col = 0
        row += 1

custom_elements_frame.pack_forget()

def reset_metrics():
    for var in hud_elements_vars.values():
        var.set(0)
    hud_preset_var.set("Default")
    hud_alignment_var.set("Top-Right")
    hud_scale_var.set("Default")
    save_data()

reset_metrics_button = ttk.Button(
    config_frame,
    text="Reset Metrics",
    command=reset_metrics,
    style="Grey.TButton"
)
reset_metrics_button.pack(anchor="e", pady=(8, 0))

def on_preset_change(*args):
    if RESTORING_FROM_PROFILE:
        return

    save_data()

hud_preset_var.trace_add("write", on_preset_change)
on_preset_change()  

# === HUD ALIGNMENT OPTIONS ===
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

position_menu = tk.Menu(hud_menu, tearoff=0)
hud_menu.add_cascade(label="Position", menu=position_menu)

for position_name in hud_alignment_display_map.keys():
    position_menu.add_radiobutton(
        label=position_name,
        variable=hud_alignment_var,
        value=position_name,
        command=save_data
    )

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

hud_scale_var = tk.StringVar(value="Default")
hud_scale_options = ["Small", "Default", "Large", "Larger", "Max"]

scale_menu = tk.Menu(hud_menu, tearoff=0)
hud_menu.add_cascade(label="Scale", menu=scale_menu)

for scale_name in hud_scale_options:
    scale_menu.add_radiobutton(
        label=scale_name,
        variable=hud_scale_var,
        value=scale_name,
        command=save_data
    )

hud_menu.add_command(
    label="Custom Metrics",
    command=open_config_panel
)

hud_menu.add_command(
    label="Reset Metrics",
    command=lambda: reset_metrics()
)

# === RESTORE SAVED HUD STATE ===
saved_preset = hud_settings_saved.get("preset", "Default")
hud_preset_var.set(saved_preset)

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

# === RESTORE SAVED LIBRARY SELECTION ===
if selected_library and selected_library in saved_paths:
    saved_paths_combo.set(selected_library)
    on_saved_path_select(None)

if library_panel_open:
    open_side_panel_instant()

# === LAUNCH METAL HUD ===
launch_button = ttk.Button(
    scrollable_frame,
    text="Launch App with Metal HUD",
    command=launch_app,
    style="Launch.TButton",
)

launch_button.pack(fill="x", padx=padx_side, pady=(10, 5))


launch_status_label = ttk.Label(
    scrollable_frame,
    text="",
    foreground="red"
)

analytics_checkbox = ttk.Checkbutton(
    scrollable_frame,
    text="Share anonymous compatibility data",
    variable=analytics_opt_in_var,
    command=lambda: save_data()
)
analytics_checkbox.pack(anchor="w", padx=padx_side, pady=(5, 0))

_analytics_info_lines = [
    "  • Device model",
    "  • Connection type (USB / Wi-Fi)",
    "  • App name & icon",
]
_analytics_info_label = tk.Label(
    scrollable_frame,
    text="\n".join(_analytics_info_lines),
    justify="left",
    bg=_BG,
    fg=_FG_TERTIARY,
    font=("SF Pro Text", 11),
)
_analytics_info_label.pack(anchor="w", padx=padx_side, pady=(2, 2))

launch_status_label.pack(anchor="w", padx=padx_side, pady=(0, 10))

def update_launch_button_text(app_name):
    """
    Update the Launch button text to include the selected app name,
    or reset to default if None or empty string is given.
    """
    if app_name:
        launch_button.config(text=f"Launch {app_name} with Metal HUD")
    else:
        launch_button.config(text="Launch App with Metal HUD")

def open_config_panel():
    custom_elements_frame.pack(fill=tk.BOTH, expand=True)
    config_window.deiconify()
    config_window.lift()
    config_window.focus_force()

# === LOG PANEL CONTROLS ===
hud_menu.add_separator()

hud_menu.add_command(
    label="Export Logs",
    command=export_logs_to_desktop
)

root.bind("<Command-r>", lambda event: list_devices())
root.bind("<Command-s>", lambda event: show_apps())
root.bind("<Command-q>", lambda event: on_close())

root.createcommand("tk::mac::Quit", on_close)
signal.signal(signal.SIGTERM, lambda *_: os._exit(0))

if is_xcode_installed():
    finish_startup_after_xcode()
else:
    show_xcode_overlay()

root.protocol("WM_DELETE_WINDOW", on_close)
root.after(100, check_xcode_version_or_exit)

root.after(200, _apply_macos_titlebar_color)
root.after(200, _remove_app_menu_items)
root.after(1000, check_for_updates)
threading.Thread(target=_backfill_icon_urls, daemon=True).start()

# === MAINLOOP ===
root.mainloop()