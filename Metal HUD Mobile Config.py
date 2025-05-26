import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import subprocess
import re
import os
import threading
import json

def is_xcode_ready():
    try:
        result = subprocess.check_output(["xcrun", "--find", "xcodebuild"], text=True)
        return "/Applications/Xcode.app" in result
    except subprocess.CalledProcessError:
        return False

def has_agreed_to_license():
    try:
        subprocess.check_output(["xcrun", "devicectl", "list", "devices"], stderr=subprocess.STDOUT, text=True)
        return True
    except subprocess.CalledProcessError as e:
        if "You have not agreed to the Xcode and Apple SDKs license" in e.output:
            return False
        return True  # Some other unrelated error

def prompt_user_to_run_script():
    messagebox.showerror(
        "Xcode Not Ready",
        "Before using this app, you need to configure Xcode:\n\n"
        "1. Open Terminal\n"
        "2. Run this command:\n\n"
        "   sudo ./setup_xcode.sh\n\n"
        "Then reopen this app."
    )
    root.destroy()
    os._exit(1)


# Save file in home directory for better permission reliability
DATA_FILE = os.path.expanduser("~/ios_device_controller_data.json")

saved_paths = {}  # dict: name -> {'udid': ..., 'app_path': ...}
command_history = []

def load_data():
    global saved_paths, command_history
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                saved_paths = data.get("saved_paths", {})
                command_history = data.get("command_history", [])
        except Exception as e:
            print("Error loading saved data:", e)
            saved_paths = {}
            command_history = []
    else:
        saved_paths = {}
        command_history = []

