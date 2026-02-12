from setuptools import setup

APP = ['Metal HUD Mobile Config Uninstaller.py']

OPTIONS = {
    "iconfile": "MyIcon Uninstall.icns",
    "packages": ["tkinter"],
    "resources": ["MyIcon Uninstall.icns"],
    "semi_standalone": False,
    "plist": {
        "CFBundleName": "Uninstaller Metal HUD Mobile Config",
        "CFBundleIdentifier": "com.stewie.metalhud.uninstaller",
        "CFBundleShortVersionString": "2.8.0",
        "CFBundleVersion": "2.8.0",
        "LSMinimumSystemVersion": "15.6",
    },
}

setup(
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
