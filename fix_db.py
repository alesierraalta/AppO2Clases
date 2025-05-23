#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para reparar y verificar la base de datos SQLite
Maneja la creación y reparación de tablas de forma robusta
"""

import sqlite3
import subprocess
import sys
import os
from sqlalchemy import create_engine, MetaData, Table

def run_script(script_name):
    """Ejecuta un script Python y retorna el código de salida"""
    try:
        result = subprocess.run([sys.executable, script_name], 
                               capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f"✓ {script_name} ejecutado exitosamente")
        else:
            print(f"✗ {script_name} falló: {result.stderr}")
        return result.returncode
    except Exception as e:
        print(f"Error ejecutando {script_name}: {str(e)}")
        return 1

def create_tables_directly():
    """Crear las tablas directamente usando SQL sin depender de SQLAlchemy"""
    try:
        print("Método directo: Creando tablas con SQLite...")
        conn = sqlite3.connect('gimnasio.db')
        cursor = conn.cursor()
        
        # Crear tabla profesor
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profesor (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR(100) NOT NULL,
                apellido VARCHAR(100) NOT NULL,
                telefono VARCHAR(20),
                email VARCHAR(120),
                fecha_contratacion DATE,
                activo BOOLEAN DEFAULT 1
            )
        ''')
        print("✓ Tabla 'profesor' creada")
        
        # Crear tabla horario_clase con todas las columnas necesarias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS horario_clase (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR(100) NOT NULL,
                dia_semana INTEGER NOT NULL,
                hora_inicio TIME NOT NULL,
                duracion INTEGER NOT NULL,
                profesor_id INTEGER,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                capacidad_maxima INTEGER DEFAULT 20,
                tipo_clase VARCHAR(50) DEFAULT 'Spinning',
                activo BOOLEAN DEFAULT 1,
                fecha_desactivacion DATE,
                FOREIGN KEY (profesor_id) REFERENCES profesor (id)
            )
        ''')
        print("✓ Tabla 'horario_clase' creada")
        
        # Crear tabla clase_realizada
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clase_realizada (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                horario_clase_id INTEGER NOT NULL,
                fecha DATE NOT NULL,
                cantidad_alumnos INTEGER DEFAULT 0,
                observaciones TEXT,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (horario_clase_id) REFERENCES horario_clase (id)
            )
        ''')
        print("✓ Tabla 'clase_realizada' creada")
        
        # Crear tabla evento_horario
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evento_horario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                horario_clase_id INTEGER NOT NULL,
                tipo_evento VARCHAR(50) NOT NULL,
                fecha_evento DATE NOT NULL,
                descripcion TEXT,
                creado_por VARCHAR(100),
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (horario_clase_id) REFERENCES horario_clase (id)
            )
        ''')
        print("✓ Tabla 'evento_horario' creada")
        
        # Crear tabla notificacion
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notificacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo VARCHAR(50) NOT NULL,
                titulo VARCHAR(200) NOT NULL,
                mensaje TEXT NOT NULL,
                enviado BOOLEAN DEFAULT 0,
                fecha_envio DATETIME,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                destinatario VARCHAR(100),
                horario_clase_id INTEGER,
                FOREIGN KEY (horario_clase_id) REFERENCES horario_clase (id)
            )
        ''')
        print("✓ Tabla 'notificacion' creada")
        
        conn.commit()
        conn.close()
        print("Base de datos creada correctamente (método directo)")
        return True
        
    except Exception as e:
        print(f"Error creando tablas directamente: {str(e)}")
        return False

def check_database(db_path="gimnasio.db"):
    """Función principal para verificar y reparar la base de datos"""
    
    # Si la base de datos no existe, crearla
    if not os.path.exists(db_path):
        print(f"La base de datos {db_path} no existe. Intentando crearla...")
        
        # Método 1: Crear directamente con SQLite (más confiable)
        if create_tables_directly():
            print("Base de datos creada con método directo")
            return True
        
        # Método 2: Ejecutar create_tables.py
        print("Método 2: Ejecutando create_tables.py...")
        if run_script('create_tables.py') == 0:
            return True
        
        # Método 3: Ejecutar create_db.py
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