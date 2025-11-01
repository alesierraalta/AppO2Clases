# Requisitos Técnicos - AppO2Clases

## 1. Versiones de Python Compatibles

### Tabla de Compatibilidad 100%

| Versión Python | Compatibilidad | Notas |
|----------------|----------------|-------|
| **Python 3.8** | ✅ 100% Compatible | Versión mínima soportada |
| **Python 3.9** | ✅ 100% Compatible | **RECOMENDADA** - Más estable y probada |
| **Python 3.10** | ✅ 100% Compatible | Compatible, probada |
| **Python 3.11** | ✅ 100% Compatible | Compatible, última versión estable |
| **Python 3.7** | ❌ No Compatible | librosa 0.11.0 requiere Python 3.8+ |
| **Python < 3.8** | ❌ No Compatible | No soportado |

### Restricciones por Librería

La versión mínima está determinada por **librosa 0.11.0**, que requiere Python 3.8 o superior.

| Librería | Versión | Python Mínimo | Python Máximo Probado |
|----------|---------|---------------|----------------------|
| Flask | 2.0.1 | 3.7+ | 3.11+ |
| SQLAlchemy | 1.4.23 | 3.6+ | 3.11+ |
| **librosa** | **0.11.0** | **3.8+** ⚠️ | **3.11+** |
| Flask-SQLAlchemy | 2.5.1 | 3.7+ | 3.11+ |
| NumPy | (sin versión fija) | 3.7+ | 3.11+ |
| Pandas | (sin versión fija) | 3.7+ | 3.11+ |
| Matplotlib | 3.10.1 | 3.8+ | 3.11+ |
| ReportLab | 3.6.9 | 3.6+ | 3.11+ |

### Recomendación

**Python 3.9.x** es la versión más recomendada porque:
- Estable y ampliamente probada
- Compatible con todas las dependencias
- Buen balance entre características y estabilidad
- Soporte extendido hasta 2025

## 2. Librerías y Dependencias

### Listado Técnico Completo (requirements.txt)

Todas las librerías listadas aquí se instalan automáticamente al ejecutar `install.bat`.

#### Framework Web
```
Flask==2.0.1
Flask-SQLAlchemy==2.5.1
Flask-Login==0.5.0
Werkzeug==2.0.1
```

**Propósito:**
- **Flask**: Framework web principal
- **Flask-SQLAlchemy**: Integración ORM con Flask
- **Flask-Login**: Autenticación de usuarios (si se implementa)
- **Werkzeug**: WSGI toolkit (incluido con Flask)

#### Base de Datos y ORM
```
SQLAlchemy==1.4.23
```

**Propósito:**
- ORM para abstracción de base de datos
- Soporta SQLite (actual) y PostgreSQL (Supabase)
- Manejo de relaciones y queries complejas

#### Templates y Formularios
```
Jinja2==3.0.1
WTForms==2.3.3
flask-wtf==0.15.1
```

**Propósito:**
- **Jinja2**: Motor de templates
- **WTForms**: Validación de formularios
- **flask-wtf**: Integración WTForms con Flask + CSRF

#### Utilidades Core
```
click==8.0.1
cryptography==3.4.8
```

**Propósito:**
- **click**: CLI y argumentos de línea de comandos
- **cryptography**: Encriptación y seguridad

#### Procesamiento de Datos
```
numpy
pandas
```

**Propósito:**
- **NumPy**: Cálculos numéricos y arrays
- **Pandas**: Manipulación y análisis de datos
- Sin versión fija: se instalan versiones compatibles

#### Visualización y Gráficos
```
matplotlib==3.10.1
```

**Propósito:**
- Generación de gráficos para informes
- Visualización de métricas y tendencias

#### Procesamiento de Audio
```
librosa==0.11.0
```

**Propósito:**
- Análisis y procesamiento de archivos de audio
- Visualización de waveforms
- Análisis de características de audio

**⚠️ Requisito Crítico:** Esta librería requiere Python 3.8+ y puede tener dependencias adicionales en sistemas Windows (FFmpeg recomendado).

#### Generación de Reportes
```
reportlab==3.6.9
Pillow==10.0.0
```

**Propósito:**
- **ReportLab**: Generación de PDFs programáticamente
- **Pillow**: Procesamiento de imágenes (soporte para gráficos en PDFs)

#### Importación/Exportación
```
openpyxl==3.0.9
```

**Propósito:**
- Lectura y escritura de archivos Excel (.xlsx)
- Importación masiva de datos de asistencia

#### Programación y Notificaciones
```
APScheduler==3.9.1
pywhatkit==5.4
pyautogui==0.9.54
```

**Propósito:**
- **APScheduler**: Programación de tareas en segundo plano
- **pywhatkit**: Envío de notificaciones WhatsApp
- **pyautogui**: Automatización (usado por pywhatkit)

**Nota sobre pywhatkit:** Requiere tener WhatsApp Web abierto en el navegador. En producción, considerar alternativas más robustas.

### Dependencias Transitivas Importantes

Estas librerías se instalan automáticamente como dependencias de las librerías principales:

- **MarkupSafe**: Seguridad en templates Jinja2
- **itsdangerous**: Firmas criptográficas (sessions, tokens)
- **greenlet**: Concurrencia para SQLAlchemy
- **typing-extensions**: Tipos para Python < 3.8 (compatibilidad)
- **scipy**: Dependencia de librosa (análisis científico)
- **soundfile**: Dependencia de librosa (lectura de archivos de audio)
- **resampy**: Dependencia de librosa (resampling de audio)

## 3. Compatibilidad Cruzada

### Matriz de Compatibilidad

