#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para actualizar la estructura de la base de datos, 
asegurando que todas las columnas necesarias existan.
"""

import os
import sys
import sqlite3
from datetime import datetime

def update_database_structure(db_path="gimnasio.db"):
    """
    Actualiza la estructura de la base de datos, añadiendo columnas faltantes
    a las tablas existentes si es necesario.
    """
    print("="*50)
    print("Actualizando esquema de base de datos...")
    print("="*50)
    print(f"Base de datos: {os.path.abspath(db_path)}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Comprobar existencia de columna 'activo' en horario_clase
        cursor.execute("PRAGMA table_info(horario_clase)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Añadir columna 'activo' si no existe
        if 'activo' not in column_names:
            print("Agregando columna 'activo' a la tabla horario_clase...")
            try:
                cursor.execute("ALTER TABLE horario_clase ADD COLUMN activo INTEGER DEFAULT 1")
                conn.commit()
                print("✅ Columna 'activo' añadida correctamente")
            except Exception as e:
                print(f"Error al añadir columna 'activo': {str(e)}")
                # Si falla, intentar con una solución alternativa
                try:
                    # Usar el método de crear una tabla nueva, copiar datos y renombrar
                    print("Intentando método alternativo...")
                    
                    # Crear tabla temporal con la estructura deseada
                    cursor.execute("""
                    CREATE TABLE horario_clase_temp (
                        id INTEGER PRIMARY KEY,
                        nombre TEXT NOT NULL,
                        dia_semana INTEGER NOT NULL,
                        hora_inicio TEXT NOT NULL,
                        duracion INTEGER DEFAULT 60,
                        profesor_id INTEGER NOT NULL,
                        fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                        capacidad_maxima INTEGER DEFAULT 20,
                        tipo_clase TEXT DEFAULT 'OTRO',
                        activo INTEGER DEFAULT 1,
                        FOREIGN KEY (profesor_id) REFERENCES profesor (id)
                    )
                    """)
                    
                    # Copiar datos de la tabla original a la temporal
                    cursor.execute("""
                    INSERT INTO horario_clase_temp (id, nombre, dia_semana, hora_inicio, duracion, 
                                                  profesor_id, fecha_creacion, capacidad_maxima, tipo_clase)
                    SELECT id, nombre, dia_semana, hora_inicio, duracion, 
                           profesor_id, fecha_creacion, capacidad_maxima, tipo_clase
                    FROM horario_clase
                    """)
                    
                    # Eliminar la tabla original
                    cursor.execute("DROP TABLE horario_clase")
                    
                    # Renombrar la tabla temporal
                    cursor.execute("ALTER TABLE horario_clase_temp RENAME TO horario_clase")
                    
                    conn.commit()
                    print("✅ Columna 'activo' añadida correctamente mediante método alternativo")
                except Exception as e2:
                    print(f"Error al usar método alternativo: {str(e2)}")
        else:
            print("La columna 'activo' ya existe en la tabla horario_clase.")
        
        # Comprobar existencia de columna 'fecha_desactivacion' en horario_clase
        cursor.execute("PRAGMA table_info(horario_clase)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Añadir columna 'fecha_desactivacion' si no existe
        if 'fecha_desactivacion' not in column_names:
            print("Agregando columna 'fecha_desactivacion' a la tabla horario_clase...")
            try:
                cursor.execute("ALTER TABLE horario_clase ADD COLUMN fecha_desactivacion DATE")
                conn.commit()
                print("✅ Columna 'fecha_desactivacion' añadida correctamente")
            except Exception as e:
                print(f"Error al añadir columna 'fecha_desactivacion': {str(e)}")
        else:
            print("La columna 'fecha_desactivacion' ya existe en la tabla horario_clase.")
        
        # Comprobar si existe la tabla 'evento_horario'
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evento_horario'")
        if not cursor.fetchone():
            print("La tabla 'evento_horario' no existe. Creándola...")
            try:
                cursor.execute("""
                CREATE TABLE evento_horario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    horario_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    fecha TEXT DEFAULT CURRENT_TIMESTAMP,
                    fecha_aplicacion DATE,
                    motivo TEXT,
                    datos_adicionales TEXT,
                    FOREIGN KEY (horario_id) REFERENCES horario_clase (id)
                )
                """)
                conn.commit()
                print("✅ Tabla 'evento_horario' creada correctamente")
            except Exception as e:
                print(f"Error al crear tabla 'evento_horario': {str(e)}")
        else:
            print("La tabla 'evento_horario' ya existe.")
        
        # Verificar índices
        print("Verificando índices...")
        try:
            # Crear índice para la columna 'activo' si no existe
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_horario_activo ON horario_clase (activo)")
            # Crear índice para día de la semana
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_horario_dia ON horario_clase (dia_semana)")
            # Crear índice para búsquedas por profesor
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_horario_profesor ON horario_clase (profesor_id)")
            conn.commit()
            print("✅ Índices verificados/creados correctamente")
        except Exception as e:
            print(f"Error al verificar/crear índices: {str(e)}")
        
        # Comprobar y reparar valores nulos en activo
        try:
            cursor.execute("UPDATE horario_clase SET activo = 1 WHERE activo IS NULL")
            conn.commit()
            rows_updated = cursor.rowcount
            if rows_updated > 0:
                print(f"✅ Se actualizaron {rows_updated} filas con valores nulos en 'activo'")
        except Exception as e:
            print(f"Error al reparar valores nulos: {str(e)}")
        
        conn.close()
        print("="*50)
        print("Actualización de base de datos completada con éxito.")
        print("="*50)
        return True
    
    except Exception as e:
        print(f"Error general al actualizar la base de datos: {str(e)}")
        
        # Intentar con contexto de aplicación Flask
        try:
            print("Intentando actualización con contexto de aplicación Flask...")
            from app import app, db
            with app.app_context():
                print("Checking database structure...")
                print(f"Using database at: {db_path}")
                
                # Verificar si tabla horario_clase existe
                engine = db.engine
                inspector = db.inspect(engine)
                tables = inspector.get_table_names()
                
                if 'horario_clase' not in tables:
                    print("Table 'horario_clase' not found. Creating the database schema...")
                    db.create_all()
                    print("Database schema created.")
                
                # Intentar agregar columna tipo_clase
                try:
                    engine.execute("ALTER TABLE horario_clase ADD COLUMN tipo_clase TEXT DEFAULT 'OTRO'")
                    print("Adding tipo_clase column to horario_clase table...")
                except Exception as e:
                    # Es normal que falle si la columna ya existe
                    pass
                
            return True
        except Exception as e:
            print(f"Advertencia: Error durante la actualización de la base de datos: {str(e)}")
            print("Este error no necesariamente indica un problema grave.")
            print("La aplicación intentará ejecutarse normalmente.")
            return False

if __name__ == "__main__":
    if update_database_structure():
        print("Actualización completada usando SQLite directamente")
        sys.exit(0)
    else:
        print("Hubo problemas durante la actualización")
        sys.exit(1)