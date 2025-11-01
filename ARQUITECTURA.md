# Arquitectura de la Aplicación AppO2Clases

## 1. Introducción

AppO2Clases es un sistema completo de gestión para academias de fitness y gimnasios desarrollado en **Flask** (Python). La aplicación gestiona profesores, horarios de clases, registro de asistencia, métricas de rendimiento y generación de informes.

**Tecnologías Principales:**
- Backend: Flask 2.0.1
- Base de Datos: SQLite (con opción Supabase para SQL externo)
- ORM: SQLAlchemy 1.4.23
- Procesamiento: NumPy, Pandas, librosa (audio)
- Reportes: ReportLab, Matplotlib

## 2. Arquitectura General

La aplicación sigue un patrón **MVC (Modelo-Vista-Controlador)** adaptado para Flask:

```
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                │
│  Templates (Jinja2) + CSS + JavaScript                 │
│  - Base HTML                                            │
│  - Formularios interactivos                             │
│  - Visualización de audio (waveform)                    │
└─────────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE CONTROL                      │
│  Flask Routes (app.py)                                  │
│  - Rutas de profesores                                  │
│  - Rutas de horarios                                    │
│  - Rutas de asistencia                                  │
│  - Rutas de informes                                    │
│  - Rutas de configuración                                │
└─────────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE LÓGICA                       │
│  Modelos + Utilidades + Servicios                      │
│  - models.py: Modelos ORM                                │
│  - utils/: Cálculos de métricas                         │
│  - notifications.py: Sistema de notificaciones           │
└─────────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE DATOS                        │
│  SQLite Database (gimnasio.db)                         │
│  - Tablas relacionales                                 │
│  - Índices para optimización                            │
└─────────────────────────────────────────────────────────┘
```

## 3. Componentes Principales

### 3.1 Backend (Flask)

**Archivo Principal:** `app.py`

**Configuración Clave:**
- Flask app con configuración UTF-8 para soporte internacional
- CSRF Protection deshabilitado (solo desarrollo)
- SQLAlchemy integrado con pool de conexiones
- Sistema de archivos estáticos y uploads (16MB max)

**Características:**
- Sistema de logging para depuración de importaciones
- Manejo de errores centralizado
- Filtros personalizados de Jinja2 (divmod)
- Configuración de notificaciones WhatsApp

### 3.2 Modelos de Datos

**Archivo:** `models.py`

#### 3.2.1 Profesor
```python
- id: Integer (PK)
- nombre: String(100)
- apellido: String(100)
- tarifa_por_clase: Float
- telefono: String(20)
- email: String(100)
```

**Relaciones:**
- Uno a muchos con `HorarioClase` (horarios)
- Uno a muchos con `ClaseRealizada` (clases realizadas)

**Métodos Principales:**
- `get_clases_periodo()`: Obtiene clases filtradas por periodo
- `calcular_metricas()`: Calcula métricas de rendimiento (con caché)
- `obtener_ranking_profesores()`: Genera ranking por tipo de métrica

#### 3.2.2 HorarioClase
```python
- id: Integer (PK)
- nombre: String(100)
- dia_semana: Integer (0=Lunes, 6=Domingo)
- hora_inicio: Time
- duracion: Integer (minutos, default 60)
- profesor_id: ForeignKey → Profesor
- fecha_creacion: DateTime
- capacidad_maxima: Integer (default 20)
- tipo_clase: String(20) (MOVE, RIDE, BOX, OTRO)
- activo: Boolean (default True)
- fecha_desactivacion: Date (nullable)
```

**Relaciones:**
- Muchos a uno con `Profesor`
- Uno a muchos con `ClaseRealizada`
- Uno a muchos con `EventoHorario` (historial)

**Propiedades:**
- `nombre_dia`: Nombre del día en español
- `hora_fin_str`: Hora de finalización calculada
- `ultimo_evento`: Último evento registrado
- `historial_estados`: Historial cronológico de eventos

#### 3.2.3 ClaseRealizada
```python
- id: Integer (PK)
- fecha: Date
- horario_id: ForeignKey → HorarioClase
- profesor_id: ForeignKey → Profesor
- hora_llegada_profesor: Time (nullable)
- cantidad_alumnos: Integer (default 0)
- observaciones: Text
- fecha_registro: DateTime (default now)
- audio_file: String(255) (nullable)
```

**Propiedades:**
- `estado`: "Pendiente" o "Realizada"
- `puntualidad`: "Puntual", "Retraso leve", "Retraso significativo"
- `minutos_diferencia`: Diferencia en minutos vs horario programado

