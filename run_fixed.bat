@echo off
setlocal enabledelayedexpansion

echo Iniciando Sistema de Clases V2O2...

:: Identificar version de Python
python --version > python_version.txt
set /p PYTHON_VERSION=<python_version.txt
del python_version.txt

echo Versión de Python detectada: %PYTHON_VERSION%

:: Verificar si el entorno virtual existe
if not exist venv (
    echo Creando entorno virtual...
    python -m venv venv
    
    if not exist venv (
        echo ERROR: No se pudo crear el entorno virtual.
        echo Verifique que Python está instalado correctamente.
        pause
        exit /b 1
    )
)

:: Activar el entorno virtual
call venv\Scripts\activate
if errorlevel 1 (
    echo ERROR: No se pudo activar el entorno virtual.
    pause
    exit /b 1
)

:: Establecer variables de entorno
set FLASK_APP=app.py
set FLASK_ENV=development
set NOTIFICATION_PHONE_NUMBER=+584244461682
set NOTIFICATION_HOUR_1=13:30
set NOTIFICATION_HOUR_2=00:05

:: Verificar si setuptools está instalado (contiene distutils)
python -c "import setuptools" 2>nul
if errorlevel 1 (
    echo Instalando setuptools (necesario para Python 3.12+)...
    pip install setuptools
    if errorlevel 1 (
        echo ERROR: No se pudo instalar setuptools.
        pause
        exit /b 1
    )
)

:: Instalar dependencias principales una por una para identificar problemas
echo Instalando dependencias principales...
pip install -e . 2>nul
pip install Flask==2.0.1
if errorlevel 1 (
    echo ADVERTENCIA: Error al instalar Flask, intentando continuar...
)

pip install Flask-SQLAlchemy==2.5.1
if errorlevel 1 (
    echo ADVERTENCIA: Error al instalar Flask-SQLAlchemy, intentando continuar...
)

pip install Jinja2==3.0.1 SQLAlchemy==1.4.23 Werkzeug==2.0.1 WTForms==2.3.3 flask-wtf==0.15.1
pip install click==8.0.1 cryptography==3.4.8 Flask-Login==0.5.0
pip install openpyxl==3.0.9 APScheduler==3.9.1 
pip install pywhatkit==5.4 pyautogui==0.9.54

:: Verificar si se pueden importar bibliotecas críticas
echo Verificando instalación de dependencias críticas...
python -c "import flask_sqlalchemy" 2>nul
if errorlevel 1 (
    echo ADVERTENCIA: flask_sqlalchemy no está instalado correctamente.
    echo Intentando instalar con pip...
    pip install Flask-SQLAlchemy==2.5.1 --force-reinstall
)

python -c "import flask_login" 2>nul
if errorlevel 1 (
    echo ADVERTENCIA: flask_login no está instalado correctamente.
    echo Intentando instalar con pip...
    pip install Flask-Login==0.5.0 --force-reinstall
)

:: Inicializar la base de datos
echo Inicializando la base de datos...
python -c "from app import app, db; from flask_sqlalchemy import SQLAlchemy; with app.app_context(): db.create_all()" 2>nul
if errorlevel 1 (
    echo ADVERTENCIA: No se pudo inicializar la base de datos con flask_sqlalchemy.
    echo Creando base de datos con sqlite3 directamente...
    python -c "import sqlite3; conn = sqlite3.connect('gimnasio.db'); conn.close()"
)

echo.
echo == INFORMACIÓN SOBRE NOTIFICACIONES ==
echo Las notificaciones WhatsApp están configuradas para enviarse a las %NOTIFICATION_HOUR_1% y %NOTIFICATION_HOUR_2%
echo.

echo Iniciando la aplicación...
flask run --host=0.0.0.0 --port=5000
if errorlevel 1 (
    echo.
    echo Ha ocurrido un error al iniciar Flask.
    echo Ejecutando verificador de dependencias...
    python check_dependencies.py
    echo.
    echo Sugiero ejecutar el script 'fix_dependencies.bat' para reparar las dependencias.
    pause
)

pause 