REM ============================================================================
REM  Writing Studio Analytics - Portable Python Build Script
REM  This script creates a self-contained Python environment with all dependencies
REM  that can be run without any Python installation on the target machine.
REM ============================================================================

@echo off
setlocal enabledelayedexpansion

title Writing Studio Analytics - Portable Build

echo.
echo  ============================================
echo   Portable Python Build Script
REM  Writing Studio Analytics
echo  ============================================
echo.
echo  This script will create a portable Python distribution with all dependencies.
echo  Estimated time: 10-15 minutes
echo.

REM --- Configuration ---
set PYTHON_VERSION=3.11.9
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip
set PYTHON_ZIP=python-embed.zip
set PIP_URL=https://bootstrap.pypa.io/get-pip.py
set GET_PIP=get-pip.py

REM --- Step 1: Download Python Embedded ---
echo [1/5] Downloading Python %PYTHON_VERSION% embedded...
echo URL: %PYTHON_URL%
echo.

curl -L -o "%PYTHON_ZIP%" "%PYTHON_URL%"
if %errorlevel% neq 0 (
    echo ERROR: Failed to download Python embedded.
    echo Please check your internet connection.
    pause
    exit /b 1
)

echo Python downloaded successfully!
echo.

REM --- Step 2: Extract Python ---
echo [2/5] Extracting Python to python/ folder...
echo.

if exist "python\" (
    echo WARNING: python/ folder already exists.
    echo.
    set /p DELETE_PYTHON="Delete existing python folder and continue? (Y/N): "
    if /i "!DELETE_PYTHON!"=="Y" (
        rmdir /s /q "python\"
        echo Existing python folder deleted.
    ) else (
        echo Build cancelled.
        del "%PYTHON_ZIP%"
        exit /b 1
    )
)

REM Extract using PowerShell (more reliable than tar on Windows)
powershell -Command "Expand-Archive -Path '%PYTHON_ZIP%' -DestinationPath 'python' -Force"
if %errorlevel% neq 0 (
    echo ERROR: Failed to extract Python.
    pause
    exit /b 1
)

echo Python extracted successfully!
echo.

REM --- Step 3: Enable pip (Manual Step Required) ---
echo [3/5] IMPORTANT MANUAL STEP REQUIRED
echo.
echo You need to enable pip by uncommenting one line in the Python configuration file.
echo.
echo Please open: python\python311._pth
echo.
echo Find this line:
echo     #import site
echo.
echo Change it to (remove the #):
echo     import site
echo.
echo This enables the site-packages module so we can install dependencies.
echo.

REM Open the file in Notepad for editing
notepad "python\python311._pth"

echo.
set /p MANUAL_DONE="Have you uncommented the 'import site' line? (Y/N): "
if /i "!MANUAL_DONE!" neq "Y" (
    echo Build cancelled.
    del "%PYTHON_ZIP%"
    exit /b 1
)

echo Configuration updated!
echo.

REM --- Step 4: Install pip ---
echo [4/5] Installing pip...
echo.

curl -L -o "%GET_PIP%" "%PIP_URL%"
if %errorlevel% neq 0 (
    echo ERROR: Failed to download get-pip.py
    pause
    exit /b 1
)

python\python.exe "%GET_PIP%"
if %errorlevel% neq 0 (
    echo ERROR: Failed to install pip
    pause
    exit /b 1
)

echo pip installed successfully!
echo.

REM --- Step 5: Install Dependencies ---
echo [5/5] Installing dependencies from requirements.txt...
echo This may take 5-10 minutes...
echo.

python\python.exe -m pip install --upgrade pip
python\python.exe -m pip install -r requirements.txt --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
if %errorlevel% neq 0 (
    echo ERROR: Failed to install some dependencies.
    echo.
    echo IMPORTANT: If llama-cpp-python failed, try:
    echo   python\python.exe -m pip install llama-cpp-python==0.3.2 --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
    echo.
    pause
    exit /b 1
)

echo All dependencies installed successfully!
echo.

REM --- Cleanup ---
echo Cleaning up temporary files...
del "%PYTHON_ZIP%"
del "%GET_PIP%"
echo Cleanup complete.
echo.

REM --- Summary ---
echo ============================================
echo   BUILD COMPLETE!
echo ============================================
echo.
echo Your portable Python environment is ready!
echo.
echo Next steps:
echo 1. Test the build by running: launch.bat
echo 2. Verify the app loads without errors
echo 3. Create a zip file of the entire folder
echo 4. Upload to SharePoint
echo.
echo Package contents:
echo - python/ (portable Python with all dependencies)
echo - src/ (your source code)
echo - app.py, launch.bat, and other files
echo.
echo Total size will be ~500-800MB when zipped.
echo.
pause