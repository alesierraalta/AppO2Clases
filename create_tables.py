#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear tablas manualmente como último recurso
"""

import sys
import sqlite3

def create_tables_manually():
    """Crea las tablas básicas manualmente usando SQL"""
    try:
        conn = sqlite3.connect('gimnasio.db')
        cursor = conn.cursor()
        
        # Crear tabla de profesores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profesor (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                activo BOOLEAN DEFAULT 1
            )
        ''')
        
        # Crear tabla de horarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS horario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hora TEXT NOT NULL,
                activo BOOLEAN DEFAULT 1
            )
        ''')
        
        # Crear tabla de clases
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clase (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE NOT NULL,
                horario_id INTEGER,
                profesor_id INTEGER,
                registrada BOOLEAN DEFAULT 0,
                FOREIGN KEY (horario_id) REFERENCES horario (id),
                FOREIGN KEY (profesor_id) REFERENCES profesor (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("Tablas básicas creadas exitosamente.")
        return True
        
    except Exception as e:
        print(f"ERROR al crear tablas manualmente: {e}")
        return False

if __name__ == '__main__':
    success = create_tables_manually()
    sys.exit(0 if success else 1)