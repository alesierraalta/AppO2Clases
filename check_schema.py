#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar el esquema actual de la base de datos
y compararlo con lo que espera la aplicación
"""

import sqlite3
import sys
import os

def check_table_schema(table_name, db_path="gimnasio.db"):
    """Verifica el esquema de una tabla específica"""
    if not os.path.exists(db_path):
        print(f"ERROR: La base de datos {db_path} no existe.")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar que la tabla existe
        cursor.execute(f"""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='{table_name}'
        """)
        
        if not cursor.fetchone():
            print(f'ERROR: La tabla {table_name} no existe.')
            return None
        
        # Obtener información de las columnas
        cursor.execute(f'PRAGMA table_info({table_name})')
        columns = cursor.fetchall()
        
        print(f"\nEsquema actual de la tabla '{table_name}':")
        print("-" * 50)
        for col in columns:
            col_id, name, data_type, not_null, default_value, pk = col
            nullable = "NOT NULL" if not_null else "NULL"
            default = f"DEFAULT {default_value}" if default_value is not None else ""
            primary = "PRIMARY KEY" if pk else ""
            print(f"  {name:<20} {data_type:<15} {nullable:<8} {default:<15} {primary}")
        
        conn.close()
        return [col[1] for col in columns]  # Retorna solo los nombres de columnas
        
    except Exception as e:
        print(f'Error verificando tabla {table_name}: {e}')
        return None

def main():
    """Función principal"""
    print("=== VERIFICACIÓN DE ESQUEMA DE BASE DE DATOS ===")
    
    # Verificar todas las tablas importantes
    tables_to_check = ['profesor', 'horario_clase', 'clase_realizada', 'evento_horario', 'notificacion']
    
    for table in tables_to_check:
        columns = check_table_schema(table)
        if columns:
            print(f"Columnas encontradas: {len(columns)}")
        print()
    
    # Verificar específicamente la tabla clase_realizada que está causando problemas
    print("=== ANÁLISIS ESPECÍFICO DE CLASE_REALIZADA ===")
    
    expected_columns = [
        'id', 'fecha', 'horario_id', 'profesor_id', 
        'hora_llegada_profesor', 'cantidad_alumnos', 
        'observaciones', 'fecha_registro', 'audio_file'
    ]
    
    actual_columns = check_table_schema('clase_realizada')
    
    if actual_columns:
        print(f"\nColumnas esperadas por la aplicación:")
        for col in expected_columns:
            status = "✓ EXISTE" if col in actual_columns else "✗ FALTA"
            print(f"  {col:<25} {status}")
        
        print(f"\nColumnas que existen pero no se esperan:")
        extra_columns = [col for col in actual_columns if col not in expected_columns]
        if extra_columns:
            for col in extra_columns:
                print(f"  {col:<25} ⚠ EXTRA")
        else:
            print("  Ninguna")

if __name__ == '__main__':
    main() 