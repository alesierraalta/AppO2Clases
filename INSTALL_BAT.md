# Documentación: install.bat

## 1. Propósito

El script `install.bat` automatiza la instalación completa del entorno de desarrollo de AppO2Clases en sistemas Windows. Realiza todas las tareas necesarias para configurar el proyecto desde cero:

- Verificación de Python
- Creación de entorno virtual
- Instalación de dependencias
- Inicialización de base de datos
- Creación de estructura de directorios

**Uso:**
```batch
install.bat
```

**Tiempo estimado:** 5-10 minutos (depende de la velocidad de internet para descargar dependencias)

## 2. Flujo de Ejecución

```
Inicio
  ↓
Configuración UTF-8
  ↓
Verificación Python 3
  ↓
Verificación/Recreación venv
  ↓
Activación entorno virtual
  ↓
Actualización pip
  ↓
Instalación dependencias (requirements.txt)
  ↓
Verificación flask-wtf
  ↓
Creación base de datos SQLite
  ↓
Creación directorios necesarios
  ↓
Mensaje de finalización
  ↓
Fin
```

## 3. Análisis Línea por Línea

### Líneas 1-6: Configuración Inicial

```batch
@echo off
setlocal EnableDelayedExpansion

chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
```

**Explicación:**
- `@echo off`: Oculta los comandos durante la ejecución (solo muestra output)
- `setlocal EnableDelayedExpansion`: Habilita expansión retardada de variables (permite usar `!variable!` para variables que cambian dentro de loops)
- `chcp 65001`: Cambia la página de códigos a UTF-8 (soporte para caracteres especiales como acentos)
  - `>nul 2>&1`: Redirige output y errores a null (silencioso)
- `set PYTHONIOENCODING=utf-8`: Configura codificación de entrada/salida de Python
- `set PYTHONUTF8=1`: Habilita modo UTF-8 en Python 3.7+

**Propósito:** Garantizar manejo correcto de caracteres especiales en nombres de profesores, clases, etc.

### Líneas 8-11: Encabezado

```batch
echo ===============================
echo INSTALADOR CLASES O2 - COMPLETO
echo ===============================
echo.
```

**Explicación:**
- Muestra encabezado visual en la consola
- `echo.`: Línea en blanco para mejor legibilidad

### Líneas 13-21: Verificación de Python

```batch
echo Verificando Python 3...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python 3 no esta instalado.
    echo Instale Python 3 desde: https://www.python.org/downloads/
    echo IMPORTANTE: Marque "Add Python to PATH" durante la instalacion
    pause
    exit /b 1
)
```

**Explicación:**
- `python --version`: Intenta ejecutar Python y obtener versión
- `> nul 2>&1`: Oculta el output de la versión (solo verifica existencia)
- `if %errorlevel% neq 0`: Si el comando falló (Python no encontrado)
  - `%errorlevel%`: Variable que contiene el código de salida del último comando
  - `neq 0`: Not Equal to 0 (error)
- Muestra mensaje de error con instrucciones
- `pause`: Espera entrada del usuario antes de cerrar
- `exit /b 1`: Sale del script con código de error 1

**Propósito:** Validar que Python está instalado y accesible antes de continuar.

### Líneas 23-24: Mostrar Versión de Python

```batch
echo Python encontrado. Verificando version...
python -c "import sys; print('Python', sys.version_info.major, sys.version_info.minor)"
```

**Explicación:**
- Ejecuta código Python inline para mostrar versión mayor y menor
- Ejemplo de output: "Python 3 9"

**Propósito:** Informar al usuario qué versión de Python se utilizará.

### Líneas 26-37: Gestión del Entorno Virtual

```batch
echo Verificando entorno virtual venv...
if exist venv\ (
    echo Eliminando entorno virtual anterior...
    rmdir /s /q venv 2>nul
)
echo Creando entorno virtual nuevo...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: No se pudo crear el entorno virtual.
    pause
    exit /b 1
)
echo Entorno virtual creado exitosamente.
```

**Explicación:**
- `if exist venv\`: Verifica si el directorio `venv/` existe
- `rmdir /s /q venv`: Elimina directorio recursivamente y silenciosamente
  - `/s`: Recursivo (subdirectorios)
  - `/q`: Quiet (sin confirmación)
  - `2>nul`: Oculta errores si el directorio no existe
- `python -m venv venv`: Crea nuevo entorno virtual
  - `-m venv`: Ejecuta módulo venv
  - `venv`: Nombre del directorio del entorno virtual
- Verificación de error y salida si falla

**Propósito:** Asegurar un entorno virtual limpio, eliminando instalaciones previas corruptas o desactualizadas.

### Líneas 40-46: Activación del Entorno Virtual

```batch
echo Activando entorno virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: No se pudo activar el entorno virtual.
    pause
    exit /b 1
)
```

**Explicación:**
- `call venv\Scripts\activate.bat`: Ejecuta script de activación
  - `call`: Necesario en batch para ejecutar scripts sin terminar el script actual
- Verificación de error

**Propósito:** Activar el entorno virtual para que comandos `pip` y `python` usen las versiones del entorno virtual.

### Líneas 48-49: Actualización de pip

```batch
echo Actualizando pip...
python -m pip install --upgrade pip
```

**Explicación:**
- `python -m pip`: Ejecuta pip como módulo (más confiable que `pip` directo)
- `--upgrade pip`: Actualiza pip a la última versión

**Propósito:** Asegurar que pip esté actualizado para mejor compatibilidad con paquetes modernos.

### Líneas 51-59: Instalación de Dependencias

```batch
echo Instalando dependencias desde requirements.txt...
pip install -r requirements.txt

