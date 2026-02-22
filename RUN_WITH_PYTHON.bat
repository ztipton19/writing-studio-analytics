@echo off
REM ============================================================
REM Writing Studio Analytics - Run with Portable Python
REM ============================================================
REM This script runs the application using the portable Python
REM environment instead of the compiled executable.
REM ============================================================

title Writing Studio Analytics (Python)

set "SCRIPT_DIR=%~dp0"
set "PYTHON_DIR=%SCRIPT_DIR%python"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"

REM Find source code directory
if exist "%SCRIPT_DIR%SOURCE_CODE\src\dashboard\main.py" (
    set "APP_ENTRY=%SCRIPT_DIR%SOURCE_CODE\src\dashboard\main.py"
    set "SRC_DIR=%SCRIPT_DIR%SOURCE_CODE"
) else if exist "%SCRIPT_DIR%src\dashboard\main.py" (
    set "APP_ENTRY=%SCRIPT_DIR%src\dashboard\main.py"
    set "SRC_DIR=%SCRIPT_DIR%"
) else (
    echo.
    echo [ERROR] Application source not found!
    echo Expected: src\dashboard\main.py
    echo.
    pause
    exit /b 1
)

REM Check if Python exists
if not exist "%PYTHON_EXE%" (
    echo.
    echo [ERROR] Portable Python not found!
    echo Expected: %PYTHON_EXE%
    echo.
    echo Please run setup_portable_python.bat first.
    echo.
    pause
    exit /b 1
)

REM Create necessary directories
if not exist "%LOCALAPPDATA%\WritingStudioAnalytics" mkdir "%LOCALAPPDATA%\WritingStudioAnalytics"

echo.
echo ========================================================
echo   Writing Studio Analytics (Python Mode)
echo ========================================================
echo.
echo Python: %PYTHON_EXE%
echo Source: %APP_ENTRY%
echo.
echo IMPORTANT: Keep this window open while using the app.
echo            Close it when you're done to exit cleanly.
echo.

REM Run the application
cd /d "%SRC_DIR%"
"%PYTHON_EXE%" "%APP_ENTRY%"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Application exited with error code: %ERRORLEVEL%
    echo.
    echo If dependencies are missing, run INSTALL_DEPENDENCIES.bat
    echo.
    pause
)