@echo off
setlocal
cd /d "%~dp0"
py -3 apply_v62027_4_structured_output.py .
if errorlevel 1 exit /b %errorlevel%
py -3 validate_v62027_4_structured_pretest_output.py
if errorlevel 1 exit /b %errorlevel%
py -3 validate_v62027_3_prompt_budget_fix.py
if errorlevel 1 exit /b %errorlevel%
echo.
echo V6.20.27.4 applied and validated.
echo Next: git status
endlocal
