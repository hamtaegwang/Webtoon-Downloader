# -*- coding: utf-8 -*-
"""
Webtoon Downloader - SAC(스마트 앱 컨트롤) 차단 방지 무설치 포터블 패키지 빌더

특징:
1. Python Software Foundation(PSF) 공식 Authenticode 디지털 서명이 유효한 정품 pythonw.exe 기반
2. Windows 11 Smart App Control(SAC) 및 Defender 차단 원천 방지
3. Python 설치가 전혀 필요 없는 완전 독립형 무설치 포터블 배포판 생성
4. Tkinter 및 필수 서드파티 라이브러리(requests, bs4, Pillow, lxml, selenium 등) 완비
5. 다중 런처 제공 (Webtoon Downloader.exe, .vbs, .bat, 바탕화면 바로가기 생성기)
"""

import os
import sys
import re
import shutil
import zipfile
import subprocess
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, 'dist')
TMP_DIR = os.path.join(BASE_DIR, 'tmp')
OUTPUT_DIR = os.path.join(DIST_DIR, 'Webtoon_Downloader_Portable')

PYTHON_EMBED_URL = 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip'
PYTHON_EMBED_ZIP = os.path.join(TMP_DIR, 'python-3.12.10-embed-amd64.zip')

def get_app_version() -> str:
    main_py = os.path.join(BASE_DIR, 'src', 'main.py')
    try:
        with open(main_py, 'r', encoding='utf-8') as f:
            content = f.read()
            m = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', content)
            if m:
                return m.group(1)
    except Exception as e:
        print(f'[!] 버전 정보 읽기 실패: {e}')
    return '1.0.0'

def find_system_python() -> str:
    """Tkinter 및 표준 라이브러리 DLL을 추출할 시스템 Python 루트 경로 반환"""
    candidates = [
        sys.base_prefix,
        os.path.dirname(sys.executable),
        os.path.expandvars(r'%LOCALAPPDATA%\Programs\Python\Python312'),
        os.path.expandvars(r'%ProgramFiles%\Python312'),
        r'C:\Python312',
    ]
    for c in candidates:
        if os.path.isdir(c) and os.path.exists(os.path.join(c, 'DLLs', '_tkinter.pyd')):
            return c
    raise RuntimeError('Tkinter DLLs를 포함하는 Python 3.12 설치 경로를 찾을 수 없습니다.')

def clean_output_directory():
    print('[1/8] 출력 디렉토리 정리 중...')
    os.makedirs(TMP_DIR, exist_ok=True)
    os.makedirs(DIST_DIR, exist_ok=True)
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def update_assets():
    print('[2/8] 로고 및 아이콘 리소스 확인...')
    clean_logo_py = os.path.join(BASE_DIR, 'clean_logo.py')
    if os.path.exists(clean_logo_py):
        try:
            subprocess.run([sys.executable, clean_logo_py], cwd=BASE_DIR, check=True)
        except Exception as e:
            print(f'[!] clean_logo 실행 경고: {e}')

def download_and_extract_embed_python():
    print('[3/8] 공식 Python 3.12.10 Embeddable 패키지 준비...')
    if not os.path.exists(PYTHON_EMBED_ZIP):
        print(f'  - 다운로드 중: {PYTHON_EMBED_URL}')
        urllib.request.urlretrieve(PYTHON_EMBED_URL, PYTHON_EMBED_ZIP)
        print('  - 다운로드 완료')
    else:
        print(f'  - 기존 캐시 사용: {PYTHON_EMBED_ZIP}')

    print('  - 런타임 파일 압축 해제...')
    with zipfile.ZipFile(PYTHON_EMBED_ZIP, 'r') as z:
        z.extractall(OUTPUT_DIR)

