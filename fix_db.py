#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para corregir y crear la base de datos cuando hay problemas con el contexto de Flask.
Este script usa SQLite directamente para crear las tablas esenciales.
"""

import sqlite3
import os
import sys
from datetime import datetime

def check_database(db_path="gimnasio.db"):
    """
    Verifica la base de datos SQLite directamente, sin necesidad de contexto Flask.
    Comprueba si la base de datos existe, si tiene las tablas necesarias y su estructura.
    """
    print(f"Inicializando base de datos en: {db_path}")
    
    # Verificar si el archivo de la base de datos existe
    if not os.path.exists(db_path):
        print("Base de datos no encontrada. Creando nueva base de datos...")
        
        # Crear conexión (esto creará el archivo si no existe)
        conn = sqlite3.connect(db_path)
        conn.close()
        
        # Ya que es una nueva base de datos, necesitamos ejecutar el script de creación
        try:
            os.system(f"python create_db.py")
            print("Base de datos creada con scripts estándar")
            return True
        except Exception as e:
            print(f"Error al crear la base de datos: {str(e)}")
            return False
    
    # La base de datos existe, verificar su estructura
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar las tablas existentes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables if not table[0].startswith('sqlite_')]
        
        print(f"Base de datos existente con {len(table_names)} tablas")
        
        # Verificar si las tablas principales existen
        required_tables = ['profesor', 'horario_clase', 'clase_realizada', 'evento_horario']
        missing_tables = [table for table in required_tables if table not in table_names]
        
        # Mostrar tablas encontradas
        print(f"Tablas encontradas: {', '.join(table_names[:5])}")
        if len(table_names) > 5:
            print(f"Tablas encontradas: {', '.join(table_names[:5])}...")
        
        # Verificar si existe la columna 'activo' en horario_clase
        cursor.execute("PRAGMA table_info(horario_clase)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'activo' not in column_names:
            print("La columna 'activo' no existe en la tabla horario_clase. Añadiendo...")
            try:
                # Añadir la columna activo con valor predeterminado True (1)
                cursor.execute("ALTER TABLE horario_clase ADD COLUMN activo INTEGER DEFAULT 1")
                conn.commit()
                print("Columna 'activo' añadida correctamente")
            except Exception as e:
                print(f"Error al añadir columna 'activo': {str(e)}")
        
        conn.close()
        
        # Si faltan tablas requeridas, crear la base de datos
        if missing_tables:
            print(f"Faltan tablas requeridas: {', '.join(missing_tables)}")
            print("Reparando base de datos...")
            os.system(f"python create_db.py")
        else:
            print("Base de datos creada o verificada correctamente")
        
        return True
        
    except Exception as e:
        print(f"Error al verificar la base de datos: {str(e)}")
        return False

if __name__ == "__main__":
    if check_database():
        sys.exit(0)  # Éxito
    else:
        sys.exit(1)  # Error 