Todas las versiones especificadas en `requirements.txt` han sido probadas juntas y son compatibles entre sí:

| Grupo | Compatibilidad | Notas |
|-------|----------------|-------|
| Flask 2.0.1 + Flask-SQLAlchemy 2.5.1 + SQLAlchemy 1.4.23 | ✅ | Versiones probadas juntas |
| librosa 0.11.0 + NumPy + Pandas | ✅ | Requiere NumPy >= 1.19.0 |
| Matplotlib 3.10.1 + ReportLab 3.6.9 | ✅ | Compatibles, usados juntos en PDFs |
| APScheduler 3.9.1 + Flask 2.0.1 | ✅ | Integración probada |
| WTForms 2.3.3 + flask-wtf 0.15.1 | ✅ | Versiones compatibles |

### Conflictos Conocidos

No se conocen conflictos entre las versiones especificadas en `requirements.txt`. Todas las versiones han sido seleccionadas específicamente para garantizar compatibilidad.

### Actualizaciones de Versiones

**⚠️ Advertencia:** No actualizar librerías sin verificar compatibilidad:

1. **Flask 2.0.1 → 2.3+**: Puede requerir cambios en código (deprecations)
2. **SQLAlchemy 1.4.23 → 2.0+**: Cambios breaking significativos en API
3. **librosa 0.11.0 → 0.12+**: Verificar compatibilidad de NumPy
4. **Matplotlib 3.10.1 → 4.0+**: Cambios en API pueden afectar código

## 4. Requisitos del Sistema

### Sistema Operativo

- **Windows 10/11**: Probado y soportado (scripts `.bat`)
- **Linux**: Compatible (usar `install.sh` y `start.sh`)
- **macOS**: Compatible teóricamente (no probado)

### Espacio en Disco

- **Mínimo**: 500 MB (Python + dependencias)
- **Recomendado**: 2 GB (espacio para base de datos, audios, backups)

### Memoria RAM

- **Mínimo**: 2 GB
- **Recomendado**: 4 GB o más
- **Nota**: librosa y procesamiento de audio pueden ser intensivos en memoria

### Procesador

- **Mínimo**: Procesador moderno (2015+)
- **Recomendado**: CPU con múltiples núcleos (mejor rendimiento en cálculos)

### Dependencias del Sistema (Opcionales pero Recomendadas)

#### Windows
- **Visual C++ Redistributable**: Requerido para algunas extensiones de Python
- **FFmpeg**: Recomendado para mejor procesamiento de audio con librosa
  - Descarga: https://ffmpeg.org/download.html
  - Agregar al PATH del sistema

#### Linux
- **build-essential**: Para compilar extensiones
  ```bash
  sudo apt-get install build-essential
  ```
- **ffmpeg**: Para procesamiento de audio
  ```bash
  sudo apt-get install ffmpeg
  ```
- **python3-dev**: Headers de Python para compilación
  ```bash
  sudo apt-get install python3-dev
  ```

### Navegador Web

La aplicación es una web app, requiere navegador moderno:

- **Chrome/Edge**: Versión 90+ (recomendado)
- **Firefox**: Versión 88+
- **Safari**: Versión 14+

**Características requeridas:**
- JavaScript habilitado
- Soporte para HTML5
- Cookies habilitadas (para sesiones)

### Puertos de Red

- **Puerto 5000**: Puerto por defecto del servidor Flask
  - Configurable en `start.bat` (variable `--port`)
  - Asegurar que esté disponible en el firewall

### Permisos

- **Lectura/Escritura**: En el directorio de la aplicación
- **Creación de directorios**: Para `venv/`, `logs/`, `backups/`, `static/uploads/`

## 5. Instalación de Dependencias

### Método Automático (Recomendado)

Ejecutar `install.bat` (Windows) o `install.sh` (Linux/macOS):

```batch
install.bat
```

Este script:
1. Verifica Python 3.8+
2. Crea entorno virtual (`venv/`)
3. Actualiza pip
4. Instala todas las dependencias de `requirements.txt`
5. Crea estructura de directorios necesaria

### Método Manual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Verificación de Instalación

```bash
# Verificar Python
python --version  # Debe mostrar 3.8, 3.9, 3.10 o 3.11

# Verificar Flask
python -c "import flask; print(flask.__version__)"  # Debe mostrar 2.0.1

# Verificar SQLAlchemy
python -c "import sqlalchemy; print(sqlalchemy.__version__)"  # Debe mostrar 1.4.23

# Verificar librosa
python -c "import librosa; print(librosa.__version__)"  # Debe mostrar 0.11.0
```

## 6. Solución de Problemas Comunes

### Error: "librosa requires Python 3.8+"

**Causa:** Versión de Python inferior a 3.8.

**Solución:** Instalar Python 3.8 o superior desde https://www.python.org/downloads/

### Error: "Microsoft Visual C++ 14.0 is required"

**Causa:** Faltan compiladores de C++ en Windows.

**Solución:** Instalar "Microsoft C++ Build Tools" desde https://visualstudio.microsoft.com/downloads/

### Error: "No module named 'numpy'"

**Causa:** Entorno virtual no activado o dependencias no instaladas.

**Solución:**
```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows
# o
source venv/bin/activate  # Linux/macOS

# Reinstalar dependencias
pip install -r requirements.txt
```

### Error al instalar librosa en Windows

**Causa:** librosa requiere compilación de extensiones C.

**Solución:**
1. Instalar Visual Studio Build Tools
2. O usar pre-compilados: `pip install librosa --only-binary :all:`

---

**Documentación generada usando herramientas MCP para precisión técnica y verificación de compatibilidades.**

