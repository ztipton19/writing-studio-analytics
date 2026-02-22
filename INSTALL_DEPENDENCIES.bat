@echo off
REM ============================================================
REM Install Python Dependencies
REM ============================================================
REM This script installs all required Python packages for
REM Writing Studio Analytics using the portable Python.
REM ============================================================

set "SCRIPT_DIR=%~dp0"
set "PYTHON_DIR=%SCRIPT_DIR%python"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"

echo.
echo ========================================================
echo   Installing Dependencies for Writing Studio Analytics
echo ========================================================
echo.

REM Check if portable Python exists
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Portable Python not found!
    echo Expected: %PYTHON_EXE%
    echo.
    echo Please run setup_portable_python.bat first.
    echo.
    pause
    exit /b 1
)

REM Check if requirements file exists
if not exist "%SCRIPT_DIR%SOURCE_CODE\requirements-release.txt" (
    if not exist "%SCRIPT_DIR%requirements-release.txt" (
        echo [ERROR] requirements-release.txt not found!
        echo Please ensure this file is in the same directory.
        pause
        exit /b 1
    )
    set "REQ_FILE=%SCRIPT_DIR%requirements-release.txt"
) else (
    set "REQ_FILE=%SCRIPT_DIR%SOURCE_CODE\requirements-release.txt"
)

echo [INFO] Using Python: %PYTHON_EXE%
echo [INFO] Installing from: %REQ_FILE%
echo.
echo This may take several minutes...
echo.

REM Upgrade pip first
"%PYTHON_EXE%" -m pip install --upgrade pip

REM Install dependencies
"%PYTHON_EXE%" -m pip install -r "%REQ_FILE%"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to install some dependencies.
    echo Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo   Dependencies Installed Successfully!
echo ========================================================
echo.
echo You can now run RUN_WITH_PYTHON.bat to start the application.
echo.
pause