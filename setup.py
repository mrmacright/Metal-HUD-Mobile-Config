from setuptools import setup

APP = ['Metal HUD Mobile Config.py']
DATA_FILES = []

OPTIONS = {
    "iconfile": "MyIcon.icns",
    "packages": ["tkinter"],
    "resources": [
        "MyIcon.icns",
        "setup_xcode.sh",
        "assets"
    ],
    "semi_standalone": False,
    "arch": "arm64",
    "plist": {
        "CFBundleName": "Metal HUD Mobile Config",
        "CFBundleShortVersionString": "3.0.5",
        "CFBundleVersion": "3.0.5",
        "CFBundleIdentifier": "com.stewie.metalhud",
        "LSMinimumSystemVersion": "15.6",
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)