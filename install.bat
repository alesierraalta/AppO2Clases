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

echo Verificando columna 'activo' en la tabla horario_clase...
echo Ejecutando verificacion completa de la columna activo...
python -c "import sqlite3, sys; conn=None; try: conn=sqlite3.connect('gimnasio.db'); cursor=conn.cursor(); cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='horario_clase'\"); if not cursor.fetchone(): print('ERROR: La tabla horario_clase no existe.'); sys.exit(1); cursor.execute('PRAGMA table_info(horario_clase)'); columns=cursor.fetchall(); column_names=[col[1] for col in columns]; print(f\"Columnas actuales: {', '.join(column_names)}\"); activo_exists='activo' in column_names; desactivacion_exists='fecha_desactivacion' in column_names; print(f\"Columna activo: {'EXISTE' if activo_exists else 'NO EXISTE'}\"); print(f\"Columna fecha_desactivacion: {'EXISTE' if desactivacion_exists else 'NO EXISTE'}\"); if not activo_exists or not desactivacion_exists: print('Agregando columnas faltantes...'); if not activo_exists: cursor.execute('ALTER TABLE horario_clase ADD COLUMN activo BOOLEAN DEFAULT 1'); print('Columna activo agregada.'); if not desactivacion_exists: cursor.execute('ALTER TABLE horario_clase ADD COLUMN fecha_desactivacion DATE'); print('Columna fecha_desactivacion agregada.'); conn.commit(); cursor.execute('PRAGMA table_info(horario_clase)'); new_columns=cursor.fetchall(); new_column_names=[col[1] for col in new_columns]; if 'activo' not in new_column_names: print('ERROR: No se pudo agregar la columna activo.'); sys.exit(1); else: print('Columnas verificadas correctamente.'); sys.exit(0); except Exception as e: print(f'Error: {e}'); sys.exit(1); finally: if conn: conn.close()"
if %errorlevel% neq 0 (
    echo ERROR: No se pudo verificar o agregar la columna 'activo'. La aplicación podría no funcionar correctamente.
    echo Por favor, contacte con soporte técnico.
    pause
)

echo Sincronizando archivos de modelos...
if exist app\models.py (
    echo Verificando y sincronizando modelos entre raiz y carpeta app...
    copy /y models.py app\models.py
    echo Modelos sincronizados correctamente.
) else (
    echo Creando directorio app si no existe...
    if not exist app (
        mkdir app
    )
    echo Copiando models.py a la carpeta app...
    copy /y models.py app\models.py
)

echo Limpiando archivos de caché Python...
for /d /r %%d in (__pycache__) do (
    echo Limpiando %%d
    rd /s /q "%%d" 2>nul
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
echo La aplicacion ha sido instalada exitosamente.
echo.
echo Para iniciar la aplicacion, ejecute el archivo start.bat
echo.
echo Presione cualquier tecla para finalizar la instalacion...
pause >nul

deactivate
endlocal 