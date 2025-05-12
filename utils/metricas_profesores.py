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
        
    total_alumnos = sum(c.cantidad_alumnos for c in clases if c.cantidad_alumnos is not None)
    return total_alumnos / len(clases)


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


def calcular_metricas_por_tipo_clase(clases):
    """
    Calcula métricas detalladas por cada tipo de clase.
    
    Args:
        clases (list): Lista de objetos ClaseRealizada
        
    Returns:
        dict: Diccionario con métricas por tipo de clase
    """
    if not clases:
        return {}
    
    # Agrupar clases por tipo
    clases_por_tipo = defaultdict(list)
    for clase in clases:
        tipo = clase.horario.tipo_clase if clase.horario and clase.horario.tipo_clase else "OTRO"
        clases_por_tipo[tipo].append(clase)
    
    # Asegurar que todos los tipos comunes estén presentes
    for tipo in ['MOVE', 'RIDE', 'BOX', 'OTRO']:
        if tipo not in clases_por_tipo:
            clases_por_tipo[tipo] = []
    
    # Calcular métricas por tipo
    resultado = {}
    total_clases = len(clases)
    
    for tipo, clases_tipo in clases_por_tipo.items():
        total_clases_tipo = len(clases_tipo)
        puntualidad = calcular_tasa_puntualidad(clases_tipo)
        
        # Calcular tendencia para este tipo de clase
        clases_tipo_ordenadas = sorted(clases_tipo, key=lambda c: c.fecha)
        if len(clases_tipo_ordenadas) >= 6:
            # Dividir en dos periodos
            mitad = len(clases_tipo_ordenadas) // 2
            primer_periodo = clases_tipo_ordenadas[:mitad]
            segundo_periodo = clases_tipo_ordenadas[mitad:]
            
            promedio_alumnos_1 = calcular_promedio_alumnos(primer_periodo)
            promedio_alumnos_2 = calcular_promedio_alumnos(segundo_periodo)
            
            if promedio_alumnos_1 > 0:
                tendencia = ((promedio_alumnos_2 / promedio_alumnos_1) - 1) * 100
            else:
                tendencia = 0
        else:
            tendencia = 0
        
        # Guardar resultados para este tipo
        resultado[tipo] = {
            'total_clases': total_clases_tipo,
            'promedio_alumnos': calcular_promedio_alumnos(clases_tipo) if clases_tipo else 0,
            'tasa_puntualidad': puntualidad['tasa'],
            'porcentaje_del_total': (total_clases_tipo / total_clases * 100) if total_clases > 0 else 0,
            'tendencia': tendencia
        }
    
    return resultado


def generar_datos_grafico(clases, tipo_grafico):
    """
    Genera datos en formato adecuado para gráficos con Chart.js.
    
    Args:
        clases (list): Lista de objetos ClaseRealizada
        tipo_grafico (str): Tipo de gráfico a generar ('puntualidad', 'alumnos', 'tipos', etc.)
        
    Returns:
        dict: Datos formateados para el gráfico correspondiente
    """
    if not clases:
        return {}
    
    if tipo_grafico == 'puntualidad':
        puntualidad = calcular_tasa_puntualidad(clases)
        etiquetas = ['Puntual', 'Retraso leve', 'Retraso significativo']
        valores = [
            puntualidad['puntual'],
            puntualidad['retraso_leve'],
            puntualidad['retraso_significativo']
        ]
        colores = [
            'rgba(40, 167, 69, 0.7)',  # Verde para puntual
            'rgba(255, 193, 7, 0.7)',  # Amarillo para retraso leve
            'rgba(220, 53, 69, 0.7)'   # Rojo para retraso significativo
        ]
        
        return {
            'tipo': 'pie',
            'etiquetas': etiquetas,
            'valores': valores,
            'colores': colores
        }
    
    elif tipo_grafico == 'tipos_clase':
        distribucion = calcular_distribucion_clases(clases)
        
        # Definir colores específicos para cada tipo
        colores_por_tipo = {
            'MOVE': 'rgba(40, 167, 69, 0.7)',  # Verde
            'RIDE': 'rgba(13, 110, 253, 0.7)',  # Azul
            'BOX': 'rgba(220, 53, 69, 0.7)',    # Rojo
            'OTRO': 'rgba(108, 117, 125, 0.7)'  # Gris
        }
        
        etiquetas = list(distribucion['tipos'].keys())
        valores = [distribucion['tipos'][tipo] for tipo in etiquetas]
        colores = [colores_por_tipo.get(tipo, 'rgba(0, 0, 0, 0.1)') for tipo in etiquetas]
        
        return {
            'tipo': 'bar',
            'etiquetas': etiquetas,
            'valores': valores,
            'colores': colores
        }
    
    elif tipo_grafico == 'evolucion_mensual':
        # Obtener datos mensuales
        tendencia = calcular_tendencia_asistencia(clases)
        datos_mensuales = tendencia['datos_mensuales']
        
        etiquetas = [dato['etiqueta'] for dato in datos_mensuales]
        valores_alumnos = [dato['promedio_alumnos'] for dato in datos_mensuales]
        valores_puntualidad = [dato['puntualidad'] for dato in datos_mensuales]
        
        datasets = [
            {
                'label': 'Promedio Alumnos',
                'data': valores_alumnos,
                'fill': False,
                'borderColor': 'rgb(54, 162, 235)',
                'tension': 0.1
            },
            {
                'label': 'Puntualidad (%)',
                'data': valores_puntualidad,
                'fill': False,
                'borderColor': 'rgb(40, 167, 69)',
                'tension': 0.1
            }
        ]
        
        return {
            'tipo': 'line',
            'etiquetas': etiquetas,
            'datasets': datasets
        }
    
    return {}


