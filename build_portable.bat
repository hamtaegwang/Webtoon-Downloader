@echo off
chcp 65001 > nul
echo ============================================================
echo   Webtoon Downloader - 무설치 포터블 패키지 빌더 (SAC 차단 방지)
echo ============================================================
echo.
echo [안내] Python Software Foundation 공식 디지털 서명(Authenticode Valid)이
echo 유효한 정품 pythonw.exe 런처 기반의 완전 독립형 무설치 패키지를 빌드합니다.
echo.

python build_portable.py
if errorlevel 1 (
    echo.
    echo ❌ 빌드 도중 오류가 발생했습니다. 위 로그를 확인해주세요.
) else (
    echo.
    echo ✅ 빌드가 성공적으로 완료되었습니다!
    echo "dist\Webtoon_Downloader_Portable" 폴더 및 ZIP 배포 파일을 확인하세요.
)

echo.
pause
