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