echo Verificando instalacion de flask-wtf...
python -c "import flask_wtf; print('flask-wtf instalado correctamente')" 2>nul
if %errorlevel% neq 0 (
    echo Reinstalando flask-wtf...
    pip install flask-wtf==0.15.1 --force-reinstall
)
```

**Explicación:**
- `pip install -r requirements.txt`: Instala todas las dependencias listadas
- Verificación específica de `flask-wtf` porque puede tener problemas de instalación
- Si falla, reinstala forzando reinstalación (`--force-reinstall`)
- `2>nul`: Oculta errores del comando de verificación

**Propósito:** Instalar todas las librerías necesarias. Verificación especial para flask-wtf debido a problemas conocidos de compatibilidad.

### Líneas 61-62: Creación de Base de Datos

```batch
echo Creando base de datos...
python -c "import sqlite3; conn = sqlite3.connect('gimnasio.db'); conn.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER)'); conn.close(); print('Base de datos creada')"
```

**Explicación:**
- Código Python inline que:
  1. Importa `sqlite3`
  2. Conecta a `gimnasio.db` (se crea automáticamente si no existe)
  3. Crea una tabla de prueba para verificar que la BD funciona
  4. Cierra conexión
  5. Imprime confirmación

**Propósito:** Crear archivo de base de datos SQLite inicial. Las tablas reales se crean cuando Flask inicia por primera vez.

### Líneas 64-67: Creación de Directorios

```batch
echo Creando directorios necesarios...
if not exist static\uploads\audios\permanent mkdir static\uploads\audios\permanent
if not exist logs mkdir logs
if not exist backups mkdir backups
```

**Explicación:**
- `if not exist ... mkdir`: Crea directorio solo si no existe
  - `static\uploads\audios\permanent`: Para almacenar audios subidos
  - `logs`: Para archivos de log
  - `backups`: Para backups de base de datos

**Propósito:** Crear estructura de directorios necesaria para funcionamiento de la aplicación.

### Líneas 69-74: Mensaje Final

```batch
echo.
echo ===============================
echo INSTALACION COMPLETADA
echo ===============================
echo Para iniciar la aplicacion ejecute: start.bat
echo.
pause
```

**Explicación:**
- Muestra mensaje de éxito
- Instrucciones para siguiente paso
- `pause`: Espera entrada del usuario antes de cerrar

**Propósito:** Confirmar instalación exitosa y guiar al usuario al siguiente paso.

## 4. Verificaciones Realizadas

El script verifica:

1. ✅ **Python instalado**: Comprueba que Python está en PATH
2. ✅ **Entorno virtual válido**: Elimina y recrea si existe
3. ✅ **Dependencias instaladas**: Verifica instalación de flask-wtf específicamente
4. ✅ **Base de datos accesible**: Crea archivo SQLite y prueba conexión
5. ✅ **Directorios creados**: Estructura de carpetas lista

## 5. Creación de Recursos

### Archivos Creados
- `venv/`: Directorio completo del entorno virtual
- `gimnasio.db`: Archivo de base de datos SQLite (vacío inicialmente)

### Directorios Creados
- `static/uploads/audios/permanent/`: Almacenamiento de audios
- `logs/`: Archivos de log
- `backups/`: Backups de base de datos

### Variables de Entorno Configuradas
- `PYTHONIOENCODING=utf-8`
- `PYTHONUTF8=1`

## 6. Manejo de Errores

### Errores Comunes y Soluciones

#### Error: "Python 3 no esta instalado"
**Causa:** Python no está en PATH del sistema.

**Solución:**
1. Instalar Python desde https://www.python.org/downloads/
2. **IMPORTANTE:** Marcar "Add Python to PATH" durante instalación
3. Reiniciar terminal/consola
4. Ejecutar `install.bat` nuevamente

#### Error: "No se pudo crear el entorno virtual"
**Causa:** Permisos insuficientes o espacio en disco.

**Solución:**
1. Ejecutar como Administrador
2. Verificar espacio en disco disponible (>500 MB)
3. Verificar que el directorio no esté protegido

#### Error: "No se pudo activar el entorno virtual"
**Causa:** Archivos del entorno virtual corruptos.

**Solución:**
1. Eliminar manualmente directorio `venv/`
2. Ejecutar `install.bat` nuevamente

#### Error al instalar dependencias
**Causa:** Problemas de red, versiones incompatibles, o falta de compiladores.

**Solución:**
1. Verificar conexión a internet
2. Instalar Microsoft Visual C++ Build Tools (Windows)
3. Reintentar instalación:
   ```batch
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

#### Error: "flask-wtf instalado correctamente" no aparece
**Causa:** Problema conocido con flask-wtf.

**Solución:** El script intenta reinstalar automáticamente. Si persiste:
```batch
venv\Scripts\activate
pip install flask-wtf==0.15.1 --force-reinstall --no-cache-dir
```

## 7. Notas Técnicas

### Por qué recrear el entorno virtual

El script elimina el entorno virtual existente para:
- Evitar conflictos de versiones
- Asegurar instalación limpia
- Prevenir problemas con actualizaciones de Python

### Orden de instalación

1. Python → 2. venv → 3. pip → 4. dependencias → 5. directorios
   
Este orden garantiza que cada paso tenga las dependencias necesarias.

### Tiempo de ejecución

- **Red rápida**: 5-7 minutos
- **Red lenta**: 10-15 minutos
- **Primera ejecución**: Más lento (descarga completa)
- **Reinstalación**: Similar (venv se recrea)

### Requisitos durante ejecución

- Conexión a internet (descarga de paquetes PyPI)
- Permisos de escritura en directorio de proyecto
- Espacio en disco (~500 MB mínimo)

---

**Documentación generada usando herramientas MCP para precisión técnica y análisis línea por línea.**