#### 3.2.4 EventoHorario
**Patrón: Event Sourcing**

```python
- id: Integer (PK)
- horario_id: ForeignKey → HorarioClase
- tipo: Enum (CREACION, MODIFICACION)
- fecha: DateTime (UTC)
- fecha_aplicacion: Date (nullable)
- motivo: String(255)
- datos_adicionales: JSON
```

Este modelo implementa **Event Sourcing** para mantener un historial completo y auditado de todos los cambios en horarios, permitiendo:
- Reconstrucción del estado histórico
- Trazabilidad completa
- Análisis de cambios temporales

### 3.3 Rutas y Controladores

**Organización por Módulos Funcionales:**

#### Rutas de Profesores (`/profesores`)
- `GET /profesores`: Lista todos los profesores
- `GET|POST /profesores/nuevo`: Crear nuevo profesor
- `GET|POST /profesores/editar/<id>`: Editar profesor
- `POST /profesores/eliminar/<id>`: Eliminar profesor
- `POST /profesores/eliminar-varios`: Eliminación masiva

#### Rutas de Horarios (`/horarios`)
- `GET /horarios`: Lista horarios activos
- `GET|POST /horarios/nuevo`: Crear horario
- `GET|POST /horarios/editar/<id>`: Editar horario
- `POST /horarios/eliminar/<id>`: Eliminar horario
- `GET|POST /horarios/confirmar-eliminar/<id>`: Confirmación
- `POST /horarios/desactivar/<id>`: Desactivar horario
- `POST /horarios/activar/<id>`: Reactivar horario

#### Rutas de Asistencia (`/asistencia`)
- `GET /asistencia`: Panel de control del día actual
- `GET|POST /asistencia/registrar/<horario_id>`: Registrar asistencia
- `GET|POST /asistencia/editar/<id>`: Editar registro
- `POST /asistencia/eliminar/<id>`: Eliminar registro
- `GET /asistencia/historial`: Historial completo
- `GET /asistencia/clases-no-registradas`: Clases pendientes
- `POST /asistencia/upload_audio/<horario_id>`: Subir audio
- `GET /asistencia/get_audio/<horario_id>`: Obtener audio
- `POST /asistencia/registrar-clases-masivo`: Registro masivo

#### Rutas de Informes (`/informes`)
- `GET /informes`: Página principal de informes
- `GET /informes/clases`: Lista de clases
- `GET /informes/clase/<nombre>/metricas`: Métricas por clase
- `GET|POST /informes/mensual`: Reporte mensual
- `POST /informes/mensual/pdf-with-charts`: Generar PDF
- `GET /informes/profesor/<id>/metricas`: Métricas por profesor

#### Rutas de Importación (`/importar`)
- `GET|POST /importar/asistencia`: Importar desde Excel
- `GET /importar`: Página principal de importación

#### Rutas de Configuración (`/configuracion`)
- `GET|POST /configuracion/notificaciones`: Configurar notificaciones
- `GET|POST /configuracion/exportar`: Exportar datos
- `GET /configuracion/exportar_db`: Exportar base de datos
- `POST /configuracion/importar_db`: Importar base de datos

#### Rutas de Mantenimiento (`/mantenimiento`)
- `GET /mantenimiento/depurar-base-datos`: Depuración
- `POST /mantenimiento/fix-dates`: Corregir fechas

### 3.4 Servicios y Utilidades

#### 3.4.1 Sistema de Métricas (`utils/metricas_profesores.py`)

**Funciones Principales:**
- `calcular_tasa_puntualidad()`: Tasa de puntualidad con categorías
- `calcular_distribucion_tipos()`: Distribución por tipo de clase
- `calcular_tendencia_mensual()`: Análisis de tendencias temporales
- `calcular_metricas_profesor()`: Métricas completas agregadas

**Características:**
- Uso de NumPy para cálculos eficientes
- Análisis de tendencias con datos mensuales
- Caché de resultados para optimización

#### 3.4.2 Generador de PDFs (`utils/pdf_generator.py`)

**Características:**
- Generación con ReportLab
- Diseño basado en iOS Design System
- Caché de datos para optimización
- Soporte para gráficos y tablas complejas

#### 3.4.3 Sistema de Notificaciones (`notifications.py`)

**Componentes:**
- **APScheduler**: Programación de tareas en segundo plano
- **PyWhatKit**: Envío de mensajes WhatsApp
- **Sistema de bloqueo**: Previene spam accidental

