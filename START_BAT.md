# Documentación: start.bat

## 1. Propósito

El script `start.bat` inicia la aplicación AppO2Clases en sistemas Windows. Realiza verificaciones exhaustivas del entorno y la base de datos antes de iniciar el servidor Flask, garantizando que la aplicación funcione correctamente desde el primer arranque.

**Uso:**
```batch
start.bat
```

**Requisitos previos:**
- Haber ejecutado `install.bat` previamente
- Entorno virtual (`venv/`) existente y configurado

## 2. Flujo de Ejecución

```
Inicio
  ↓
Configuración UTF-8 y Locale
  ↓
Verificación de entorno virtual
  ↓
Activación de entorno virtual
  ↓
Verificación/Reparación de base de datos (múltiples métodos)
  ↓
Verificación de columna 'activo'
  ↓
Sincronización de modelos
  ↓
Limpieza de caché Python
  ↓
Configuración de variables Flask
  ↓
Configuración de notificaciones WhatsApp
  ↓
Verificación de directorios
  ↓
Verificación final de integridad BD
  ↓
Abrir navegador (http://127.0.0.1:5000)
  ↓
Iniciar servidor Flask
  ↓
Método alternativo si falla (python app.py)
  ↓
Desactivar entorno virtual
  ↓
Fin
```

## 3. Análisis Línea por Línea

### Líneas 1-8: Configuración Inicial y Locale

```batch
@echo off
setlocal EnableDelayedExpansion

chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set LC_ALL=es_ES.UTF-8
set LANG=es_ES.UTF-8
```

**Explicación:**
- Similar a `install.bat`, pero adicionalmente:
- `set LC_ALL=es_ES.UTF-8`: Configura locale para español (formato de fechas, números)
- `set LANG=es_ES.UTF-8`: Idioma del sistema en español

**Propósito:** Configurar correctamente codificación UTF-8 y formato español para la aplicación.

### Líneas 10-13: Encabezado

```batch
echo ===============================
echo INICIANDO CLASES O2
echo ===============================
echo.
```

**Explicación:** Encabezado visual.

### Líneas 15-20: Verificación de Entorno Virtual

```batch
if not exist venv\Scripts\activate.bat (
    echo ERROR: Entorno virtual no encontrado. 
    echo Por favor, ejecute install.bat primero para configurar el entorno.
    pause
    exit /b 1
)
```

**Explicación:**
- `if not exist venv\Scripts\activate.bat`: Verifica existencia del script de activación
- Si no existe, indica que se debe ejecutar `install.bat` primero
- Sale con error si falta

**Propósito:** Validar que la instalación se completó antes de intentar iniciar.

### Líneas 22-29: Activación del Entorno Virtual

```batch
echo Activando entorno virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Fallo al activar el entorno virtual.
    echo Intente reinstalar la aplicacion ejecutando install.bat
    pause
    exit /b 1
)
```

**Explicación:**
- Similar a `install.bat`
- Si falla, sugiere reinstalar

**Propósito:** Activar entorno virtual para usar Python y librerías correctas.

### Líneas 31-59: Verificación y Reparación de Base de Datos (Sistema de Fallback)

```batch
echo Verificando base de datos directamente...
python fix_db.py
if %errorlevel% neq 0 (
    echo ADVERTENCIA: El script independiente de base de datos fallo.
    echo Intentando metodos alternativos...
    
    echo 1. Verificando si la base de datos existe...
    python check_db.py
    
    if %errorlevel% neq 0 (
        echo 2. Intentando crear la base de datos desde cero...
        python create_db.py
        
        if %errorlevel% neq 0 (
            echo 3. Ultimo intento: creando tablas manualmente...
            python create_tables.py
            
            if %errorlevel% neq 0 (
                echo ERROR: No se pudo crear la base de datos tras multiples intentos.
                echo Por favor, ejecute install.bat para una instalacion completa o contacte soporte.
            pause
            exit /b 1
            )
        )
    )
    
    echo 4. Actualizando estructura de la base de datos...
    python update_db.py
)
```

**Explicación:**
Este bloque implementa un **sistema de fallback en cascada**:

1. **Primer intento:** `fix_db.py` - Script de reparación general
2. **Segundo intento:** `check_db.py` - Verificar si la BD existe
3. **Tercer intento:** `create_db.py` - Crear BD desde cero con SQLAlchemy
4. **Cuarto intento:** `create_tables.py` - Crear tablas manualmente con SQL directo
5. **Actualización:** `update_db.py` - Actualizar esquema si es necesario

Cada nivel se ejecuta solo si el anterior falla.

**Propósito:** Garantizar que la base de datos esté lista, probando múltiples métodos de reparación/creación.

