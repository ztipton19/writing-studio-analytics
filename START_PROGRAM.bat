@echo off
REM ============================================================
REM Writing Studio Analytics - USB Launcher
REM ============================================================
REM Double-click this file to start the program (Python mode).
REM ============================================================

title Writing Studio Analytics

REM Get the directory where this batch file is located
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

REM Ensure Python launcher exists
if not exist "%APP_DIR%RUN_WITH_PYTHON.bat" (
    echo.
    echo [ERROR] RUN_WITH_PYTHON.bat not found!
    echo.
    echo Expected location: %APP_DIR%RUN_WITH_PYTHON.bat
    echo.
    echo Please ensure USB package files are intact.
    echo.
    pause
    exit /b 1
)

REM First-run setup if portable Python is missing
if not exist "%APP_DIR%python\python.exe" (
    echo.
    echo ========================================================
    echo   First-time setup required
    echo ========================================================
    echo Portable Python was not found in this folder.
    echo.
    echo This will run:
    echo   1) setup_portable_python.bat
    echo   2) INSTALL_DEPENDENCIES.bat
    echo   3) RUN_WITH_PYTHON.bat
    echo.
    set /p CONTINUE_SETUP="Continue now? (y/n): "
    if /i not "%CONTINUE_SETUP%"=="y" (
        echo Setup cancelled.
        pause
        exit /b 1
    )

    call "%APP_DIR%setup_portable_python.bat"
    if %ERRORLEVEL% neq 0 (
        echo.
        echo [ERROR] Python setup failed.
        pause
        exit /b %ERRORLEVEL%
    )

    call "%APP_DIR%INSTALL_DEPENDENCIES.bat"
    if %ERRORLEVEL% neq 0 (
        echo.
        echo [ERROR] Dependency installation failed.
        pause
        exit /b %ERRORLEVEL%
    )
)

echo.
echo ========================================================
echo   Writing Studio Analytics
echo   Starting application (Python mode)...
echo ========================================================
echo.
echo IMPORTANT: Keep this window open while using the app.
echo            Close it when you're done to exit cleanly.
echo.

call "%APP_DIR%RUN_WITH_PYTHON.bat"
