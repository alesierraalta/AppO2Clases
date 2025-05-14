"""
Módulo de utilidades para el cálculo de métricas de profesores.
Proporciona funciones para analizar el rendimiento de profesores
basado en asistencia, puntualidad, tipos de clase, y evolución temporal.
"""
from datetime import datetime, timedelta
import calendar
from collections import defaultdict
import numpy as np


def calcular_tasa_puntualidad(clases):
    """
    Calcula la tasa de puntualidad del profesor basada en sus clases.
    
    Args:
        clases (list): Lista de objetos ClaseRealizada
        
    Returns:
        dict: Diccionario con tasa de puntualidad y conteos por categoría
    """
    if not clases:
        return {
            'tasa': 0,
            'puntual': 0,
            'retraso_leve': 0,
            'retraso_significativo': 0,
            'total': 0
        }
    
    puntual = 0
    retraso_leve = 0
    retraso_significativo = 0
    
    for clase in clases:
        if not clase.hora_llegada_profesor:
            continue
            
        # Calcular la diferencia en minutos
        hora_inicio = clase.horario.hora_inicio
        hora_llegada = clase.hora_llegada_profesor
        
        diferencia_minutos = ((hora_llegada.hour * 60 + hora_llegada.minute) - 
                             (hora_inicio.hour * 60 + hora_inicio.minute))
        
        if diferencia_minutos <= 0:
            puntual += 1
        elif diferencia_minutos <= 10:
            retraso_leve += 1
        else:
            retraso_significativo += 1
    
    total_con_registro = puntual + retraso_leve + retraso_significativo
    
    return {
        'tasa': (puntual / total_con_registro * 100) if total_con_registro > 0 else 0,
        'puntual': puntual,
        'retraso_leve': retraso_leve,
        'retraso_significativo': retraso_significativo,
        'total': total_con_registro
    }


def calcular_promedio_alumnos(clases):
    """
    Calcula el promedio de alumnos por clase para un profesor.
    
    Args:
        clases (list): Lista de objetos ClaseRealizada
        
    Returns:
        float: Promedio de alumnos por clase
    """
    if not clases:
        return 0.0
        
    # Filtrar clases que tienen datos válidos de alumnos    
    clases_con_alumnos = [c for c in clases if c.cantidad_alumnos is not None]
    if not clases_con_alumnos:
        return 0.0
        
    total_alumnos = sum(c.cantidad_alumnos for c in clases_con_alumnos)
    return total_alumnos / len(clases_con_alumnos)


def calcular_distribucion_clases(clases):
    """
    Calcula la distribución de clases por tipo (MOVE, RIDE, BOX, etc).
    
    Args:
        clases (list): Lista de objetos ClaseRealizada
        
    Returns:
        dict: Diccionario con conteos por tipo de clase y porcentajes
    """
    if not clases:
        return {
            'total': 0,
            'tipos': {},
            'porcentajes': {}
        }
    
    conteo = defaultdict(int)
    
    for clase in clases:
        tipo = clase.horario.tipo_clase if clase.horario and clase.horario.tipo_clase else "OTRO"
        conteo[tipo] += 1
    
    # Asegurar que todos los tipos comunes estén presentes
    for tipo in ['MOVE', 'RIDE', 'BOX', 'OTRO']:
        if tipo not in conteo:
            conteo[tipo] = 0
    
    total = len(clases)
    porcentajes = {tipo: (count / total * 100) for tipo, count in conteo.items()}
    
    return {
        'total': total,
        'tipos': dict(conteo),
        'porcentajes': porcentajes
    }


