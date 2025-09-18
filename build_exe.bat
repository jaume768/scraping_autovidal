@echo off
setlocal

echo ====== CONSTRUYENDO EJECUTABLE AUTOVIDAL SCRAPER ======

REM Rutas del venv relativas a este .bat
set VENV_PY=%~dp0venv\Scripts\python.exe
set VENV_PIP=%~dp0venv\Scripts\pip.exe

echo Usando Python: %VENV_PY%
"%VENV_PY%" -c "import sys; print('Exe:', sys.executable)"

REM Actualizar pip correctamente en Windows
"%VENV_PY%" -m pip install --upgrade pip

REM Instalar dependencias EN EL VENV (incluye PyInstaller en el venv)
"%VENV_PY%" -m pip install pyinstaller requests beautifulsoup4 lxml

REM Limpiar artefactos previos
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q autovidal_scraper.spec 2>nul

REM Construir con el PyInstaller del venv
"%VENV_PY%" -m PyInstaller ^
  --onefile ^
  --name autovidal_scraper ^
  --clean ^
  --collect-binaries lxml ^
  --hidden-import bs4 ^
  autovidal_scraper.py

echo.
echo ====== CONSTRUCCION COMPLETADA ======
echo El ejecutable se encuentra en: dist\autovidal_scraper.exe
echo.
pause
endlocal
