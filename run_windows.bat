@echo off
setlocal
cd /d "%~dp0"

echo Starting Cardan Joint Engineering Tool v1.2.4...
where py >nul 2>&1
if %errorlevel%==0 (
    py -m streamlit run streamlit_app.py
) else (
    python -m streamlit run streamlit_app.py
)

if errorlevel 1 (
    echo.
    echo The application could not be started.
    echo Run install_windows.bat first and review the error above.
    pause
)
