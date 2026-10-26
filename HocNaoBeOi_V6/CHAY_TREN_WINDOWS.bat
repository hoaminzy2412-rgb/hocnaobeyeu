@echo off
cd /d "%~dp0"
set SCHOOL_OPEN_BROWSER=1
py -3 -c "import sys; assert sys.version_info >= (3,11)" >nul 2>nul
if %errorlevel% equ 0 (
    py -3 server.py
    goto end
)
python -c "import sys; assert sys.version_info >= (3,11)" >nul 2>nul
if %errorlevel% equ 0 (
    python server.py
    goto end
)
set "SCHOOL_PYTHON="
for /d %%D in ("%LocalAppData%\Programs\Python\Python*") do if exist "%%D\python.exe" set "SCHOOL_PYTHON=%%D\python.exe"
if defined SCHOOL_PYTHON (
    "%SCHOOL_PYTHON%" server.py
    goto end
)
echo.
echo Chua tim thay Python 3.11 tro len.
echo Mo server.py trong VS Code, nhan Ctrl+Shift+P,
echo chon: Python: Run Python File in Terminal.
echo Neu chua cai Python, cai tu python.org va chon Add python.exe to PATH.
:end
pause
