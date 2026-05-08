import glob
import os
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox, scrolledtext
from datetime import datetime

def _trim_app_menu_to_quit_only(root):
    """Strip the macOS application menu down to a single Quit item via PyObjC."""
    try:
        from AppKit import NSApplication, NSMenuItem
    except ImportError:
        return

    def _apply():
        app = NSApplication.sharedApplication()
        main_menu = app.mainMenu()
        if not main_menu:
            return
        app_menu_item = main_menu.itemAtIndex_(0)
        if not app_menu_item:
            return
        app_submenu = app_menu_item.submenu()
        if not app_submenu:
            return
        app_submenu.removeAllItems()
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "terminate:", "q"
        )
        quit_item.setTarget_(app)
        app_submenu.addItem_(quit_item)

    root.after(150, _apply)

APP_NAME = "Metal HUD Mobile Config.app"
APP_FALLBACK_PATH = "/Applications/Metal HUD Mobile Config/Metal HUD Mobile Config.app"
APP_DATA_PATHS = [
    os.path.expanduser("~/ios_device_controller_data.json"),
    os.path.expanduser("~/Library/Application Support/MrMacRight.Metal-HUD-Mobile-Config"),
    os.path.expanduser("~/Library/Application Support/com.stewie.metalhud"),
]

APP_GLOB_PATHS = [
    os.path.expanduser("~/Desktop/MetalHUD_Logs*.txt"),
]

def find_app_paths():
    """Return all paths to the app found via Spotlight, falling back to the known install location."""
    try:
        result = subprocess.run(
            ["mdfind", f'kMDItemFSName == "{APP_NAME}"'],
            capture_output=True, text=True, timeout=10
        )
        paths = [p for p in result.stdout.strip().splitlines() if p]
    except Exception:
        paths = []

    if not paths and os.path.exists(APP_FALLBACK_PATH):
        paths = [APP_FALLBACK_PATH]

    return paths

XCODE_PATHS = [
    "/Applications/Xcode.app",
    "/Applications/Xcode-beta.app",
    "/Library/Developer/CommandLineTools",
    "/Library/Developer",
]

# Glob patterns — must NOT be single-quoted so the shell expands them
XCODE_GLOB_PATHS = [
    "/System/Library/Receipts/com.apple.pkg.CLTools_*",
    "/System/Library/Receipts/com.apple.pkg.DeveloperToolsCLI.*",
]

XCODE_USER_PATHS = [
    os.path.expanduser("~/Library/Developer"),
    os.path.expanduser("~/Library/Caches/com.apple.dt.Xcode"),
    os.path.expanduser("~/Library/Preferences/com.apple.dt.Xcode.plist"),
]

_logs = []
_log_widget = None
_status_label = None

def set_status(text, good=True):
    if _status_label and _status_label.winfo_exists():
        color = '#34c759' if good else '#ff3b30'
        _status_label.config(text=text, fg=color)

def add_log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    _logs.append(entry)
    if _log_widget and _log_widget.winfo_exists():
        _log_widget.config(state="normal")
        _log_widget.insert("end", entry + "\n")
        _log_widget.see("end")
        _log_widget.config(state="disabled")

def show_logs_window():
    global _log_widget
    win = tk.Toplevel()
    win.title("Logs")
    win.geometry("520x320")
    win.resizable(True, True)
    _log_widget = scrolledtext.ScrolledText(win, state="disabled", font=("Menlo", 11))
    _log_widget.pack(fill="both", expand=True, padx=10, pady=10)
    _log_widget.config(state="normal")
    _log_widget.insert("end", "\n".join(_logs) + "\n" if _logs else "No logs yet.\n")
    _log_widget.see("end")
    _log_widget.config(state="disabled")
    win.protocol("WM_DELETE_WINDOW", lambda: _close_logs_window(win))

def _close_logs_window(win):
    global _log_widget
    _log_widget = None
    win.destroy()

def export_logs():
    from tkinter import filedialog
    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        initialfile="uninstall_logs.txt",
        title="Export Logs"
    )
    if not path:
        return
    try:
        with open(path, "w") as f:
            f.write("\n".join(_logs) + "\n")
        set_status(f"Logs exported to {os.path.basename(path)}", good=True)
    except Exception as e:
        messagebox.showerror("Export Failed", str(e))

