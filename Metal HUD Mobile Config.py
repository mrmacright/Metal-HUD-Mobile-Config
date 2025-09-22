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

os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ["LANG"] = "en_US.UTF-8"

DEVICE_INFO_CACHE = {}  

WARNING_SHOWN = False  
OPEN_GAME_WARNING_SHOWN = False

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
    """Attempt to accept the Xcode license using AppleScript (GUI prompt for password)."""
    applescript = '''
    do shell script "xcodebuild -license accept" with administrator privileges
    '''
    try:
        subprocess.run(["osascript", "-e", applescript], check=True)
        return True
    except subprocess.CalledProcessError as e:
        messagebox.showwarning(
            "Xcode License",
            "Failed to automatically accept the Xcode license.\n"
            "Please run 'sudo xcodebuild -license accept' manually."
        )
        return False

def run_setup_xcode():
    """Ensure Xcode is installed and the license is accepted."""
    if not os.path.exists("/Applications/Xcode.app"):
        messagebox.showwarning(
            "Xcode Missing",
            "Xcode is not in the Applications folder.\nPlease download it from the App Store before continuing."
        )
        subprocess.Popen(["open", "macappstore://itunes.apple.com/app/id497799835"])
        root.destroy()
        os._exit(0)

    if not has_agreed_to_license():
        success = accept_xcode_license_gui()
        if not success:
            root.destroy()
            os._exit(0)

# === GUI root ===
root = tk.Tk()
root.withdraw()  

run_setup_xcode()  

root.deiconify()  

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

def on_close():
    print("on_close called")
    save_data()
    root.destroy()

def run_command(command):
    try:
        output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
        print(f"Output:\n{output}")
        if "Developer Mode is disabled" in output:
            root.after(0, lambda: messagebox.showwarning(
                "Developer Mode Disabled",
                "Operation failed because Developer Mode is disabled on your iPhone or iPad.\n\n"
                "Go to Settings > Privacy & Security > Developer Mode on your device to enable it."
            ))
        return output.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error output:\n{e.output}")
        if e.output and "Developer Mode is disabled" in e.output:
            root.after(0, lambda: messagebox.showwarning(
                "Developer Mode Disabled",
                "Operation failed because Developer Mode is disabled on your iPhone or iPad.\n\n"
                "Go to Settings > Privacy & Security > Developer Mode on your device to enable it."
            ))
        return f"Error:\n{e.output.strip() if e.output else str(e)}"

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

def show_apps():
    global OPEN_GAME_WARNING_SHOWN

    udid = device_udid_combo.get().strip()
    if not udid:
        return

    if not OPEN_GAME_WARNING_SHOWN:
        messagebox.showwarning(
            "Open Game Reminder",
            "Make sure your selected game is open and all other apps are closed before clicking Show Running Games"
        )
        OPEN_GAME_WARNING_SHOWN = True

    command = f"xcrun devicectl device info processes --device {udid} | grep 'Bundle/Application'"
    output = run_command(command)
    ...

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
        "FaceTime.app", "Image Playground.app", "MobileStore.app", 
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

    display_names = [
        app_name[:-4] if app_name.endswith(".app") else app_name
        for _, app_name in sorted_apps
    ]

    set_text_widget(apps_text, "\n".join(display_names))

    app_name_to_full_path = {}
    for full_path, app_name in sorted_apps:
        key = app_name[:-4] if app_name.endswith(".app") else app_name
        app_name_to_full_path[key] = full_path

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

def update_command_history(cmd):
    if cmd not in command_history:
        command_history.insert(0, cmd)
        if len(command_history) > 10:
            command_history.pop()
        refresh_command_history_combo()
        display_str, _ = extract_device_and_app_from_command(cmd)
        command_history_combo.set(display_str)
        save_data()

def update_launch_output(output):
    set_text_widget(launch_output_text, output)

    if "OpenGL" in output:
        messagebox.showwarning("OpenGL Detected",
            "Warning: OpenGL detected in the logs. Metal HUD may not work!")

def run_command_in_thread(command):
    output = run_command(command)
    launch_output_text.after(0, lambda: update_launch_output(output))

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

def launch_app():
    udid = device_udid_combo.get().strip()
    app_path = getattr(app_path_combo, "full_path", None)

    alignment = get_alignment_internal()

    if not udid or not app_path:
        messagebox.showwarning("Missing Info", "Please select Device and Game")
        return

    show_temporary_status_message(
        "If the Metal HUD doesn't appear, please close and reopen App on your device"
    )

    preset = hud_preset_var.get()
    env_vars = get_hud_env_vars(preset)
    env_vars["MTL_HUD_ALIGNMENT"] = alignment
    selected_label = hud_scale_var.get()
    env_vars["MTL_HUD_SCALE"] = hud_scale_map.get(selected_label, "0.4")
    env_json = json.dumps(env_vars)

    command = (
        f"xcrun devicectl device process launch "
        f"-e '{env_json}' "
        f"--console --device {udid} \"{app_path}\""
    )

    update_command_history(command)
    threading.Thread(target=run_command_in_thread, args=(command,), daemon=True).start()

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

# === GUI SETUP ===
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

def prompt_install_xcode():
    messagebox.showwarning(
        "Xcode Missing",
        "Xcode is not in the Applications folder.\nPlease download it from the App Store before continuing."
    )

    subprocess.Popen(["open", "macappstore://itunes.apple.com/app/id497799835"])
    
    root.destroy()
    os._exit(0)

if not is_xcode_installed():
    prompt_install_xcode()

ttk.Label(scrollable_frame, text="Devices").pack(anchor="w", padx=padx_side)
ttk.Button(scrollable_frame, text="List Devices (Cmd+L)", command=list_devices).pack(anchor="w", padx=padx_side)

device_text = scrolledtext.ScrolledText(scrollable_frame, height=10, state='disabled')
device_text.tag_configure("selected_device", background="#ffcc66", foreground="black")
device_text.pack(fill=tk.BOTH, padx=padx_side, pady=5, expand=True)
device_text.bind("<Button-1>", on_device_text_click)

device_udid_combo = ttk.Combobox(scrollable_frame, values=[])

ttk.Button(scrollable_frame, text="Unpair", command=unpair_device).pack(anchor="w", padx=padx_side, pady=(0, 10))

ttk.Button(scrollable_frame, text="Show Running Games", command=show_apps).pack(anchor="w", padx=padx_side)
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
    else:
        app_name = "Unknown App"

    return f"{device_display} - {app_name}", cmd

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

            app_path_combo.set(app_name)
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

status_label = ttk.Label(scrollable_frame, text="", foreground="red")
status_label.pack(anchor="w", padx=padx_side, pady=(0, 5))

def update_launch_button_text(app_name):
    """
    Update the Launch button text to include the selected app name,
    or reset to default if None or empty string is given.
    """
    if app_name:
        launch_button.config(text=f"Launch {app_name} with Metal Performance HUD")
    else:
        launch_button.config(text="Launch App with Metal Performance HUD")

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

root.bind("<Command-l>", lambda event: list_devices())

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()