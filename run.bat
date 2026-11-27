@echo off
setlocal enabledelayedexpansion
title ChitChat

rem Always run from the folder this script lives in, so "-m core.daemon"
rem resolves no matter where the shortcut was launched from.
cd /d "%~dp0"
set "ROOT=%CD%"
set "VENV=%ROOT%\.venv"

rem ---- Locate a Python interpreter ----
set "PYTHON="
if exist "%VENV%\Scripts\python.exe" set "PYTHON=%VENV%\Scripts\python.exe"
if not defined PYTHON (
    where py >nul 2>&1
    if not errorlevel 1 set "PYTHON=py -3"
)
if not defined PYTHON (
    where python >nul 2>&1
    if not errorlevel 1 set "PYTHON=python"
)
if not defined PYTHON (
    echo.
    echo   Python 3.10+ was not found.
    echo   Install it from https://python.org and run this file again.
    echo.
    pause
    exit /b 1
)

rem ---- First run: create the virtual environment ----
if not exist "%VENV%\Scripts\python.exe" (
    echo   First run - setting up the Python environment...
    %PYTHON% "%ROOT%\install.py" --no-shortcuts
    if errorlevel 1 (
        echo   Setup failed. See the messages above.
        pause
        exit /b 1
    )
    if exist "%VENV%\Scripts\python.exe" set "PYTHON=%VENV%\Scripts\python.exe"
)

rem ---- Inspect arguments (values are for display only; %* is forwarded) ----
set "HTTP_PORT=9875"
set "HAS_NAME=0"
set "SHOW_HELP=0"

:parse
if "%~1"=="" goto parsed
if /i "%~1"=="--http-port" set "HTTP_PORT=%~2"
if /i "%~1"=="--name" set "HAS_NAME=1"
if /i "%~1"=="-n" set "HAS_NAME=1"
if /i "%~1"=="--help" set "SHOW_HELP=1"
if /i "%~1"=="-h" set "SHOW_HELP=1"
shift
goto parse

:parsed
if "%SHOW_HELP%"=="1" (
    %PYTHON% -m core.daemon --help
    goto done
)

echo.
echo   Starting ChitChat - Web UI: http://127.0.0.1:%HTTP_PORT%
echo   Press Ctrl+C to stop.
echo.

start "" /b powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:%HTTP_PORT%'"

rem Forward the user's arguments untouched. When no name was given, append
rem one: argparse keeps the last occurrence, so this cannot clash.
if "%HAS_NAME%"=="0" (
    %PYTHON% -m core.daemon %* --name "%COMPUTERNAME%"
) else (
    %PYTHON% -m core.daemon %*
)

:done
echo.
pause
