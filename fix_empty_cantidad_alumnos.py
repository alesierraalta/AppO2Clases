#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir campos cantidad_alumnos vacíos que están causando errores de conversión de tipos
"""

import sqlite3
import sys
import os

def fix_empty_cantidad_alumnos():
    """
    Corrige campos cantidad_alumnos que están vacíos o tienen valores no numéricos
    """
    db_path = 'gimnasio.db'
    
    if not os.path.exists(db_path):
        print(f"ERROR: La base de datos {db_path} no existe.")
        return False
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== CORRIGIENDO CAMPOS CANTIDAD_ALUMNOS ===")
        
        # Verificar registros con cantidad_alumnos problemáticos
        cursor.execute("""
            SELECT id, cantidad_alumnos, fecha 
            FROM clase_realizada 
            WHERE cantidad_alumnos IS NULL 
            OR cantidad_alumnos = ''
            OR (typeof(cantidad_alumnos) = 'text' AND cantidad_alumnos NOT GLOB '[0-9]*')
        """)
        
        registros_problematicos = cursor.fetchall()
        print(f"Encontrados {len(registros_problematicos)} registros con cantidad_alumnos problemática")
        
        if registros_problematicos:
            for record in registros_problematicos:
                record_id, cantidad_actual, fecha = record
                print(f"  ID {record_id} (fecha: {fecha}): cantidad_alumnos = '{cantidad_actual}'")
            
            # Corregir registros problemáticos estableciendo cantidad_alumnos = 0
            cursor.execute("""
                UPDATE clase_realizada 
                SET cantidad_alumnos = 0 
                WHERE cantidad_alumnos IS NULL 
                OR cantidad_alumnos = ''
                OR (typeof(cantidad_alumnos) = 'text' AND cantidad_alumnos NOT GLOB '[0-9]*')
            """)
            
            registros_actualizados = cursor.rowcount
            print(f"✓ {registros_actualizados} registros actualizados")
            
            # Verificar que no queden registros problemáticos
            cursor.execute("""
                SELECT COUNT(*) 
                FROM clase_realizada 
                WHERE cantidad_alumnos IS NULL 
                OR cantidad_alumnos = ''
                OR (typeof(cantidad_alumnos) = 'text' AND cantidad_alumnos NOT GLOB '[0-9]*')
            """)
            
            registros_restantes = cursor.fetchone()[0]
            if registros_restantes == 0:
                print("✓ Todos los registros problemáticos han sido corregidos")
            else:
                print(f"⚠️ Quedan {registros_restantes} registros problemáticos")
        
        # También verificar el tipo de datos de la columna
        cursor.execute("PRAGMA table_info(clase_realizada)")
        columns = cursor.fetchall()
        for col in columns:
            if col[1] == 'cantidad_alumnos':
                print(f"Tipo de columna cantidad_alumnos: {col[2]}")
                break
        
        # Mostrar algunos ejemplos de datos actualizados
        cursor.execute("""
            SELECT id, cantidad_alumnos, fecha 
            FROM clase_realizada 
            ORDER BY id DESC 
            LIMIT 5
        """)
        
        ejemplos = cursor.fetchall()
        print("\nEjemplos de registros (últimos 5):")
        for ejemplo in ejemplos:
            record_id, cantidad, fecha = ejemplo
            print(f"  ID {record_id}: cantidad_alumnos = {cantidad} (tipo: {type(cantidad).__name__})")
        
        conn.commit()
        print("\n✅ Corrección completada exitosamente")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if fix_empty_cantidad_alumnos():
        print("\nLos campos cantidad_alumnos han sido corregidos.")
        print("Reinicie la aplicación Flask para que los cambios surtan efecto.")
        sys.exit(0)
    else:
        print("\nError al corregir los campos cantidad_alumnos.")
        sys.exit(1) 