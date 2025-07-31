@echo off
setlocal EnableDelayedExpansion

:: Configurar codificación UTF-8
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo ===============================
echo INSTALADOR SIMPLE CLASES O2
echo ===============================
echo.

:: Paso 1: Verificar Python
echo [PASO 1] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERROR: Python no encontrado
    echo.
    echo SOLUCION:
    echo 1. Instale Python desde https://www.python.org/downloads/
    echo 2. Durante la instalacion, marque "Add Python to PATH"
    echo 3. Reinicie el sistema
    echo 4. Ejecute este script nuevamente
    echo.
    pause
    exit /b 1
)
echo ✅ Python encontrado
python --version

:: Paso 2: Crear entorno virtual
echo.
echo [PASO 2] Creando entorno virtual...
if exist venv\ (
    echo ⚠️ El entorno virtual ya existe. Eliminando...
    rmdir /s /q venv
)

python -m venv venv
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERROR: No se pudo crear el entorno virtual
    echo.
    echo POSIBLES SOLUCIONES:
    echo 1. Ejecute como Administrador
    echo 2. Verifique que tiene permisos en esta carpeta
    echo 3. Temporalmente deshabilite el antivirus
    echo.
    pause
    exit /b 1
)
echo ✅ Entorno virtual creado

:: Paso 3: Activar entorno virtual
echo.
echo [PASO 3] Activando entorno virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ ERROR: No se pudo activar el entorno virtual
    pause
    exit /b 1
)
echo ✅ Entorno virtual activado

:: Paso 4: Actualizar pip
echo.
echo [PASO 4] Actualizando pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo ⚠️ ADVERTENCIA: No se pudo actualizar pip, continuando...
)

:: Paso 5: Instalar dependencias básicas
echo.
echo [PASO 5] Instalando dependencias básicas...
pip install Flask==2.0.1 Flask-SQLAlchemy==2.5.1 Werkzeug==2.0.1
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERROR: No se pudieron instalar las dependencias básicas
    echo.
    echo POSIBLES SOLUCIONES:
    echo 1. Verifique su conexión a internet
    echo 2. Temporalmente deshabilite el antivirus
    echo 3. Use una VPN si hay restricciones de red
    echo.
    pause
    exit /b 1
)
echo ✅ Dependencias básicas instaladas

:: Paso 6: Instalar dependencias adicionales
echo.
echo [PASO 6] Instalando dependencias adicionales...
pip install openpyxl matplotlib pandas numpy
if %errorlevel% neq 0 (
    echo ⚠️ ADVERTENCIA: Algunas dependencias adicionales fallaron
    echo La aplicación funcionará pero con funcionalidad limitada
)

:: Paso 7: Crear base de datos
echo.
echo [PASO 7] Inicializando base de datos...
python create_db.py
if %errorlevel% neq 0 (
    echo ⚠️ ADVERTENCIA: create_db.py falló, intentando método alternativo...
    python -c "import sqlite3; conn = sqlite3.connect('gimnasio.db'); cursor = conn.cursor(); cursor.execute('CREATE TABLE IF NOT EXISTS profesor (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, apellido TEXT NOT NULL, telefono TEXT, email TEXT)'); cursor.execute('CREATE TABLE IF NOT EXISTS clase (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, descripcion TEXT)'); cursor.execute('CREATE TABLE IF NOT EXISTS horario_clase (id INTEGER PRIMARY KEY AUTOINCREMENT, clase_id INTEGER, profesor_id INTEGER, dia_semana INTEGER, hora_inicio TEXT, hora_fin TEXT, activo INTEGER DEFAULT 1, fecha_desactivacion TEXT, FOREIGN KEY (clase_id) REFERENCES clase (id), FOREIGN KEY (profesor_id) REFERENCES profesor (id))'); cursor.execute('CREATE TABLE IF NOT EXISTS asistencia (id INTEGER PRIMARY KEY AUTOINCREMENT, horario_clase_id INTEGER, fecha DATE, cantidad_alumnos INTEGER, observaciones TEXT, FOREIGN KEY (horario_clase_id) REFERENCES horario_clase (id))'); conn.commit(); conn.close(); print('✅ Base de datos creada exitosamente')"
    if %errorlevel% neq 0 (
        echo ❌ ERROR: No se pudo crear la base de datos
        pause
        exit /b 1
    )
)

:: Paso 8: Crear directorios necesarios
echo.
echo [PASO 8] Creando directorios...
if not exist "static\uploads\audios\permanent" mkdir "static\uploads\audios\permanent"
if not exist "logs" mkdir "logs"
echo ✅ Directorios creados

echo.
echo ===============================
echo ✅ INSTALACION COMPLETADA
echo ===============================
echo.
echo La aplicación ha sido instalada exitosamente.
echo.
echo SIGUIENTE PASO:
echo Ejecute start.bat para iniciar la aplicación
echo.
echo Presione cualquier tecla para continuar...
pause >nul

deactivate
endlocal