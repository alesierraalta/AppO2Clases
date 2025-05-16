#!/usr/bin/env python
"""
Script to fix the TipoEventoHorario enum values in the database by
converting all lowercase values to uppercase to match the enum definition.
"""
import os
import sqlite3
from sqlalchemy import create_engine, text
import sys

def check_and_fix_evento_horario():
    print("Comprobando y corrigiendo valores en tabla evento_horario...")
    conn = sqlite3.connect('gimnasio.db')
    cursor = conn.cursor()
    
    # Comprobar los valores actuales
    cursor.execute('SELECT id, tipo FROM evento_horario')
    rows = cursor.fetchall()
    
    print(f"Se encontraron {len(rows)} registros en evento_horario")
    
    # Contar casos por tipo
    tipos = {}
    for _, tipo in rows:
        if tipo not in tipos:
            tipos[tipo] = 0
        tipos[tipo] += 1
    
    print("Distribución de tipos:")
    for tipo, count in tipos.items():
        print(f"  - {tipo}: {count} registros")
    
    # Comprobar si hay valores en minúsculas
    lowercase_types = [t for t in tipos.keys() if t.islower()]
    if lowercase_types:
        print(f"¡Atención! Se encontraron {len(lowercase_types)} tipos en minúsculas: {lowercase_types}")
        
        # Actualizar registros a mayúsculas
        updates = 0
        for tipo_lower in lowercase_types:
            tipo_upper = tipo_lower.upper()
            cursor.execute('UPDATE evento_horario SET tipo = ? WHERE tipo = ?', (tipo_upper, tipo_lower))
            updates += cursor.rowcount
        
        conn.commit()
        print(f"Se actualizaron {updates} registros a mayúsculas")
    else:
        print("No se encontraron tipos en minúsculas, no es necesario hacer correcciones")
    
    # Verificar tipos después de la actualización
    cursor.execute('SELECT DISTINCT tipo FROM evento_horario')
    current_types = cursor.fetchall()
    print("Tipos actuales después de la actualización:")
    for tipo in current_types:
        print(f"  - {tipo[0]}")
    
    conn.close()
    print("Comprobación y corrección completadas")

if __name__ == "__main__":
    check_and_fix_evento_horario() 