def calcular_metricas_profesor(profesor_id, clases):
    """
    Función principal que calcula todas las métricas para un profesor.
    
    Args:
        profesor_id (int): ID del profesor
        clases (list): Lista de objetos ClaseRealizada del profesor
        
    Returns:
        dict: Todas las métricas calculadas para el profesor
    """
    if not clases:
        return {
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
            },
            'promedio_profesores': {
                'puntualidad': 0,
                'alumnos': 0,
                'clases_por_mes': 0,
                'variedad_clases': 0
            },
            'ranking_profesores': []
        }
    
    # Ordenar clases por fecha descendente (más recientes primero)
    clases_ordenadas = sorted(clases, key=lambda c: c.fecha, reverse=True)
    
    # Calcular métricas básicas
    total_clases = len(clases)
    total_alumnos = sum(c.cantidad_alumnos for c in clases if c.cantidad_alumnos is not None)
    
    # Calcular puntualidad
    puntualidad = calcular_tasa_puntualidad(clases)
    
    # Calcular distribución por tipo de clase
    distribucion = calcular_distribucion_clases(clases)
    
    # Calcular tendencia de asistencia
    tendencia = calcular_tendencia_asistencia(clases)
    
    # Calcular métricas por tipo de clase
    datos_por_tipo = calcular_metricas_por_tipo_clase(clases)
    
    # Calcular clases por mes (promedio)
    fechas = [c.fecha for c in clases]
    if fechas:
        min_fecha = min(fechas)
        max_fecha = max(fechas)
        
        # Calcular diferencia en meses
        meses_diff = (max_fecha.year - min_fecha.year) * 12 + max_fecha.month - min_fecha.month
        if meses_diff > 0:
            clases_por_mes = total_clases / meses_diff
        else:
            clases_por_mes = total_clases
    else:
        clases_por_mes = 0
    
    # Calcular variedad de clases (porcentaje de tipos de clase diferentes)
    tipos_distintos = len([t for t, c in distribucion['tipos'].items() if c > 0])
    total_tipos_posibles = 4  # MOVE, RIDE, BOX, OTRO
    variedad_clases = (tipos_distintos / total_tipos_posibles) * 100
    
    # Calcular tendencias globales
    tendencia_global = tendencia['tendencia']
    
    # Preparar tendencias individuales
    if len(tendencia['datos_mensuales']) >= 2:
        datos_recientes = tendencia['datos_mensuales'][-3:]  # Últimos 3 meses o menos
        datos_antiguos = tendencia['datos_mensuales'][:-3]   # Meses anteriores
        
        if datos_antiguos and datos_recientes:
            # Promedios recientes
            prom_alumnos_reciente = np.mean([d['promedio_alumnos'] for d in datos_recientes])
            prom_puntualidad_reciente = np.mean([d['puntualidad'] for d in datos_recientes])
            prom_clases_mes_reciente = np.mean([d['total_clases'] for d in datos_recientes])
            
            # Promedios antiguos
            prom_alumnos_antiguo = np.mean([d['promedio_alumnos'] for d in datos_antiguos])
            prom_puntualidad_antiguo = np.mean([d['puntualidad'] for d in datos_antiguos])
            prom_clases_mes_antiguo = np.mean([d['total_clases'] for d in datos_antiguos])
            
            # Calcular tendencias porcentuales
            tendencia_alumnos = ((prom_alumnos_reciente / prom_alumnos_antiguo) - 1) * 100 if prom_alumnos_antiguo > 0 else 0
            tendencia_puntualidad = ((prom_puntualidad_reciente / prom_puntualidad_antiguo) - 1) * 100 if prom_puntualidad_antiguo > 0 else 0
            tendencia_clases_mes = ((prom_clases_mes_reciente / prom_clases_mes_antiguo) - 1) * 100 if prom_clases_mes_antiguo > 0 else 0
        else:
            tendencia_alumnos = 0
            tendencia_puntualidad = 0
            tendencia_clases_mes = 0
    else:
        tendencia_alumnos = 0
        tendencia_puntualidad = 0
        tendencia_clases_mes = 0
    
    # Añadir datos para comparativa (simulados - en producción vendrían de la BD)
    promedio_profesores = {
        'puntualidad': 85.0,
        'alumnos': 12.5,
        'clases_por_mes': 15.0,
        'variedad_clases': 75.0
    }
    
    # Simular datos de ranking (en producción vendrían de la BD)
    ranking_profesores = [
        {
            'id': 1,
            'nombre': 'Carlos',
            'apellido': 'García',
            'total_clases': 150,
            'puntualidad': 92.5,
            'promedio_alumnos': 15.8,
            'calificacion': 4.8
        },
        {
            'id': 2,
            'nombre': 'María',
            'apellido': 'López',
            'total_clases': 120,
            'puntualidad': 88.0,
            'promedio_alumnos': 14.2,
            'calificacion': 4.5
        },
        {
            'id': profesor_id,  # El profesor actual
            'nombre': 'Actual',
            'apellido': 'Profesor',
            'total_clases': total_clases,
            'puntualidad': puntualidad['tasa'],
            'promedio_alumnos': calcular_promedio_alumnos(clases),
            'calificacion': 4.0
        },
        {
            'id': 3,
            'nombre': 'Juan',
            'apellido': 'Martínez',
            'total_clases': 90,
            'puntualidad': 82.5,
            'promedio_alumnos': 11.5,
            'calificacion': 3.7
        },
        {
            'id': 4,
            'nombre': 'Ana',
            'apellido': 'Rodríguez',
            'total_clases': 75,
            'puntualidad': 78.0,
            'promedio_alumnos': 10.3,
            'calificacion': 3.5
        }
    ]
    
    # Preparar datos de clases para mostrar en tabla
    clases_con_puntualidad = []
    for clase in clases_ordenadas:
        estado_puntualidad = "N/A"
        if clase.hora_llegada_profesor:
            diferencia_minutos = ((clase.hora_llegada_profesor.hour * 60 + clase.hora_llegada_profesor.minute) - 
                                 (clase.horario.hora_inicio.hour * 60 + clase.horario.hora_inicio.minute))
            if diferencia_minutos <= 0:
                estado_puntualidad = "Puntual"
            elif diferencia_minutos <= 10:
                estado_puntualidad = "Retraso leve"
            else:
                estado_puntualidad = "Retraso significativo"
        
        clases_con_puntualidad.append({
            'fecha': clase.fecha,
            'horario': clase.horario,
            'hora_llegada_profesor': clase.hora_llegada_profesor,
            'cantidad_alumnos': clase.cantidad_alumnos,
            'puntualidad': estado_puntualidad
        })
    
    # Combinar todos los resultados
    return {
        'total_clases': total_clases,
        'total_alumnos': total_alumnos,
        'puntualidad': puntualidad,
        'distribucion': distribucion,
        'tendencia': tendencia,
        'datos_por_tipo': datos_por_tipo,
        'datos_mensuales': tendencia['datos_mensuales'],
        'clases': clases_con_puntualidad,
        'clases_por_mes': clases_por_mes,
        'variedad_clases': variedad_clases,
        'tendencia_global': tendencia_global,
        'tendencias': {
            'alumnos': tendencia_alumnos,
            'puntualidad': tendencia_puntualidad,
            'clases_por_mes': tendencia_clases_mes
        },
        'promedio_profesores': promedio_profesores,
        'ranking_profesores': ranking_profesores
    }


