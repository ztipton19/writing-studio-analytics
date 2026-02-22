@echo off
REM ============================================================
REM Portable Python Environment Setup
REM ============================================================
REM This script downloads and sets up a portable Python environment
REM for running Writing Studio Analytics from source.
REM ============================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PYTHON_DIR=%SCRIPT_DIR%python"
set "PYTHON_VERSION=3.11.9"
set "PYTHON_EMBED_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip"
set "GETPIP_URL=https://bootstrap.pypa.io/get-pip.py"

echo.
echo ========================================================
echo   Portable Python Setup for Writing Studio Analytics
echo ========================================================
echo.

REM Check if Python directory already exists
if exist "%PYTHON_DIR%" (
    echo [INFO] Python directory already exists at: %PYTHON_DIR%
    echo.
    set /p REINSTALL="Reinstall? (y/n): "
    if /i "!REINSTALL!" neq "y" (
        echo [INFO] Skipping installation.
        goto :end
    )
    echo [INFO] Removing existing Python directory...
    rmdir /s /q "%PYTHON_DIR%"
)

REM Create Python directory
echo [STEP 1/5] Creating Python directory...
mkdir "%PYTHON_DIR%"

REM Download embedded Python
echo [STEP 2/5] Downloading Python %PYTHON_VERSION% embedded distribution...
echo URL: %PYTHON_EMBED_URL%

REM Use PowerShell to download
powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_EMBED_URL%' -OutFile '%PYTHON_DIR%\python-embed.zip' }"

if not exist "%PYTHON_DIR%\python-embed.zip" (
    echo [ERROR] Failed to download Python.
    echo Please download manually from: %PYTHON_EMBED_URL%
    pause
    exit /b 1
)

REM Extract Python
echo [STEP 3/5] Extracting Python...
powershell -Command "& { Expand-Archive -Path '%PYTHON_DIR%\python-embed.zip' -DestinationPath '%PYTHON_DIR%' -Force }"
del "%PYTHON_DIR%\python-embed.zip"

REM Enable site-packages by modifying python311._pth file
echo [STEP 4/5] Configuring Python for pip support...
set "PTH_FILE=%PYTHON_DIR%\python311._pth"
if exist "%PTH_FILE%" (
    echo import site >> "%PTH_FILE%"
    echo [INFO] Enabled site-packages in %PTH_FILE%
)

REM Download and install pip
echo [STEP 5/5] Installing pip...
powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%GETPIP_URL%' -OutFile '%PYTHON_DIR%\get-pip.py' }"

if exist "%PYTHON_DIR%\get-pip.py" (
    "%PYTHON_DIR%\python.exe" "%PYTHON_DIR%\get-pip.py" --no-warn-script-location
    del "%PYTHON_DIR%\get-pip.py"
)

echo.
echo ========================================================
echo   Python Setup Complete!
echo ========================================================
echo.
echo Python installed to: %PYTHON_DIR%
echo.
echo Next steps:
echo 1. Run INSTALL_DEPENDENCIES.bat to install required packages
echo 2. Run RUN_WITH_PYTHON.bat to start the application
echo.

:end
pause