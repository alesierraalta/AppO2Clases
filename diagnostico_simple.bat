@echo off
setlocal EnableDelayedExpansion

:: Configurar codificacion UTF-8
chcp 65001 >nul 2>&1

echo ===============================
echo DIAGNOSTICO SIMPLE CLASES O2
echo ===============================
echo.

:: Verificar Python
echo [1/4] Verificando Python...
python --version 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python no encontrado
    echo SOLUCION: Instalar Python desde https://www.python.org/downloads/
    echo IMPORTANTE: Marcar "Add Python to PATH" durante la instalacion
    set PYTHON_OK=0
) else (
    echo OK: Python encontrado
    python --version
    set PYTHON_OK=1
)

:: Verificar pip
echo.
echo [2/4] Verificando pip...
if %PYTHON_OK%==1 (
    python -m pip --version 2>nul
    if %errorlevel% neq 0 (
        echo ERROR: pip no encontrado
    ) else (
        echo OK: pip encontrado
        python -m pip --version
    )
) else (
    echo SALTANDO: Python no disponible
)

:: Verificar permisos
echo.
echo [3/4] Verificando permisos de escritura...
echo test > test_write.tmp 2>nul
if exist test_write.tmp (
    echo OK: Permisos de escritura correctos
    del test_write.tmp
) else (
    echo ERROR: Sin permisos de escritura
    echo SOLUCION: Ejecutar como Administrador
)

:: Verificar requirements.txt
echo.
echo [4/4] Verificando archivo requirements.txt...
if exist requirements.txt (
    echo OK: requirements.txt encontrado
) else (
    echo ERROR: requirements.txt no encontrado
    echo SOLUCION: Asegurese de estar en el directorio correcto
)

echo.
echo ===============================
echo INSTRUCCIONES
echo ===============================
echo.
echo Si Python no esta instalado:
echo 1. Ir a https://www.python.org/downloads/
echo 2. Descargar Python 3.8 o superior
echo 3. Durante instalacion marcar "Add Python to PATH"
echo 4. Reiniciar el sistema
echo.
echo Si hay problemas de permisos:
echo 1. Clic derecho en install_compatible.bat
echo 2. Seleccionar "Ejecutar como administrador"
echo.
echo Despues de resolver problemas, ejecutar:
echo install_compatible.bat
echo.
echo Presione cualquier tecla para cerrar...
pause >nul

endlocal