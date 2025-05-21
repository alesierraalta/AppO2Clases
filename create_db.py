#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para inicializar la base de datos de la aplicación.
Implementa varios métodos de creación de tablas para asegurar 
el funcionamiento en cualquier entorno.
"""

import sqlite3
import os
import sys

def create_tables_manually():
    """
    Crea las tablas directamente con SQLite, sin depender de Flask.
    Es el método más confiable para inicializar la base de datos.
    """
    print("Método directo: Creando tablas con SQLite...")
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
        print("✓ Tabla 'profesor' creada")
        
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
        print("✓ Tabla 'horario_clase' creada")
        
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
        print("✓ Tabla 'clase_realizada' creada")
        
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
        print("✓ Tabla 'evento_horario' creada")
        
        # Crear tabla notificacion
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
        print("✓ Tabla 'notificacion' creada")
        
        conn.commit()
        conn.close()
        
        # Verificar que las tablas se hayan creado correctamente
        conn = sqlite3.connect('gimnasio.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        conn.close()
        
        required_tables = ['profesor', 'horario_clase', 'clase_realizada', 'evento_horario', 'notificacion']
        missing = [table for table in required_tables if table not in table_names]
        
        if missing:
            print(f"ADVERTENCIA: Faltan tablas: {', '.join(missing)}")
            return False
        
        print("Base de datos creada correctamente (método directo)")
        return True
    except Exception as e:
        print(f"Error al crear tablas manualmente: {str(e)}")
        return False

def create_with_flask():
    """
    Usa Flask-SQLAlchemy para crear las tablas. Este método depende
    del contexto de Flask y se usa como respaldo.
    """
    try:
        from app import app, db
        with app.app_context():
            db.create_all()
        print('Base de datos inicializada correctamente (método Flask-SQLAlchemy)')
        return True
    except Exception as e:
        print(f'Error al inicializar con Flask-SQLAlchemy: {str(e)}')
        return False

if __name__ == "__main__":
    # Verificar si la base de datos existe
    if not os.path.exists('gimnasio.db'):
        print("Base de datos no encontrada. Creando archivo gimnasio.db...")
        try:
            conn = sqlite3.connect('gimnasio.db')
            conn.close()
            print("Archivo de base de datos creado correctamente.")
        except Exception as e:
            print(f"Error al crear el archivo de base de datos: {str(e)}")
            sys.exit(1)
    
    # Método 1: Crear tablas directamente con SQLite (método más confiable)
    if create_tables_manually():
        sys.exit(0)
    
    # Método 2: Usar Flask-SQLAlchemy como respaldo
    print("Intentando método alternativo con Flask-SQLAlchemy...")
    if create_with_flask():
        sys.exit(0)
    
    # Si llegamos aquí, ambos métodos fallaron
    print("ERROR: No se pudo crear la base de datos por ningún método disponible.")
    sys.exit(1) 
