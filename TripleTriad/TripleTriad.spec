# -*- mode: python ; coding: utf-8 -*-
# Empaquetado de Triple Triad.
#   python -m PyInstaller TripleTriad.spec
# Los datos (cartas, assets y assets/musica) se incluyen de forma recursiva.

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('cartas', 'cartas'), ('assets', 'assets')],
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
    a.binaries,
    a.datas,
    [],
    name='TripleTriad',
    version='version_info.txt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
