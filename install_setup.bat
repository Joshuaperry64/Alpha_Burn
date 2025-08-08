@echo off
title Alpha_Burn Installer

REM This script installs the required Python packages for Alpha_Burn.

REM Check if requirements.txt exists
if not exist requirements.txt (
    echo requirements.txt not found!
    pause
    exit /b 1
)

REM Install packages
echo Installing required packages...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo There was an error installing the packages.
    echo Please check your Python and pip installation.
    pause
    exit /b 1
)

echo.
echo Installation successful. You can now run the application using START.bat.
pause