def remove_path(path):
    if not os.path.exists(path):
        return
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    else:
        os.remove(path)

def uninstall_keep_data():
    removed_count = 0
    set_status("", good=True)
    add_log("Starting: Uninstall App — Keep Profiles & Settings")

    app_paths = find_app_paths()
    if app_paths:
        for path in app_paths:
            remove_path(path)
            add_log(f"Removed: {path}")
            removed_count += 1
    else:
        add_log(f"Not found: {APP_NAME}")

    if removed_count > 0:
        add_log("App removed. Profiles and settings were kept.")
        set_status("App removed. Your profiles and settings were kept.", good=True)
    else:
        add_log("Nothing found to remove")
        set_status("Nothing to remove — Metal HUD Mobile Config is not installed.", good=True)

def uninstall_app_and_data():
    removed_count = 0
    missing_count = 0
    set_status("", good=True)
    add_log("Starting: Uninstall App — Erase Profiles & Settings")

    app_paths = find_app_paths()
    if app_paths:
        for path in app_paths:
            remove_path(path)
            add_log(f"Removed: {path}")
            removed_count += 1
    else:
        add_log(f"Not found: {APP_NAME}")
        missing_count += 1

    for data_path in APP_DATA_PATHS:
        if os.path.exists(data_path):
            remove_path(data_path)
            add_log(f"Removed: {data_path}")
            removed_count += 1
        else:
            add_log(f"Not found: {data_path}")
            missing_count += 1

    for pattern in APP_GLOB_PATHS:
        matches = glob.glob(pattern)
        if matches:
            for match in matches:
                remove_path(match)
                add_log(f"Removed: {match}")
                removed_count += 1
        else:
            add_log(f"Not found: {pattern}")
            missing_count += 1

    if removed_count > 0:
        add_log("Uninstall complete: app and all data removed")
        msg = f"Removed {removed_count} item{'s' if removed_count != 1 else ''}."
        if missing_count > 0:
            msg += f" {missing_count} item{'s' if missing_count != 1 else ''} already missing — see Logs."
        set_status(msg, good=True)
    else:
        add_log("Nothing found to remove")
        set_status("Nothing to remove — Metal HUD Mobile Config is not installed.", good=True)

def uninstall_with_xcode():
    confirm = messagebox.askyesno(
        "Remove Xcode and Command Line Tools",
        "This will permanently remove:\n\n"
        "• Metal HUD Mobile Config\n"
        "• Xcode\n"
        "• Command Line Tools\n"
        "• Xcode support files and caches\n\n"
        "Only continue if you no longer need Xcode installed on this Mac.\n\n"
        "Are you sure you want to continue?"
    )

    if not confirm:
        add_log("Uninstall everything: cancelled by user")
        return

    set_status("", good=True)
    add_log("Starting: Uninstall Everything")

    for path in find_app_paths():
        remove_path(path)
        add_log(f"Removed: {path}")

    for data_path in APP_DATA_PATHS:
        if os.path.exists(data_path):
            remove_path(data_path)
            add_log(f"Removed: {data_path}")

    for pattern in APP_GLOB_PATHS:
        for match in glob.glob(pattern):
            remove_path(match)
            add_log(f"Removed: {match}")

    cmds = " && ".join(
        [f"rm -rf '{p}'" for p in XCODE_PATHS] +
        [f"rm -rf {p}" for p in XCODE_GLOB_PATHS] +
        ["xcode-select --reset"]
    )
    add_log("Running privileged removal of Xcode paths")
    result = subprocess.run([
        "osascript", "-e",
        f'do shell script "{cmds}" with administrator privileges'
    ], check=False, capture_output=True, text=True)

    privileged_ok = result.returncode == 0
    if privileged_ok:
        for path in XCODE_PATHS:
            add_log(f"Removed: {path}")
        for path in XCODE_GLOB_PATHS:
            add_log(f"Removed: {path}")
        add_log("xcode-select reset")
    else:
        err = result.stderr.strip() or result.stdout.strip() or "unknown error"
        add_log(f"Privileged removal failed (code {result.returncode}): {err}")
        add_log("Xcode and Command Line Tools may NOT have been removed")

    for path in XCODE_USER_PATHS:
        if os.path.exists(path):
            remove_path(path)
            add_log(f"Removed user path: {path}")
        else:
            add_log(f"Not found (skipped): {path}")

    user_removed = sum(1 for p in XCODE_USER_PATHS if not os.path.exists(p))
    user_missing = len(XCODE_USER_PATHS) - user_removed

    if privileged_ok:
        add_log("Cleanup complete: all Apple developer tools removed")
        msg = f"All done. Removed Xcode, CLT, and {user_removed} support folder{'s' if user_removed != 1 else ''}."
        if user_missing > 0:
            msg += f" {user_missing} support item{'s' if user_missing != 1 else ''} already missing — see Logs."
        set_status(msg, good=True)
    else:
        add_log("Partial cleanup: app data removed, but Xcode/CLT removal failed — check logs")
        set_status("Partial removal — Xcode/CLT may not be deleted. Check Logs.", good=False)

