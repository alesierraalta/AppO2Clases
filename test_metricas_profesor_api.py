#!/usr/bin/env python3
"""
Script para probar la API y los métodos de base de datos para las métricas de profesores.
"""
import sys
import os
import json
import time
import requests
from datetime import datetime, timedelta
import random

# Asegurar que los módulos del proyecto estén en el path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos necesarios
try:
    from models import Profesor, HorarioClase, ClaseRealizada, db, clear_metrics_cache
    from app import app
    DB_AVAILABLE = True
except ImportError:
    print("AVISO: No se pudieron importar los modelos directamente. Modo API solamente.")
    DB_AVAILABLE = False

# URL base para las pruebas de API
BASE_URL = "http://localhost:5000/api"  # Ajustar según la configuración

def test_api_get_profesores():
    """Prueba la obtención de la lista de profesores via API."""
    print("\n=== Prueba: Obtener lista de profesores ===")
    try:
        response = requests.get(f"{BASE_URL}/profesores")
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data['status']}")
            print(f"Total profesores: {len(data['data'])}")
            if data['data']:
                for i, profesor in enumerate(data['data'][:3], 1):  # Mostrar solo los primeros 3
                    print(f"{i}. {profesor['nombre']} {profesor['apellido']}")
                if len(data['data']) > 3:
                    print(f"... y {len(data['data']) - 3} más")
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error en la solicitud: {str(e)}")

def test_api_get_profesor(profesor_id):
    """Prueba la obtención de los datos de un profesor específico via API."""
    print(f"\n=== Prueba: Obtener datos del profesor ID={profesor_id} ===")
    try:
        response = requests.get(f"{BASE_URL}/profesores/{profesor_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data['status']}")
            profesor = data['data']
            print(f"Nombre: {profesor['nombre']} {profesor['apellido']}")
            print(f"Email: {profesor['email']}")
            print(f"Teléfono: {profesor['telefono']}")
        elif response.status_code == 404:
            print(f"Profesor con ID {profesor_id} no encontrado")
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error en la solicitud: {str(e)}")

def test_api_get_clases_profesor(profesor_id, periodo=30):
    """Prueba la obtención de las clases de un profesor específico via API."""
    print(f"\n=== Prueba: Obtener clases del profesor ID={profesor_id} (últimos {periodo} días) ===")
    try:
        response = requests.get(f"{BASE_URL}/profesores/{profesor_id}/clases", 
                               params={"periodo": periodo})
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data['status']}")
            clases = data['data']
            print(f"Total clases: {len(clases)}")
            if clases:
                for i, clase in enumerate(clases[:5], 1):  # Mostrar solo las primeras 5
                    print(f"{i}. {clase['fecha']} - {clase['nombre_clase']} - {clase['hora_inicio']} - " +
                          f"Alumnos: {clase['cantidad_alumnos']} - Puntualidad: {clase['puntualidad']}")
                if len(clases) > 5:
                    print(f"... y {len(clases) - 5} más")
            else:
                print("No hay clases registradas en el período seleccionado")
        elif response.status_code == 404:
            print(f"Profesor con ID {profesor_id} no encontrado")
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error en la solicitud: {str(e)}")

def test_api_get_metricas_profesor(profesor_id, periodo_meses=12, force_recalculate=False):
    """Prueba la obtención de métricas para un profesor específico via API."""
    print(f"\n=== Prueba: Obtener métricas del profesor ID={profesor_id} " +
          f"(últimos {periodo_meses} meses, recalculo forzado: {force_recalculate}) ===")
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/profesores/{profesor_id}/metricas", 
                               params={"periodo": periodo_meses, 
                                      "force_recalculate": "true" if force_recalculate else "false"})
        end_time = time.time()
        tiempo_respuesta = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data['status']}")
            print(f"Tiempo de respuesta: {tiempo_respuesta:.2f} segundos")
            
            if data['status'] == 'warning':
                print(f"Aviso: {data['message']}")
                return
                
            metricas = data['data']
            print(f"Total clases: {metricas['total_clases']}")
            
            if metricas['total_clases'] > 0:
                print(f"Tasa de puntualidad: {metricas['puntualidad']['tasa']:.2f}%")
                
                # Mostrar distribución por tipo de clase
                print("\nDistribución por tipo de clase:")
                for tipo, count in metricas['distribucion']['tipos'].items():
                    porcentaje = metricas['distribucion']['porcentajes'][tipo]
                    print(f"  - {tipo}: {count} clases ({porcentaje:.2f}%)")
                
                # Mostrar tendencia
                print(f"\nTendencia global: {metricas['tendencia_global']:.2f}%")
                print(f"Tendencia alumnos: {metricas['tendencias']['alumnos']:.2f}%")
                print(f"Tendencia puntualidad: {metricas['tendencias']['puntualidad']:.2f}%")
                
                # Mostrar algunas métricas por tipo de clase
                print("\nMétricas por tipo de clase:")
                for tipo, datos in metricas['datos_por_tipo'].items():
                    print(f"  - {tipo}: {datos['total_clases']} clases, " +
                          f"puntualidad {datos['tasa_puntualidad']:.2f}%, " +
                          f"promedio alumnos {datos['promedio_alumnos']:.2f}")
            else:
                print("No hay clases registradas en el período seleccionado")
        elif response.status_code == 404:
            print(f"Profesor con ID {profesor_id} no encontrado")
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error en la solicitud: {str(e)}")