def inject_tkinter_runtime(sys_py: str):
    print('[4/8] 정품 Tkinter 그래픽스 엔진 및 DLL 통합...')
    # 1. DLLs (_tkinter.pyd, tcl86t.dll, tk86t.dll, zlib1.dll)
    dll_names = ['_tkinter.pyd', 'tcl86t.dll', 'tk86t.dll', 'zlib1.dll']
    dll_dir = os.path.join(sys_py, 'DLLs')
    for d in dll_names:
        src_path = os.path.join(dll_dir, d)
        if os.path.exists(src_path):
            shutil.copy2(src_path, os.path.join(OUTPUT_DIR, d))
        else:
            raise FileNotFoundError(f'필수 DLL 미발견: {src_path}')

    # 2. tcl 디렉토리 (tcl8.6, tk8.6 등)
    tcl_src = os.path.join(sys_py, 'tcl')
    tcl_dst = os.path.join(OUTPUT_DIR, 'tcl')
    if os.path.exists(tcl_src):
        if os.path.exists(tcl_dst):
            shutil.rmtree(tcl_dst)
        shutil.copytree(tcl_src, tcl_dst)
    else:
        raise FileNotFoundError(f'tcl 디렉토리 미발견: {tcl_src}')

    # 3. Lib/tkinter 디렉토리
    lib_dir = os.path.join(OUTPUT_DIR, 'Lib')
    os.makedirs(lib_dir, exist_ok=True)
    tk_lib_src = os.path.join(sys_py, 'Lib', 'tkinter')
    tk_lib_dst = os.path.join(lib_dir, 'tkinter')
    if os.path.exists(tk_lib_dst):
        shutil.rmtree(tk_lib_dst)
    shutil.copytree(tk_lib_src, tk_lib_dst)

def install_dependencies():
    print('[5/8] 필수 라이브러리(site-packages) 설치 중...')
    site_packages = os.path.join(OUTPUT_DIR, 'Lib', 'site-packages')
    os.makedirs(site_packages, exist_ok=True)

    pkgs = [
        'requests>=2.31.0',
        'beautifulsoup4>=4.12.0',
        'Pillow>=10.0.0',
        'lxml>=4.9.0',
        'selenium>=4.0.0',
        'webdriver-manager>=4.0.1'
    ]

    cmd = [
        sys.executable, '-m', 'pip', 'install',
        *pkgs,
        '--target', site_packages,
        '--no-user',
        '--quiet'
    ]
    subprocess.run(cmd, check=True)

def copy_application_code():
    print('[6/8] 애플리케이션 소스 및 리소스 복사 중...')
    # 1. src 복사
    src_dst = os.path.join(OUTPUT_DIR, 'src')
    if os.path.exists(src_dst):
        shutil.rmtree(src_dst)
    shutil.copytree(os.path.join(BASE_DIR, 'src'), src_dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))

    # 2. assets 복사
    assets_dst = os.path.join(OUTPUT_DIR, 'assets')
    if os.path.exists(assets_dst):
        shutil.rmtree(assets_dst)
    shutil.copytree(os.path.join(BASE_DIR, 'assets'), assets_dst, ignore=shutil.ignore_patterns('Thumbs.db'))

    # 3. python312._pth 격리 환경 설정
    pth_path = os.path.join(OUTPUT_DIR, 'python312._pth')
    with open(pth_path, 'w', encoding='ascii') as f:
        f.write('python312.zip\n')
        f.write('.\n')
        f.write('Lib\n')
        f.write('Lib/site-packages\n')
        f.write('src\n')
        f.write('import site\n')

    # 4. Lib/sitecustomize.py 자동 실행 브릿지 생성
    sitecustomize_path = os.path.join(OUTPUT_DIR, 'Lib', 'sitecustomize.py')
    with open(sitecustomize_path, 'w', encoding='utf-8') as f:
        f.write('''# -*- coding: utf-8 -*-
import sys
import os

# 인자 없이 더블클릭으로 단독 실행된 경우 src/main.py 자동 기동
if sys.argv == [''] or (len(sys.argv) == 1 and not sys.argv[0].endswith('.py') and not sys.argv[0].endswith('.pyc') and sys.argv[0] not in ('-c', '-m')):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_dir = os.path.join(base_dir, 'src')
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    os.chdir(base_dir)
    import runpy
    main_py = os.path.join(src_dir, 'main.py')
    if os.path.exists(main_py):
        runpy.run_path(main_py, run_name='__main__')
''')

    # 5. pythonw.exe -> Webtoon Downloader.exe 복사 (공식 디지털 서명 보존)
    pythonw_exe = os.path.join(OUTPUT_DIR, 'pythonw.exe')
    app_exe = os.path.join(OUTPUT_DIR, 'Webtoon Downloader.exe')
    shutil.copy2(pythonw_exe, app_exe)

