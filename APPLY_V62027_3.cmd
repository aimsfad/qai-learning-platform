@echo off
setlocal
cd /d "%~dp0"
py -3 apply_v62027_3_prompt_budget.py .
if errorlevel 1 exit /b %errorlevel%
py -3 validate_v62027_3_prompt_budget_fix.py
if errorlevel 1 exit /b %errorlevel%
echo.
echo V6.20.27.3 applied and validated.
echo Next: git status
endlocal
