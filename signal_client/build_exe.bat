@echo off
setlocal
cd /d "%~dp0"

python -m pip show pyinstaller >nul 2>nul
if errorlevel 1 (
  echo Instalando PyInstaller...
  python -m pip install pyinstaller
  if errorlevel 1 exit /b 1
)

python -m PyInstaller ^
  --onefile ^
  --clean ^
  --name PocketSignalClient ^
  pocket_signal_client.py
if errorlevel 1 exit /b 1

echo.
echo EXE gerado em: %CD%\dist\PocketSignalClient.exe
endlocal