def calcular_tendencia_asistencia(clases, periodo_meses=3):
    """
    Calcula la tendencia de asistencia en los últimos meses.
    
    Args:
        clases (list): Lista de objetos ClaseRealizada
        periodo_meses (int): Número de meses a analizar
        
    Returns:
        dict: Diccionario con datos de tendencia mensual
    """
    if not clases:
        return {
            'tendencia': 0,
            'datos_mensuales': []
        }
    
    # Ordenar clases por fecha
    clases_ordenadas = sorted(clases, key=lambda c: c.fecha)
    
    # Agrupar por mes
    clases_por_mes = defaultdict(list)
    for clase in clases_ordenadas:
        clave_mes = f"{clase.fecha.year}-{clase.fecha.month:02d}"
        clases_por_mes[clave_mes].append(clase)
    
    # Calcular métricas por mes
    datos_mensuales = []
    for clave_mes, clases_mes in sorted(clases_por_mes.items()):
        year, month = map(int, clave_mes.split('-'))
        
        # Obtener el nombre del mes en español
        nombre_mes = calendar.month_name[month]
        
        puntualidad = calcular_tasa_puntualidad(clases_mes)
        distribucion = calcular_distribucion_clases(clases_mes)
        
        datos_mensuales.append({
            'anio': year,
            'mes': month,
            'etiqueta': f"{nombre_mes} {year}",
            'total_clases': len(clases_mes),
            'promedio_alumnos': calcular_promedio_alumnos(clases_mes),
            'puntualidad': puntualidad['tasa'],
            'clases_por_tipo': distribucion['tipos']
        })
    
    # Calcular tendencia comparando periodos recientes
    if len(datos_mensuales) >= 2:
        ultimo_mes = datos_mensuales[-1]
        meses_anteriores = datos_mensuales[:-1]
        
        # Promedio de alumnos de meses anteriores
        prom_alumnos_anterior = np.mean([m['promedio_alumnos'] for m in meses_anteriores])
        
        # Calcular tendencia (porcentaje de cambio)
        if prom_alumnos_anterior > 0:
            tendencia = ((ultimo_mes['promedio_alumnos'] / prom_alumnos_anterior) - 1) * 100
        else:
            tendencia = 0
    else:
        tendencia = 0
    
    return {
        'tendencia': tendencia,
        'datos_mensuales': datos_mensuales
    }

# ... existing code ...

def get_profesores_promedio(exclude_profesor_id=None):
    """
    Calcula los promedios de métricas para todos los profesores.
    
    Args:
        exclude_profesor_id (int, optional): ID del profesor a excluir del cálculo
        
    Returns:
        dict: Diccionario con promedios de métricas para todos los profesores
    """
    from models import Profesor, ClaseRealizada
    
    # Obtener datos de todos los profesores para los últimos 3 meses
    fecha_fin = datetime.now().date()
    fecha_inicio = fecha_fin - timedelta(days=90)
    
    profesores = Profesor.query.all()
    stats_puntualidad = []
    stats_alumnos = []
    stats_clases = []
    stats_variedad = []
    
    for prof in profesores:
        if exclude_profesor_id and prof.id == exclude_profesor_id:
            continue  # Excluir al profesor actual para no afectar el promedio
            
        clases_prof = prof.get_clases_periodo(fecha_inicio, fecha_fin)
        if not clases_prof:
            continue
            
        # Calcular puntualidad
        puntualidad = calcular_tasa_puntualidad(clases_prof)
        if puntualidad['total'] > 0:
            stats_puntualidad.append(puntualidad['tasa'])
        
        # Calcular promedio de alumnos
        prom_alumnos = calcular_promedio_alumnos(clases_prof)
        stats_alumnos.append(prom_alumnos)
        
        # Calcular clases por mes
        # Asumiendo un período de 3 meses completos
        stats_clases.append(len(clases_prof) / 3)
        
        # Calcular variedad de clases
        distribucion = calcular_distribucion_clases(clases_prof)
        tipos_distintos = len([t for t, c in distribucion['tipos'].items() if c > 0])
        total_tipos_posibles = 4  # MOVE, RIDE, BOX, OTRO
        variedad = (tipos_distintos / total_tipos_posibles) * 100
        stats_variedad.append(variedad)
    
    # Calcular promedios finales
    prom_puntualidad = np.mean(stats_puntualidad) if stats_puntualidad else 0
    prom_alumnos = np.mean(stats_alumnos) if stats_alumnos else 0
    prom_clases = np.mean(stats_clases) if stats_clases else 0
    prom_variedad = np.mean(stats_variedad) if stats_variedad else 0
    
    return {
        'puntualidad': prom_puntualidad,
        'alumnos': prom_alumnos,
        'clases_por_mes': prom_clases,
        'variedad_clases': prom_variedad
    }

