@echo off
echo ========================================================
echo Solucion al error "no such column: horario_clase.activo"
echo ========================================================
echo.

REM Detener cualquier proceso de Python
echo 1. Cerrando aplicaciones Python en ejecucion...
taskkill /f /im python.exe 2>nul
timeout /t 2 /nobreak >nul

REM Ejecutar el script de Python que soluciona el problema
echo 2. Ejecutando solucion automatica...
echo.
python sincronizar_modelos.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: No se pudo completar la solucion automatica.
    echo Ejecutando metodo alternativo...
    echo.
    
    REM Método alternativo si el script de Python falla
    echo  - Limpiando cache...
    for /d /r %%d in (__pycache__) do (
        rd /s /q "%%d" 2>nul
    )
    
    echo  - Verificando columna 'activo'...
    python add_activo_column.py
    
    echo  - Sincronizando modelos...
    copy /y models.py app\models.py
)

echo.
echo 3. Verificando solucion...
python -c "import sqlite3; conn = sqlite3.connect('gimnasio.db'); cursor = conn.cursor(); cursor.execute(\"PRAGMA table_info(horario_clase)\"); cols = [col[1] for col in cursor.fetchall()]; print('La columna activo ' + ('EXISTE' if 'activo' in cols else 'NO EXISTE') + ' en la base de datos.'); conn.close()"

echo.
echo 4. Reiniciando aplicacion...
start python app.py

echo.
echo ========================================================
echo                 SOLUCION COMPLETADA
echo ========================================================
echo.
echo Para evitar este error en el futuro, asegurese de:
echo  1. No modificar manualmente los archivos models.py
echo  2. Siempre realizar las actualizaciones usando los scripts
echo  3. Mantener sincronizados los modelos en raiz y carpeta app/
echo.
echo Si el problema persiste, ejecute manualmente:
echo   python sincronizar_modelos.py
echo.
pause 