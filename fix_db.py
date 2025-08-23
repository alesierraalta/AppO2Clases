#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simple para verificar y crear la base de datos si es necesario
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Configuración básica de Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gimnasio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def check_and_create_db():
    """Verifica si la base de datos existe y la crea si es necesario"""
    try:
        with app.app_context():
            # Verificar si el archivo de base de datos existe
            db_path = 'gimnasio.db'
            if not os.path.exists(db_path):
                print("Base de datos no encontrada. Creando nueva base de datos...")
                db.create_all()
                print("Base de datos creada exitosamente.")
            else:
                print("Base de datos encontrada. Verificando integridad...")
                # Intentar una consulta simple para verificar que la DB funciona
                db.engine.execute('SELECT 1')
                print("Base de datos verificada correctamente.")
            return True
    except Exception as e:
        print(f"Error al verificar/crear la base de datos: {e}")
        return False

if __name__ == '__main__':
    success = check_and_create_db()
    sys.exit(0 if success else 1)