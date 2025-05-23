#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar la consulta que está fallando en la aplicación
"""

import sqlite3
from datetime import date

def test_direct_sql():
    """Probar la consulta SQL directamente"""
    print("=== PRUEBA CON SQL DIRECTO ===")
    try:
        conn = sqlite3.connect('gimnasio.db')
        cursor = conn.cursor()
        
        # La consulta exacta que está fallando
        query = """
        SELECT clase_realizada.id AS clase_realizada_id, 
               clase_realizada.fecha AS clase_realizada_fecha, 
               clase_realizada.horario_id AS clase_realizada_horario_id, 
               clase_realizada.profesor_id AS clase_realizada_profesor_id, 
               clase_realizada.hora_llegada_profesor AS clase_realizada_hora_llegada_profesor, 
               clase_realizada.cantidad_alumnos AS clase_realizada_cantidad_alumnos, 
               clase_realizada.observaciones AS clase_realizada_observaciones, 
               clase_realizada.fecha_registro AS clase_realizada_fecha_registro, 
               clase_realizada.audio_file AS clase_realizada_audio_file
        FROM clase_realizada
        WHERE clase_realizada.fecha = ?
        """
        
        cursor.execute(query, ('2025-05-23',))
        results = cursor.fetchall()
        
        print(f"Consulta SQL directa exitosa! Resultados encontrados: {len(results)}")
        for row in results:
            print(f"  ID: {row[0]}, Fecha: {row[1]}, Horario ID: {row[2]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error en SQL directo: {e}")
        return False

def test_sqlalchemy():
    """Probar con SQLAlchemy"""
    print("\n=== PRUEBA CON SQLALCHEMY ===")
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from models import db, ClaseRealizada
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gimnasio.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        
        with app.app_context():
            # Probar la consulta que está fallando
            clases = ClaseRealizada.query.filter_by(fecha=date(2025, 5, 23)).all()
            print(f"Consulta SQLAlchemy exitosa! Resultados encontrados: {len(clases)}")
            for clase in clases:
                print(f"  ID: {clase.id}, Fecha: {clase.fecha}, Horario ID: {clase.horario_id}")
        
        return True
        
    except Exception as e:
        print(f"Error en SQLAlchemy: {e}")
        return False

def main():
    print("Probando la consulta que está fallando en la aplicación...")
    
    # Primero probar SQL directo
    direct_success = test_direct_sql()
    
    # Luego probar SQLAlchemy
    sqlalchemy_success = test_sqlalchemy()
    
    print(f"\n=== RESUMEN ===")
    print(f"SQL Directo: {'✓ ÉXITO' if direct_success else '✗ FALLO'}")
    print(f"SQLAlchemy: {'✓ ÉXITO' if sqlalchemy_success else '✗ FALLO'}")
    
    if direct_success and not sqlalchemy_success:
        print("\nEl problema es específico de SQLAlchemy - posiblemente caché o metadatos.")
    elif not direct_success:
        print("\nEl problema está en la estructura de la base de datos.")

if __name__ == '__main__':
    main() 