# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['http_server.py'],
    pathex=[],
    binaries=[],
    datas=[('../../config/config.json', 'config/'), ('../../config/setting.py', 'config/'), ('../../config/log_settings.py', 'config/'), ('../../config/nginx/data_extration.conf', 'config/'), ('../../data/download/templates', 'templates'), ('../../data/logs/dataextraction.log', 'logs'), ('../../data/uploads/templates', 'uploads/templates'), ('../../services/ocr.py', 'services/'), ('../../services/llm.py', 'services/'), ('../../utils', 'utils')],
    hiddenimports=['requests', 'openai', 'docx', 'cv2', 'fitz', 'logging.config', 'pdf2image', 'PyPDF2', 'sqlalchemy', 'sqlalchemy.ext.declarative', 'sqlalchemy.orm.sessionmaker'],
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
    name='http_server',
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
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='http_server',
)
