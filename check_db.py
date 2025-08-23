#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar el estado de la base de datos
"""

import os
import sys
import sqlite3

def check_database():
    """Verifica si la base de datos existe y es accesible"""
    try:
        db_path = 'gimnasio.db'
        if not os.path.exists(db_path):
            print("ERROR: Archivo de base de datos no encontrado.")
            return False
        
        # Intentar conectar y hacer una consulta simple
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        if tables:
            print(f"Base de datos OK. Tablas encontradas: {len(tables)}")
            return True
        else:
            print("ADVERTENCIA: Base de datos existe pero no tiene tablas.")
            return False
            
    except Exception as e:
        print(f"ERROR al verificar la base de datos: {e}")
        return False

if __name__ == '__main__':
    success = check_database()
    sys.exit(0 if success else 1)