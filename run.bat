@echo off
setlocal enabledelayedexpansion
title ChitChat Daemon

set "ROOT=%~dp0"
set "VENV=%ROOT%.venv"

:: Find python in venv or system
if exist "%VENV%\Scripts\python.exe" (
    set "PYTHON=%VENV%\Scripts\python.exe"
) else (
    where python3 >nul 2>&1 && (set "PYTHON=python3") || (
        where python >nul 2>&1 && (set "PYTHON=python") || (
            echo Python 3.10+ not found. Install from https://python.org
            echo Then run: python "%ROOT%setup.py"
            pause
            exit /b 1
        )
    )
)

:: First-time setup hint
if not exist "%VENV%\Scripts\python.exe" (
    echo First time? Running setup...
    "%PYTHON%" "%ROOT%setup.py"
    if exist "%VENV%\Scripts\python.exe" (set "PYTHON=%VENV%\Scripts\python.exe")
)

:: Detect local IP for display
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4" 2^>nul') do (
    set "LAN_IP=%%a"
    set "LAN_IP=!LAN_IP: =!"
)

:: Run daemon with friendly name if not provided
set "HAS_NAME=0"
:parse_args
if "%~1"=="" goto :run
if /i "%~1"=="--name" set "HAS_NAME=1"
if /i "%~1"=="-n" set "HAS_NAME=1"
shift
goto :parse_args

:run
if "%HAS_NAME%"=="0" (
    echo Starting ChitChat daemon on port 9875...
    "%PYTHON%" -m core.daemon --name "%COMPUTERNAME%"
) else (
    "%PYTHON%" -m core.daemon %*
)

pause
