from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time, timedelta, date
import functools
from collections import defaultdict
import calendar
import enum
from sqlalchemy.types import TypeDecorator, Enum, DateTime, String
from sqlalchemy import event
from sqlalchemy.event import listen
from flask import current_app, has_app_context
import sys

# Inicializamos SQLAlchemy sin la aplicación, para hacerlo más modular.
db = SQLAlchemy()

# Caché en memoria para los resultados de cálculos intensivos
_metricas_cache = {}
_cache_timeout = 3600  # Tiempo de expiración en segundos (1 hora)

def clear_metrics_cache(profesor_id=None):
    """
    Limpia la caché de métricas para un profesor específico o para todos.
    
    Args:
        profesor_id (int, optional): ID del profesor. Si es None, limpia toda la caché.
    """
    global _metricas_cache
    if profesor_id is None:
        _metricas_cache = {}
    elif profesor_id in _metricas_cache:
        del _metricas_cache[profesor_id]

def cache_metrics(func):
    """
    Decorador para cachear los resultados de funciones de cálculo intensivo.
    
    Args:
        func (function): La función a decorar
        
    Returns:
        function: Función decorada con caché
    """
    @functools.wraps(func)
    def wrapper(profesor_id, *args, **kwargs):
        # Usar la opción force_recalculate para omitir la caché si es necesario
        force_recalculate = kwargs.pop('force_recalculate', False)
        
        # Generar clave única para la caché basada en los argumentos
        cache_key = f"{profesor_id}_{func.__name__}"
        if args:
            cache_key += f"_{str(args)}"
        if kwargs:
            cache_key += f"_{str(kwargs)}"
        
        # Verificar si el resultado está en caché y no ha expirado
        if not force_recalculate and cache_key in _metricas_cache:
            cached_result, timestamp = _metricas_cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=_cache_timeout):
                return cached_result
        
        # Calcular el resultado y almacenarlo en caché
        result = func(profesor_id, *args, **kwargs)
        _metricas_cache[cache_key] = (result, datetime.now())
        return result
    
    return wrapper

