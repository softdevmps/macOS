# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).resolve().parents[1]
SENDER_SCRIPT = PROJECT_ROOT / "sender" / "sender.py"
APP_ICON = PROJECT_ROOT / "assets" / "icons" / "macOS.icns"

a = Analysis(
    [str(SENDER_SCRIPT)],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='macOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='macOS',
)
app = BUNDLE(
    coll,
    name='macOS.app',
    icon=str(APP_ICON),
    bundle_identifier=None,
    info_plist={
        "LSUIElement": True,
        "CFBundleName": "macOS",
        "CFBundleDisplayName": "macOS",
    },
)
