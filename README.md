# Sistema de Gestión de Clases

Este sistema permite gestionar clases, horarios, profesores y asistencias para un gimnasio o centro deportivo.

## Características

- Gestión de profesores y sus datos de contacto
- Configuración de horarios semanales por tipo de clase
- Registro de asistencia de clases con control de puntualidad
- Registro de audio para las clases
- Informes mensuales y por períodos específicos
- Exportación de datos a Excel
- Envío de notificaciones automáticas

## Últimas Actualizaciones

### Fecha de Desactivación para Horarios

Ahora se puede especificar una fecha exacta desde la cual un horario queda inactivo. Esto permite:

- Mantener los registros históricos de horarios inactivos para fechas pasadas
- Mostrar correctamente en informes las clases realizadas antes de la desactivación
- Filtrar automáticamente clases basadas en su fecha de desactivación

#### Cómo usar esta función:

1. Al desactivar un horario, el sistema ahora pedirá una fecha de desactivación
2. Las clases realizadas antes de esa fecha seguirán apareciendo en los informes
3. El sistema mostrará en los listados la fecha desde la que cada horario está inactivo
4. Los informes de períodos anteriores a la fecha de desactivación incluirán estas clases
5. Al reactivar un horario, la fecha de desactivación se elimina automáticamente

Esta función es especialmente útil para mantener un historial preciso cuando se cambian clases o profesores, sin perder información histórica de asistencia y métricas.

# ClasesO2 
Un sistema completo de gestión para academias de fitness y gimnasios. 
ECHO is off.
## Características 
- Gestión de horarios de clases 
- Control de asistencia de profesores 
- Registro de alumnos en clases 
- Informes y estadísticas 
- Importación/exportación de datos 
ECHO is off.
## Instalación 
1. Clonar el repositorio 
2. Ejecutar run.bat para instalar dependencias e iniciar la aplicación 
# ClasesV2O2

## Solución a errores comunes

### Error: "no such column: horario_clase.activo"

Si encuentras el siguiente error:

```
Error: (sqlite3.OperationalError) no such column: horario_clase.activo [SQL: SELECT horario_clase.id AS horario_clase_id, horario_clase.nombre AS horario_clase_nombre, horario_clase.dia_semana AS horario_clase_dia_semana, horario_clase.hora_inicio AS horario_clase_hora_inicio, horario_clase.duracion AS horario_clase_duracion, horario_clase.profesor_id AS horario_clase_profesor_id, horario_clase.fecha_creacion AS horario_clase_fecha_creacion, horario_clase.capacidad_maxima AS horario_clase_capacidad_maxima, horario_clase.tipo_clase AS horario_clase_tipo_clase, horario_clase.activo AS horario_clase_activo, horario_clase.fecha_desactivacion AS horario_clase_fecha_desactivacion FROM horario_clase WHERE horario_clase.dia_semana = ? ORDER BY horario_clase.hora_inicio] [parameters: (2,)]
```

Puedes solucionarlo fácilmente ejecutando el script de corrección automática:

```
fix_activo_column.bat
```

Este script:
1. Detiene cualquier proceso de Python en ejecución
2. Limpia el caché de Python
3. Verifica y añade la columna 'activo' a la base de datos si es necesario
4. Sincroniza los archivos de modelos
5. Reinicia la aplicación

Si prefieres solucionar el problema manualmente, puedes:

1. Ejecutar `python sincronizar_modelos.py`
2. O asegurarte de que el archivo `app/models.py` incluya las columnas `activo` y `fecha_desactivacion` en el modelo HorarioClase