class RoundedButton(tk.Canvas):
    _W, _H, _R = 420, 50, 12
    _BG, _BG_HOVER, _FG = '#ffffff', '#e5e6ea', '#1c1c1e'
    _FONT = ('Helvetica', 14)

    def __init__(self, parent, text, command):
        super().__init__(parent, width=self._W, height=self._H,
                         bg=parent.cget('bg'), highlightthickness=0)
        self._text = text
        self._command = command
        self._draw(self._BG)
        self.bind('<Button-1>', lambda _: command())
        self.bind('<Enter>', lambda _: self._draw(self._BG_HOVER))
        self.bind('<Leave>', lambda _: self._draw(self._BG))

    def _draw(self, bg):
        self.delete('all')
        w, h, r = self._W, self._H, self._R
        self.create_polygon(
            r, 0,  w-r, 0,  w, 0,  w, r,
            w, h-r,  w, h,  w-r, h,  r, h,
            0, h,  0, h-r,  0, r,  0, 0,
            smooth=True, fill=bg, outline=''
        )
        self.create_text(w // 2, h // 2, text=f'≡  {self._text}',
                         font=self._FONT, fill=self._FG, anchor='center')

def main():
    global _status_label

    root = tk.Tk()
    root.title("Metal HUD Mobile Config Uninstaller")
    root.geometry("500x250")
    root.resizable(False, False)
    root.configure(bg='#f2f3f7')

    # Remove the title bar separator line on macOS
    try:
        root.tk.call(
            "::tk::unsupported::MacWindowStyle",
            "style", root._w, "document", "unifiedTitleAndToolbar"
        )
    except Exception:
        pass

    # Custom menu bar: removes File/Edit/Window/Help, keeps only app menu (Quit) + Logs
    menubar = tk.Menu(root)

    app_menu = tk.Menu(menubar, name="apple", tearoff=0)
    menubar.add_cascade(menu=app_menu)
    app_menu.add_command(label="Quit", command=root.destroy, accelerator="Cmd+Q")
    root.bind_all("<Command-q>", lambda _: root.destroy())

    logs_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Logs", menu=logs_menu)
    logs_menu.add_command(label="View Logs", command=show_logs_window)
    logs_menu.add_command(label="Export Logs…", command=export_logs)

    root.config(menu=menubar)
    _trim_app_menu_to_quit_only(root)

    RoundedButton(root, "Uninstall App — Keep Profiles & Settings", uninstall_keep_data).pack(pady=(20, 8))
    RoundedButton(root, "Uninstall App — Erase Profiles & Settings", uninstall_app_and_data).pack(pady=(0, 8))
    RoundedButton(root, "Uninstall Everything (Xcode + CLT)", uninstall_with_xcode).pack(pady=(0, 8))

    _status_label = tk.Label(
        root, text="", bg='#f2f3f7',
        font=('Helvetica', 11), wraplength=460, justify='center'
    )
    _status_label.pack(pady=(0, 10))

    root.mainloop()

if __name__ == "__main__":
    main()