def validar_datos_comparacion(clases_mes_actual, clases_mes_comparacion):
    """
    Valida que existan suficientes datos para realizar una comparación válida entre meses.
    
    Args:
        clases_mes_actual (list): Lista de clases del mes actual
        clases_mes_comparacion (list): Lista de clases del mes de comparación
        
    Returns:
        dict: {'valido': bool, 'mensaje': str} indicando si la comparación es válida y mensaje de error
    """
    resultado = {'valido': True, 'mensaje': ''}
    
    # Verificar si hay suficientes clases en cada mes
    if not clases_mes_actual or len(clases_mes_actual) == 0:
        resultado['valido'] = False
        resultado['mensaje'] = "No hay datos disponibles para el mes actual seleccionado."
        return resultado
    
    if not clases_mes_comparacion or len(clases_mes_comparacion) == 0:
        resultado['valido'] = False
        resultado['mensaje'] = "No hay datos disponibles para el mes de comparación seleccionado."
        return resultado
    
    # Verificar mínimo de clases para comparación significativa
    if len(clases_mes_actual) < 3:
        resultado['valido'] = False
        resultado['mensaje'] = f"Datos insuficientes para el mes actual ({len(clases_mes_actual)} clases). Se requieren al menos 3 clases para una comparación significativa."
        return resultado
    
    if len(clases_mes_comparacion) < 3:
        resultado['valido'] = False
        resultado['mensaje'] = f"Datos insuficientes para el mes de comparación ({len(clases_mes_comparacion)} clases). Se requieren al menos 3 clases para una comparación significativa."
        return resultado
    
    return resultado

