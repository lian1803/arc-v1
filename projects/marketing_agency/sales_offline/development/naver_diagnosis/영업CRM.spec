# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/lian1/Documents/Work/core/team/[진행중] 오프라인 마케팅/소상공인_영업툴/sales_crm/app.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/lian1/Documents/Work/core/team/[진행중] 오프라인 마케팅/소상공인_영업툴/sales_crm/templates', 'templates'), ('C:/Users/lian1/Documents/Work/core/team/[진행중] 오프라인 마케팅/소상공인_영업툴/sales_crm/static', 'static')],
    hiddenimports=['anthropic', 'google.generativeai', 'flask', 'PIL', 'openpyxl', 'dotenv'],
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
    name='영업CRM',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
