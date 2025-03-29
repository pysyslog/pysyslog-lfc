@echo off
setlocal enabledelayedexpansion

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Please run as administrator
    exit /b 1
)

REM Create configuration directories
mkdir "C:\ProgramData\pysyslog\conf.d" 2>nul

REM Copy configuration files
copy /Y "etc\pysyslog\main.ini" "C:\ProgramData\pysyslog\"
copy /Y "etc\pysyslog\conf.d\*.ini" "C:\ProgramData\pysyslog\conf.d\"

REM Install Python package
pip install .

REM Install Windows service
python -m pysyslog install-service

echo PySyslog LFC installed successfully! 