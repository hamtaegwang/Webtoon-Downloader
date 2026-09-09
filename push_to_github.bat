@echo off
chcp 65001 > nul
set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"

echo ======================================================
echo   Webtoon Downloader - GitHub 소스 코드 업로드 (Push)
echo ======================================================
echo.
echo 현재 로컬 커밋을 원격 저장소(origin main)로 업로드합니다...
echo (처음 실행 시 브라우저에서 GitHub 로그인 창이 뜰 수 있습니다.)
echo.

git push -u origin main

echo.
if %ERRORLEVEL% equ 0 (
    echo ======================================================
    echo   [성공] GitHub(hamtaegwang/Webtoon-Downloader)에 
    echo          모든 소스 코드가 성공적으로 업로드되었습니다!
    echo ======================================================
) else (
    echo ======================================================
    echo   [안내] GitHub 로그인 인증이 완료되지 않았거나
    echo          원격 저장소 권한을 확인해주세요.
    echo ======================================================
)
echo.
pause
