@echo off
setlocal
cd /d "%~dp0"
py -3 apply_v62027_ai_pretest.py .
if errorlevel 1 exit /b %errorlevel%
echo.
echo V6.20.27 installer finished successfully.
echo Review with: git status
endlocal
