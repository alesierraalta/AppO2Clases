#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para corregir y crear la base de datos cuando hay problemas con el contexto de Flask.
Este script usa SQLite directamente para crear las tablas esenciales.
"""

import sqlite3
import os
import sys
import subprocess
from datetime import datetime

def run_script(script_name):
    """Ejecuta un script de Python y devuelve el código de salida"""
    try:
        result = subprocess.run(['python', script_name], capture_output=True, text=True)
        print(f"Salida de {script_name}:\n{result.stdout}")
        if result.stderr:
            print(f"Errores de {script_name}:\n{result.stderr}")
        return result.returncode
    except Exception as e:
        print(f"Error al ejecutar {script_name}: {str(e)}")
        return 1

def check_database(db_path="gimnasio.db"):
    """
    Verifica la base de datos SQLite directamente, sin necesidad de contexto Flask.
    Comprueba si la base de datos existe, si tiene las tablas necesarias y su estructura.
    """
    print(f"Inicializando base de datos en: {db_path}")
    
    # Verificar si el archivo de la base de datos existe
    if not os.path.exists(db_path):
        print("Base de datos no encontrada. Creando nueva base de datos...")
        
        # Intentar varios métodos para crear la base de datos
        # Método 1: Ejecutar create_db.py
        print("Método 1: Ejecutando create_db.py...")
        if run_script('create_db.py') == 0:
            return True
            
        # Método 2: Ejecutar create_tables.py
        print("Método 2: Ejecutando create_tables.py...")
        if run_script('create_tables.py') == 0:
            return True
        
        # Método 3: Crear manualmente con SQLite
        print("Método 3: Creando base de datos manualmente...")
        try:
            conn = sqlite3.connect(db_path)
            conn.close()
            print("Base de datos creada correctamente (método manual)")
            return True
        except Exception as e:
            print(f"Error al crear la base de datos manualmente: {str(e)}")
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
        print(f"Tablas encontradas: {', '.join(table_names) if table_names else 'Ninguna'}")
        
        # Verificar si las tablas principales existen
        required_tables = ['profesor', 'horario_clase', 'clase_realizada', 'evento_horario']
        missing_tables = [table for table in required_tables if table not in table_names]
        
        # Si no hay tablas o faltan tablas requeridas, intentar crearlas
        if not table_names or missing_tables:
            conn.close()
            
            if missing_tables:
                print(f"Faltan tablas requeridas: {', '.join(missing_tables)}")
            else:
                print("La base de datos está vacía. Creando tablas...")
            
            print("Reparando base de datos...")
            
            # Probar diferentes métodos para crear las tablas
            # Método 1: Ejecutar create_db.py
            print("Método 1: Ejecutando create_db.py...")
            if run_script('create_db.py') == 0:
                return True
                
            # Método 2: Ejecutar create_tables.py
            print("Método 2: Ejecutando create_tables.py...")
            if run_script('create_tables.py') == 0:
                return True
                
            # Si llegamos aquí, no se pudieron crear las tablas
            print("ERROR: No se pudieron crear las tablas requeridas.")
            return False
        
        # Si existen las tablas requeridas, verificar la columna 'activo' en horario_clase
        try:
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
            
            if 'fecha_desactivacion' not in column_names:
                print("La columna 'fecha_desactivacion' no existe en la tabla horario_clase. Añadiendo...")
                try:
                    # Añadir la columna fecha_desactivacion como nullable
                    cursor.execute("ALTER TABLE horario_clase ADD COLUMN fecha_desactivacion DATE")
                    conn.commit()
                    print("Columna 'fecha_desactivacion' añadida correctamente")
                except Exception as e:
                    print(f"Error al añadir columna 'fecha_desactivacion': {str(e)}")
        except Exception as e:
            print(f"Error al verificar columnas de horario_clase: {str(e)}")
        
        conn.close()
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