def generar_colores_chart(cantidad, tema_oscuro=False):
    """
    Genera una lista de colores para gráficos según la cantidad solicitada.
    
    Args:
        cantidad (int): Número de colores a generar
        tema_oscuro (bool): Si se debe usar la paleta para tema oscuro
        
    Returns:
        list: Lista de colores en formato rgba
    """
    # Paletas base
    paleta_claro = [
        'rgba(54, 162, 235, 0.7)',   # Azul
        'rgba(40, 167, 69, 0.7)',    # Verde
        'rgba(220, 53, 69, 0.7)',    # Rojo
        'rgba(255, 193, 7, 0.7)',    # Amarillo
        'rgba(111, 66, 193, 0.7)',   # Morado
        'rgba(23, 162, 184, 0.7)',   # Cian
        'rgba(255, 127, 80, 0.7)',   # Coral
        'rgba(128, 128, 128, 0.7)'   # Gris
    ]
    
    paleta_oscuro = [
        'rgba(54, 162, 235, 0.8)',   # Azul
        'rgba(40, 167, 69, 0.8)',    # Verde
        'rgba(220, 53, 69, 0.8)',    # Rojo
        'rgba(255, 193, 7, 0.8)',    # Amarillo
        'rgba(111, 66, 193, 0.8)',   # Morado
        'rgba(23, 162, 184, 0.8)',   # Cian
        'rgba(255, 127, 80, 0.8)',   # Coral
        'rgba(160, 160, 160, 0.8)'   # Gris
    ]
    
    paleta = paleta_oscuro if tema_oscuro else paleta_claro
    
    # Si se necesitan más colores de los disponibles en la paleta
    if cantidad > len(paleta):
        # Repetir la paleta tantas veces como sea necesario
        repeticiones = (cantidad // len(paleta)) + 1
        paleta_extendida = paleta * repeticiones
        return paleta_extendida[:cantidad]
    
    return paleta[:cantidad] 