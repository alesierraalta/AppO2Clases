#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar y agregar columnas faltantes en la base de datos
"""

import sys
import sqlite3

def verify_and_add_columns():
    """Verifica y agrega columnas faltantes en las tablas"""
    try:
        conn = sqlite3.connect('gimnasio.db')
        cursor = conn.cursor()
        
        # Verificar si existe la tabla horario_clase
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='horario_clase';")
        if cursor.fetchone():
            # Verificar si existe la columna activo
            cursor.execute("PRAGMA table_info(horario_clase);")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'activo' not in columns:
                print("Agregando columna 'activo' a la tabla horario_clase...")
                cursor.execute("ALTER TABLE horario_clase ADD COLUMN activo BOOLEAN DEFAULT 1;")
                conn.commit()
                print("Columna 'activo' agregada exitosamente.")
            else:
                print("Columna 'activo' ya existe en horario_clase.")
        else:
            print("Tabla horario_clase no existe. Esto es normal si usa un esquema diferente.")
        
        # Verificar otras tablas comunes
        tables_to_check = ['profesor', 'horario', 'clase']
        for table in tables_to_check:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
            if cursor.fetchone():
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'activo' not in columns:
                    print(f"Agregando columna 'activo' a la tabla {table}...")
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN activo BOOLEAN DEFAULT 1;")
                    conn.commit()
                    print(f"Columna 'activo' agregada a {table}.")
        
        conn.close()
        print("Verificación de columnas completada exitosamente.")
        return True
        
    except Exception as e:
        print(f"ERROR al verificar/agregar columnas: {e}")
        return False

if __name__ == '__main__':
    success = verify_and_add_columns()
    sys.exit(0 if success else 1)