def test_api_clear_cache():
    """Prueba la limpieza de caché de métricas via API."""
    print("\n=== Prueba: Limpiar caché de métricas ===")
    try:
        response = requests.post(f"{BASE_URL}/cache/metricas/clear")
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data['status']}")
            print(f"Mensaje: {data['message']}")
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error en la solicitud: {str(e)}")

def test_model_get_clases(profesor_id):
    """Prueba la obtención de clases usando métodos del modelo."""
    if not DB_AVAILABLE:
        print("\n=== Prueba: Obtener clases del profesor (Modo DB) ===")
        print("No disponible - No se pudieron importar los modelos")
        return
        
    print(f"\n=== Prueba: Obtener clases del profesor ID={profesor_id} usando el modelo ===")
    try:
        profesor = Profesor.query.get(profesor_id)
        if not profesor:
            print(f"Profesor con ID {profesor_id} no encontrado")
            return
            
        # Obtener clases de los últimos 30 días
        fecha_fin = datetime.now().date()
        fecha_inicio = fecha_fin - timedelta(days=30)
        clases = profesor.get_clases_periodo(fecha_inicio, fecha_fin)
        
        print(f"Nombre: {profesor.nombre} {profesor.apellido}")
        print(f"Total clases últimos 30 días: {len(clases)}")
        
        if clases:
            for i, clase in enumerate(clases[:5], 1):  # Mostrar solo las primeras 5
                print(f"{i}. {clase.fecha} - {clase.horario.nombre if clase.horario else 'N/A'} - " +
                      f"Alumnos: {clase.cantidad_alumnos} - Puntualidad: {clase.puntualidad}")
            if len(clases) > 5:
                print(f"... y {len(clases) - 5} más")
        else:
            print("No hay clases registradas en el período seleccionado")
    except Exception as e:
        print(f"Error al obtener clases: {str(e)}")

def test_model_calcular_metricas(profesor_id):
    """Prueba el cálculo de métricas usando métodos del modelo."""
    if not DB_AVAILABLE:
        print("\n=== Prueba: Calcular métricas del profesor (Modo DB) ===")
        print("No disponible - No se pudieron importar los modelos")
        return
        
    print(f"\n=== Prueba: Calcular métricas del profesor ID={profesor_id} usando el modelo ===")
    try:
        profesor = Profesor.query.get(profesor_id)
        if not profesor:
            print(f"Profesor con ID {profesor_id} no encontrado")
            return
            
        # Primera llamada - debería calcular desde cero
        print("Primera llamada (sin caché):")
        start_time = time.time()
        metricas = profesor.calcular_metricas(periodo_meses=12)
        end_time = time.time()
        tiempo_primera = end_time - start_time
        print(f"Tiempo de cálculo: {tiempo_primera:.2f} segundos")
        print(f"Total clases: {metricas['total_clases']}")
        
        # Segunda llamada - debería usar la caché
        print("\nSegunda llamada (con caché):")
        start_time = time.time()
        metricas = profesor.calcular_metricas(periodo_meses=12)
        end_time = time.time()
        tiempo_segunda = end_time - start_time
        print(f"Tiempo de cálculo: {tiempo_segunda:.2f} segundos")
        print(f"Mejora por caché: {(tiempo_primera / max(tiempo_segunda, 0.001)):.2f}x más rápido")
        
        # Tercera llamada - forzando recálculo
        print("\nTercera llamada (forzando recálculo):")
        start_time = time.time()
        metricas = profesor.calcular_metricas(periodo_meses=12, force_recalculate=True)
        end_time = time.time()
        tiempo_tercera = end_time - start_time
        print(f"Tiempo de cálculo: {tiempo_tercera:.2f} segundos")
        
        # Limpiar caché y medir una vez más
        print("\nLimpiando caché y realizando nueva llamada:")
        clear_metrics_cache(profesor_id)
        start_time = time.time()
        metricas = profesor.calcular_metricas(periodo_meses=12)
        end_time = time.time()
        tiempo_cuarta = end_time - start_time
        print(f"Tiempo de cálculo: {tiempo_cuarta:.2f} segundos")
    except Exception as e:
        print(f"Error al calcular métricas: {str(e)}")

