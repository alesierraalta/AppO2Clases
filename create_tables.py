#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear las tablas de la base de datos de forma independiente,
sin necesidad de contexto de aplicación Flask.
"""

import os
import sys
import sqlite3
from datetime import datetime

def verify_table_exists(db_path, table_name):
    """Verifica si una tabla específica existe en la base de datos"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"Error al verificar tabla {table_name}: {str(e)}")
        return False

def create_tables_manually(db_path='gimnasio.db'):
    """
    Crea las tablas manualmente utilizando SQLite directamente.
    """
    print(f"Creando tablas manualmente en {db_path} usando SQLite...")
    
    try:
        conn = sqlite3.connect(db_path)
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
        print("✓ Tabla 'profesor' creada o ya existente")
        
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
        print("✓ Tabla 'horario_clase' creada o ya existente")
        
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
        print("✓ Tabla 'clase_realizada' creada o ya existente")
        
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
        print("✓ Tabla 'evento_horario' creada o ya existente")
        
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
        print("✓ Tabla 'notificacion' creada o ya existente")
        
        conn.commit()
        conn.close()
        
        # Verificar que todas las tablas existan
        required_tables = ['profesor', 'horario_clase', 'clase_realizada', 'evento_horario', 'notificacion']
        missing = []
        
        for table in required_tables:
            if not verify_table_exists(db_path, table):
                missing.append(table)
        
        if missing:
            print(f"ERROR: No se pudieron crear las siguientes tablas: {', '.join(missing)}")
            return False
            
        print("✓ Todas las tablas fueron creadas exitosamente")
        return True
    except Exception as e:
        print(f"Error al crear tablas manualmente: {str(e)}")
        return False

def create_db_with_flask():
    """Intenta crear la base de datos usando Flask-SQLAlchemy (método secundario)"""
    print("Intentando crear tablas usando Flask-SQLAlchemy...")
    
    try:
        # Intentar crear tablas usando Flask-SQLAlchemy
        from app import app, db
        from models import Profesor, HorarioClase, ClaseRealizada, EventoHorario
        
        # Execute within the app context
        with app.app_context():
            # Create all tables if they don't exist
            db.create_all()
            print("Tables created successfully with Flask-SQLAlchemy.")
            return True
    except Exception as e:
        print(f"Error al crear tablas con Flask-SQLAlchemy: {str(e)}")
        return False

if __name__ == "__main__":
    db_path = 'gimnasio.db'
    print(f"=== Inicializando base de datos en: {db_path} ===")
    
    # Verificar si la base de datos existe, y crearla si no
    if not os.path.exists(db_path):
        print(f"Archivo de base de datos no encontrado. Creando {db_path}...")
        try:
            conn = sqlite3.connect(db_path)
            conn.close()
            print(f"Archivo de base de datos {db_path} creado correctamente.")
        except Exception as e:
            print(f"ERROR: No se pudo crear el archivo de base de datos: {str(e)}")
            sys.exit(1)
    
    # Método 1: Crear tablas manualmente con SQLite (más confiable)
    if create_tables_manually(db_path):
        print("Base de datos inicializada correctamente (método manual directo)")
        sys.exit(0)
    
    # Método 2: Intentar con Flask-SQLAlchemy como respaldo
    if create_db_with_flask():
        print("Base de datos inicializada correctamente (método Flask-SQLAlchemy)")
        sys.exit(0)
    
    # Si llegamos aquí, ambos métodos fallaron
    print("ERROR: No se pudo crear la base de datos por ningún método.")
    sys.exit(1) 