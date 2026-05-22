# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules
hidden_dns = collect_submodules('dns')
hidden_eventlet = collect_submodules('eventlet')

a_app = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[('C:\\Users\\betoo\\AppData\\Roaming\\Python\\Python314\\site-packages\\snap7\\lib\\snap7.dll', 'snap7/lib')],
    datas=[('templates', 'templates'), ('static', 'static'), ('cert.pem', '.'), ('key.pem', '.')],
    hiddenimports=['psycopg2', 'cryptography', 'snap7'] + hidden_dns + hidden_eventlet,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

a_gtw = Analysis(
    ['gateway_service.py'],
    pathex=[],
    binaries=[('C:\\Users\\betoo\\AppData\\Roaming\\Python\\Python314\\site-packages\\snap7\\lib\\snap7.dll', 'snap7/lib')],
    datas=[],
    hiddenimports=['psycopg2', 'cryptography', 'snap7'] + hidden_dns + hidden_eventlet,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz_app = PYZ(a_app.pure)
pyz_gtw = PYZ(a_gtw.pure)

exe_app = EXE(
    pyz_app,
    a_app.scripts,
    [],
    exclude_binaries=True,
    name='NexgenCore_v7',
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

exe_gtw = EXE(
    pyz_gtw,
    a_gtw.scripts,
    [],
    exclude_binaries=True,
    name='GatewayService',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe_app,
    a_app.binaries,
    a_app.datas,
    exe_gtw,
    a_gtw.binaries,
    a_gtw.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Nexgen_SCADA_Dist',
)
