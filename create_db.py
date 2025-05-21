import sqlite3
import os
import sys

# Método 1: Usar Flask-SQLAlchemy
try:
    from app import app, db
    with app.app_context():
        db.create_all()
    print('Base de datos inicializada correctamente (método 1: Flask-SQLAlchemy)')
    
    # Intentar ejecutar create_tables.py si está disponible
    if os.path.exists('create_tables.py'):
        try:
            os.system('python create_tables.py')
            print('Tablas adicionales creadas con create_tables.py')
        except Exception as e:
            print(f'Advertencia: No se pudieron crear tablas adicionales: {str(e)}')
    
    sys.exit(0)  # Salir con éxito
except Exception as e1:
    print(f'Error al inicializar con Flask-SQLAlchemy: {str(e1)}')
    print('Intentando método alternativo...')

# Método 2: Crear archivo SQLite directamente y luego ejecutar create_tables.py
try:
    conn = sqlite3.connect('gimnasio.db')
    conn.close()
    print('Base de datos creada correctamente (método 2: SQLite directo)')
    
    # Intentar ejecutar create_tables.py
    if os.path.exists('create_tables.py'):
        try:
            os.system('python create_tables.py')
            print('Tablas creadas con create_tables.py')
            sys.exit(0)  # Salir con éxito
        except Exception as e:
            print(f'Error al crear tablas: {str(e)}')
    else:
        print('Error: No se encontró create_tables.py para crear las tablas necesarias')
except Exception as e2:
    print(f'Error al crear la base de datos: {str(e2)}')

# Si llegamos aquí, hubo un error
sys.exit(1) 
