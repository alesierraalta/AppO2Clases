@echo off
echo ===== VERIFICADOR DE VERSION ClasesO2 =====
echo.

:: Activar entorno virtual
call venv\Scripts\activate

set VERSION_FILE=app_version.txt
set CURRENT_DATE=%DATE:~6,4%%DATE:~3,2%%DATE:~0,2%

:: Verificar si estamos en un repositorio git
git rev-parse --is-inside-work-tree >nul 2>&1
if %errorlevel% equ 0 (
    echo Obteniendo información de versión desde Git...
    
    :: Obtener hash de commit actual
    for /f "tokens=*" %%a in ('git rev-parse --short HEAD') do set COMMIT_HASH=%%a
    
    :: Obtener rama actual
    for /f "tokens=*" %%a in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%a
    
    :: Obtener fecha de último commit
    for /f "tokens=*" %%a in ('git log -1 --format^=%%cd --date=format:%%Y-%%m-%%d') do set COMMIT_DATE=%%a
    
    echo INFORMACIÓN DE VERSIÓN:
    echo -----------------------
    echo Rama: %BRANCH%
    echo Commit: %COMMIT_HASH%
    echo Fecha último commit: %COMMIT_DATE%
    echo Fecha actual: %DATE%
    
    :: Guardar información en archivo
    echo ClasesO2 Version > %VERSION_FILE%
    echo Rama: %BRANCH% >> %VERSION_FILE%
    echo Commit: %COMMIT_HASH% >> %VERSION_FILE%
    echo Fecha último commit: %COMMIT_DATE% >> %VERSION_FILE%
    echo Fecha verificación: %DATE% >> %VERSION_FILE%
) else (
    echo No se detectó un repositorio Git.
    echo Usando método alternativo para generar información de versión.
    
    :: Fecha actual como versión
    echo ClasesO2 Version > %VERSION_FILE%
    echo Fecha instalación: %DATE% >> %VERSION_FILE%
)

:: Verificar archivos esenciales
echo.
echo VERIFICANDO ARCHIVOS ESENCIALES:
echo -------------------------------
if exist app.py (
    echo app.py: OK
) else (
    echo app.py: FALTA
)

if exist models.py (
    echo models.py: OK
) else (
    echo models.py: FALTA
)

if exist requirements.txt (
    echo requirements.txt: OK
) else (
    echo requirements.txt: FALTA
)

if exist run.bat (
    echo run.bat: OK
) else (
    echo run.bat: FALTA
)

if exist gimnasio.db (
    echo gimnasio.db: OK
) else (
    echo gimnasio.db: FALTA
)

if exist notifications.py (
    echo notifications.py: OK
) else (
    echo notifications.py: FALTA
)

echo.
echo Información de versión guardada en %VERSION_FILE%
echo.

pause 