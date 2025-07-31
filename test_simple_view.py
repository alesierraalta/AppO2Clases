#!/usr/bin/env python3
"""
Test script para probar la nueva vista simple de informes
"""

import requests
from datetime import datetime

def test_simple_view():
    """Probar la vista simple del informe"""
    print("🔍 Probando Vista Simple del Informe...")
    
    # URL del endpoint con parámetros para vista simple
    url = "http://localhost:5000/informes/mensual"
    params = {
        'mes': 1,
        'anio': 2025,
        'auto': 1  # Sin export=pdf para vista HTML simple
    }
    
    try:
        print(f"📤 Enviando GET request a: {url}")
        print(f"📤 Parámetros: {params}")
        
        response = requests.get(url, params=params)
        
        print(f"📥 Status Code: {response.status_code}")
        print(f"📥 Content-Type: {response.headers.get('Content-Type')}")
        print(f"📥 Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            if 'text/html' in response.headers.get('Content-Type', ''):
                print("✅ Vista simple HTML generada correctamente")
                
                # Verificar que contiene las secciones esperadas
                content = response.text
                if 'Métricas Mensuales Básicas' in content:
                    print("✅ Sección de métricas básicas encontrada")
                else:
                    print("⚠️ Sección de métricas básicas NO encontrada")
                
                if 'Métricas por Profesor' in content:
                    print("✅ Sección de métricas por profesor encontrada")
                else:
                    print("⚠️ Sección de métricas por profesor NO encontrada")
                
                # Verificar que NO contiene elementos complejos
                if 'GuÃ­a de navegaciÃ³n del informe' not in content:
                    print("✅ Vista simplificada - sin navegación compleja")
                else:
                    print("⚠️ Contiene elementos complejos (no debería)")
                    
            else:
                print("⚠️ Respuesta no es HTML")
                print(f"📄 Content-Type: {response.headers.get('Content-Type')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"❌ Respuesta: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error en test_simple_view: {e}")

def test_pdf_charts_still_works():
    """Verificar que PDF con gráficos sigue funcionando"""
    print("\n🔍 Verificando que PDF con Gráficos sigue funcionando...")
    
    url = "http://localhost:5000/informes/mensual/pdf-with-charts"
    
    test_data = {
        'month': 1,
        'year': 2025,
        'includeCharts': True,
        'charts': {
            'test_chart': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
        }
    }
    
    try:
        response = requests.post(url, json=test_data, headers={'Content-Type': 'application/json'})
        
        print(f"📥 Status Code: {response.status_code}")
        print(f"📥 Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
            print("✅ PDF con gráficos sigue funcionando correctamente")
        else:
            print("❌ PDF con gráficos tiene problemas")
            
    except Exception as e:
        print(f"❌ Error en test_pdf_charts_still_works: {e}")

def main():
    """Función principal"""
    print("=" * 60)
    print("PRUEBA DE VISTA SIMPLE VS PDF CON GRÁFICOS")
    print("=" * 60)
    print(f"Hora de inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_simple_view()
    test_pdf_charts_still_works()
    
    print("\n" + "=" * 60)
    print("PRUEBAS COMPLETADAS")
    print("=" * 60)
    print("Resultados esperados:")
    print("• Informe Simple: HTML con métricas básicas y lista de profesores")
    print("• PDF con Gráficos: Descarga PDF completo con análisis avanzado")

if __name__ == "__main__":
    main()