@echo off
echo Building PC Slowdown Diagnoser Collector...
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install Python 3.11+ and try again.
    pause
    exit /b 1
)

where pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Packaging into single .exe...
pyinstaller --onefile --name pc-diagnoser-collector --console collect.py

echo.
if exist dist\pc-diagnoser-collector.exe (
    echo SUCCESS: dist\pc-diagnoser-collector.exe created.
) else (
    echo ERROR: Build failed. Check PyInstaller output above.
)
pause
