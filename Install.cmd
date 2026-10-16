@echo off
cd /d "%~dp0"
"%~dp0runtime\python\python.exe" "%~dp0launcher.py" --install
if errorlevel 1 pause
