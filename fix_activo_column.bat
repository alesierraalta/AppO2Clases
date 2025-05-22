@echo off
echo ========================================================
echo Solucion al error "no such column: horario_clase.activo"
echo ========================================================
echo.

REM Detener cualquier proceso de Python
echo 1. Cerrando aplicaciones Python en ejecucion...
taskkill /f /im python.exe 2>nul
timeout /t 2 /nobreak >nul

REM Activar entorno virtual si existe
if exist venv\Scripts\activate.bat (
    echo 2. Activando entorno virtual...
    call venv\Scripts\activate.bat
) else (
    echo ADVERTENCIA: No se encontro entorno virtual. Ejecutando con Python del sistema.
)

REM Ejecutar el script de reparación de esquema
echo 3. Ejecutando reparación de esquema...
python fix_schema.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: La reparación automática falló.
    echo Ejecutando método alternativo...
    
    REM Método alternativo directo
    echo  - Agregando columna 'activo' directamente...
    python -c "import sqlite3; conn = sqlite3.connect('gimnasio.db'); cursor = conn.cursor(); try: cursor.execute('ALTER TABLE horario_clase ADD COLUMN activo BOOLEAN DEFAULT 1'); conn.commit(); print('Columna activo agregada.'); except Exception as e: print(f'Error: {e}'); try: cursor.execute('ALTER TABLE horario_clase ADD COLUMN fecha_desactivacion DATE'); conn.commit(); print('Columna fecha_desactivacion agregada.'); except Exception as e: print(f'Error: {e}'); conn.close()"
    
    echo  - Sincronizando modelos...
    if exist models.py (
        if not exist app\ mkdir app
        copy /y models.py app\models.py
        echo Modelos sincronizados.
    )
)

REM Limpiar caché de Python
echo 4. Limpiando caché de Python...
for /d /r %%d in (__pycache__) do (
    rd /s /q "%%d" 2>nul
)

REM Verificación final
echo 5. Verificando solución...
python -c "import sqlite3; conn = sqlite3.connect('gimnasio.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(horario_clase)'); cols = [col[1] for col in cursor.fetchall()]; activo_ok = 'activo' in cols; desactivacion_ok = 'fecha_desactivacion' in cols; print(f'Columna activo: {'EXISTE' if activo_ok else 'NO EXISTE'}'); print(f'Columna fecha_desactivacion: {'EXISTE' if desactivacion_ok else 'NO EXISTE'}'); conn.close(); exit(0 if activo_ok and desactivacion_ok else 1)"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ADVERTENCIA: La verificación final detectó que las columnas aún no existen.
    echo Es posible que necesite ejecutar el script fix_on_other_pc.bat o contactar a soporte.
) else (
    echo.
    echo ========================================================
    echo                 SOLUCIÓN COMPLETADA
    echo ========================================================
    echo.
    echo El error "no such column: horario_clase.activo" ha sido solucionado.
    echo Puede iniciar la aplicación nuevamente usando start.bat
)

echo.
pause 