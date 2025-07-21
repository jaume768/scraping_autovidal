@echo off
echo ====== CONSTRUYENDO EJECUTABLE AUTOVIDAL SCRAPER ======

REM Activar el entorno virtual
echo Activando entorno virtual...
call .\autovidal_env\Scripts\activate.bat

REM Instalar pyinstaller si no está instalado
echo Instalando pyinstaller...
pip install pyinstaller==6.2.0

REM Crear el ejecutable
echo Creando ejecutable...
pyinstaller --onefile --clean --name autovidal_scraper autovidal_scraper.py

REM Mostrar resultado
echo.
echo ====== CONSTRUCCION COMPLETADA ======
echo El ejecutable se encuentra en: dist\autovidal_scraper.exe
echo.
pause
