@echo off
cd /d "%~dp0"
py -3 --version >nul 2>nul
if not errorlevel 1 goto install
python --version >nul 2>nul
if errorlevel 1 goto no_python
python -m pip install -r requirements.txt
goto done
:install
py -3 -m pip install -r requirements.txt
goto done
:no_python
echo Install Python 3.10 or later, then run this file again.
:done
pause
