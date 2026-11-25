@echo off
setlocal
cd /d "%~dp0"
py -3 apply_v62027_2_recovery.py .
if errorlevel 1 exit /b %errorlevel%
py -3 validate_v62027_ai_course_pretest.py
if errorlevel 1 exit /b %errorlevel%
py -3 validate_v62027_2_pretest_recovery.py
if errorlevel 1 exit /b %errorlevel%
echo.
echo V6.20.27.2 applied and validated.
echo Run git status, review the changes, then commit/push.
endlocal