def save_data():
    data = {
        "saved_paths": saved_paths,
        "command_history": command_history
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
        if "Developer Mode is disabled" in output:
            messagebox.showwarning("Developer Mode Disabled",
                "Operation failed because Developer Mode is disabled on your iPhone or iPad.\n\n"
                "Go to Settings > Privacy & Security > Developer Mode on your device to enable it.")
        return output.strip()
    except subprocess.CalledProcessError as e:
        if e.output and "Developer Mode is disabled" in e.output:
            messagebox.showwarning("Developer Mode Disabled",
                "Operation failed because Developer Mode is disabled on your iPhone or iPad.\n\n"
                "Go to Settings > Privacy & Security > Developer Mode on your device to enable it.")
        return f"Error:\n{e.output.strip() if e.output else str(e)}"

def is_xcode_installed():
    return os.path.exists("/Applications/Xcode.app")

def open_xcode_download():
    subprocess.Popen(["open", "macappstore://itunes.apple.com/app/id497799835"])

def list_devices():
    raw_output = run_command("xcrun devicectl list devices")

    # Show blue status message temporarily
    show_temporary_status_message("Please connect device to Mac. You can disconnect after successful pairing and do this wirelessly.", duration=6000)

    lines = raw_output.splitlines()
    content_lines = lines[2:]  # skip header
    ...

    device_lines = []
    device_ids = []
    for line in content_lines:
        match = re.match(r"^(.*?)\s{2,}.*?\s{2,}(.*?)\s{2,}(.*?)\s{2,}(.*)$", line)
        if match:
            name = match.group(1).strip()
            identifier = match.group(2).strip()
            state = match.group(3).strip()
            model = match.group(4).strip()
            device_lines.append(f"{name:<20}  {identifier:<40}  {state:<20}  {model}")
            device_ids.append(identifier)

    if device_lines:
        header = f"{'Name':<20}  {'Identifier':<40}  {'State':<20}  Model"
        separator = "-" * 110
        formatted = header + "\n" + separator + "\n\n" + "\n\n".join(device_lines)
    else:
        formatted = "No devices found."

    device_text.delete(1.0, tk.END)
    device_text.insert(tk.END, formatted)

    device_udid_combo['values'] = device_ids
    if device_ids:
        device_udid_combo.current(0)
    else:
        device_udid_combo.set('')

def show_apps():


    udid = device_udid_combo.get().strip()
    if not udid:
        messagebox.showwarning("Missing UDID", "Please select device Identifier.")
        return

    command = f"xcrun devicectl device info processes --device {udid} | grep 'Bundle/Application'"
    output = run_command(command)

    # Filter substrings to hide
    filter_out = [
        "Photos.app",
        "Weather.app",
        "VoiceMemos.app",
        "News.app",
        "Tips.app",
        "Reminders.app",
        "Music.app",
        "Maps.app",
        "Stocks.app",
        "AppStore.app",
        "Measure.app",
        "Magnifier.app",
        "Books.app",
        "Shortcuts.app",
        "Podcasts.app",
        "Calculator.app",
        "Health.app",
        "FindMy.app",
        "Freeform.app",
        "Camera.app",
        "AppleTV.app",
        "YouTube.app",
        "TestFlight.app",
	"MobileCal.app",
	"MobileMail.app",
	"MobileSafari.app",
	"SequoiaTranslator.app",
	"MobileNotes.app",
	"MobileTimer.app",
	"Home.app",
	"Journal.app",
	"Files.app",
	"Fitness.app",
	"Passbook.app", #Wallet App
	"MobileSMS.app", #iMessage app
	"Bridge.app", #Watch app
	"Messenger.app", 
	"ChatGPT.app", 
	"WhatsApp.app", 
	"Drive.app", 
	"Spotify.app", 
	"Discord.app", 
	"Bumble.app", 
	"Meetup.app", 
	"ProtonNative.app", 
	"YouTubeCreator.app", 
	"Tinder.app", 
	"Hinge.app", 
	"TikTok.app", 
	"Google.app", 
	"maps.app",
	"Docs.app",
	"Gmail.app", 
	"Twitch.app", 
	"Instagram.app", 
	"Snapchat.app", 
	"Authenticator.app",

    ]

    processed_lines = []
    unique_paths = set()
    for line in output.splitlines():
        cleaned_line = re.sub(r"^\s*\d+\s+", "", line.strip())
        if '/' in cleaned_line:
            cleaned_line = '/'.join(cleaned_line.split('/')[:-1])
        # Filter out undesired apps
        if any(substring in cleaned_line for substring in filter_out):
            continue
        if cleaned_line not in unique_paths:
            unique_paths.add(cleaned_line)
            processed_lines.append(cleaned_line)

    apps_text.delete(1.0, tk.END)
    apps_text.insert(tk.END, "\n\n".join(processed_lines))

    app_path_combo['values'] = processed_lines
    if processed_lines:
        app_path_combo.set(processed_lines[-1])

def update_command_history(cmd):
    if cmd not in command_history:
        command_history.insert(0, cmd)
        if len(command_history) > 10:
            command_history.pop()
        command_history_combo['values'] = command_history
        command_history_combo.set(cmd)
        save_data()  # <--- Save immediately

def update_launch_output(output):
    launch_output_text.delete(1.0, tk.END)
    launch_output_text.insert(tk.END, output)

    # Check for MoltenVK in logs and warn user
    if "MoltenVK" in output:
        messagebox.showwarning("MoltenVK Detected",
            "Warning: MoltenVK detected in the logs. Metal HUD may not work!")

    # Check for OpenGL in logs and warn user
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
    app_path = app_path_combo.get().strip()
    if not udid or not app_path:
        messagebox.showwarning("Missing Info", "Please select both Device Identifier and App Path before saving.")
        return
    name = simpledialog.askstring("Save Path", "Enter a name for this app/device combo:")
    if not name:
        return
    saved_paths[name] = {'udid': udid, 'app_path': app_path}
    refresh_saved_paths_combo()
    saved_paths_combo.set(name)
    save_data()  # <--- Save immediately

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
        save_data()  # <--- Save immediately

def on_saved_path_select(event):
    name = saved_paths_combo.get()
    if name in saved_paths:
        device_udid_combo.set(saved_paths[name]['udid'])
        app_path_combo.set(saved_paths[name]['app_path'])

def on_command_history_select(event):
    selected_cmd = command_history_combo.get()

    udid_match = re.search(r"--device\s+([^\s]+)", selected_cmd)
    if udid_match:
        device_udid_combo.set(udid_match.group(1))

    app_path_match = re.search(r'"([^"]+)"$', selected_cmd)
    if app_path_match:
        app_path_combo.set(app_path_match.group(1))

    alignment_match = re.search(r'"MTL_HUD_ALIGNMENT"\s*:\s*"(\d+)"', selected_cmd)
    if alignment_match:
        hud_alignment_entry.delete(0, tk.END)
        hud_alignment_entry.insert(0, alignment_match.group(1))
    else:
        hud_alignment_entry.delete(0, tk.END)

def launch_app():
    udid = device_udid_combo.get().strip()
    app_path = app_path_combo.get().strip()
    if not udid or not app_path:
        messagebox.showwarning("Missing Info", "Please select Identifier and App Path.")
        return

    show_temporary_status_message("If the Metal HUD doesn't appear, please close and reopen App on your device.")

    command = (
        f"xcrun devicectl device process launch "
        f"-e '{{\"MTL_HUD_ENABLED\": \"1\"}}' "
        f"--console --device {udid} \"{app_path}\""
    )
    update_command_history(command)
    threading.Thread(target=run_command_in_thread, args=(command,), daemon=True).start()

def launch_app_with_alignment():
    udid = device_udid_combo.get().strip()
    app_path = app_path_combo.get().strip()
    alignment = hud_alignment_entry.get().strip()

    if not udid or not app_path or not alignment:
        messagebox.showwarning("Missing Info", "Please enter Identifier, App Path, and HUD Alignment number.")
        return

    if not alignment.isdigit():
        messagebox.showwarning("Invalid Input", "HUD Alignment must be a number.")
        return

    show_temporary_status_message("Click OK to launch HUD.\nIf it doesn't appear, please close and reopen it on your device.")

    command = (
        f"xcrun devicectl device process launch "
        f"-e '{{\"MTL_HUD_ENABLED\": \"1\", \"MTL_HUD_ALIGNMENT\":\"{alignment}\"}}' "
        f"--console --device {udid} \"{app_path}\""
    )
    update_command_history(command)
    threading.Thread(target=run_command_in_thread, args=(command,), daemon=True).start()


def on_device_text_click(event):
    index = device_text.index(f"@{event.x},{event.y}")
    line_num = index.split('.')[0]
    line_text = device_text.get(f"{line_num}.0", f"{line_num}.end").strip()
    if not line_text or line_text.startswith("Name") or set(line_text) == {'-'}:
        return
    parts = re.split(r"\s{2,}", line_text)
    if len(parts) >= 2:
        device_id = parts[1]
        device_udid_combo.set(device_id)

def on_apps_text_click(event):
    index = apps_text.index(f"@{event.x},{event.y}")
    line_num = index.split('.')[0]
    line_text = apps_text.get(f"{line_num}.0", f"{line_num}.end").strip()
    if line_text:
        app_path_combo.set(line_text)

# === GUI SETUP ===
# === GUI SETUP ===
root = tk.Tk()
root.title("Metal HUD Mobile Config")

root.update_idletasks()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}+0+0")

