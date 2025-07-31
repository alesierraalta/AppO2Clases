@echo off
setlocal EnableDelayedExpansion

:: Configurar codificación UTF-8
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo ===============================
echo DIAGNOSTICO CLASES O2
echo ===============================
echo.
echo Este script diagnosticara posibles problemas en el sistema.
echo.

:: Verificar Python
echo [1/8] Verificando Python...
python --version 2>nul
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python no encontrado
    echo    - Python no esta instalado o no esta en el PATH
    echo    - Descargar desde: https://www.python.org/downloads/
    echo    - Asegurese de marcar "Add Python to PATH" durante la instalacion
    set PYTHON_OK=0
) else (
    echo ✅ Python encontrado
    python --version
    set PYTHON_OK=1
)

:: Verificar pip
echo.
echo [2/8] Verificando pip...
if %PYTHON_OK%==1 (
    python -m pip --version 2>nul
    if %errorlevel% neq 0 (
        echo ❌ ERROR: pip no encontrado
        set PIP_OK=0
    ) else (
        echo ✅ pip encontrado
        python -m pip --version
        set PIP_OK=1
    )
) else (
    echo ⏭️ Saltando (Python no disponible)
    set PIP_OK=0
)

:: Verificar venv
echo.
echo [3/8] Verificando capacidad de crear entornos virtuales...
if %PYTHON_OK%==1 (
    python -m venv --help >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ ERROR: modulo venv no disponible
        set VENV_OK=0
    ) else (
        echo ✅ Modulo venv disponible
        set VENV_OK=1
    )
) else (
    echo ⏭️ Saltando (Python no disponible)
    set VENV_OK=0
)

:: Verificar permisos de escritura
echo.
echo [4/8] Verificando permisos de escritura...
echo test > test_write.tmp 2>nul
if exist test_write.tmp (
    echo ✅ Permisos de escritura OK
    del test_write.tmp
    set WRITE_OK=1
) else (
    echo ❌ ERROR: Sin permisos de escritura en el directorio actual
    set WRITE_OK=0
)

:: Verificar si ya existe venv
echo.
echo [5/8] Verificando entorno virtual existente...
if exist venv\ (
    echo ⚠️ Ya existe un directorio venv
    if exist venv\Scripts\activate.bat (
        echo ✅ El entorno virtual parece valido
        set VENV_EXISTS=1
    ) else (
        echo ❌ El directorio venv existe pero no es valido
        set VENV_EXISTS=0
    )
) else (
    echo ✅ No hay entorno virtual previo (normal para primera instalacion)
    set VENV_EXISTS=0
)

:: Verificar requirements.txt
echo.
echo [6/8] Verificando archivo requirements.txt...
if exist requirements.txt (
    echo ✅ requirements.txt encontrado
    echo Contenido:
    type requirements.txt | findstr /n "^"
    set REQ_OK=1
) else (
    echo ❌ ERROR: requirements.txt no encontrado
    set REQ_OK=0
)

:: Verificar antivirus/seguridad
echo.
echo [7/8] Verificando posibles bloqueos de seguridad...
echo Creando script de prueba...
echo @echo off > test_script.bat
echo echo Prueba exitosa >> test_script.bat
call test_script.bat >test_output.txt 2>&1
if exist test_output.txt (
    findstr "Prueba exitosa" test_output.txt >nul
    if %errorlevel%==0 (
        echo ✅ Los scripts pueden ejecutarse normalmente
        set SECURITY_OK=1
    ) else (
        echo ⚠️ Posible interferencia de seguridad
        set SECURITY_OK=0
    )
    del test_output.txt
) else (
    echo ❌ No se pudo crear archivo de salida
    set SECURITY_OK=0
)
del test_script.bat 2>nul

:: Verificar conectividad a internet
echo.
echo [8/8] Verificando conectividad a internet...
ping -n 1 google.com >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Conectividad a internet OK
    set INTERNET_OK=1
) else (
    echo ⚠️ Problemas de conectividad a internet
    set INTERNET_OK=0
)

:: Resumen
echo.
echo ===============================
echo RESUMEN DEL DIAGNOSTICO
echo ===============================
echo.

set TOTAL_ERRORS=0

if %PYTHON_OK%==0 (
    echo ❌ CRITICO: Python no instalado
    set /a TOTAL_ERRORS+=1
)

if %PIP_OK%==0 if %PYTHON_OK%==1 (
    echo ❌ CRITICO: pip no disponible
    set /a TOTAL_ERRORS+=1
)

if %VENV_OK%==0 if %PYTHON_OK%==1 (
    echo ❌ CRITICO: venv no disponible
    set /a TOTAL_ERRORS+=1
)

if %WRITE_OK%==0 (
    echo ❌ CRITICO: Sin permisos de escritura
    set /a TOTAL_ERRORS+=1
)

if %REQ_OK%==0 (
    echo ❌ CRITICO: requirements.txt faltante
    set /a TOTAL_ERRORS+=1
)

if %SECURITY_OK%==0 (
    echo ⚠️ ADVERTENCIA: Posible bloqueo de seguridad
)

if %INTERNET_OK%==0 (
    echo ⚠️ ADVERTENCIA: Sin internet (necesario para descargar dependencias)
)

echo.
if %TOTAL_ERRORS%==0 (
    echo ✅ RESULTADO: El sistema parece estar listo para la instalacion
    echo    Puede proceder con install.bat
) else (
    echo ❌ RESULTADO: Se encontraron %TOTAL_ERRORS% problemas criticos
    echo    Debe resolver estos problemas antes de continuar
)

echo.
echo SOLUCION DE PROBLEMAS:
echo.
if %PYTHON_OK%==0 (
    echo Para instalar Python:
    echo 1. Vaya a https://www.python.org/downloads/
    echo 2. Descargue Python 3.8 o superior
    echo 3. Durante la instalacion, marque "Add Python to PATH"
    echo 4. Reinicie el sistema despues de instalar
    echo.
)

if %WRITE_OK%==0 (
    echo Para resolver permisos:
    echo 1. Ejecute como Administrador
    echo 2. O mueva la aplicacion a una carpeta donde tenga permisos
    echo.
)

if %SECURITY_OK%==0 (
    echo Para resolver bloqueos de seguridad:
    echo 1. Temporalmente deshabilite el antivirus
    echo 2. Agregue la carpeta a las excepciones del antivirus
    echo 3. Verifique la politica de ejecucion de PowerShell
    echo.
)

echo.
echo Presione cualquier tecla para cerrar...
pause >nul

endlocal