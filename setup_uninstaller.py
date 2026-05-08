from setuptools import setup

APP = ['Metal HUD Mobile Config Uninstaller.py']

OPTIONS = {
    "iconfile": "assets/App Icons/MyIcon Uninstall.icns",
    "packages": ["tkinter"],
    "resources": ["assets/App Icons/MyIcon Uninstall.icns"],
    "semi_standalone": False,
    "arch": "arm64",
    "plist": {
        "CFBundleName": "Uninstaller Metal HUD Mobile Config",
        "CFBundleIdentifier": "com.stewie.metalhud.uninstaller",
        "CFBundleShortVersionString": "2.0.0",
        "CFBundleVersion": "2.0.0",
        "LSMinimumSystemVersion": "15.6",
        "NSHumanReadableCopyright": "Copyright © 2025 Stewie (MrMacRight). All rights reserved.",
    },
}

setup(
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
