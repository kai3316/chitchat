@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "PYTHON="

:: Find Python 3
where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON=python3"
) else (
    where python >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set "PYTHON=python"
    ) else (
        echo Python 3.10+ is required but was not found.
        exit /b 1
    )
)

:: Verify it is Python 3
%PYTHON% --version 2>&1 | findstr "Python 3" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Python 3.10+ is required.
    exit /b 1
)

:: --setup flag: first-time setup
if "%1"=="--setup" (
    echo Creating virtual environment at "%VENV_DIR%"...
    %PYTHON% -m venv "%VENV_DIR%"
    echo Installing dependencies...
    call "%VENV_DIR%\Scripts\activate.bat"
    pip install -r "%SCRIPT_DIR%requirements.txt"
    echo.
    echo Setup complete. Run run.bat without --setup to start ChitChat.
    exit /b 0
)

:: Ensure venv exists
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Virtual environment not found. Creating...
    %PYTHON% -m venv "%VENV_DIR%"
    echo Installing dependencies...
    call "%VENV_DIR%\Scripts\activate.bat"
    pip install -r "%SCRIPT_DIR%requirements.txt"
)

:: Run the daemon, passing through all arguments
"%VENV_DIR%\Scripts\python.exe" -m core.daemon %*
