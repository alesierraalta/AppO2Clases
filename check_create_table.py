#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar la sentencia CREATE TABLE de clase_realizada
"""

import sqlite3

def check_create_statement():
    try:
        conn = sqlite3.connect('gimnasio.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='clase_realizada'
        """)
        
        result = cursor.fetchone()
        if result:
            print("CREATE TABLE statement for clase_realizada:")
            print("-" * 60)
            print(result[0])
        else:
            print("Table clase_realizada not found!")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_create_statement() 