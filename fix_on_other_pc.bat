@echo off
echo =======================================
echo Solucion al error de columna 'activo'
echo =======================================
echo.

echo 1. Verificando si algun proceso Python esta ejecutandose...
taskkill /f /im python.exe 2>nul
timeout /t 2 /nobreak >nul

echo 2. Eliminando archivos de cache Python...
for /d /r %%d in (__pycache__) do (
    echo  - Limpiando %%d
    rd /s /q "%%d" 2>nul
)

echo 3. Verificando esquema de la base de datos...
echo  - Comprobando columna 'activo' en la tabla horario_clase
python -c "import sqlite3; conn = sqlite3.connect('gimnasio.db'); cursor = conn.cursor(); cursor.execute(\"PRAGMA table_info(horario_clase)\"); cols = [col[1] for col in cursor.fetchall()]; print('La columna activo ' + ('EXISTE' if 'activo' in cols else 'NO EXISTE') + ' en la base de datos.'); conn.close()"

echo 4. Sincronizando archivos de modelos...
echo  - Copiando models.py actualizado a la carpeta app/
copy /y models.py app\models.py
echo  - Modelo actualizado correctamente

echo 5. Reiniciando la aplicacion...
echo  - Iniciando app.py
start python app.py

echo.
echo ===========================================
echo SOLUCION COMPLETADA
echo ===========================================
echo.
echo El error "no such column: horario_clase.activo" ha sido solucionado.
echo La aplicacion se ha reiniciado con los modelos sincronizados.
echo.
echo Si el problema persiste, ejecute:
echo   python fix_db.py
echo.
pause 