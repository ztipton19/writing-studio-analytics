@echo off
REM ============================================================
REM Writing Studio Analytics - USB Launcher
REM ============================================================
REM Double-click this file to start the program.
REM ============================================================

title Writing Studio Analytics

REM Get the directory where this batch file is located
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

REM Check if executable exists
if not exist "WritingStudioAnalytics.exe" (
    echo.
    echo [ERROR] WritingStudioAnalytics.exe not found!
    echo.
    echo Expected location: %APP_DIR%WritingStudioAnalytics.exe
    echo.
    echo Please ensure the executable is in the same folder as this batch file.
    echo.
    pause
    exit /b 1
)

REM Create necessary directories for the application
if not exist "%LOCALAPPDATA%\WritingStudioAnalytics" mkdir "%LOCALAPPDATA%\WritingStudioAnalytics"

echo.
echo ========================================================
echo   Writing Studio Analytics
echo   Starting application...
echo ========================================================
echo.
echo NOTE: First launch may take 10-30 seconds to unpack.
echo       Subsequent launches will be faster.
echo.
echo IMPORTANT: Keep this window open while using the app.
echo            Close it when you're done to exit cleanly.
echo.

REM Launch the application
start "" "%APP_DIR%WritingStudioAnalytics.exe"

REM Wait a moment then show success message
timeout /t 3 /nobreak > nul
echo [SUCCESS] Application launched! You can minimize this window.
echo.