### Líneas 61-71: Verificación de Columna 'activo'

```batch
echo Verificando columna activo en la tabla horario_clase...
echo Esta comprobacion es esencial para evitar el error: no such column: horario_clase.activo

python verify_columns.py

if %errorlevel% neq 0 (
    echo ERROR CRITICO: No se pudo agregar la columna activo. La aplicacion no funcionara correctamente.
    echo Por favor, ejecute install.bat para reinstalar la aplicacion completamente.
    pause
    exit /b 1
)
```

**Explicación:**
- Verifica específicamente que la columna `activo` existe en `horario_clase`
- Error crítico conocido: "no such column: horario_clase.activo"
- `verify_columns.py` agrega la columna si no existe
- Si falla, la aplicación no puede iniciar correctamente

**Propósito:** Prevenir un error específico común causado por esquemas de BD antiguos o incompletos.

### Líneas 73-85: Sincronización de Modelos

```batch
echo Sincronizando archivos de modelos...
if exist models.py (
    if exist app\ (
        echo Verificando sincronizacion de modelos...
        copy /y models.py app\models.py
    ) else (
        echo Creando carpeta app...
        mkdir app
        echo Copiando models.py a app...
        copy /y models.py app\models.py
    )
    echo Modelos sincronizados correctamente.
)
```

**Explicación:**
- Verifica si existe `models.py` en la raíz
- Si existe directorio `app/`, copia `models.py` a `app/models.py`
- Si no existe `app/`, lo crea primero
- `copy /y`: Copia sobrescribiendo si existe (`/y` = yes, sin confirmación)

**Propósito:** Mantener sincronizada la copia de modelos en `app/models.py` (posible estructura de blueprints o imports).

### Líneas 87-90: Limpieza de Caché Python

```batch
echo Limpiando cache de Python...
for /d /r %%d in (__pycache__) do (
    rd /s /q "%%d" 2>nul
)
```

**Explicación:**
- `for /d /r %%d in (__pycache__)`: Busca recursivamente todos los directorios `__pycache__`
  - `/d`: Solo directorios
  - `/r`: Recursivo desde directorio actual
  - `%%d`: Variable del loop (necesita `%%` en batch files)
- `rd /s /q "%%d"`: Elimina cada directorio encontrado
  - `/s`: Recursivo
  - `/q`: Quiet (sin confirmación)
- `2>nul`: Oculta errores si no encuentra directorios

**Propósito:** Eliminar archivos `.pyc` compilados para forzar recompilación y evitar problemas con código modificado.

### Líneas 92-93: Configuración de Variables Flask

```batch
set FLASK_APP=app.py
set FLASK_ENV=development
```

**Explicación:**
- `FLASK_APP`: Indica a Flask cuál es el archivo de la aplicación
- `FLASK_ENV=development`: Modo desarrollo (auto-reload, debug, etc.)

**Propósito:** Configurar variables de entorno que Flask necesita para funcionar.

### Líneas 95-107: Configuración de Notificaciones WhatsApp

```batch
echo Configurando notificaciones...
if not defined NOTIFICATION_PHONE_NUMBER (
    set NOTIFICATION_PHONE_NUMBER=+584244461682
)
if not defined NOTIFICATION_HOUR_1 (
    set NOTIFICATION_HOUR_1=13:30
)
if not defined NOTIFICATION_HOUR_2 (
    set NOTIFICATION_HOUR_2=20:30
)

echo Notificaciones configuradas para el numero: %NOTIFICATION_PHONE_NUMBER%
echo a las horas: %NOTIFICATION_HOUR_1% y %NOTIFICATION_HOUR_2%
```

**Explicación:**
- `if not defined`: Verifica si la variable de entorno no está definida
- Si no está definida, establece valores por defecto:
  - Número de teléfono: +584244461682
  - Hora 1: 13:30 (1:30 PM)
  - Hora 2: 20:30 (8:30 PM)
- Muestra configuración al usuario

**Propósito:** Configurar sistema de notificaciones automáticas para recordar clases no registradas.

**Nota:** Estos valores pueden sobrescribirse con variables de entorno del sistema si están definidas antes de ejecutar el script.

### Líneas 109-118: Verificación de Directorios

```batch
echo Verificando directorios necesarios...
if not exist "static\uploads\audio" (
    mkdir "static\uploads\audio" 2>nul
)
if not exist "static\uploads\audios\permanent" (
    mkdir "static\uploads\audios\permanent" 2>nul
)
if not exist "logs" (
    mkdir "logs" 2>nul
)
```

**Explicación:**
- Crea directorios si no existen
- `2>nul`: Oculta errores si ya existen
- Similar a `install.bat`, pero verifica en cada inicio

