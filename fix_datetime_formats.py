#!/usr/bin/env python
"""
Script to check and fix datetime formats in the database
"""
import os
import sqlite3
from dateutil import parser
import json

def fix_datetime_formats():
    print("Comprobando y corrigiendo formatos de fecha en la base de datos...")
    
    conn = sqlite3.connect('gimnasio.db')
    cursor = conn.cursor()
    
    # Check for evento_horario table with datetime columns
    cursor.execute("PRAGMA table_info(evento_horario)")
    columns = cursor.fetchall()
    date_columns = []
    
    for col in columns:
        col_name = col[1]
        col_type = col[2].upper()
        if 'DATE' in col_type or 'TIME' in col_type:
            date_columns.append(col_name)
    
    print(f"Columnas de fecha/hora en la tabla evento_horario: {date_columns}")
    
    # Display a sample of date strings for each column
    for col in date_columns:
        try:
            cursor.execute(f"SELECT {col} FROM evento_horario WHERE {col} IS NOT NULL LIMIT 5")
            sample_rows = cursor.fetchall()
            print(f"Muestra de valores en columna {col}:")
            for row in sample_rows:
                print(f"  - {row[0]}")
        except Exception as e:
            print(f"Error al obtener muestra de columna {col}: {str(e)}")
    
    # For each date column, check for problematic formats
    problematic_rows = []
    
    for col in date_columns:
        try:
            cursor.execute(f"SELECT id, {col} FROM evento_horario WHERE {col} IS NOT NULL")
            rows = cursor.fetchall()
            
            print(f"Comprobando columna {col} ({len(rows)} registros)...")
            
            for row_id, date_str in rows:
                if not date_str:
                    continue
                    
                if isinstance(date_str, str):
                    try:
                        # Try to parse with dateutil
                        parser.parse(date_str)
                    except Exception as e:
                        print(f"  Formato problemático en id={row_id}, {col}='{date_str}': {str(e)}")
                        problematic_rows.append((row_id, col, date_str))
        except Exception as e:
            print(f"Error al comprobar columna {col}: {str(e)}")
    
    if problematic_rows:
        print(f"Se encontraron {len(problematic_rows)} registros con formatos de fecha problemáticos.")
        
        # Auto-fix without asking for confirmation
        fixed = 0
        
        for row_id, col, date_str in problematic_rows:
            try:
                # Extract date components manually if needed
                fixed_date = None
                
                # Common patterns: try to extract parts manually
                if 'T' in date_str:  # ISO-like format
                    parts = date_str.replace('T', ' ').split(' ')
                    if len(parts) >= 2:
                        date_part = parts[0]
                        time_part = parts[1]
                        
                        # Remove problematic characters
                        time_part = time_part.split('.')[0]  # Remove milliseconds
                        
                        fixed_date = f"{date_part} {time_part}"
                else:
                    # Other formats: try to clean up
                    fixed_date = date_str.split('.')[0]  # Remove milliseconds
                
                if fixed_date:
                    # Update the database
                    cursor.execute(f"UPDATE evento_horario SET {col} = ? WHERE id = ?", 
                                  (fixed_date, row_id))
                    fixed += 1
                    print(f"  Corregido: id={row_id}, {col}: '{date_str}' -> '{fixed_date}'")
            except Exception as e:
                print(f"  Error al corregir id={row_id}: {str(e)}")
        
        conn.commit()
        print(f"Se corrigieron {fixed} registros.")
    else:
        print("No se encontraron formatos de fecha problemáticos.")
    
    # Check datos_adicionales JSON for date values
    print("\nComprobando datos_adicionales para valores de fecha...")
    
    cursor.execute("SELECT id, datos_adicionales FROM evento_horario WHERE datos_adicionales IS NOT NULL")
    rows = cursor.fetchall()
    
    print(f"Comprobando {len(rows)} registros con datos_adicionales...")
    
    json_problems = []
    
    for row_id, json_data in rows:
        if not json_data:
            continue
            
        try:
            # Parse JSON data
            data = json.loads(json_data)
            
            # Check for date-like strings in the data
            date_issues = []
            
            def check_value(key, value):
                if isinstance(value, str) and ('T' in value or '-' in value) and ':' in value:
                    # Might be a date string
                    try:
                        parser.parse(value)
                    except Exception:
                        date_issues.append((key, value))
            
            # Recursively check all values
            def check_dict(data, prefix=''):
                for key, value in data.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    
                    if isinstance(value, dict):
                        check_dict(value, full_key)
                    elif isinstance(value, list):
                        for i, item in enumerate(value):
                            if isinstance(item, dict):
                                check_dict(item, f"{full_key}[{i}]")
                            else:
                                check_value(f"{full_key}[{i}]", item)
                    else:
                        check_value(full_key, value)
            
            check_dict(data)
            
            if date_issues:
                json_problems.append((row_id, date_issues))
                print(f"  Problemas en id={row_id}: {date_issues}")
        except Exception as e:
            print(f"  Error al analizar JSON en id={row_id}: {str(e)}")
    
    if json_problems:
        print(f"Se encontraron problemas de fecha en {len(json_problems)} JSON de datos_adicionales.")
        # We won't fix these automatically as they're more complex
    else:
        print("No se encontraron problemas de fecha en datos_adicionales.")
    
    # Close connection
    conn.close()
    print("Comprobación y corrección completadas")

if __name__ == "__main__":
    fix_datetime_formats() 