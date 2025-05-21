@echo off
setlocal EnableDelayedExpansion

echo ===============================
echo INSTALADOR CLASES O2 - COMPLETO
echo ===============================
echo.

echo Verificando Python 3...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python 3 no esta instalado o no se encuentra en el PATH.
    echo Instale Python 3 y asegurese de agregarlo al PATH del sistema.
    echo Descargue Python desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python encontrado. Verificando version...
python -c "import sys; print(sys.version_info.major, sys.version_info.minor)" > python_version.txt
set /p PY_VERSION=<python_version.txt
del python_version.txt

echo Version de Python: %PY_VERSION%

echo Verificando entorno virtual (venv)...
if not exist venv\ (
    echo Creando entorno virtual en el directorio 'venv'...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Fallo al crear el entorno virtual.
        echo Intente instalar manualmente: pip install virtualenv
        pause
        exit /b 1
    )
    echo Entorno virtual creado correctamente.
) else (
    echo Entorno virtual ya existe.
)

echo Activando entorno virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Fallo al activar el entorno virtual. Verifique que exista 'venv\Scripts\activate.bat'.
    pause
    exit /b 1
)

echo Actualizando herramientas de construccion...
python -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
    echo ADVERTENCIA: Fallo al actualizar herramientas de construccion. La instalacion podria fallar.
)

echo Instalando dependencias desde requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ADVERTENCIA: Fallo al instalar algunas dependencias. Intentando instalar manualmente...
    echo Instalando dependencias criticas una por una...
    
    pip install Flask==2.0.1
    pip install Flask-SQLAlchemy==2.5.1
    pip install Jinja2==3.0.1
    pip install SQLAlchemy==1.4.23
    pip install Werkzeug==2.0.1
    pip install WTForms==2.3.3
    pip install flask-wtf==0.15.1
    pip install click==8.0.1
    pip install cryptography==3.4.8
    pip install Flask-Login==0.5.0
    pip install openpyxl==3.0.9
    pip install APScheduler==3.9.1
    pip install pywhatkit==5.4
    pip install pyautogui==0.9.54
    
    echo Instalando dependencias para procesamiento de datos y audio...
    pip install numpy
    pip install pandas
    pip install matplotlib==3.10.1
    pip install librosa==0.11.0 || echo ADVERTENCIA: No se pudo instalar librosa, las funciones de audio podrian no funcionar correctamente.
)

echo Verificando dependencias...
python check_dependencies.py
if %errorlevel% neq 0 (
    echo ADVERTENCIA: La verificacion de dependencias reporto problemas. La aplicacion podria no funcionar correctamente.
) else (
    echo Verificacion de dependencias exitosa.
)

echo.
echo Configurando notificaciones...

REM Configuración de número de teléfono
echo Estableciendo numero de telefono predeterminado para notificaciones...
set NOTIFICATION_PHONE_NUMBER=+584244461682
  
REM Configuración de horas de notificación
echo Configurando horas de notificacion predeterminadas: 13:30 y 20:30
set NOTIFICATION_HOUR_1=13:30
set NOTIFICATION_HOUR_2=20:30

echo Configuracion de notificaciones completada.

echo Inicializando la base de datos...
REM Secuencia completa de inicialización de base de datos con múltiples métodos
echo Método 1: Usar fix_db.py (método recomendado)...
python fix_db.py
if %errorlevel% neq 0 (
    echo ADVERTENCIA: El script principal de base de datos falló.
    echo Método 2: Usando create_db.py...
    python create_db.py
    
    if %errorlevel% neq 0 (
        echo ADVERTENCIA: create_db.py falló.
        echo Método 3: Usando create_tables.py...
        python create_tables.py
        
        if %errorlevel% neq 0 (
            echo ERROR: No se pudo inicializar la base de datos.
            echo La aplicación no funcionará correctamente.
            echo Por favor, contacte con soporte técnico.
            pause
            exit /b 1
        )
    )
)

echo Verificando actualización de estructura de base de datos...
python update_db.py

echo Verificando integridad final de la base de datos...
python -c "import os, sqlite3; conn=sqlite3.connect('gimnasio.db'); c=conn.cursor(); c.execute('SELECT count(name) FROM sqlite_master WHERE type=\"table\"'); count=c.fetchone()[0]; conn.close(); print(f'Tablas encontradas: {count}'); exit(0 if count >= 4 else 1)"
if %errorlevel% neq 0 (
    echo ADVERTENCIA: La base de datos no contiene todas las tablas necesarias.
    echo Intentando un último método de recuperación...
    python create_tables.py
    if %errorlevel% neq 0 (
        echo ERROR: No se pudo completar la inicialización de la base de datos.
        echo Puede intentar ejecutar manualmente los scripts:
        echo   python create_db.py
        echo   python create_tables.py
        echo   python update_db.py
        pause
    )
)

echo Verificando directorios necesarios...
if not exist "static\uploads\audio" (
    echo Creando directorios para archivos de audio...
    mkdir "static\uploads\audio" 2>nul
)

if not exist "static\uploads\audios\permanent" (
    echo Creando directorios para archivos permanentes...
    mkdir "static\uploads\audios\permanent" 2>nul
)

if not exist "logs" (
    echo Creando directorio de logs...
    mkdir "logs" 2>nul
)

echo.
echo ===============================
echo INSTALACION COMPLETADA
echo ===============================
echo.
echo Puede iniciar la aplicacion ejecutando start.bat
echo.

deactivate
endlocal 