def create_launchers(version: str):
    print('[7/8] 다양한 환경의 런처 및 사용자 편의 도구 생성 중...')

    # 1. Webtoon Downloader.vbs (완전 무창/무음 실행)
    vbs_path = os.path.join(OUTPUT_DIR, 'Webtoon Downloader.vbs')
    with open(vbs_path, 'w', encoding='cp949') as f:
        f.write('''Set oShell = CreateObject("WScript.Shell")
Set oFSO = CreateObject("Scripting.FileSystemObject")
strFolder = oFSO.GetParentFolderName(WScript.ScriptFullName)
oShell.CurrentDirectory = strFolder
oShell.Run """" & strFolder & "\\Webtoon Downloader.exe"" ""src\\main.py""", 0, False
''')

    # 2. Webtoon Downloader.bat (기본 배치 런처)
    bat_path = os.path.join(OUTPUT_DIR, 'Webtoon Downloader.bat')
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write('''@echo off
setlocal
cd /d "%~dp0"
start "" "%~dp0Webtoon Downloader.exe" "src\\main.py" %*
''')

    # 3. 디버그 콘솔 실행.bat (오류 추적용 콘솔 런처)
    debug_bat = os.path.join(OUTPUT_DIR, '디버그 콘솔 실행.bat')
    with open(debug_bat, 'w', encoding='utf-8') as f:
        f.write('''@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================
echo  Webtoon Downloader 디버그 콘솔 모드
echo  (오류 발생 시 로그 및 트레이스백을 확인할 수 있습니다.)
echo ========================================================
echo.
"%~dp0python.exe" "src\\main.py"
echo.
echo [프로그램이 종료되었습니다.]
pause
''')

    # 4. 바탕화면 바로가기 생성.bat (아이콘 적용된 .lnk 자동 생성)
    shortcut_bat = os.path.join(OUTPUT_DIR, '바탕화면 바로가기 생성.bat')
    with open(shortcut_bat, 'w', encoding='utf-8') as f:
        f.write('''@echo off
chcp 65001 > nul
echo 바탕화면에 바로가기를 생성하고 있습니다...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $desktop = [Environment]::GetFolderPath('Desktop'); $s = $ws.CreateShortcut([IO.Path]::Combine($desktop, 'Webtoon Downloader.lnk')); $s.TargetPath = '%~dp0Webtoon Downloader.exe'; $s.WorkingDirectory = '%~dp0'; $s.Arguments = 'src\\main.py'; $s.IconLocation = '%~dp0assets\\icon.ico, 0'; $s.Description = '웹툰 다운로더 무설치 포터블'; $s.Save(); Write-Host '✅ 바탕화면에 바로가기(Webtoon Downloader.lnk) 생성이 완료되었습니다!' -ForegroundColor Green"
echo.
pause
''')

    # 5. README_포터블.txt
    readme_path = os.path.join(OUTPUT_DIR, 'README_포터블.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(f'''Webtoon Downloader v{version} - 무설치 포터블 패키지
================================================================================

[특징]
- 파이썬 설치가 전혀 필요 없는 완전 독립형 무설치 포터블 패키지입니다.
- Windows 11 스마트 앱 컨트롤(SAC) 차단 방지를 위해 Python Software Foundation(PSF)의
  정품 공식 디지털 서명(Authenticode Valid)이 적용된 런처를 기반으로 동작합니다.

[실행 방법 (선택)]
1. 'Webtoon Downloader.exe' 더블 클릭 (추천)
   - 가장 직관적이며 Windows 정품 서명으로 SAC 경고 없이 실행됩니다.
2. 'Webtoon Downloader.vbs' 더블 클릭
   - 콘솔 창 깜빡임이 전혀 없는 완전 무음 런처입니다.
3. '바탕화면 바로가기 생성.bat' 실행
   - 바탕화면에 예쁜 공식 아이콘이 포함된 바로가기를 한 번의 클릭으로 생성합니다.
4. '디버그 콘솔 실행.bat'
   - 실행 중 오류가 발생할 때 로그 및 에러 메시지를 확인하는 용도입니다.

[폴더 설명]
- src/    : 프로그램 메인 소스 코드
- assets/ : 프로그램 아이콘 및 이미지 리소스
- Lib/    : 런타임 및 필수 라이브러리 (requests, beautifulsoup4, selenium, Pillow 등)
- tcl/    : GUI 그래픽 엔진 라이브러리
================================================================================
''')

def verify_and_package(version: str):
    print('[8/8] 서명 검증 및 ZIP 배포 파일 생성 중...')
    
    # 디지털 서명 검증
    check_files = [
        os.path.join(OUTPUT_DIR, 'Webtoon Downloader.exe'),
        os.path.join(OUTPUT_DIR, 'pythonw.exe'),
        os.path.join(OUTPUT_DIR, 'python.exe'),
        os.path.join(OUTPUT_DIR, 'python312.dll'),
        os.path.join(OUTPUT_DIR, '_tkinter.pyd'),
    ]
    
    print('  - Authenticode 디지털 서명 검증 결과:')
    for cf in check_files:
        if os.path.exists(cf):
            ps_cmd = f"powershell -NoProfile -Command \"(Get-AuthenticodeSignature '{cf}').Status\""
            res = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True)
            status = res.stdout.strip()
            print(f'    [{status}] {os.path.basename(cf)}')

    # ZIP 패키징
    zip_filename = f'Webtoon_Downloader_v{version}_Portable.zip'
    zip_path = os.path.join(DIST_DIR, zip_filename)
    if os.path.exists(zip_path):
        os.remove(zip_path)

    print(f'  - ZIP 아카이브 압축 생성 중: {zip_filename}')
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for file in files:
                abs_file = os.path.join(root, file)
                rel_file = os.path.relpath(abs_file, DIST_DIR)
                z.write(abs_file, rel_file)

    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f'  - ZIP 압축 완료! (크기: {zip_size_mb:.1f} MB)')
    print(f'  - 생성 위치: {zip_path}')

def main():
    version = get_app_version()
    print('============================================================')
    print(f' Webtoon Downloader v{version} SAC 차단 방지 포터블 빌드 시작')
    print('============================================================')

    sys_py = find_system_python()
    print(f'[*] 시스템 Python 감지: {sys_py}')

    clean_output_directory()
    update_assets()
    download_and_extract_embed_python()
    inject_tkinter_runtime(sys_py)
    install_dependencies()
    copy_application_code()
    create_launchers(version)
    verify_and_package(version)

    print('\n' + '='*60)
    print(' [OK] 포터블 빌드 완벽 성공!')
    print(f' - 포터블 폴더: {OUTPUT_DIR}')
    print(f' - 배포용 ZIP : {os.path.join(DIST_DIR, f"Webtoon_Downloader_v{version}_Portable.zip")}')
    print('============================================================')

if __name__ == '__main__':
    try:
        if sys.platform == "win32":
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass
    main()

