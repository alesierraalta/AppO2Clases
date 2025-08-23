#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear la base de datos desde cero
"""

import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Importar modelos
try:
    from models import *
except ImportError:
    print("ERROR: No se pudieron importar los modelos.")
    sys.exit(1)

def create_database():
    """Crea la base de datos y todas las tablas"""
    try:
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gimnasio.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db = SQLAlchemy(app)
        
        with app.app_context():
            # Crear todas las tablas
            db.create_all()
            print("Base de datos y tablas creadas exitosamente.")
            return True
            
    except Exception as e:
        print(f"ERROR al crear la base de datos: {e}")
        return False

if __name__ == '__main__':
    success = create_database()
    sys.exit(0 if success else 1)