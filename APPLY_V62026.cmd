@echo off
setlocal
cd /d "%~dp0"
py -3 apply_v62026.py .
if errorlevel 1 exit /b %errorlevel%
py -3 -m py_compile published_course_runtime.py
if errorlevel 1 exit /b %errorlevel%
py -3 validate_v62026_pretest_content_grid.py
if errorlevel 1 exit /b %errorlevel%
echo.
echo V6.20.26 applied and validated.
endlocal
