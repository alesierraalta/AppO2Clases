"""
Módulo de utilidades para el cálculo de métricas de clases agrupadas por nombre.
Proporciona funciones para analizar el rendimiento de clases independientemente del horario,
agrupando todas las instancias de una clase por su nombre (ej: "Power Bike" de 7:30 AM y 6:30 PM).

Reutiliza funciones auxiliares de metricas_profesores.py para mantener consistencia.
"""
from datetime import datetime, timedelta
from models import HorarioClase, ClaseRealizada

# Importar funciones auxiliares reutilizables desde metricas_profesores
from utils.metricas_profesores import (
    calcular_tasa_puntualidad,
    calcular_promedio_alumnos,
    calcular_distribucion_clases,
    calcular_tendencia_asistencia,
    calcular_costo_por_alumno,
    validar_datos_comparacion,
    comparar_metricas_mensuales,
    get_profesores_promedio
)


def obtener_clases_por_nombre(nombre_clase):
    """
    Obtiene todas las clases realizadas (ClaseRealizada) para un nombre de clase dado,
    agrupando todas las instancias independientemente del horario.
    
    Por ejemplo, para "Power Bike", retorna todas las clases realizadas tanto de 
    "Power Bike" de las 7:30 AM como de las 6:30 PM.
    
    Args:
        nombre_clase (str): Nombre de la clase (ej: "Power Bike")
        
    Returns:
        list: Lista de objetos ClaseRealizada para todas las instancias de esa clase
    """
    try:
        # Obtener todos los horarios con el nombre dado
        horarios = HorarioClase.query.filter_by(nombre=nombre_clase).all()
        
        if not horarios:
            return []
        
        # Obtener todos los IDs de horarios
        horario_ids = [h.id for h in horarios]
        
        # Obtener todas las clases realizadas para esos horarios
        clases = ClaseRealizada.query.filter(
            ClaseRealizada.horario_id.in_(horario_ids)
        ).order_by(ClaseRealizada.fecha.desc()).all()
        
        return clases
    except Exception as e:
        print(f"Error al obtener clases por nombre '{nombre_clase}': {str(e)}")
        return []


