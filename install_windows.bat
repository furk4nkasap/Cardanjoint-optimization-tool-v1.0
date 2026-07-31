@echo off
setlocal
cd /d "%~dp0"

echo =============================================================
echo  Cardan Joint Engineering Tool v1.2.4 - Dependency Installation
echo =============================================================

where py >nul 2>&1
if %errorlevel%==0 (
    py -m pip install --upgrade pip
    py -m pip install -r requirements.txt
) else (
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
)

if errorlevel 1 (
    echo.
    echo Installation failed. Review the error messages above.
    pause
    exit /b 1
)

echo.
echo Installation completed successfully.
pause