**Configuración:**
- Horarios predeterminados: 13:30 y 20:30
- Verificación de clases no registradas
- Notificaciones automáticas programadas

## 4. Base de Datos

### 4.1 Esquema (SQLite)

**Base de Datos:** `gimnasio.db`

**Tablas Principales:**

```
profesor
├── id (PK)
├── nombre
├── apellido
├── tarifa_por_clase
├── telefono
├── email
└── [relaciones: horarios, clases_realizadas]

horario_clase
├── id (PK)
├── nombre
├── dia_semana (0-6)
├── hora_inicio
├── duracion
├── profesor_id (FK → profesor.id)
├── fecha_creacion
├── capacidad_maxima
├── tipo_clase
├── activo
├── fecha_desactivacion
└── [relaciones: clases_realizadas, eventos]

clase_realizada
├── id (PK)
├── fecha
├── horario_id (FK → horario_clase.id)
├── profesor_id (FK → profesor.id)
├── hora_llegada_profesor
├── cantidad_alumnos
├── observaciones
├── fecha_registro
└── audio_file

evento_horario
├── id (PK)
├── horario_id (FK → horario_clase.id)
├── tipo (CREACION, MODIFICACION)
├── fecha (UTC)
├── fecha_aplicacion
├── motivo
└── datos_adicionales (JSON)
```

### 4.2 Relaciones entre Modelos

```
Profesor (1) ────< (N) HorarioClase
   │                      │
   │                      │
   └───< (N) ClaseRealizada >───┘
                      │
                      │
            HorarioClase (1) ────< (N) EventoHorario
```

**Relaciones SQLAlchemy:**
- `Profesor.horarios`: Lista de horarios del profesor
- `Profesor.clases_realizadas`: Lista de clases realizadas
- `HorarioClase.profesor`: Profesor asignado (backref)
- `HorarioClase.clases_realizadas`: Clases realizadas del horario
- `HorarioClase.eventos`: Historial de eventos (Event Sourcing)
- `ClaseRealizada.horario`: Horario asociado (backref)
- `ClaseRealizada.profesor`: Profesor de la clase (backref)

### 4.3 Opción Supabase (Futuro)

La aplicación actualmente utiliza **SQLite** como base de datos local. Para escenarios que requieran:

- **Base de datos SQL externa**
- **Acceso remoto**
- **Escalabilidad horizontal**
- **Backup automatizado en la nube**
- **Colaboración multi-usuario en tiempo real**

Se puede migrar a **Supabase** (PostgreSQL), que ofrece:

- API REST y GraphQL automática
- Autenticación integrada
- Tiempo real con suscripciones
- Almacenamiento de archivos
- Funciones Edge (serverless)

**Nota:** La migración requeriría cambiar la URI de conexión de SQLite a PostgreSQL y ajustar algunas consultas específicas de SQLite, pero SQLAlchemy facilita este proceso al ser agnóstico de base de datos.

## 5. Flujo de Datos

### 5.1 Registro de Asistencia

```
Usuario → Interfaz Web
    ↓
Flask Route: /asistencia/registrar/<horario_id>
    ↓
Validación de datos (CSRF, formato)
    ↓
Crear/Actualizar ClaseRealizada
    ↓
SQLAlchemy ORM → SQLite
    ↓
Procesar audio (si existe)
    ↓
Almacenar archivo en static/uploads/audios/permanent/
    ↓
Actualizar caché de métricas
    ↓
Respuesta JSON/HTML
    ↓
Usuario ve confirmación
```

### 5.2 Generación de Informes

```
Usuario → /informes/mensual
    ↓
Selección de periodo (GET/POST)
    ↓
Consultar ClaseRealizada con filtros
    ↓
Calcular métricas (utils/metricas_profesores.py)
    ↓
Generar gráficos (Matplotlib)
    ↓
Generar PDF (utils/pdf_generator.py)
    ↓
Retornar PDF o mostrar HTML
    ↓
Usuario descarga/visualiza informe
```

### 5.3 Sistema de Notificaciones

```
APScheduler (background thread)
    ↓
Verificar horarios del día
    ↓
Identificar clases no registradas
    ↓
Enviar notificación WhatsApp (PyWhatKit)
    ↓
Registrar en log (notifications.log)
    ↓
Aplicar bloqueo temporal (anti-spam)
```

## 6. Patrones de Diseño

