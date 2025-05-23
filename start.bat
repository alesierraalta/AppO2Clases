@echo off
setlocal EnableDelayedExpansion

echo ===============================
echo INICIANDO CLASES O2
echo ===============================
echo.

:: Verificar si el entorno virtual existe
if not exist venv\Scripts\activate.bat (
    echo ERROR: Entorno virtual no encontrado. 
    echo Por favor, ejecute install.bat primero para configurar el entorno.
    pause
    exit /b 1
)

:: Activar el entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Fallo al activar el entorno virtual.
    echo Intente reinstalar la aplicacion ejecutando install.bat
    pause
    exit /b 1
)

:: Verificar y reparar base de datos (sin depender de Flask)
echo Verificando base de datos directamente...
python fix_db.py
if %errorlevel% neq 0 (
    echo ADVERTENCIA: El script independiente de base de datos falló.
    echo Intentando métodos alternativos...
    
    echo 1. Verificando si la base de datos existe...
    python check_db.py
    
    if %errorlevel% neq 0 (
        echo 2. Intentando crear la base de datos desde cero...
        python create_db.py
        
        if %errorlevel% neq 0 (
            echo 3. Último intento: creando tablas manualmente...
            python create_tables.py
            
            if %errorlevel% neq 0 (
                echo ERROR: No se pudo crear la base de datos tras múltiples intentos.
                echo Por favor, ejecute install.bat para una instalación completa o contacte soporte.
                pause
                exit /b 1
            )
        )
    )
    
    echo 4. Actualizando estructura de la base de datos...
    python update_db.py
)

:: Verificación CRÍTICA de la columna 'activo' en la tabla horario_clase
echo Verificando columna 'activo' en la tabla horario_clase...
echo Esta comprobacion es esencial para evitar el error: "no such column: horario_clase.activo"

:: Verificar si la columna existe y crearla si no existe usando una sola línea de Python
python -c "import sqlite3, sys; conn=None; try: conn=sqlite3.connect('gimnasio.db'); cursor=conn.cursor(); cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='horario_clase'\"); if not cursor.fetchone(): print('ERROR: La tabla horario_clase no existe.'); sys.exit(1); cursor.execute('PRAGMA table_info(horario_clase)'); columns=cursor.fetchall(); column_names=[col[1] for col in columns]; print(f\"Columnas actuales: {', '.join(column_names)}\"); activo_exists='activo' in column_names; desactivacion_exists='fecha_desactivacion' in column_names; print(f\"Columna activo: {'EXISTE' if activo_exists else 'NO EXISTE'}\"); print(f\"Columna fecha_desactivacion: {'EXISTE' if desactivacion_exists else 'NO EXISTE'}\"); if not activo_exists or not desactivacion_exists: print('Agregando columnas faltantes...'); if not activo_exists: cursor.execute('ALTER TABLE horario_clase ADD COLUMN activo BOOLEAN DEFAULT 1'); print('Columna activo agregada.'); if not desactivacion_exists: cursor.execute('ALTER TABLE horario_clase ADD COLUMN fecha_desactivacion DATE'); print('Columna fecha_desactivacion agregada.'); conn.commit(); cursor.execute('PRAGMA table_info(horario_clase)'); new_columns=cursor.fetchall(); new_column_names=[col[1] for col in new_columns]; if 'activo' not in new_column_names: print('ERROR: No se pudo agregar la columna activo.'); sys.exit(1); else: print('Columnas verificadas correctamente.'); sys.exit(0); except Exception as e: print(f'Error: {e}'); sys.exit(1); finally: if conn: conn.close()"

if %errorlevel% neq 0 (
    echo ERROR CRITICO: No se pudo agregar la columna 'activo'. La aplicacion no funcionara correctamente.
    echo Por favor, ejecute install.bat para reinstalar la aplicacion completamente.
    pause
    exit /b 1
)

:: Sincronizar archivos de modelos
echo Sincronizando archivos de modelos...
if exist models.py (
    if exist app\ (
        echo Verificando sincronizacion de modelos...
        copy /y models.py app\models.py
    ) else (
        echo Creando carpeta app...
        mkdir app
        echo Copiando models.py a app...
        copy /y models.py app\models.py
    )
    echo Modelos sincronizados correctamente.
)

:: Limpiar caché de Python
echo Limpiando cache de Python...
for /d /r %%d in (__pycache__) do (
    rd /s /q "%%d" 2>nul
)

:: Establecer variables de entorno de Flask
set FLASK_APP=app.py
set FLASK_ENV=development

:: Configuración de notificaciones
echo Configurando notificaciones...
if not defined NOTIFICATION_PHONE_NUMBER (
    set NOTIFICATION_PHONE_NUMBER=+584244461682
)
if not defined NOTIFICATION_HOUR_1 (
    set NOTIFICATION_HOUR_1=13:30
)
if not defined NOTIFICATION_HOUR_2 (
    set NOTIFICATION_HOUR_2=20:30
)

echo Notificaciones configuradas para el numero: %NOTIFICATION_PHONE_NUMBER%
echo a las horas: %NOTIFICATION_HOUR_1% y %NOTIFICATION_HOUR_2%

:: Verificar directorios necesarios
echo Verificando directorios necesarios...
if not exist "static\uploads\audio" (
    mkdir "static\uploads\audio" 2>nul
)
if not exist "static\uploads\audios\permanent" (
    mkdir "static\uploads\audios\permanent" 2>nul
)
if not exist "logs" (
    mkdir "logs" 2>nul
)

:: Eliminar cualquier base de datos vacía que pueda haber quedado
echo Verificando integridad final de la base de datos...
python -c "import os, sqlite3; conn=sqlite3.connect('gimnasio.db'); c=conn.cursor(); c.execute('SELECT count(name) FROM sqlite_master WHERE type=\"table\"'); count=c.fetchone()[0]; conn.close(); exit(0 if count > 0 else 1)"
if %errorlevel% neq 0 (
    echo ADVERTENCIA: La base de datos existe pero está vacía. Intentando un último método...
    python create_tables.py
    if %errorlevel% neq 0 (
        echo ERROR: No se pudo inicializar la base de datos.
        pause
        exit /b 1
    )
)

echo.
echo ===============================
echo INICIANDO APLICACION
echo ===============================
echo Puede acceder a la aplicacion en: http://127.0.0.1:5000
echo.
echo NOTA: Los mensajes "Error setting up date handling" son advertencias
echo       inofensivas y no afectan el funcionamiento de la aplicacion.
echo.

:: Intentar abrir el navegador automáticamente
start "" http://127.0.0.1:5000

:: Iniciar la aplicación Flask
echo Iniciando servidor...
flask run --host=0.0.0.0 --port=5000

:: Si falla, intentar métodos alternativos
if %errorlevel% neq 0 (
    echo ADVERTENCIA: Fallo al iniciar con flask run. Intentando metodo alternativo...
    echo.
    
    echo Ejecutando python app.py directamente...
    python app.py
    
    if %errorlevel% neq 0 (
        echo ERROR: La aplicacion no pudo iniciarse.
        echo Verifique la instalacion y las dependencias ejecutando:
        echo   python check_dependencies.py
        echo.
        echo Puede intentar reparar las dependencias con:
        echo   fix_dependencies.bat
    )
)

deactivate
endlocal 