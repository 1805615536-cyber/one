@echo off
cd /d "%~dp0"
py -3 --version >nul 2>nul
if not errorlevel 1 goto use_launcher
python --version >nul 2>nul
if errorlevel 1 goto no_python
set "PY=python"
goto check_deps
:use_launcher
set "PY=py -3"
:check_deps
%PY% -c "import faster_whisper" >nul 2>nul
if errorlevel 1 (
  echo Speech recognition dependency is missing. Run setup_asr.bat first.
  pause
  exit /b 1
)
echo Starting local speech-recognition bridge on 127.0.0.1:8765...
%PY% batch_edit_service.py
pause
exit /b
:no_python
echo Python 3.10 or later was not found. Install Python, then run setup_asr.bat.
pause
exit /b 1