### 6.1 ORM (Object-Relational Mapping)
SQLAlchemy mapea objetos Python a tablas SQL, proporcionando:
- Abstracción de base de datos
- Relaciones tipo-safe
- Queries expresivas

### 6.2 MVC (Model-View-Controller)
Separación clara de responsabilidades:
- **Modelos**: Lógica de datos (`models.py`)
- **Vistas**: Templates Jinja2 (`templates/`)
- **Controladores**: Rutas Flask (`app.py`)

### 6.3 Event Sourcing
El modelo `EventoHorario` implementa Event Sourcing:
- Historial inmutable de cambios
- Reconstrucción de estado histórico
- Auditoría completa

### 6.4 Decorador de Caché
`@cache_metrics` en `models.py`:
- Caché en memoria para cálculos intensivos
- TTL configurable (3600 segundos)
- Invalidación selectiva

### 6.5 Factory Pattern (PDF Generator)
`PDFDataCache` y generadores modulares:
- Separación de creación y uso
- Reutilización de componentes

### 6.6 Singleton (Scheduler)
El scheduler de notificaciones:
- Instancia única global
- Inicialización lazy
- Thread-safe

## 7. Estructura de Directorios

```
AppO2Clases/
│
├── app.py                    # Aplicación Flask principal
├── models.py                 # Modelos de datos ORM
├── notifications.py          # Sistema de notificaciones
├── requirements.txt          # Dependencias Python
├── install.bat               # Script de instalación Windows
├── start.bat                  # Script de inicio Windows
│
├── app/
│   └── models.py             # Copia sincronizada de models.py
│
├── utils/
│   ├── metricas_profesores.py    # Cálculo de métricas
│   ├── metricas_clases.py         # Métricas por clase
│   └── pdf_generator.py            # Generación de PDFs
│
├── static/
│   ├── css/                  # Estilos (dark-mode, themes)
│   ├── js/                   # JavaScript (audio controls)
│   ├── img/                  # Logos e imágenes
│   ├── audio/                # Audios por defecto
│   └── uploads/
│       └── audios/
│           └── permanent/    # Audios subidos por horario
│
├── templates/
│   ├── base.html             # Template base
│   ├── index.html            # Página principal
│   ├── profesores/           # Templates de profesores
│   ├── horarios/             # Templates de horarios
│   ├── asistencia/           # Templates de asistencia
│   ├── informes/             # Templates de informes
│   ├── configuracion/        # Templates de configuración
│   └── importar/             # Templates de importación
│
├── logs/                     # Archivos de log
├── backups/                  # Backups de base de datos
└── gimnasio.db               # Base de datos SQLite
```

## 8. Consideraciones de Escalabilidad

### 8.1 Optimizaciones Actuales

1. **Caché de Métricas**: Reduce cálculos repetitivos
2. **Índices de Base de Datos**: Optimización de queries
3. **Lazy Loading**: Carga bajo demanda de relaciones
4. **Pool de Conexiones**: Reutilización de conexiones DB

### 8.2 Posibles Mejoras

1. **Migración a PostgreSQL (Supabase)**:
   - Mejor rendimiento en alta concurrencia
   - Escalabilidad horizontal
   - Replicación automática

2. **Caché Distribuido (Redis)**:
   - Caché compartido entre instancias
   - TTL más sofisticado
   - Invalidación eficiente

3. **CDN para Assets**:
   - Servir archivos estáticos desde CDN
   - Reducir carga del servidor Flask

4. **Background Workers**:
   - Procesar generación de PDFs en cola
   - Notificaciones asíncronas
   - Tareas pesadas fuera del request cycle

5. **API REST Separada**:
   - Separar lógica de negocio
   - Frontend independiente (React/Vue)
   - Mobile apps nativas

6. **Microservicios**:
   - Servicio de métricas independiente
   - Servicio de notificaciones
   - Servicio de reportes

### 8.3 Limitaciones Actuales

- **SQLite**: No recomendado para alta concurrencia (>100 usuarios simultáneos)
- **Single-threaded**: Flask en modo desarrollo no es óptimo para producción
- **Sin Load Balancer**: Una sola instancia

### 8.4 Recomendaciones para Producción

1. Usar **Gunicorn** o **uWSGI** con múltiples workers
2. **Nginx** como reverse proxy
3. **PostgreSQL** en lugar de SQLite
4. **Redis** para sesiones y caché
5. **Monitoreo** con herramientas como Prometheus
6. **Logs centralizados** (ELK Stack)

---

**Documentación generada usando herramientas MCP para precisión técnica y optimización de tokens.**