def test_tipos_clase():
    """Prueba la obtención de tipos de clase disponibles."""
    if not DB_AVAILABLE:
        print("\n=== Prueba: Obtener tipos de clase (Modo DB) ===")
        print("No disponible - No se pudieron importar los modelos")
        return
        
    print("\n=== Prueba: Obtener tipos de clase disponibles ===")
    try:
        tipos = HorarioClase.obtener_tipos_clase()
        print(f"Tipos de clase disponibles: {', '.join(tipos)}")
        
        # Probar estadísticas por tipo
        print("\nEstadísticas por tipo de clase:")
        estadisticas = HorarioClase.estadisticas_por_tipo()
        
        for tipo, datos in estadisticas.items():
            print(f"{tipo}:")
            print(f"  - Total horarios: {datos['total_horarios']}")
            print(f"  - Horarios activos: {datos['horarios_activos']}")
            print(f"  - Clases realizadas: {datos['clases_realizadas']}")
    except Exception as e:
        print(f"Error al obtener tipos de clase: {str(e)}")

def test_ranking_profesores():
    """Prueba la obtención del ranking de profesores."""
    if not DB_AVAILABLE:
        print("\n=== Prueba: Obtener ranking de profesores (Modo DB) ===")
        print("No disponible - No se pudieron importar los modelos")
        return
        
    print("\n=== Prueba: Obtener ranking de profesores ===")
    try:
        # Probar los diferentes tipos de ranking
        for tipo in ['puntualidad', 'alumnos', 'clases']:
            print(f"\nRanking por {tipo}:")
            ranking = Profesor.obtener_ranking_profesores(tipo_metrica=tipo, limite=5)
            
            for i, prof in enumerate(ranking, 1):
                if tipo == 'puntualidad':
                    valor = f"{prof['puntualidad']:.2f}%"
                elif tipo == 'alumnos':
                    valor = f"{prof['promedio_alumnos']:.2f} alumnos/clase"
                else:  # 'clases'
                    valor = f"{prof['clases_por_mes']:.2f} clases/mes"
                    
                print(f"{i}. {prof['nombre']} {prof['apellido']} - {valor} ({prof['total_clases']} clases)")
    except Exception as e:
        print(f"Error al obtener ranking: {str(e)}")

def main():
    """Función principal para ejecutar todas las pruebas."""
    print("=== Iniciando pruebas de métricas de profesores ===")
    
    # Obtener ID de profesor para pruebas
    profesor_id = None
    
    if DB_AVAILABLE:
        # Intentar obtener el primer profesor disponible
        try:
            profesor = Profesor.query.first()
            if profesor:
                profesor_id = profesor.id
                print(f"Usando profesor para pruebas: {profesor.nombre} {profesor.apellido} (ID: {profesor_id})")
            else:
                print("No hay profesores en la base de datos")
        except Exception as e:
            print(f"Error al obtener profesor: {str(e)}")
    
    # Si no se encontró profesor, usar un ID predeterminado
    if profesor_id is None:
        profesor_id = int(input("Ingrese ID de profesor para pruebas: "))
    
    # Probar la API
    try:
        test_api_get_profesores()
        test_api_get_profesor(profesor_id)
        test_api_get_clases_profesor(profesor_id)
        
        # Prueba 1: Obtener métricas normales
        test_api_get_metricas_profesor(profesor_id)
        
        # Prueba 2: Forzar recálculo
        test_api_get_metricas_profesor(profesor_id, force_recalculate=True)
        
        # Prueba 3: Limpiar caché y obtener de nuevo
        test_api_clear_cache()
        test_api_get_metricas_profesor(profesor_id)
    except Exception as e:
        print(f"Error en pruebas de API: {str(e)}")
    
    # Probar los modelos (si están disponibles)
    if DB_AVAILABLE:
        try:
            test_model_get_clases(profesor_id)
            test_model_calcular_metricas(profesor_id)
            test_tipos_clase()
            test_ranking_profesores()
        except Exception as e:
            print(f"Error en pruebas de modelos: {str(e)}")
    
    print("\n=== Pruebas completadas ===")

if __name__ == "__main__":
    main() 