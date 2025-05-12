#!/usr/bin/env python3
"""
Test script para verificar la funcionalidad de métricas de profesores.
Este script crea datos de prueba y muestra el resultado de los cálculos de métricas.
"""
import sys
import os
from datetime import datetime, timedelta
import json
import random

# Asegurar que los módulos del proyecto estén en el path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos necesarios
from utils.metricas_profesores import (
    calcular_tasa_puntualidad,
    calcular_promedio_alumnos,
    calcular_distribucion_clases,
    calcular_tendencia_asistencia,
    calcular_metricas_por_tipo_clase,
    generar_datos_grafico,
    calcular_metricas_profesor,
    generar_colores_chart
)

# Crear clases simuladas para pruebas
class HorarioClase:
    def __init__(self, id, nombre, tipo_clase, hora_inicio):
        self.id = id
        self.nombre = nombre
        self.tipo_clase = tipo_clase
        self.hora_inicio = hora_inicio

class ClaseRealizada:
    def __init__(self, id, horario, fecha, hora_llegada_profesor, cantidad_alumnos):
        self.id = id
        self.horario = horario
        self.fecha = fecha
        self.hora_llegada_profesor = hora_llegada_profesor
        self.cantidad_alumnos = cantidad_alumnos

def generar_datos_prueba(num_clases=50):
    """Genera datos de prueba para las métricas de profesor."""
    tipos_clase = ['MOVE', 'RIDE', 'BOX', 'OTRO']
    nombres_clase = {
        'MOVE': ['MOVE Básico', 'MOVE Avanzado', 'MOVE Funcional'],
        'RIDE': ['RIDE Intenso', 'RIDE Suave', 'RIDE Mixto'],
        'BOX': ['BOX Técnica', 'BOX Combat', 'BOX Fitness'],
        'OTRO': ['Funcional', 'Stretching', 'Yoga']
    }
    
    # Crear horarios de clase
    horarios = []
    for i in range(10):
        tipo = random.choice(tipos_clase)
        nombre = random.choice(nombres_clase[tipo])
        hora = datetime.strptime(f"{random.randint(8, 20)}:00", "%H:%M")
        horarios.append(HorarioClase(i+1, nombre, tipo, hora))
    
    # Crear clases realizadas
    clases = []
    fecha_base = datetime.now() - timedelta(days=180)  # 6 meses atrás
    
    for i in range(num_clases):
        horario = random.choice(horarios)
        fecha = fecha_base + timedelta(days=i)
        
        # Generar hora de llegada del profesor (puede ser puntual o con retraso)
        puntualidad = random.choices([0, 1, 2], weights=[70, 20, 10])[0]  # 0=puntual, 1=retraso leve, 2=retraso significativo
        
        if puntualidad == 0:
            # Puntual (llegada entre 15 min antes y justo a tiempo)
            minutos_diferencia = -random.randint(0, 15)
        elif puntualidad == 1:
            # Retraso leve (1-10 minutos)
            minutos_diferencia = random.randint(1, 10)
        else:
            # Retraso significativo (11-20 minutos)
            minutos_diferencia = random.randint(11, 20)
        
        hora_llegada = horario.hora_inicio + timedelta(minutes=minutos_diferencia)
        
        # Cantidad de alumnos (entre 5 y 20)
        alumnos = random.randint(5, 20)
        
        clases.append(ClaseRealizada(i+1, horario, fecha, hora_llegada, alumnos))
    
    return clases

def imprimir_resultados(metricas):
    """Imprime los resultados de las métricas calculadas."""
    print("\n=== MÉTRICAS DEL PROFESOR ===")
    print(f"Total de clases: {metricas['total_clases']}")
    print(f"Total de alumnos: {metricas['total_alumnos']}")
    print(f"Promedio de alumnos por clase: {metricas['total_alumnos'] / metricas['total_clases']:.2f}" if metricas['total_clases'] > 0 else "No hay clases")
    
    print("\n--- Puntualidad ---")
    print(f"Tasa de puntualidad: {metricas['puntualidad']['tasa']:.2f}%")
    print(f"Clases puntuales: {metricas['puntualidad']['puntual']}")
    print(f"Retrasos leves: {metricas['puntualidad']['retraso_leve']}")
    print(f"Retrasos significativos: {metricas['puntualidad']['retraso_significativo']}")
    
    print("\n--- Distribución por Tipo de Clase ---")
    for tipo, cantidad in metricas['distribucion']['tipos'].items():
        porcentaje = metricas['distribucion']['porcentajes'][tipo]
        print(f"{tipo}: {cantidad} clases ({porcentaje:.2f}%)")
    
    print("\n--- Métricas por Tipo de Clase ---")
    for tipo, datos in metricas['datos_por_tipo'].items():
        print(f"{tipo}:")
        print(f"  - Total clases: {datos['total_clases']}")
        print(f"  - Promedio alumnos: {datos['promedio_alumnos']:.2f}")
        print(f"  - Tasa puntualidad: {datos['tasa_puntualidad']:.2f}%")
        print(f"  - Tendencia: {datos['tendencia']:.2f}%")
    
    print("\n--- Tendencias ---")
    print(f"Tendencia global: {metricas['tendencia_global']:.2f}%")
    print(f"Tendencia alumnos: {metricas['tendencias']['alumnos']:.2f}%")
    print(f"Tendencia puntualidad: {metricas['tendencias']['puntualidad']:.2f}%")
    print(f"Tendencia clases por mes: {metricas['tendencias']['clases_por_mes']:.2f}%")
    
    print("\n--- Datos Mensuales ---")
    for mes in metricas['datos_mensuales']:
        print(f"{mes['etiqueta']}: {mes['total_clases']} clases, {mes['promedio_alumnos']:.2f} alumnos, {mes['puntualidad']:.2f}% puntualidad")

def main():
    """Función principal del script de prueba."""
    print("Generando datos de prueba...")
    clases = generar_datos_prueba(100)
    print(f"Se generaron {len(clases)} clases de prueba.")
    
    # Calcular métricas
    print("Calculando métricas...")
    metricas = calcular_metricas_profesor(1, clases)
    
    # Mostrar resultados
    imprimir_resultados(metricas)
    
    print("\nPrueba completada con éxito.")

if __name__ == "__main__":
    main() 