def calcular_metricas_profesor(profesor_id, clases=None, mes_actual=None, mes_comparacion=None, usar_promedios=False):
    """
    Calcula las métricas para un profesor específico.
    
    Args:
        profesor_id (int): ID del profesor
        clases (list, optional): Lista de clases realizadas. Si es None, se obtienen todas las clases del profesor.
        mes_actual (tuple, optional): Tuple (año, mes) para filtrar el mes actual.
        mes_comparacion (tuple, optional): Tuple (año, mes) para comparar con el mes actual.
        usar_promedios (bool, optional): Si True, usa promedios globales en vez de datos específicos del profesor.
        
    Returns:
        dict: Diccionario con las métricas calculadas
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
            total_alumnos_comp = sum(c.cantidad_alumnos for c in clases_mes_comparacion if c.cantidad_alumnos is not None)
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
            
            # Asegurar que los datos mensuales estén disponibles para la comparación 
            # (usamos los datos para todos los meses, no solo el mes de comparación)
            
            # Construir el objeto de métricas para el mes de comparación
            metricas_comparacion = {
                'total_clases': total_clases_comp,
                'total_alumnos': total_alumnos_comp,
                'promedio_alumnos': calcular_promedio_alumnos(clases_mes_comparacion),
                'puntualidad': puntualidad_comp,
                'distribucion': distribucion_comp,
                'tendencia': tendencia_comp,
                'clases': clases_ordenadas_comp,
                'clases_por_mes': clases_por_mes_comp,
                'variedad_clases': variedad_clases_comp,
                'datos_mensuales': metricas.get('datos_mensuales', [])  # Incluir datos mensuales completos
            }
            
            # Guardar métricas de comparación
            metricas['metricas_comparacion'] = metricas_comparacion
            
            # Calcular la comparación entre ambos meses
            comparacion = comparar_metricas_mensuales(
                # Usamos clases_mes_actual para calcular métricas actuales
                {
                    'clases': clases_mes_actual, 
                    'puntualidad': calcular_tasa_puntualidad(clases_mes_actual),
                    'variedad_clases': (len([t for t, c in calcular_distribucion_clases(clases_mes_actual)['tipos'].items() if c > 0]) / 4) * 100
                },
                # Usamos clases_mes_comparacion para calcular métricas de comparación
                {
                    'clases': clases_mes_comparacion,
                    'puntualidad': puntualidad_comp,
                    'variedad_clases': variedad_clases_comp
                }
            )
            
            # Guardar los resultados de la comparación
            if comparacion:
                metricas['comparacion'] = comparacion
    # Si solo tenemos mes actual sin comparación
    elif mes_actual:
        # Filtrar clases solo para el mes actual
        clases_mes_actual = filtrar_clases_por_mes(clases, mes_actual[0], mes_actual[1])
        clases_a_procesar = clases_mes_actual
        
        # Mantener los datos mensuales completos para mostrar tendencia mensual
        # aunque filtremos para las métricas actuales
    
    # Ahora calculamos las métricas normales con los datos que tenemos
    if clases_a_procesar:
        # Ordenar clases por fecha descendente (más recientes primero)
        clases_ordenadas = sorted(clases_a_procesar, key=lambda c: c.fecha, reverse=True)
        
        # Calcular métricas básicas para mostrar
        total_clases = len(clases_a_procesar)
        distribucion = calcular_distribucion_clases(clases_a_procesar)
        puntualidad = calcular_tasa_puntualidad(clases_a_procesar)
        tendencia = calcular_tendencia_asistencia(clases_a_procesar)
        
        # Calcular total de alumnos
        total_alumnos = sum(c.cantidad_alumnos for c in clases_a_procesar if c.cantidad_alumnos is not None)
        
        # Calcular promedio de alumnos por clase
        promedio_alumnos = calcular_promedio_alumnos(clases_a_procesar)
        
        # Calcular clases por mes (promedio)
        fechas = [c.fecha for c in clases_a_procesar]
        clases_por_mes = total_clases  # Valor predeterminado si no hay suficientes datos
        
        if fechas and len(fechas) >= 2:
            min_fecha = min(fechas)
            max_fecha = max(fechas)
            # Calcular diferencia en meses
            meses_diff = (max_fecha.year - min_fecha.year) * 12 + max_fecha.month - min_fecha.month
            if meses_diff > 0:
                clases_por_mes = total_clases / meses_diff
        
        # Calcular variedad de clases (porcentaje de tipos diferentes)
        tipos_distintos = len([t for t, c in distribucion['tipos'].items() if c > 0])
        total_tipos_posibles = 4  # MOVE, RIDE, BOX, OTRO
        variedad_clases = (tipos_distintos / total_tipos_posibles) * 100
        
        # Calcular tendencias
        tendencia_global = 0
        tendencia_alumnos = 0
        tendencia_puntualidad = 0
        tendencia_clases_mes = 0
        
        # Compilar todas las métricas
        metricas_actuales = {
        'total_clases': total_clases,
        'total_alumnos': total_alumnos,
            'promedio_alumnos': promedio_alumnos,
            'clases': clases_ordenadas,
            'distribucion': distribucion,
        'puntualidad': puntualidad,
            'tendencia': tendencia,  # Este es el cálculo para el período específico
            'datos_mensuales': metricas.get('datos_mensuales', []),  # Estos son TODOS los datos mensuales
        'clases_por_mes': clases_por_mes,
        'variedad_clases': variedad_clases,
        'tendencia_global': tendencia_global,
        'tendencias': {
            'alumnos': tendencia_alumnos,
            'puntualidad': tendencia_puntualidad,
                'clases_por_mes': tendencia_clases_mes
            }
        }
        
        # Añadir promedios de profesores para comparación cuando no estemos en modo de comparación
        if not mes_comparacion:
            # Obtener promedios de otros profesores para comparación
            promedios_profesores = get_profesores_promedio(exclude_profesor_id=profesor_id)
            metricas_actuales['promedio_profesores'] = promedios_profesores
        
        # Asegurarnos de que los datos mensuales estén presentes en las métricas actuales
        metricas_actuales['datos_mensuales'] = metricas.get('datos_mensuales', [])
        
        # Actualizar el objeto de retorno con las métricas calculadas
        metricas['metricas_actual'] = metricas_actuales
        
    # Añadir nombres de meses para mostrar en la UI
    if mes_actual:
        anio_actual, mes_actual_num = mes_actual
        import calendar
        metricas['mes_actual_nombre'] = f"{calendar.month_name[mes_actual_num]} {anio_actual}"
    else:
        metricas['mes_actual_nombre'] = "Todas las clases"
    
    if mes_comparacion:
        anio_comp, mes_comp_num = mes_comparacion
        import calendar
        metricas['mes_comparacion_nombre'] = f"{calendar.month_name[mes_comp_num]} {anio_comp}"
    else:
        metricas['mes_comparacion_nombre'] = "Sin comparación"
    
    return metricas

# ... existing code ...

def comparar_metricas_mensuales(metricas_actual, metricas_comparacion):
    """
    Compara dos conjuntos de métricas y calcula las diferencias porcentuales.
    
    Args:
        metricas_actual (dict): Métricas del mes actual
        metricas_comparacion (dict): Métricas del mes de comparación
        
    Returns:
        dict: Diferencias porcentuales entre ambos conjuntos de métricas
    """
    # Verificar que ambos conjuntos de datos estén presentes
    if not metricas_actual or not metricas_comparacion:
        return None
    
    # Extraer métricas de comparación si están en la estructura con metricas_actual
    if 'metricas_actual' in metricas_comparacion:
        metricas_comparacion = metricas_comparacion['metricas_actual']
    
    # Calcular diferencias en métricas clave
    try:
        # Promedio de alumnos
        prom_alumnos_actual = calcular_promedio_alumnos(metricas_actual.get('clases', []))
        prom_alumnos_comp = calcular_promedio_alumnos(metricas_comparacion.get('clases', []))
        
        # Valores por defecto en caso de error o datos insuficientes
        diff_prom_alumnos = 0
        diff_puntualidad = 0
        diff_clases = 0
        diff_variedad = 0
        
        # Calcular diferencia en promedio de alumnos con manejo de excepciones
        try:
        if prom_alumnos_comp > 0:
            diff_prom_alumnos = ((prom_alumnos_actual / prom_alumnos_comp) - 1) * 100
        except (ZeroDivisionError, TypeError):
            pass
            
        # Puntualidad
        puntualidad_actual = metricas_actual.get('puntualidad', {}).get('tasa', 0)
        puntualidad_comp = metricas_comparacion.get('puntualidad', {}).get('tasa', 0)
        
        try:
        if puntualidad_comp > 0:
            diff_puntualidad = ((puntualidad_actual / puntualidad_comp) - 1) * 100
        except (ZeroDivisionError, TypeError):
            pass
            
        # Total de clases
        clases_actual = len(metricas_actual.get('clases', []))
        clases_comp = len(metricas_comparacion.get('clases', []))
        
        try:
        if clases_comp > 0:
            diff_clases = ((clases_actual / clases_comp) - 1) * 100
        except (ZeroDivisionError, TypeError):
            pass
            
        # Variedad de clases
        variedad_actual = metricas_actual.get('variedad_clases', 0)
        variedad_comp = metricas_comparacion.get('variedad_clases', 0)
        
        try:
        if variedad_comp > 0:
            diff_variedad = ((variedad_actual / variedad_comp) - 1) * 100
        except (ZeroDivisionError, TypeError):
            pass
            
        # Distribución por tipo
        tipos_actual = metricas_actual.get('distribucion', {}).get('tipos', {})
        tipos_comp = metricas_comparacion.get('distribucion', {}).get('tipos', {})
        
        diff_tipos = {}
        try:
        for tipo in set(list(tipos_actual.keys()) + list(tipos_comp.keys())):
            actual = tipos_actual.get(tipo, 0)
            comp = tipos_comp.get(tipo, 0)
            
                try:
            if comp > 0:
                diff_tipos[tipo] = ((actual / comp) - 1) * 100
            else:
                diff_tipos[tipo] = 100 if actual > 0 else 0
                except (ZeroDivisionError, TypeError):
                    diff_tipos[tipo] = 0
        except Exception as e:
            print(f"Error al calcular diferencias por tipo: {str(e)}")
            diff_tipos = {}
                
        # Calcular diferencia global usando pesos recalibrados (sin variedad de clases)
        diff_global = (
            0.45 * diff_prom_alumnos +
            0.30 * diff_puntualidad +
            0.25 * diff_clases
            # Variedad de clases eliminada del cálculo por solicitud
        )
        
        # Extraer nombres de meses para mostrar en la UI
        # Los nombres de meses ahora deben venir en los parámetros o se calculan arriba
        mes_actual_nombre = metricas_actual.get('mes_actual_nombre', "Mes actual")
        mes_comparacion_nombre = metricas_comparacion.get('mes_comparacion_nombre', "Mes comparación")
        
        # Construir y retornar el resultado
        return {
            'global': diff_global,
            'promedio_alumnos': diff_prom_alumnos,
            'puntualidad': diff_puntualidad,
            'total_clases': diff_clases,
            'variedad_clases': diff_variedad,
            'distribucion_tipos': diff_tipos,
            'mes_actual': {
                'promedio_alumnos': prom_alumnos_actual,
                'puntualidad': puntualidad_actual,
                'total_clases': clases_actual,
                'variedad_clases': variedad_actual
            },
            'mes_comparacion': {
                'promedio_alumnos': prom_alumnos_comp,
                'puntualidad': puntualidad_comp,
                'total_clases': clases_comp,
                'variedad_clases': variedad_comp
            },
            'mes_actual_nombre': mes_actual_nombre,
            'mes_comparacion_nombre': mes_comparacion_nombre
        }
    except Exception as e:
        print(f"Error en comparar_metricas_mensuales: {str(e)}")
        return {
            'error': f"Error al comparar métricas: {str(e)}",
            'global': 0,
            'promedio_alumnos': 0,
            'puntualidad': 0,
            'total_clases': 0,
            'variedad_clases': 0,
            'distribucion_tipos': {},
            'mes_actual': {
                'promedio_alumnos': 0,
                'puntualidad': 0,
                'total_clases': 0,
                'variedad_clases': 0
            },
            'mes_comparacion': {
                'promedio_alumnos': 0,
                'puntualidad': 0,
                'total_clases': 0,
                'variedad_clases': 0
            },
            'mes_actual_nombre': "Mes actual",
            'mes_comparacion_nombre': "Mes comparación"
        } 