def calcular_metricas_clase(nombre_clase, clases=None, mes_actual=None, mes_comparacion=None, generar_resumen=True):
    """
    Calcula las métricas para una clase específica agrupada por nombre,
    independientemente del horario.
    
    Similar a calcular_metricas_profesor(), pero agrupa por nombre de clase
    en lugar de por profesor.
    
    Args:
        nombre_clase (str): Nombre de la clase (ej: "Power Bike")
        clases (list, optional): Lista de clases realizadas. Si es None, se obtienen todas las clases con ese nombre.
        mes_actual (tuple, optional): Tuple (año, mes) para filtrar el mes actual.
        mes_comparacion (tuple, optional): Tuple (año, mes) para comparar con el mes actual.
        generar_resumen (bool, optional): Si True, incluye un resumen estructurado del rendimiento.
        
    Returns:
        dict: Diccionario con las métricas calculadas (misma estructura que calcular_metricas_profesor)
    """
    # Estructura de métricas vacías
    metricas_vacias = {
        'total_clases': 0,
        'total_alumnos': 0,
        'puntualidad': calcular_tasa_puntualidad([]),
        'distribucion': calcular_distribucion_clases([]),
        'tendencia': calcular_tendencia_asistencia([]),
        'datos_por_tipo': {},
        'datos_mensuales': [],
        'clases': [],
        'clases_por_mes': 0,
        'variedad_clases': 0,
        'tendencia_global': 0,
        'tendencias': {
            'alumnos': 0,
            'puntualidad': 0,
            'clases_por_mes': 0
        }
    }
    
    # Inicializar la estructura de retorno
    metricas = {
        'metricas_actual': metricas_vacias,
        'metricas_comparacion': None,
        'comparacion': None,
        'mes_actual': mes_actual,
        'mes_comparacion': mes_comparacion
    }
    
    # Si no se proporcionan clases, obtenerlas por nombre
    if clases is None:
        clases = obtener_clases_por_nombre(nombre_clase)
    
    if not clases:
        return metricas
    
    # Función auxiliar para filtrar clases por mes
    def filtrar_clases_por_mes(clases_list, anio, mes):
        """Filtra la lista de clases por año y mes"""
        return [c for c in clases_list if c.fecha.year == anio and c.fecha.month == mes]
    
    # Preparar variables para cuando se filtran por mes
    clases_mes_actual = clases
    clases_a_procesar = clases
    
    # Calcular tendencia general para todos los meses (evolución mensual)
    tendencia_general = calcular_tendencia_asistencia(clases, periodo_meses=12)
    # Asegurarnos de tener esta información en el resultado final
    metricas['datos_mensuales'] = tendencia_general['datos_mensuales']
    
    # Si se solicita comparación de meses
    if mes_actual and mes_comparacion:
        # Filtrar clases para cada mes
        clases_mes_actual = filtrar_clases_por_mes(clases, mes_actual[0], mes_actual[1])
        clases_mes_comparacion = filtrar_clases_por_mes(clases, mes_comparacion[0], mes_comparacion[1])
        
        # Validar que existan suficientes datos para la comparación
        validacion = validar_datos_comparacion(clases_mes_actual, clases_mes_comparacion)
        if not validacion['valido']:
            metricas['error_comparacion'] = validacion['mensaje']
            # No retornamos aún, continuamos calculando métricas normales
        else:
            # Si la comparación es válida, calcular las métricas comparativas
            # Ordenar clases del mes de comparación (más recientes primero)
            clases_ordenadas_comp = sorted(clases_mes_comparacion, key=lambda c: c.fecha, reverse=True)
            
            # Calcular métricas para el mes de comparación
            total_clases_comp = len(clases_mes_comparacion)
            total_alumnos_comp = 0
            for c in clases_mes_comparacion:
                if c.cantidad_alumnos is not None:
                    try:
                        # Convertir a entero si es una cadena o cualquier otro tipo
                        if isinstance(c.cantidad_alumnos, str):
                            total_alumnos_comp += int(c.cantidad_alumnos)
                        else:
                            total_alumnos_comp += c.cantidad_alumnos
                    except (ValueError, TypeError):
                        # Si hay error en la conversión, ignorar este valor
                        print(f"Error al calcular total_alumnos: {c.cantidad_alumnos} de tipo {type(c.cantidad_alumnos)}")
                        continue
            
            puntualidad_comp = calcular_tasa_puntualidad(clases_mes_comparacion)
            distribucion_comp = calcular_distribucion_clases(clases_mes_comparacion)
            tendencia_comp = calcular_tendencia_asistencia(clases_mes_comparacion)
            
            # Calcular clases por mes para mes de comparación
            fechas_comp = [c.fecha for c in clases_mes_comparacion]
            clases_por_mes_comp = total_clases_comp  # Valor predeterminado
            
            if fechas_comp and len(fechas_comp) >= 2:
                min_fecha_comp = min(fechas_comp)
                max_fecha_comp = max(fechas_comp)
                meses_diff_comp = (max_fecha_comp.year - min_fecha_comp.year) * 12 + max_fecha_comp.month - min_fecha_comp.month
                if meses_diff_comp > 0:
                    clases_por_mes_comp = total_clases_comp / meses_diff_comp
            
            # Calcular variedad de clases para mes de comparación
            tipos_distintos_comp = len([t for t, c in distribucion_comp['tipos'].items() if c > 0])
            variedad_clases_comp = (tipos_distintos_comp / 4) * 100  # MOVE, RIDE, BOX, OTRO
            
            # Calcular score global para mes de comparación
            promedio_alumnos_comp = calcular_promedio_alumnos(clases_mes_comparacion)
            
            # Ponderación de factores para score global
            peso_puntualidad = 0.30
            peso_alumnos = 0.40
            peso_clases = 0.15
            peso_costo = 0.15
            
            # Normalizar valores a escala 0-100
            puntualidad_norm_comp = puntualidad_comp['tasa']  # Ya está en porcentaje
            
            # Obtener datos de promedio de profesores (para normalización)
            promedios_profesores = get_profesores_promedio(exclude_profesor_id=None)
            
            alumnos_norm_comp = 0
            if promedios_profesores and promedios_profesores['alumnos'] > 0:
                # Normalizar respecto al promedio (100% = doble del promedio)
                alumnos_norm_comp = min(100, (promedio_alumnos_comp / promedios_profesores['alumnos']) * 50)
            else:
                # Si no hay promedio, usar escala arbitraria (100% = 20 alumnos)
                alumnos_norm_comp = min(100, (promedio_alumnos_comp / 20) * 100)
            
            clases_norm_comp = min(100, (clases_por_mes_comp / 20) * 100)  # 20 clases/mes = 100%
            
            # Calcular costo por alumno para el mes de comparación
            costo_por_alumno_comp = calcular_costo_por_alumno(clases_mes_comparacion)
            
            # Normalizar costo por alumno de forma relativa (menor costo = mejor puntuación)
            costo_norm_comp = 0
            try:
                # Asegurar que costo_por_alumno_comp sea numérico
                if isinstance(costo_por_alumno_comp, str):
                    costo_por_alumno_comp = float(costo_por_alumno_comp)
                    
                if costo_por_alumno_comp > 0 and promedios_profesores and 'costo_por_alumno' in promedios_profesores:
                    min_costo = promedios_profesores['costo_por_alumno'].get('minimo', 0)
                    max_costo = promedios_profesores['costo_por_alumno'].get('maximo', 50)
                    
                    # Asegurar que min_costo y max_costo sean numéricos
                    if isinstance(min_costo, str):
                        min_costo = float(min_costo)
                    if isinstance(max_costo, str):
                        max_costo = float(max_costo)
                    
                    if min_costo == max_costo:  # Evitar división por cero
                        costo_norm_comp = 100 if costo_por_alumno_comp <= min_costo else 0
                    elif max_costo > min_costo:
                        # Normalización relativa: el costo más bajo (mejor) recibe 100 puntos,
                        # el más alto recibe 0 puntos, y el resto se distribuye linealmente
                        costo_norm_comp = max(0, 100 - ((costo_por_alumno_comp - min_costo) / (max_costo - min_costo)) * 100)
            except (ValueError, TypeError) as e:
                print(f"Error al normalizar costo por alumno: {str(e)}")
                costo_norm_comp = 0
            
            # Calcular score global para comparación
            score_global_comp = (
                peso_puntualidad * puntualidad_norm_comp +
                peso_alumnos * alumnos_norm_comp +
                peso_clases * clases_norm_comp +
                peso_costo * costo_norm_comp
            )
            
            # Asegurar que score_global_comp esté definido
            score_global_comp = round(score_global_comp, 1) if score_global_comp is not None else 0
            
            # Construir el objeto de métricas para el mes de comparación
            metricas_comparacion = {
                'total_clases': total_clases_comp,
                'total_alumnos': total_alumnos_comp,
                'promedio_alumnos': promedio_alumnos_comp,
                'puntualidad': puntualidad_comp,
                'distribucion': distribucion_comp,
                'tendencia': tendencia_comp,
                'clases': clases_ordenadas_comp,
                'clases_por_mes': clases_por_mes_comp,
                'variedad_clases': variedad_clases_comp,
                'score_global': score_global_comp,
                'puntuacion': score_global_comp,
                'costo_por_alumno': costo_por_alumno_comp,
                'datos_mensuales': metricas.get('datos_mensuales', [])
            }
            
            # Guardar métricas de comparación
            metricas['metricas_comparacion'] = metricas_comparacion
            
            # Si se proporcionó mes actual, filtrar clases
            if mes_actual:
                clases_a_procesar = filtrar_clases_por_mes(clases, mes_actual[0], mes_actual[1])
                clases_mes_actual = clases_a_procesar
    
    # Procesar métricas del mes actual o período total
    if mes_actual:
        clases_a_procesar = filtrar_clases_por_mes(clases, mes_actual[0], mes_actual[1])
        clases_mes_actual = clases_a_procesar
    
    if not clases_a_procesar:
        # Si no hay clases para procesar, retornar métricas vacías
        return metricas
    
    # Ordenar clases (más recientes primero)
    clases_ordenadas = sorted(clases_a_procesar, key=lambda c: c.fecha, reverse=True)
    
    # Calcular métricas básicas
    total_clases = len(clases_a_procesar)
    total_alumnos = 0
    for c in clases_a_procesar:
        if c.cantidad_alumnos is not None:
            try:
                if isinstance(c.cantidad_alumnos, str):
                    total_alumnos += int(c.cantidad_alumnos)
                else:
                    total_alumnos += c.cantidad_alumnos
            except (ValueError, TypeError):
                print(f"Error al calcular total_alumnos: {c.cantidad_alumnos} de tipo {type(c.cantidad_alumnos)}")
                continue
    
    # Calcular métricas usando funciones auxiliares reutilizables
    promedio_alumnos = calcular_promedio_alumnos(clases_a_procesar)
    puntualidad = calcular_tasa_puntualidad(clases_a_procesar)
    distribucion = calcular_distribucion_clases(clases_a_procesar)
    tendencia = calcular_tendencia_asistencia(clases_a_procesar)
    costo_por_alumno = calcular_costo_por_alumno(clases_a_procesar)
    
    # Calcular clases por mes
    fechas = [c.fecha for c in clases_a_procesar]
    clases_por_mes = total_clases  # Valor predeterminado
    
    if fechas and len(fechas) >= 2:
        min_fecha = min(fechas)
        max_fecha = max(fechas)
        meses_diff = (max_fecha.year - min_fecha.year) * 12 + max_fecha.month - min_fecha.month
        if meses_diff > 0:
            clases_por_mes = total_clases / meses_diff
    
    # Calcular variedad de clases
    tipos_distintos = len([t for t, c in distribucion['tipos'].items() if c > 0])
    variedad_clases = (tipos_distintos / 4) * 100  # MOVE, RIDE, BOX, OTRO
    
    # Calcular tendencias globales (usando todos los meses disponibles)
    tendencia_global = tendencia_general.get('tendencia', 0)
    
    # Calcular tendencias específicas
    if len(metricas['datos_mensuales']) >= 2:
        datos_actuales = metricas['datos_mensuales'][-1] if metricas['datos_mensuales'] else {}
        datos_anteriores = metricas['datos_mensuales'][-2] if len(metricas['datos_mensuales']) >= 2 else {}
        
        # Tendencia de alumnos
        alumnos_actuales = datos_actuales.get('promedio_alumnos', 0)
        alumnos_anteriores = datos_anteriores.get('promedio_alumnos', 0)
        if alumnos_anteriores > 0:
            tendencia_alumnos = ((alumnos_actuales / alumnos_anteriores) - 1) * 100
        else:
            tendencia_alumnos = 0
        
        # Tendencia de puntualidad
        punt_actual = datos_actuales.get('puntualidad', 0)
        punt_anterior = datos_anteriores.get('puntualidad', 0)
        if punt_anterior > 0:
            tendencia_puntualidad = ((punt_actual / punt_anterior) - 1) * 100
        else:
            tendencia_puntualidad = 0
        
        # Tendencia de clases por mes
        clases_actuales = datos_actuales.get('total_clases', 0)
        clases_anteriores = datos_anteriores.get('total_clases', 0)
        if clases_anteriores > 0:
            tendencia_clases_mes = ((clases_actuales / clases_anteriores) - 1) * 100
        else:
            tendencia_clases_mes = 0
    else:
        tendencia_alumnos = 0
        tendencia_puntualidad = 0
        tendencia_clases_mes = 0
    
    # Calcular score global (similar a métricas de profesor)
    peso_puntualidad = 0.30
    peso_alumnos = 0.40
    peso_clases = 0.15
    peso_costo = 0.15
    
    puntualidad_norm = puntualidad['tasa']
    
    # Obtener promedios de profesores para normalización
    promedios_profesores = get_profesores_promedio(exclude_profesor_id=None)
    
    alumnos_norm = 0
    if promedios_profesores and promedios_profesores['alumnos'] > 0:
        alumnos_norm = min(100, (promedio_alumnos / promedios_profesores['alumnos']) * 50)
    else:
        alumnos_norm = min(100, (promedio_alumnos / 20) * 100)
    
    clases_norm = min(100, (clases_por_mes / 20) * 100)
    
    # Normalizar costo por alumno
    costo_norm = 0
    try:
        if isinstance(costo_por_alumno, str):
            costo_por_alumno = float(costo_por_alumno)
            
        if costo_por_alumno > 0 and promedios_profesores and 'costo_por_alumno' in promedios_profesores:
            min_costo = promedios_profesores['costo_por_alumno'].get('minimo', 0)
            max_costo = promedios_profesores['costo_por_alumno'].get('maximo', 50)
            
            if isinstance(min_costo, str):
                min_costo = float(min_costo)
            if isinstance(max_costo, str):
                max_costo = float(max_costo)
            
            if min_costo == max_costo:
                costo_norm = 100 if costo_por_alumno <= min_costo else 0
            elif max_costo > min_costo:
                costo_norm = max(0, 100 - ((costo_por_alumno - min_costo) / (max_costo - min_costo)) * 100)
    except (ValueError, TypeError) as e:
        print(f"Error al normalizar costo por alumno: {str(e)}")
        costo_norm = 0
    
    score_global = (
        peso_puntualidad * puntualidad_norm +
        peso_alumnos * alumnos_norm +
        peso_clases * clases_norm +
        peso_costo * costo_norm
    )
    
    score_global = round(score_global, 1) if score_global is not None else 0
    
    # Compilar todas las métricas
    metricas_actuales = {
        'total_clases': total_clases,
        'total_alumnos': total_alumnos,
        'promedio_alumnos': promedio_alumnos,
        'clases': clases_ordenadas,
        'distribucion': distribucion,
        'puntualidad': puntualidad,
        'tendencia': tendencia,
        'score_global': score_global,
        'puntuacion': score_global,
        'costo_por_alumno': costo_por_alumno,
        'datos_mensuales': metricas.get('datos_mensuales', []),
        'clases_por_mes': clases_por_mes,
        'variedad_clases': variedad_clases,
        'tendencia_global': tendencia_global,
        'tendencias': {
            'alumnos': tendencia_alumnos,
            'puntualidad': tendencia_puntualidad,
            'clases_por_mes': tendencia_clases_mes
        },
        'promedio_profesores': promedios_profesores
    }
    
    # Actualizar el objeto de retorno con las métricas calculadas
    metricas['metricas_actual'] = metricas_actuales
    
    # Si hay comparación, calcular diferencias
    if mes_comparacion and metricas.get('metricas_comparacion'):
        metricas['comparacion'] = comparar_metricas_mensuales(
            metricas_actuales,
            metricas['metricas_comparacion']
        )
    
    return metricas