**Propósito:** Asegurar que directorios necesarios existan (pueden haber sido eliminados).

### Líneas 120-130: Verificación Final de Integridad de Base de Datos

```batch
echo Verificando integridad final de la base de datos...
python -c "import os, sqlite3; conn=sqlite3.connect('gimnasio.db'); c=conn.cursor(); c.execute('SELECT count(name) FROM sqlite_master WHERE type=\"table\"'); count=c.fetchone()[0]; conn.close(); exit(0 if count > 0 else 1)"
if %errorlevel% neq 0 (
    echo ADVERTENCIA: La base de datos existe pero esta vacia. Intentando un ultimo metodo...
    python create_tables.py
    if %errorlevel% neq 0 (
        echo ERROR: No se pudo inicializar la base de datos.
        pause
        exit /b 1
    )
)
```

**Explicación:**
- Código Python inline que:
  1. Conecta a SQLite
  2. Consulta `sqlite_master` (tabla del sistema con metadata)
  3. Cuenta cuántas tablas existen
  4. Sale con código 0 si hay tablas, 1 si no hay
- Si no hay tablas, intenta crear con `create_tables.py`
- Si falla, muestra error y sale

**Propósito:** Verificación final de que la BD tiene al menos una tabla antes de iniciar Flask.

### Líneas 132-140: Mensajes Pre-Inicio

```batch
echo.
echo ===============================
echo INICIANDO APLICACION
echo ===============================
echo Puede acceder a la aplicacion en: http://127.0.0.1:5000
echo.
echo NOTA: Los mensajes Error setting up date handling son advertencias
echo       inofensivas y no afectan el funcionamiento de la aplicacion.
echo.
```

**Explicación:**
- Muestra URL de acceso
- **Nota importante:** Advierte sobre advertencias inofensivas relacionadas con manejo de fechas
- Estas advertencias aparecen por configuración de locale y no afectan funcionalidad

**Propósito:** Informar al usuario y evitar confusión con advertencias esperadas.

### Líneas 142: Abrir Navegador

```batch
start "" http://127.0.0.1:5000
```

**Explicación:**
- `start ""`: Abre aplicación asociada a la URL (navegador por defecto)
- `""`: Título vacío para la ventana (no aplica para URLs)
- Abre automáticamente la aplicación en el navegador

**Propósito:** Experiencia de usuario mejorada: abre la app automáticamente.

### Líneas 144-161: Inicio del Servidor Flask (con Método Alternativo)

```batch
echo Iniciando servidor...
flask run --host=0.0.0.0 --port=5000

if %errorlevel% neq 0 (
    echo ADVERTENCIA: Fallo al iniciar con flask run. Intentando metodo alternativo...
    echo.
    
    echo Ejecutando python app.py directamente...
    python app.py
    
    if %errorlevel% neq 0 (
        echo ERROR: La aplicacion no pudo iniciarse.
        echo Verifique la instalacion y las dependencias ejecutando:
        echo   python check_dependencies.py
        echo.
        echo Puede intentar reparar las dependencias con:
        echo   fix_dependencies.bat
    )
)
```

**Explicación:**
- **Primer método:** `flask run --host=0.0.0.0 --port=5000`
  - Usa CLI de Flask
  - `--host=0.0.0.0`: Escucha en todas las interfaces (accesible desde red local)
  - `--port=5000`: Puerto 5000
- **Si falla:** Intenta `python app.py` directamente
  - Ejecuta el archivo Python directamente
  - Flask tiene código `if __name__ == '__main__'` que inicia el servidor
- **Si ambos fallan:** Muestra mensaje de error con instrucciones

**Propósito:** Sistema de fallback para iniciar el servidor, probando múltiples métodos.

**Nota:** El método alternativo puede usar configuración diferente (por ejemplo, puerto 8111 según `app.py`).

### Líneas 164-165: Limpieza Final

```batch
deactivate
endlocal
```

**Explicación:**
- `deactivate`: Desactiva el entorno virtual (si se ejecuta manualmente)
- `endlocal`: Termina el contexto local de variables (restaura variables anteriores)

**Propósito:** Limpieza al terminar el script (aunque normalmente el script se mantiene corriendo con Flask).

## 4. Verificaciones Pre-Inicio

El script realiza las siguientes verificaciones en orden:

1. ✅ **Entorno virtual existe**: Verifica `venv/Scripts/activate.bat`
2. ✅ **Entorno virtual funciona**: Activa y verifica éxito
3. ✅ **Base de datos accesible**: Múltiples métodos de reparación/creación
4. ✅ **Columna 'activo' existe**: Previene error específico conocido
5. ✅ **Modelos sincronizados**: Copia `models.py` a `app/models.py`
6. ✅ **Directorios existen**: Crea si faltan
7. ✅ **Tablas en BD**: Verifica que la BD no está vacía

