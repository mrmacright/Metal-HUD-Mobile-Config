from setuptools import setup

APP = ['Metal HUD Mobile Config.py']
DATA_FILES = []
OPTIONS = {
    "iconfile": "MyIcon.icns",
    "packages": ["tkinter"],
    "resources": ["MyIcon.icns", "setup_xcode.sh"],
    "semi_standalone": False, 
    "plist": {
        "CFBundleName": "Metal HUD Mobile Config",
        "CFBundleShortVersionString": "2.0.2",
        "CFBundleVersion": "2.0.2",
        "CFBundleIdentifier": "com.stewie.metalhud",
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
