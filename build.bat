@echo off
chcp 65001 > nul
echo ====================================
echo  Webtoon Downloader 빌드 스크립트
echo ====================================

set PYTHON=python

echo [1/4] 라이브러리 확인 및 설치...
%PYTHON% -m pip install -r requirements.txt --quiet

echo [2/4] 로고/아이콘 최신화 및 버전 정보 리소스 생성...
%PYTHON% clean_logo.py
%PYTHON% generate_version_info.py

echo [3/4] PyInstaller로 빌드 중...
echo (.spec 파일을 사용하여 빌드 설정과 버전 정보를 읽어옵니다.)
%PYTHON% -m PyInstaller "Webtoon Downloader.spec" --noconfirm

echo [4/4] 완료!

rem dist 폴더에서 생성된 실행 파일 찾기
set "EXE_PATH="
for %%F in ("dist\Webtoon Downloader v*.exe") do (
    set "EXE_PATH=%%F"
)

if "%EXE_PATH%" == "" (
    echo.
    echo ❌ 빌드 실패. "dist" 폴더에서 실행 파일을 찾을 수 없습니다.
    echo "build" 폴더 내 로그를 확인하거나 PyInstaller 메시지를 검토해주세요.
) else (
    echo.
    echo ✅ 빌드 성공!
    echo 실행 파일 위치: %EXE_PATH%
)

pause
