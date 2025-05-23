#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar la página de horarios
"""

import requests
import time

def test_horarios_page():
    """
    Prueba si la página de horarios está funcionando correctamente
    """
    try:
        print("Probando la página de horarios...")
        
        # Test main page first
        main_response = requests.get('http://127.0.0.1:5000', timeout=10)
        print(f"Main page status: {main_response.status_code}")
        
        if main_response.status_code != 200:
            print("❌ La aplicación no está funcionando")
            return False
        
        # Test horarios page
        response = requests.get('http://127.0.0.1:5000/horarios', timeout=10)
        print(f"Horarios page status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error en página de horarios: {response.status_code}")
            return False
        
        # Check content
        content = response.text
        print(f"Page length: {len(content)} characters")
        
        # Check for key elements
        has_tbody = 'tbody' in content
        has_data_tipo = 'data-tipo=' in content
        has_horario_name = 'horario.nombre' in content
        has_checkbox = 'checkbox-horario' in content
        
        print(f"Contains tbody: {has_tbody}")
        print(f"Contains data-tipo: {has_data_tipo}")
        print(f"Contains horario.nombre: {has_horario_name}")
        print(f"Contains checkbox: {has_checkbox}")
        
        # Check for specific horario rows
        import re
        horario_rows = re.findall(r'<tr[^>]+data-tipo=', content)
        print(f"Found {len(horario_rows)} horario rows")
        
        if len(horario_rows) > 0:
            print("✅ La página de horarios está mostrando datos correctamente")
            return True
        else:
            print("⚠️ La página carga pero no muestra horarios")
            
            # Check for "No hay horarios" message
            if "No hay horarios de clases registrados" in content:
                print("📝 Mensaje: No hay horarios registrados")
            else:
                print("❌ La tabla de horarios parece estar vacía sin mensaje explicativo")
            
            return False
        
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a la aplicación. ¿Está ejecutándose?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_horarios_page() 