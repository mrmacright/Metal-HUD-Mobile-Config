from setuptools import setup

APP = ['Metal HUD Mobile Config.py']
DATA_FILES = []
OPTIONS = {
    "iconfile": "MyIcon.icns",
    "packages": ["tkinter"],
    "resources": ["MyIcon.icns", "setup_xcode.sh"],
    "plist": {
        "CFBundleName": "Metal HUD Mobile Config",
        "CFBundleShortVersionString": "2.0.0",  # Human-readable version
        "CFBundleVersion": "2.0.0",             # Internal build number
        "CFBundleIdentifier": "com.stewie.metalhud",
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
