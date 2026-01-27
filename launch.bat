@echo off
REM ============================================================================
REM  Writing Studio Analytics - Launcher
REM  Double-click this file to start the application.
REM ============================================================================

title Writing Studio Analytics

echo.
echo  ============================================
echo   Writing Studio Analytics
echo   University of Arkansas Writing Studio
echo  ============================================
echo.

REM --- Locate this script's directory (works from USB or local) ---
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

REM --- Check for portable Python (shipped alongside this script) ---
if exist "%APP_DIR%python\python.exe" (
    set "PYTHON=%APP_DIR%python\python.exe"
    echo  Using portable Python: %APP_DIR%python\python.exe
) else if exist "%APP_DIR%python\Scripts\python.exe" (
    set "PYTHON=%APP_DIR%python\Scripts\python.exe"
    echo  Using portable Python: %APP_DIR%python\Scripts\python.exe
) else (
    REM Fall back to system Python
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        echo  ERROR: Python not found.
        echo  Please install Python 3.10+ or place a portable Python folder
        echo  next to this script.
        echo.
        pause
        exit /b 1
    )
    set "PYTHON=python"
    echo  Using system Python
)

echo.

REM --- Launch Streamlit ---
echo  Starting application... A browser window should open shortly.
echo  (Keep this window open while using the app.)
echo.
echo  To stop the app, close this window or press Ctrl+C.
echo.

"%PYTHON%" -m streamlit run app.py --server.headless true

REM --- If we get here, Streamlit exited ---
echo.
echo  Application stopped.
pause
