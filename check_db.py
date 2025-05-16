import sqlite3
import os
import sys

def check_database_directly():
    """Verifica la base de datos sin depender de la aplicación Flask"""
    db_path = 'gimnasio.db'
    
    print(f"Verificando la base de datos en: {db_path}")
    
    # Verificar si el archivo existe
    if not os.path.exists(db_path):
        print(f"Error: Base de datos '{db_path}' no encontrada.")
        return False
    
    # Conexión a la base de datos
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        if not table_names:
            print("Advertencia: La base de datos existe pero no contiene tablas.")
            conn.close()
            return False
        
        print(f"Tablas encontradas ({len(table_names)}): {', '.join(table_names[:5])}")
        if len(table_names) > 5:
            print(f"... y {len(table_names) - 5} tablas más")
        
        # Verificar tablas principales
        required_tables = ['profesor', 'horario_clase', 'clase_realizada', 'evento_horario']
        missing_tables = [table for table in required_tables if table not in table_names]
        
        if missing_tables:
            print(f"Error: Faltan tablas fundamentales: {', '.join(missing_tables)}")
            conn.close()
            return False
        
        # Verificar estructura de la tabla horario_clase
        cursor.execute("PRAGMA table_info(horario_clase)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Verificar columna 'activo'
        if 'activo' not in column_names:
            print("Advertencia: La columna 'activo' no existe en horario_clase.")
            print("Es necesario ejecutar update_db.py o fix_db.py para actualizar la estructura.")
        
        # Contar registros en tablas principales
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Tabla '{table}': {count} registros")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"Error SQLite durante la verificación: {str(e)}")
        return False
        
    except Exception as e:
        print(f"Error general durante la verificación: {str(e)}")
        return False

def check_flask_db_config():
    """Verifica la configuración de la base de datos en Flask"""
    try:
        # Esta parte podría dar error si no hay contexto de Flask
        from app import app, db
        
        print("\nConfiguración de base de datos en Flask:")
        print(f"URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'No configurado')}")
        print(f"Track modifications: {app.config.get('SQLALCHEMY_TRACK_MODIFICATIONS', 'No configurado')}")
        
        return True
    except Exception as e:
        print(f"\nNo se pudo verificar la configuración de Flask: {str(e)}")
        print("Esto es normal si se ejecuta fuera del contexto de la aplicación.")
        return False

if __name__ == "__main__":
    db_ok = check_database_directly()
    
    # Intentar verificar la configuración Flask solo si la BD está bien
    if db_ok:
        flask_ok = check_flask_db_config()
        
        if db_ok and flask_ok:
            print("\nBase de datos verificada correctamente.")
            sys.exit(0)
        else:
            print("\nBase de datos existe pero podría tener problemas con Flask.")
            sys.exit(0)  # Salir con éxito para no detener inicio
    else:
        print("\nProblemas detectados con la base de datos.")
        print("Ejecute fix_db.py o create_db.py para reparar o crear la base de datos.")
        sys.exit(1) 