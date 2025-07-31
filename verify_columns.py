#!/usr/bin/env python3
"""
Verificador de columnas para la base de datos O2 Fitness
Verifica y agrega columnas faltantes en las tablas necesarias
"""

import sqlite3
import sys
import os
from pathlib import Path

def verify_and_add_activo_column():
    """Verifica y agrega la columna 'activo' a la tabla horario_clase si no existe"""
    
    # Buscar la base de datos
    db_paths = ['gimnasio.db', 'instance/gimnasio.db']
    db_path = None
    
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("ERROR: No se encontró la base de datos gimnasio.db")
        return False
    
    try:
        print(f"Conectando a la base de datos: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si la tabla horario_clase existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='horario_clase'")
        if not cursor.fetchone():
            print("ERROR: La tabla horario_clase no existe")
            conn.close()
            return False
        
        # Verificar si la columna 'activo' existe
        cursor.execute("PRAGMA table_info(horario_clase)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'activo' not in columns:
            print("Agregando columna 'activo' a la tabla horario_clase...")
            cursor.execute("ALTER TABLE horario_clase ADD COLUMN activo BOOLEAN DEFAULT 1")
            conn.commit()
            print("✓ Columna 'activo' agregada exitosamente!")
        else:
            print("✓ La columna 'activo' ya existe en la tabla horario_clase")
        
        # Verificar el esquema final
        cursor.execute("PRAGMA table_info(horario_clase)")
        columns = cursor.fetchall()
        print(f"\nEsquema actual de la tabla horario_clase ({len(columns)} columnas):")
        for column in columns:
            column_info = f"  {column[1]} ({column[2]})"
            if column[3]:  # NOT NULL
                column_info += " NOT NULL"
            if column[4] is not None:  # DEFAULT value
                column_info += f" DEFAULT {column[4]}"
            if column[5]:  # PRIMARY KEY
                column_info += " PRIMARY KEY"
            print(column_info)
        
        # Verificar que la columna activo funcione
        cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"✓ Verificación exitosa: {count} registros con columna 'activo' válida")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"ERROR de SQLite: {e}")
        return False
    except Exception as e:
        print(f"ERROR inesperado: {e}")
        return False

def main():
    """Función principal"""
    print("=" * 50)
    print("VERIFICADOR DE COLUMNAS - O2 FITNESS")
    print("=" * 50)
    
    success = verify_and_add_activo_column()
    
    if success:
        print("\n✓ Verificación de columnas completada exitosamente")
        return 0
    else:
        print("\n✗ Error en la verificación de columnas")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)