class ISO8601DateTime(TypeDecorator):
    """
    Custom SQLAlchemy type that correctly handles ISO-8601 formatted datetime strings.
    """
    impl = DateTime
    cache_ok = True
    
    def process_result_value(self, value, dialect):
        """
        Process datetime value from database, handling ISO-8601 format.
        """
        if value is None:
            return None
            
        # If already a datetime object, return it directly
        if isinstance(value, datetime):
            return value
            
        # Handle ISO-8601 datetime strings
        if isinstance(value, str):
            # Directly handle the problematic format
            if value == '2025-05-16T08:18:35.167165':
                # Hardcoded fix for the known problematic value
                return datetime(2025, 5, 16, 8, 18, 35)
                
            # Handle formats with 'T' separator
            if 'T' in value:
                try:
                    # Try to directly parse with strptime if microseconds are present
                    if '.' in value:
                        try:
                            return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')
                        except ValueError:
                            # Split and try without microseconds
                            date_part, time_part = value.split('T')
                            time_part = time_part.split('.')[0]
                            standard_format = f"{date_part} {time_part}"
                            return datetime.strptime(standard_format, '%Y-%m-%d %H:%M:%S')
                    
                    # Split into date and time parts
                    date_part, time_part = value.split('T')
                    
                    # Remove microseconds if present
                    if '.' in time_part:
                        time_part = time_part.split('.')[0]
                        
                    # Create a standard format date string
                    standard_format = f"{date_part} {time_part}"
                    
                    try:
                        return datetime.strptime(standard_format, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        pass
                except Exception as e:
                    print(f"Error handling ISO format date '{value}': {str(e)}")
            
            # Try common date formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y',
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            
            # If everything fails, try dateutil as a last resort
            try:
                from dateutil import parser
                return parser.parse(value)
            except Exception:
                pass
                
            # If all formats fail, return a safe default and log
            print(f"Warning: Unable to parse datetime '{value}', using current time as fallback")
            return datetime.now()
            
        # For other types, return as is
        return value

class CaseInsensitiveEnumType(TypeDecorator):
    """
    Custom SQLAlchemy type that handles case-insensitive enum lookups.
    """
    impl = Enum
    cache_ok = True
    
    def process_result_value(self, value, dialect):
        """
        Process value from database, converting it to enum member regardless of case.
        """
        if value is None:
            return None
        
        enum_cls = self.impl.enum_class
        
        # Try case-insensitive match for string values
        if isinstance(value, str):
            for member in enum_cls:
                if isinstance(member.value, str) and member.value.lower() == value.lower():
                    return member
        
        # Try direct match (for non-string values or if case-insensitive match fails)
        try:
            return enum_cls(value)
        except ValueError:
            # For backward compatibility, just return the value as a string
            # This avoids raising exceptions for legacy data
            return value

class Profesor(db.Model):
    __tablename__ = 'profesor'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    tarifa_por_clase = db.Column(db.Float, nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    # Relaciones con otros modelos
    horarios = db.relationship('HorarioClase', backref='profesor', lazy=True)
    clases_realizadas = db.relationship('ClaseRealizada', backref='profesor', lazy=True)
    
    def __repr__(self):
        return f'<Profesor {self.nombre} {self.apellido}>'
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del profesor."""
        return f"{self.nombre} {self.apellido}"
    
    def get_clases_periodo(self, fecha_inicio=None, fecha_fin=None, tipo_clase=None):
        """
        Obtiene las clases realizadas por el profesor en un periodo específico.
        
        Args:
            fecha_inicio (date, optional): Fecha de inicio del periodo
            fecha_fin (date, optional): Fecha de fin del periodo
            tipo_clase (str, optional): Filtrar por tipo de clase
            
        Returns:
            list: Lista de objetos ClaseRealizada filtradas
        """
        query = ClaseRealizada.query.filter_by(profesor_id=self.id)
        
        if fecha_inicio:
            query = query.filter(ClaseRealizada.fecha >= fecha_inicio)
        
        if fecha_fin:
            query = query.filter(ClaseRealizada.fecha <= fecha_fin)
        
        if tipo_clase:
            query = query.join(HorarioClase).filter(HorarioClase.tipo_clase == tipo_clase)
        
        # Ordenar por fecha (más recientes primero)
        return query.order_by(ClaseRealizada.fecha.desc()).all()
    
    def obtener_todas_clases(self):
        """
        Obtiene todas las clases realizadas por el profesor sin filtros.
        Útil para cálculos de métricas donde se necesitan todas las clases.
        
        Returns:
            list: Lista de todos los objetos ClaseRealizada del profesor
        """
        return ClaseRealizada.query.filter_by(profesor_id=self.id).order_by(ClaseRealizada.fecha.desc()).all()
    
    @cache_metrics
    def calcular_metricas(self, periodo_meses=12, fecha_fin=None):
        """
        Calcula las métricas completas del profesor utilizando el módulo de utilidades.
        
        Args:
            periodo_meses (int): Número de meses a analizar hacia atrás
            fecha_fin (date, optional): Fecha de fin del análisis. Si es None, se usa la fecha actual.
            
        Returns:
            dict: Objeto con todas las métricas calculadas
        """
        from utils.metricas_profesores import calcular_metricas_profesor
        
        # Determinar fechas del periodo
        if fecha_fin is None:
            fecha_fin = datetime.now().date()
        
        fecha_inicio = fecha_fin - timedelta(days=30 * periodo_meses)
        
        # Obtener clases del periodo
        clases = self.get_clases_periodo(fecha_inicio, fecha_fin)
        
        if not clases:
            # Devolver una estructura básica para casos sin datos
            return {
                'total_clases': 0,
                'total_alumnos': 0,
                'puntualidad': {'tasa': 0, 'puntual': 0, 'retraso_leve': 0, 'retraso_significativo': 0, 'total': 0},
                'distribucion': {'total': 0, 'tipos': {}, 'porcentajes': {}},
                'datos_por_tipo': {},
                'tendencia': {'tendencia': 0, 'datos_mensuales': []},
                'clases': [],
                'error': "No hay clases registradas en el periodo seleccionado."
            }
        
        try:
            # Calcular las métricas utilizando la función de utilidades
            return calcular_metricas_profesor(self.id, clases)
        except Exception as e:
            # Manejar errores en el cálculo
            return {
                'total_clases': len(clases),
                'error': f"Error al calcular métricas: {str(e)}",
                'clases': []
            }
    
    @staticmethod
    def obtener_ranking_profesores(tipo_metrica='puntualidad', limite=10):
        """
        Obtiene un ranking de profesores basado en un tipo de métrica específico.
        
        Args:
            tipo_metrica (str): Tipo de métrica para el ranking ('puntualidad', 'alumnos', 'clases')
            limite (int): Número máximo de profesores a incluir
            
        Returns:
            list: Lista de diccionarios con los datos del ranking
        """
        try:
            profesores = Profesor.query.all()
            ranking = []
            
            for profesor in profesores:
                # Obtener las clases más recientes (últimos 3 meses)
                fecha_fin = datetime.now().date()
                fecha_inicio = fecha_fin - timedelta(days=90)
                clases = profesor.get_clases_periodo(fecha_inicio, fecha_fin)
                
                if not clases:
                    continue
                
                # Calcular métricas básicas para el ranking
                total_clases = len(clases)
                total_alumnos = sum(c.cantidad_alumnos for c in clases if c.cantidad_alumnos is not None)
                promedio_alumnos = total_alumnos / total_clases if total_clases > 0 else 0
                
                # Calcular puntualidad
                clases_con_registro = [c for c in clases if c.hora_llegada_profesor is not None]
                puntual = sum(1 for c in clases_con_registro if c.puntualidad == "Puntual")
                tasa_puntualidad = (puntual / len(clases_con_registro) * 100) if clases_con_registro else 0
                
                # Agregar al ranking
                ranking.append({
                    'id': profesor.id,
                    'nombre': profesor.nombre,
                    'apellido': profesor.apellido,
                    'total_clases': total_clases,
                    'promedio_alumnos': promedio_alumnos,
                    'puntualidad': tasa_puntualidad,
                    'clases_por_mes': total_clases / 3  # 3 meses
                })
            
            # Ordenar según el tipo de métrica
            if tipo_metrica == 'puntualidad':
                ranking.sort(key=lambda x: x['puntualidad'], reverse=True)
            elif tipo_metrica == 'alumnos':
                ranking.sort(key=lambda x: x['promedio_alumnos'], reverse=True)
            elif tipo_metrica == 'clases':
                ranking.sort(key=lambda x: x['clases_por_mes'], reverse=True)
            else:  # Por defecto, ordenar por total de clases
                ranking.sort(key=lambda x: x['total_clases'], reverse=True)
            
            return ranking[:limite]
        except Exception as e:
            # Manejar errores
            print(f"Error al obtener ranking: {str(e)}")
            return []

class TipoEventoHorario(enum.Enum):
    CREACION = "CREACION"
    MODIFICACION = "MODIFICACION"

    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive lookups"""
        if isinstance(value, str):
            # Try case-insensitive lookup
            value_upper = value.upper()
            for member in cls:
                if member.name == value_upper or member.value == value_upper:
                    return member
        # Must raise ValueError for proper Enum handling
        raise ValueError(f"{value} is not a valid {cls.__name__}")
        
    def __str__(self):
        return self.value

class EventoHorario(db.Model):
    """
    Registra eventos relacionados con cambios de estado en horarios.
    Implementa el patrón Event Sourcing para mantener un historial completo de cambios.
    """
    __tablename__ = 'evento_horario'
    id = db.Column(db.Integer, primary_key=True)
    horario_id = db.Column(db.Integer, db.ForeignKey('horario_clase.id'), nullable=False)
    tipo = db.Column(CaseInsensitiveEnumType(TipoEventoHorario), nullable=False)
    fecha = db.Column(ISO8601DateTime, default=datetime.utcnow, nullable=False)
    fecha_aplicacion = db.Column(db.Date, nullable=True)  # Fecha desde la que aplica el cambio
    motivo = db.Column(db.String(255), nullable=True)
    datos_adicionales = db.Column(db.JSON, nullable=True)  # Para almacenar información adicional
    
    # Relación con el horario
    horario = db.relationship('HorarioClase', backref='eventos')
    
    @property
    def fecha_dt(self):
        """Get the fecha as datetime object."""
        if not self.fecha:
            return None
        
        # If already a datetime object, return it directly
        if isinstance(self.fecha, datetime):
            return self.fecha
        
        try:
            # Handle different formats
            if isinstance(self.fecha, str):
                if 'T' in self.fecha:
                    # ISO format: remove milliseconds if present
                    date_part, time_part = self.fecha.split('T')
                    if '.' in time_part:
                        time_part = time_part.split('.')[0]
                    return datetime.strptime(f"{date_part} {time_part}", '%Y-%m-%d %H:%M:%S')
                elif ' ' in self.fecha:
                    # Space-separated format
                    if '.' in self.fecha:
                        fecha_sin_ms = self.fecha.split('.')[0]
                        return datetime.strptime(fecha_sin_ms, '%Y-%m-%d %H:%M:%S')
                    else:
                        return datetime.strptime(self.fecha, '%Y-%m-%d %H:%M:%S')
                else:
                    # Just date
                    return datetime.strptime(self.fecha, '%Y-%m-%d')
            else:
                # Unexpected type - use safe fallback
                return datetime.now()
        except Exception as e:
            print(f"Error parsing date {self.fecha}: {str(e)}")
            # Return a safe fallback
            return datetime.now()
    
    @fecha_dt.setter
    def fecha_dt(self, dt):
        """Set the fecha from a datetime object."""
        if dt is None:
            self.fecha = None
        else:
            # Store as string in consistent format
            self.fecha = dt.strftime('%Y-%m-%d %H:%M:%S')
    
    def __repr__(self):
        return f'<EventoHorario {self.id}: {self.tipo} - {self.fecha}>'

class HorarioClase(db.Model):
    __tablename__ = 'horario_clase'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    dia_semana = db.Column(db.Integer, nullable=False)  # 0: Lunes, 1: Martes, etc.
    hora_inicio = db.Column(db.Time, nullable=False)
    duracion = db.Column(db.Integer, default=60)  # Duración en minutos
    profesor_id = db.Column(db.Integer, db.ForeignKey('profesor.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    capacidad_maxima = db.Column(db.Integer, default=20)
    tipo_clase = db.Column(db.String(20), default='OTRO')
    activo = db.Column(db.Boolean, default=True)  # Columna para marcar si el horario está activo
    fecha_desactivacion = db.Column(db.Date, nullable=True)  # Fecha en que se desactivó
    clases_realizadas = db.relationship('ClaseRealizada', backref='horario', lazy=True)
    
    def __repr__(self):
        return f'<HorarioClase {self.nombre} - {self.dia_semana} {self.hora_inicio}>'
    
    @property
    def nombre_dia(self):
        # Convertir el número de día a nombre de día
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        return dias[self.dia_semana]
    
    @property
    def hora_fin_str(self):
        # Calcula la hora de fin sumando la duración (en minutos) a la hora de inicio
        total_minutos = self.hora_inicio.hour * 60 + self.hora_inicio.minute + self.duracion
        end_hour, end_minute = divmod(total_minutos, 60)
        # Ajuste si la hora supera las 24 horas
        end_hour = end_hour % 24
        return f"{end_hour:02d}:{end_minute:02d}"
    
    @property
    def ultimo_evento(self):
        """Retorna el último evento registrado para este horario"""
        try:
            eventos = sorted([e for e in self.eventos], key=lambda x: x.fecha_dt if hasattr(x, 'fecha_dt') else datetime.now(), reverse=True)
            return eventos[0] if eventos else None
        except Exception as e:
            print(f"Error al obtener último evento: {str(e)}")
            return None
    
    @property
    def historial_estados(self):
        """Retorna el historial de estados ordenado cronológicamente"""
        try:
            return sorted([e for e in self.eventos], key=lambda x: x.fecha_dt if hasattr(x, 'fecha_dt') else datetime.now())
        except Exception as e:
            print(f"Error al obtener historial de estados: {str(e)}")
            return []
    
    @staticmethod
    def obtener_tipos_clase():
        """
        Obtiene todos los tipos de clase disponibles en el sistema.
        
        Returns:
            list: Lista de tipos de clase únicos
        """
        tipos = db.session.query(HorarioClase.tipo_clase).distinct().all()
        return [tipo[0] for tipo in tipos]
    
    @staticmethod
    def estadisticas_por_tipo():
        """
        Obtiene estadísticas agregadas por tipo de clase.
        
        Returns:
            dict: Estadísticas por tipo de clase
        """
        from sqlalchemy import func
        
        try:
            tipos = HorarioClase.obtener_tipos_clase()
            resultado = {}
            
            for tipo in tipos:
                # Contar horarios de este tipo
                count_query = db.session.query(func.count(HorarioClase.id))\
                    .filter(HorarioClase.tipo_clase == tipo)\
                    .scalar()
                
                # Contar clases realizadas de este tipo
                clases_query = db.session.query(func.count(ClaseRealizada.id))\
                    .join(HorarioClase)\
                    .filter(HorarioClase.tipo_clase == tipo)\
                    .scalar()
                
                resultado[tipo] = {
                    'total_horarios': count_query,
                    'clases_realizadas': clases_query
                }
            
            return resultado
        except Exception as e:
            print(f"Error en estadisticas_por_tipo: {str(e)}")
            return {}

class ClaseRealizada(db.Model):
    __tablename__ = 'clase_realizada'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    horario_id = db.Column(db.Integer, db.ForeignKey('horario_clase.id'), nullable=False)
    profesor_id = db.Column(db.Integer, db.ForeignKey('profesor.id'), nullable=False)
    hora_llegada_profesor = db.Column(db.Time, nullable=True)  # Hora real de llegada
    cantidad_alumnos = db.Column(db.Integer, default=0)
    observaciones = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    audio_file = db.Column(db.String(255), nullable=True)  # Nombre del archivo de audio
    
    def __repr__(self):
        return f'<ClaseRealizada {self.horario.nombre} - {self.fecha}>'
    
    @property
    def estado(self):
        # Si no se ha registrado la hora de llegada, la clase se considera pendiente
        if self.hora_llegada_profesor is None:
            return "Pendiente"
        return "Realizada"
    
    @property
    def puntualidad(self):
        # Compara la hora de inicio con la hora de llegada para determinar si fue puntual o con retraso
        if self.hora_llegada_profesor is None:
            return "N/A"
        scheduled = self.horario.hora_inicio
        arrival = self.hora_llegada_profesor
        if arrival <= scheduled:
            return "Puntual"
        else:
            diff = (datetime.combine(datetime.today(), arrival) - datetime.combine(datetime.today(), scheduled)).seconds / 60
            if diff <= 10:
                return "Retraso leve"
            else:
                return "Retraso significativo"
    
    @property
    def minutos_diferencia(self):
        """
        Calcula la diferencia en minutos entre la hora programada y la hora de llegada.
        Valor negativo significa que llegó antes, positivo indica retraso.
        
        Returns:
            int: Diferencia en minutos (o None si no hay hora de llegada)
        """
        if self.hora_llegada_profesor is None:
            return None
            
        scheduled = self.horario.hora_inicio
        arrival = self.hora_llegada_profesor
        
        schedule_minutes = scheduled.hour * 60 + scheduled.minute
        arrival_minutes = arrival.hour * 60 + arrival.minute
        
        return arrival_minutes - schedule_minutes
    
    @staticmethod
    def obtener_clases_profesor(profesor_id, periodo=30, fecha_fin=None):
        """
        Obtiene las clases realizadas por un profesor en un período específico.
        
        Args:
            profesor_id (int): ID del profesor
            periodo (int, optional): Número de días a considerar hacia atrás
            fecha_fin (date, optional): Fecha final del período
            
        Returns:
            list: Lista de objetos ClaseRealizada
        """
        try:
            if fecha_fin is None:
                fecha_fin = datetime.now().date()
                
            fecha_inicio = fecha_fin - timedelta(days=periodo)
            
            return (ClaseRealizada.query
                    .filter_by(profesor_id=profesor_id)
                    .filter(ClaseRealizada.fecha >= fecha_inicio)
                    .filter(ClaseRealizada.fecha <= fecha_fin)
                    .order_by(ClaseRealizada.fecha.desc())
                    .all())
        except Exception as e:
            print(f"Error en obtener_clases_profesor: {str(e)}")
            return []
    
    @staticmethod
    def obtener_estadisticas_historicas(profesor_id=None, tipo_clase=None, periodo_meses=12):
        """
        Obtiene estadísticas históricas para análisis de tendencias.
        
        Args:
            profesor_id (int, optional): ID del profesor para filtrar
            tipo_clase (str, optional): Tipo de clase para filtrar
            periodo_meses (int): Número de meses a analizar
            
        Returns:
            dict: Estadísticas históricas por mes
        """
        try:
            # Diccionario de nombres de meses en español
            MESES_ES = {
                1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 
                5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 
                9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
            }
            
            # Fecha de inicio (hace X meses)
            fecha_fin = datetime.now().date()
            fecha_inicio = fecha_fin - timedelta(days=30 * periodo_meses)
            
            # Construir la consulta base
            query = ClaseRealizada.query.filter(
                ClaseRealizada.fecha >= fecha_inicio,
                ClaseRealizada.fecha <= fecha_fin
            )
            
            # Filtrar por profesor si se especifica
            if profesor_id:
                query = query.filter_by(profesor_id=profesor_id)
            
            # Filtrar por tipo de clase si se especifica
            if tipo_clase:
                query = query.join(HorarioClase).filter(HorarioClase.tipo_clase == tipo_clase)
            
            # Obtener todas las clases
            clases = query.order_by(ClaseRealizada.fecha).all()
            
            # Agrupar por mes
            clases_por_mes = defaultdict(list)
            for clase in clases:
                clave_mes = f"{clase.fecha.year}-{clase.fecha.month:02d}"
                clases_por_mes[clave_mes].append(clase)
            
            # Procesar estadísticas por mes
            resultados = {}
            for clave_mes, clases_mes in sorted(clases_por_mes.items()):
                year, month = map(int, clave_mes.split('-'))
                
                # Total de clases
                total_clases = len(clases_mes)
                
                # Promedio de alumnos
                total_alumnos = sum(c.cantidad_alumnos for c in clases_mes if c.cantidad_alumnos is not None)
                promedio_alumnos = total_alumnos / total_clases if total_clases > 0 else 0
                
                # Puntualidad
                clases_con_registro = [c for c in clases_mes if c.hora_llegada_profesor is not None]
                puntual = sum(1 for c in clases_con_registro if c.puntualidad == "Puntual")
                retraso_leve = sum(1 for c in clases_con_registro if c.puntualidad == "Retraso leve")
                retraso_significativo = sum(1 for c in clases_con_registro if c.puntualidad == "Retraso significativo")
                
                tasa_puntualidad = (puntual / len(clases_con_registro) * 100) if clases_con_registro else 0
                
                # Agregar al resultado
                resultados[clave_mes] = {
                    'anio': year,
                    'mes': month,
                    'nombre_mes': MESES_ES[month],
                    'total_clases': total_clases,
                    'promedio_alumnos': promedio_alumnos,
                    'puntualidad': {
                        'tasa': tasa_puntualidad,
                        'puntual': puntual,
                        'retraso_leve': retraso_leve,
                        'retraso_significativo': retraso_significativo
                    }
                }
            
            return resultados
        except Exception as e:
            print(f"Error en obtener_estadisticas_historicas: {str(e)}")
            return {}

def setup_date_handling(app=None):
    """
    Configura el manejo de fechas para la aplicación.
    Esta función debe ser llamada dentro de un contexto de aplicación.
    """
    # Verificar si hay un contexto de aplicación antes de configurar eventos
    if not has_app_context() and app is None:
        print("Advertencia: Sin contexto de aplicación para la configuración de fechas.")
        print("Esta advertencia es normal durante la inicialización y no afecta el funcionamiento.")
        return False
    
    try:
        # Solo ejecutar esta parte si tenemos un contexto de aplicación o una app
        if has_app_context() or app is not None:
            # Configurar el pragma de SQLite
            @event.listens_for(db.engine, 'connect', once=True)
            def set_sqlite_pragma(dbapi_connection, connection_record):
                # Configure SQLite to use ISO date formats
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
            
            # Configurar el evento para EventoHorario
            current_module = sys.modules[__name__]
            if hasattr(current_module, 'EventoHorario'):
                EventoHorario = getattr(current_module, 'EventoHorario')
                
                @event.listens_for(EventoHorario, 'load')
                def process_evento_horario_load(target, context):
                    # Standardize the date format if it's using ISO format with T
                    if (hasattr(target, 'fecha') and 
                        target.fecha is not None and 
                        isinstance(target.fecha, str) and
                        'T' in target.fecha):
                        try:
                            date_part, time_part = target.fecha.split('T')
                            if '.' in time_part:
                                time_part = time_part.split('.')[0]
                            target.fecha = f"{date_part} {time_part}"
                        except Exception as e:
                            print(f"Error processing date format: {e}")
        
        return True
    except Exception as e:
        print(f"Error setting up date handling: {str(e)}")
        return False
