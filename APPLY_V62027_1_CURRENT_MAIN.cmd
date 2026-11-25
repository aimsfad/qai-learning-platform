@echo off
setlocal
cd /d "%~dp0"
py -3 apply_v62027_1_current_main.py .
if errorlevel 1 exit /b %errorlevel%
echo.
echo V6.20.27.1 current-main AI pre-test patch completed.
endlocal
