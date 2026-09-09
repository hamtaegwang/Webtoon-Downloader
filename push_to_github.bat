@echo off
set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"

echo ======================================================
echo   Webtoon Downloader - GitHub Push
echo ======================================================
echo.
echo [1/2] Connecting to GitHub...
echo Target: https://github.com/hamtaegwang/Webtoon-Downloader.git
echo.
echo Uploading to branch 'main'...
echo (A browser window will open if GitHub login is required)
echo.

git push -u origin main

if errorlevel 1 goto FAILED

:SUCCESS
echo.
echo ======================================================
echo   [SUCCESS] All files uploaded to GitHub successfully!
echo ======================================================
goto END

:FAILED
echo.
echo ======================================================
echo   [FAILED] Push failed.
echo   Please check your GitHub permissions or login.
echo ======================================================
goto END

:END
echo.
pause