## 5. Configuración de Entorno

### Variables de Entorno Configuradas

- `PYTHONIOENCODING=utf-8`
- `PYTHONUTF8=1`
- `LC_ALL=es_ES.UTF-8`
- `LANG=es_ES.UTF-8`
- `FLASK_APP=app.py`
- `FLASK_ENV=development`
- `NOTIFICATION_PHONE_NUMBER` (si no definida: +584244461682)
- `NOTIFICATION_HOUR_1` (si no definida: 13:30)
- `NOTIFICATION_HOUR_2` (si no definida: 20:30)

### Puertos y Hosts

- **Puerto por defecto:** 5000
- **Host:** 0.0.0.0 (todas las interfaces)
- **URL local:** http://127.0.0.1:5000
- **URL red local:** http://[IP_MAQUINA]:5000

## 6. Inicio del Servidor

### Método Principal: `flask run`

Ventajas:
- Usa CLI oficial de Flask
- Configuración estándar
- Mejor para desarrollo

### Método Alternativo: `python app.py`

Ventajas:
- Más directo
- Usa configuración en `app.py` (puede diferir: puerto 8111)
- Útil si CLI de Flask tiene problemas

### Estado del Servidor

El servidor Flask se ejecuta en **primer plano**, por lo que:
- La ventana de consola permanece abierta
- Los logs se muestran en tiempo real
- Ctrl+C detiene el servidor

## 7. Manejo de Errores

### Error: "Entorno virtual no encontrado"

**Causa:** No se ejecutó `install.bat` o el entorno virtual fue eliminado.

**Solución:**
```batch
install.bat
```

### Error: "Fallo al activar el entorno virtual"

**Causa:** Archivos corruptos o permisos.

**Solución:**
1. Eliminar `venv/` manualmente
2. Ejecutar `install.bat` nuevamente

### Error: "No se pudo crear la base de datos tras multiples intentos"

**Causa:** Permisos insuficientes o espacio en disco.

**Solución:**
1. Verificar permisos de escritura
2. Verificar espacio en disco
3. Ejecutar como Administrador si es necesario

### Error: "ERROR CRITICO: No se pudo agregar la columna activo"

**Causa:** Base de datos corrupta o esquema incompatible.

**Solución:**
1. Hacer backup de `gimnasio.db` si contiene datos importantes
2. Eliminar `gimnasio.db`
3. Ejecutar `install.bat` para recrear
4. O ejecutar manualmente:
   ```batch
   venv\Scripts\activate
   python verify_columns.py
   ```

### Error: "Fallo al iniciar con flask run"

**Causa:** Puerto ocupado, dependencias faltantes, o error en código.

**Solución:**
1. Verificar que puerto 5000 esté libre:
   ```batch
   netstat -ano | findstr :5000
   ```
2. Verificar dependencias:
   ```batch
   venv\Scripts\activate
   pip list
   ```
3. Verificar logs de error en consola
4. El script intentará `python app.py` automáticamente

### Puerto 5000 Ocupado

**Solución:**
1. Cambiar puerto en línea 145:
   ```batch
   flask run --host=0.0.0.0 --port=8080
   ```
2. O cerrar aplicación que usa el puerto

### Advertencias: "Error setting up date handling"

**Causa:** Configuración de locale no disponible en el sistema.

**Solución:** **IGNORAR** - Son advertencias inofensivas. La aplicación funciona correctamente.

## 8. Notas Técnicas

### Por qué múltiples métodos para la base de datos

Diferentes escenarios requieren diferentes enfoques:
- `fix_db.py`: Reparación general
- `create_db.py`: Creación con SQLAlchemy (recomendado)
- `create_tables.py`: Creación manual (último recurso)

### Sincronización de modelos

La copia de `models.py` a `app/models.py` sugiere que la aplicación puede haber usado blueprints en el pasado, o que algunos imports esperan la estructura `app/models.py`.

### Caché de Python

La limpieza de `__pycache__` asegura que cambios en código se reflejen inmediatamente sin reiniciar.

### Variables de entorno

Las variables pueden definirse antes de ejecutar el script para sobrescribir valores por defecto:
```batch
set NOTIFICATION_PHONE_NUMBER=+1234567890
start.bat
```

### Modo Desarrollo vs Producción

`FLASK_ENV=development` habilita:
- Auto-reload en cambios de código
- Debug mode (stack traces detallados)
- Mejor para desarrollo

**⚠️ Para producción:** Cambiar a `production` y usar servidor WSGI como Gunicorn.

---

**Documentación generada usando herramientas MCP para precisión técnica y análisis línea por línea.**

