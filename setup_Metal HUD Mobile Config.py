from setuptools import setup

APP = ['Metal HUD Mobile Config.py']
DATA_FILES = []

OPTIONS = {
    "iconfile": "assets/App Icons/MyIcon.icns",
    "packages": ["tkinter"],
    "resources": [
        "assets/App Icons/MyIcon.icns",
        "setup_xcode.sh",
        "assets"
    ],
    "semi_standalone": False,
    "arch": "arm64",
    "plist": {
        "CFBundleName": "Metal HUD Mobile Config",
        "CFBundleShortVersionString": "4.0.4",
        "CFBundleVersion": "4.0.4",
        "CFBundleIdentifier": "com.stewie.metalhud",
        "LSMinimumSystemVersion": "15.6",
        "NSHumanReadableCopyright": "Copyright © 2025 Stewie (MrMacRight). All rights reserved.",
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)