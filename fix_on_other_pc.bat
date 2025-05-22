@echo off
echo ========================================================
echo REPARACION EMERGENCIA: Error "no such column: horario_clase.activo"
echo ========================================================
echo.

REM Detener cualquier proceso de Python
echo 1. Cerrando aplicaciones Python en ejecucion...
taskkill /f /im python.exe 2>nul
taskkill /f /im flask.exe 2>nul
timeout /t 2 /nobreak >nul

REM Activar entorno virtual si existe
if exist venv\Scripts\activate.bat (
    echo 2. Activando entorno virtual...
    call venv\Scripts\activate.bat
) else (
    echo ADVERTENCIA: No se encontro entorno virtual. Ejecutando con Python del sistema.
)

REM Verificar estructura de base de datos
echo 3. Verificando estructura de base de datos...
python -c "import sqlite3; conn = sqlite3.connect('gimnasio.db'); cursor = conn.cursor(); cursor.execute(\"PRAGMA table_info(horario_clase)\"); cols = [col[1] for col in cursor.fetchall()]; activo_existe = 'activo' in cols; desactivacion_existe = 'fecha_desactivacion' in cols; print(f'Columna activo: {'EXISTE' if activo_existe else 'NO EXISTE'}'); print(f'Columna fecha_desactivacion: {'EXISTE' if desactivacion_existe else 'NO EXISTE'}'); conn.close(); exit(0 if activo_existe and desactivacion_existe else 1)"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 4. Agregando columnas faltantes a la base de datos...
    python -c "import sqlite3; conn = sqlite3.connect('gimnasio.db'); cursor = conn.cursor(); print('Agregando columna activo...'); try: cursor.execute('ALTER TABLE horario_clase ADD COLUMN activo BOOLEAN DEFAULT 1'); conn.commit(); print('Columna activo agregada.'); except sqlite3.OperationalError as e: print(f'No se pudo agregar columna activo: {e}'); print('Agregando columna fecha_desactivacion...'); try: cursor.execute('ALTER TABLE horario_clase ADD COLUMN fecha_desactivacion DATE'); conn.commit(); print('Columna fecha_desactivacion agregada.'); except sqlite3.OperationalError as e: print(f'No se pudo agregar columna fecha_desactivacion: {e}'); conn.close()"
) else (
    echo Columnas ya existen en la base de datos. No es necesario modificar.
)

REM Sincronizar modelos
echo.
echo 5. Sincronizando archivos de modelos...
if exist models.py (
    if not exist app\ (
        mkdir app
    )
    copy /y models.py app\models.py
    echo Modelos sincronizados correctamente.
) else (
    echo ADVERTENCIA: No se encontro el archivo models.py en la raiz.
)

REM Limpiar cache
echo.
echo 6. Limpiando cache de Python...
for /d /r %%d in (__pycache__) do (
    rd /s /q "%%d" 2>nul
)

REM Crear backup de la base de datos
echo.
echo 7. Creando backup de la base de datos...
copy gimnasio.db gimnasio_backup_%date:~-4,4%%date:~-7,2%%date:~-10,2%.db
echo Backup creado.

REM Verificación final
echo.
echo 8. Verificando solucion...
python -c "import sqlite3; conn = sqlite3.connect('gimnasio.db'); cursor = conn.cursor(); cursor.execute(\"PRAGMA table_info(horario_clase)\"); cols = [col[1] for col in cursor.fetchall()]; print('Verificacion final:'); print('La columna activo ' + ('EXISTE' if 'activo' in cols else 'NO EXISTE') + ' en la base de datos.'); print('La columna fecha_desactivacion ' + ('EXISTE' if 'fecha_desactivacion' in cols else 'NO EXISTE') + ' en la base de datos.'); conn.close()"

echo.
echo ========================================================
echo                 REPARACION COMPLETADA
echo ========================================================
echo.
echo Para reiniciar la aplicacion, ejecute:
echo   start.bat
echo.
echo Si el problema persiste, por favor contacte al soporte tecnico.
echo.
pause 