padx_side = 30

load_data()

# Scrollable Canvas
canvas = tk.Canvas(root)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

def resize_scrollable_frame(event):
    canvas.itemconfig(canvas_window, width=event.width)

canvas.bind("<Configure>", resize_scrollable_frame)

canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# GUI widgets go in scrollable_frame, not root
def prompt_install_xcode():
    result = messagebox.showwarning(
        "Xcode Missing", 
        "Xcode is not installed.\nPlease download it from the App Store before continuing."
    )
    open_xcode_download()
    root.destroy()
    os._exit(0)

if not is_xcode_installed():
    prompt_install_xcode()

ttk.Label(scrollable_frame, text="Devices").pack(anchor="w", padx=padx_side)
ttk.Button(scrollable_frame, text="List Devices", command=list_devices).pack(anchor="w", padx=padx_side)
device_text = scrolledtext.ScrolledText(scrollable_frame, height=10)
device_text.pack(fill=tk.BOTH, padx=padx_side, pady=5, expand=True)
device_text.bind("<Button-1>", on_device_text_click)

ttk.Label(scrollable_frame, text="Device Identifier").pack(anchor="w", padx=padx_side)
device_udid_combo = ttk.Combobox(scrollable_frame, values=[])
device_udid_combo.pack(fill=tk.X, padx=padx_side, pady=5)

