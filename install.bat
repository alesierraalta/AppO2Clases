@echo off
setlocal EnableDelayedExpansion

chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo ===============================
echo INSTALADOR CLASES O2 - COMPLETO
echo ===============================
echo.

echo Verificando Python 3...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python 3 no esta instalado.
    echo Instale Python 3 desde: https://www.python.org/downloads/
    echo IMPORTANTE: Marque "Add Python to PATH" durante la instalacion
    pause
    exit /b 1
)

echo Python encontrado. Verificando version...
python -c "import sys; print('Python', sys.version_info.major, sys.version_info.minor)" 

echo Verificando entorno virtual venv...
if exist venv\ (
    echo Eliminando entorno virtual anterior...
    rmdir /s /q venv 2>nul
)
echo Creando entorno virtual nuevo...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: No se pudo crear el entorno virtual.
    pause
    exit /b 1
)
echo Entorno virtual creado exitosamente.

echo Activando entorno virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: No se pudo activar el entorno virtual.
    pause
    exit /b 1
)

echo Actualizando pip...
python -m pip install --upgrade pip

echo Instalando dependencias desde requirements.txt...
pip install -r requirements.txt

echo Verificando instalacion de flask-wtf...
python -c "import flask_wtf; print('flask-wtf instalado correctamente')" 2>nul
if %errorlevel% neq 0 (
    echo Reinstalando flask-wtf...
    pip install flask-wtf==0.15.1 --force-reinstall
)

echo Creando base de datos...
python -c "import sqlite3; conn = sqlite3.connect('gimnasio.db'); conn.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER)'); conn.close(); print('Base de datos creada')"

echo Creando directorios necesarios...
if not exist static\uploads\audios\permanent mkdir static\uploads\audios\permanent
if not exist logs mkdir logs
if not exist backups mkdir backups

echo.
echo ===============================
echo INSTALACION COMPLETADA
echo ===============================
echo Para iniciar la aplicacion ejecute: start.bat
echo.
pause