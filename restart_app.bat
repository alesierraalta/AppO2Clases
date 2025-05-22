@echo off
echo ========================================================
echo      REINICIO DE APLICACION DESPUES DE REPARACION
echo ========================================================
echo.

REM Detener cualquier proceso Python
echo 1. Cerrando aplicaciones Python en ejecucion...
taskkill /f /im python.exe 2>nul
taskkill /f /im flask.exe 2>nul
timeout /t 2 /nobreak >nul

REM Limpiar archivos de caché
echo 2. Limpiando archivos de cache Python...
for /d /r %%d in (__pycache__) do (
    rd /s /q "%%d" 2>nul
)

REM Verificar el arreglo
echo 3. Verificando reparacion...
python check_column.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ADVERTENCIA: La columna 'activo' todavia presenta problemas.
    echo Ejecute fix_activo_column.bat antes de continuar.
    pause
    exit /b 1
)

REM Sincronizar modelos
echo 4. Sincronizando modelos...
if exist models.py (
    if not exist app\ mkdir app
    copy /y models.py app\models.py
    echo Modelos sincronizados correctamente.
) else (
    echo ADVERTENCIA: No se encontro models.py en la raiz.
)

REM Iniciar la aplicación
echo.
echo 5. Iniciando aplicacion...
echo.
echo ========================================================
echo             APLICACION REINICIADA
echo ========================================================
echo.
echo La aplicacion se iniciara en un momento.
echo Si sigue viendo errores, ejecute:
echo   fix_on_other_pc.bat
echo.

REM Iniciar la aplicación con el script original
start cmd /c "start.bat"

exit /b 0 