tk.Label(scrollable_frame, text="Launch the app you want HUD enabled for, then press Show Running Apps. Have no other Apps open in the background", fg="red").pack(anchor="w", padx=padx_side)
ttk.Button(scrollable_frame, text="Show Running Apps", command=show_apps).pack(anchor="w", padx=padx_side)
apps_text = scrolledtext.ScrolledText(scrollable_frame, height=7)
apps_text.pack(fill=tk.BOTH, padx=padx_side, pady=15, expand=True)
apps_text.bind("<Button-1>", on_apps_text_click)

ttk.Label(scrollable_frame, text="App Path").pack(anchor="w", padx=padx_side)
app_path_combo = ttk.Combobox(scrollable_frame, values=[])
app_path_combo.pack(fill=tk.X, padx=padx_side, pady=5)

ttk.Button(scrollable_frame, text="Save App Path", command=save_app_path).pack(anchor="w", padx=padx_side, pady=(0, 5))

ttk.Label(scrollable_frame, text="Saved Paths").pack(anchor="w", padx=padx_side)
saved_paths_combo = ttk.Combobox(scrollable_frame, values=sorted(saved_paths.keys()))
saved_paths_combo.pack(fill=tk.X, padx=padx_side, pady=5)
saved_paths_combo.bind("<<ComboboxSelected>>", on_saved_path_select)

ttk.Button(scrollable_frame, text="Delete Saved Path", command=delete_saved_path).pack(anchor="w", padx=padx_side, pady=(0, 10))

ttk.Label(scrollable_frame, text="Previous Commands").pack(anchor="w", padx=padx_side)
command_history_combo = ttk.Combobox(scrollable_frame, values=command_history, state="readonly")
command_history_combo.pack(fill=tk.X, padx=padx_side, pady=(0, 10))
command_history_combo.bind("<<ComboboxSelected>>", on_command_history_select)

ttk.Button(scrollable_frame, text="Launch App with Metal Performance HUD", command=launch_app).pack(anchor="w", padx=padx_side, pady=(0, 10))

ttk.Label(scrollable_frame, text="HUD Alignment (enter number)").pack(anchor="w", padx=padx_side)
hud_alignment_entry = ttk.Entry(scrollable_frame)
hud_alignment_entry.pack(fill=tk.X, padx=padx_side, pady=5)

ttk.Button(scrollable_frame, text="Launch App with HUD and Alignment", command=launch_app_with_alignment).pack(anchor="w", padx=padx_side, pady=(0, 10))

# Toggleable log output
def toggle_logs():
    if launch_output_text.winfo_ismapped():
        launch_output_text.pack_forget()
        toggle_log_button.config(text="Show Logs")
    else:
        launch_output_text.pack(fill=tk.BOTH, padx=padx_side, pady=10, expand=True)
        toggle_log_button.config(text="Hide Logs")

toggle_log_button = ttk.Button(scrollable_frame, text="Show Logs", command=toggle_logs)
toggle_log_button.pack(anchor="w", padx=padx_side, pady=(0, 5))

launch_output_text = scrolledtext.ScrolledText(scrollable_frame, height=12)
launch_output_text.pack_forget()

status_label = ttk.Label(scrollable_frame, text="", foreground="blue")
status_label.pack(anchor="w", padx=padx_side, pady=(0, 10))

root.protocol("WM_DELETE_WINDOW", on_close)


# Check if Xcode is configured
if not is_xcode_ready() or not has_agreed_to_license():
    prompt_user_to_run_script()

root.mainloop()


