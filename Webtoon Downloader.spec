# -*- mode: python ; coding: utf-8 -*-
import os
import re

# src/main.py에서 APP_VERSION 추출 및 Windows 버전 정보 파일 생성
version = "unknown"
try:
    import generate_version_info
    generate_version_info.generate()
    version = generate_version_info.get_app_version()
except Exception as e:
    pass

app_name = f"Webtoon Downloader v{version}"

a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=[
        'PIL._tkinter_finder', 
        'lxml.etree', 
        'lxml._elementpath',
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome.webdriver',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.options',
        'webdriver_manager',
        'webdriver_manager.chrome'
    ],
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
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icon.ico'],
    version='file_version_info.txt',
)
