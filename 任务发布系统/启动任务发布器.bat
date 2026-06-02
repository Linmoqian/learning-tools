@echo off
chcp 65001 >nul
echo ======================================
echo Task Randomizer - Starting...
echo ======================================
echo.
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo [Error] Failed to start! Please check if Python is installed correctly.
    echo.
    pause
)
