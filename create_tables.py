#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear las tablas de la base de datos, con capacidad de recuperación
en caso de que falle el método principal que utiliza Flask-SQLAlchemy.
"""

import os
import sys
import sqlite3
from datetime import datetime

def create_tables_manually():
    """
    Crea las tablas manualmente utilizando SQLite directamente.
    Esta función se utiliza como respaldo si falla el método Flask-SQLAlchemy.
    """
    print("Creando tablas manualmente con SQLite...")
    
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
        
        conn.commit()
        conn.close()
        
        print("Tablas creadas manualmente con éxito")
        return True
    except Exception as e:
        print(f"Error al crear tablas manualmente: {str(e)}")
        return False

# Método principal usando Flask-SQLAlchemy
print("Starting database table creation...")

try:
    # Intentar crear tablas usando Flask-SQLAlchemy
    from app import app, db
    from models import Profesor, HorarioClase, ClaseRealizada, EventoHorario
    
    # Execute within the app context
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        print("Tables created successfully.")
        
        # Check if tables exist
        print("Verifying tables...")
        try:
            # Trying to query the tables to see if they exist
            profesor_count = Profesor.query.count()
            horario_count = HorarioClase.query.count()
            clase_count = ClaseRealizada.query.count()
            
            print(f"Database contains:")
            print(f"- {profesor_count} profesores")
            print(f"- {horario_count} horarios de clase")
            print(f"- {clase_count} clases realizadas")
            
        except Exception as e:
            print(f"Error verifying tables: {e}")
        
        print("Database setup complete.")
    
    sys.exit(0)  # Éxito
except Exception as e:
    print(f"Error al crear tablas con Flask-SQLAlchemy: {str(e)}")
    print("Intentando método alternativo...")

# Si llegamos aquí, el método principal falló, intentar crear tablas manualmente
if create_tables_manually():
    print("Base de datos creada correctamente mediante método alternativo")
    sys.exit(0)  # Éxito
else:
    print("ERROR: No se pudo crear la base de datos por ningún método.")
    sys.exit(1)  # Error 