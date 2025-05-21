#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para corregir y crear la base de datos de forma independiente,
sin necesidad de contexto de Flask. Utiliza SQLite directamente.
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

def create_tables_directly():
    """Crear las tablas directamente en SQLite sin depender de otros scripts"""
    print("Creando tablas directamente con SQLite...")
    try:
        conn = sqlite3.connect('gimnasio.db')
        cursor = conn.cursor()
        
        # Crear tabla profesor
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS profesor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            tarifa_por_clase REAL NOT NULL,
            telefono TEXT,
            email TEXT
        )
        ''')
        
        # Crear tabla horario_clase
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS horario_clase (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            dia_semana INTEGER NOT NULL,
            hora_inicio TEXT NOT NULL,
            duracion INTEGER DEFAULT 60,
            profesor_id INTEGER NOT NULL,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
            capacidad_maxima INTEGER DEFAULT 20,
            tipo_clase TEXT DEFAULT 'OTRO',
            activo INTEGER DEFAULT 1,
            fecha_desactivacion DATE,
            FOREIGN KEY (profesor_id) REFERENCES profesor (id)
        )
        ''')
        
        # Crear tabla clase_realizada
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clase_realizada (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            horario_id INTEGER NOT NULL,
            profesor_id INTEGER NOT NULL,
            hora_llegada_profesor TEXT,
            cantidad_alumnos INTEGER DEFAULT 0,
            observaciones TEXT,
            fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,
            audio_file TEXT,
            FOREIGN KEY (horario_id) REFERENCES horario_clase (id),
            FOREIGN KEY (profesor_id) REFERENCES profesor (id)
        )
        ''')
        
        # Crear tabla evento_horario
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS evento_horario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            horario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP,
            fecha_aplicacion DATE,
            motivo TEXT,
            datos_adicionales TEXT,
            FOREIGN KEY (horario_id) REFERENCES horario_clase (id)
        )
        ''')
        
        # Crear tabla notificacion (si no existe ya)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notificacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            destinatario TEXT,
            fecha_programada DATETIME,
            estado TEXT DEFAULT 'pendiente',
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            fecha_envio DATETIME,
            datos_adicionales TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        print("Tablas creadas directamente con éxito")
        return True
    except Exception as e:
        print(f"Error al crear tablas directamente: {str(e)}")
        return False

def check_database(db_path="gimnasio.db"):
    """
    Verifica la base de datos SQLite directamente, sin necesidad de contexto Flask.
    Comprueba si la base de datos existe, si tiene las tablas necesarias y su estructura.
    """
    print(f"Inicializando base de datos en: {db_path}")
    
    # Verificar si el archivo de la base de datos existe
    if not os.path.exists(db_path):
        print("Base de datos no encontrada. Creando nueva base de datos...")
        
        # Método 1: Crear la base de datos y tablas directamente (más confiable)
        if create_tables_directly():
            print("Base de datos y tablas creadas directamente con éxito")
            return True
        
        # Método 2: Ejecutar create_tables.py que también tiene método directo
        print("Método 2: Ejecutando create_tables.py...")
        if run_script('create_tables.py') == 0:
            return True
        
        # Método 3: Ejecutar create_db.py (requiere contexto Flask)
        print("Método 3: Ejecutando create_db.py...")
        if run_script('create_db.py') == 0:
            return True
        
        # Si llegamos aquí, todos los métodos fallaron
        print("ERROR: No se pudo crear la base de datos.")
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
            
            # Método 1: Crear las tablas directamente (más confiable)
            if create_tables_directly():
                print("Tablas creadas directamente con éxito")
                return True
                
            # Método 2: Ejecutar create_tables.py
            print("Método 2: Ejecutando create_tables.py...")
            if run_script('create_tables.py') == 0:
                return True
                
            # Método 3: Ejecutar create_db.py
            print("Método 3: Ejecutando create_db.py...")
            if run_script('create_db.py') == 0:
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