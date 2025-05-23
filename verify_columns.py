#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar y añadir columnas necesarias en la base de datos
Reemplaza la línea compleja de código que está causando errores de sintaxis en los batch files
"""

import sqlite3
import sys
import os

def verify_and_add_columns():
    """
    Verifica que las columnas necesarias existan en la tabla horario_clase
    y las crea si no existen
    """
    db_path = 'gimnasio.db'
    
    if not os.path.exists(db_path):
        print(f"ERROR: La base de datos {db_path} no existe.")
        return False
    
    conn = None
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar que la tabla horario_clase existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='horario_clase'
        """)
        
        if not cursor.fetchone():
            print('ERROR: La tabla horario_clase no existe.')
            return False
        
        # Obtener información de las columnas actuales
        cursor.execute('PRAGMA table_info(horario_clase)')
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"Columnas actuales: {', '.join(column_names)}")
        
        # Verificar columnas específicas
        activo_exists = 'activo' in column_names
        desactivacion_exists = 'fecha_desactivacion' in column_names
        
        print(f"Columna activo: {'EXISTE' if activo_exists else 'NO EXISTE'}")
        print(f"Columna fecha_desactivacion: {'EXISTE' if desactivacion_exists else 'NO EXISTE'}")
        
        # Agregar columnas faltantes
        changes_made = False
        
        if not activo_exists:
            print('Agregando columna activo...')
            cursor.execute('ALTER TABLE horario_clase ADD COLUMN activo BOOLEAN DEFAULT 1')
            changes_made = True
            print('Columna activo agregada.')
        
        if not desactivacion_exists:
            print('Agregando columna fecha_desactivacion...')
            cursor.execute('ALTER TABLE horario_clase ADD COLUMN fecha_desactivacion DATE')
            changes_made = True
            print('Columna fecha_desactivacion agregada.')
        
        # Confirmar cambios si se realizaron
        if changes_made:
            conn.commit()
            print('Cambios guardados en la base de datos.')
        
        # Verificación final
        cursor.execute('PRAGMA table_info(horario_clase)')
        new_columns = cursor.fetchall()
        new_column_names = [col[1] for col in new_columns]
        
        if 'activo' not in new_column_names:
            print('ERROR: No se pudo agregar la columna activo.')
            return False
        
        if 'fecha_desactivacion' not in new_column_names:
            print('ERROR: No se pudo agregar la columna fecha_desactivacion.')
            return False
        
        print('✅ Columnas verificadas correctamente.')
        return True
        
    except Exception as e:
        print(f'Error: {e}')
        return False
        
    finally:
        if conn:
            conn.close()

def main():
    """Función principal"""
    print("Verificando columnas de la base de datos...")
    
    if verify_and_add_columns():
        print("Verificación completada exitosamente.")
        sys.exit(0)
    else:
        print("Verificación falló.")
        sys.exit(1)

if __name__ == '__main__':
    main() 