import os
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox

APP_PATH = "/Applications/Metal HUD Mobile Config.app"
APP_DATA = os.path.expanduser("~/ios_device_controller_data.json")

XCODE_PATHS = [
    "/Applications/Xcode.app",
    "/Applications/Xcode-beta.app",
    "/Library/Developer/CommandLineTools",
]

XCODE_USER_PATHS = [
    os.path.expanduser("~/Library/Developer"),
    os.path.expanduser("~/Library/Caches/com.apple.dt.Xcode"),
    os.path.expanduser("~/Library/Preferences/com.apple.dt.Xcode.plist"),
]

def remove_path(path):
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)

def uninstall_app_only(root):
    removed = False

    if os.path.exists(APP_PATH):
        remove_path(APP_PATH)
        removed = True

    if os.path.exists(APP_DATA):
        os.remove(APP_DATA)
        removed = True

    if removed:
        messagebox.showinfo(
            "Uninstall Complete",
            "Metal HUD Mobile Config has been removed.\n\nXcode was not touched."
        )
        root.destroy()
    else:
        messagebox.showinfo(
            "Nothing Found",
            "Metal HUD Mobile Config is not installed."
        )

def uninstall_with_xcode(root):
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
        return

    # App
    remove_path(APP_PATH)
    if os.path.exists(APP_DATA):
        os.remove(APP_DATA)

    # Xcode system paths
    def sudo_rm(path):
        subprocess.run([
            "osascript",
            "-e",
            f'do shell script "rm -rf \\"{path}\\"" with administrator privileges'
        ], check=False)

    # Remove Xcode system paths (requires admin)
    for path in XCODE_PATHS:
        sudo_rm(path)

    # User Xcode data
    for path in XCODE_USER_PATHS:
        remove_path(path)

    # Reset xcode-select (requires admin)
    subprocess.run([
        "osascript",
        "-e",
        'do shell script "xcode-select --reset" with administrator privileges'
    ], check=False)

    messagebox.showinfo(
        "Cleanup Complete",
        "Metal HUD Mobile Config and all Apple developer tools have been removed."
    )
    root.destroy()

def main():
    root = tk.Tk()
    root.title("Metal HUD Mobile Config Uninstaller")
    root.geometry("460x240")
    root.resizable(False, False)

    label = tk.Label(
    	root,
    	text="Choose how you want to uninstall:\n\n",
    	justify="center",
    	wraplength=420
    )
    label.pack(pady=20)

    tk.Button(
        root,
        text="Uninstall Metal HUD Only",
        width=30,
        command=lambda: uninstall_app_only(root)
    ).pack(pady=5)

    tk.Button(
        root,
        text="Remove Xcode and Command Line Tools",
        width=30,
        command=lambda: uninstall_with_xcode(root)
    ).pack(pady=5)

    tk.Button(
        root,
        text="Quit",
        width=30,
        command=root.destroy
    ).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
