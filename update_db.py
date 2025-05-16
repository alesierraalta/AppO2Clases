from app import db, app
import sqlite3
import os
import sys

def add_tipo_clase_column():
    """
    Adds the tipo_clase column to the HorarioClase table if it doesn't exist.
    This script should be run once after updating the model.
    """
    print("Checking database structure...")
    
    # Find the database file
    db_path = 'gimnasio.db'
    if not os.path.exists(db_path):
        instance_path = os.path.join('instance', 'gimnasio.db')
        if os.path.exists(instance_path):
            db_path = instance_path
        else:
            print("Database file not found. Please make sure the application has been initialized.")
            return
    
    print(f"Using database at: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='horario_clase'")
    if not cursor.fetchone():
        print("Table 'horario_clase' not found. Creating the database schema...")
        # Use SQLAlchemy to create all tables - need app context
        with app.app_context():
            db.create_all()
        print("Database schema created.")
    
    # Check if the column already exists
    cursor.execute("PRAGMA table_info(horario_clase)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'tipo_clase' not in column_names:
        print("Adding tipo_clase column to horario_clase table...")
        
        # Add the new column
        cursor.execute("ALTER TABLE horario_clase ADD COLUMN tipo_clase TEXT DEFAULT 'OTRO'")
        conn.commit()
        
        # Attempt to detect types based on class names
        print("Attempting to automatically categorize existing classes...")
        
        # Get all horarios
        cursor.execute("SELECT id, nombre FROM horario_clase")
        horarios = cursor.fetchall()
        
        # Update tipo_clase based on class name
        for horario_id, nombre in horarios:
            nombre_upper = nombre.upper()
            
            if nombre_upper.startswith('MOVE'):
                tipo = 'MOVE'
            elif nombre_upper.startswith('RIDE'):
                tipo = 'RIDE'
            elif nombre_upper.startswith('BOX'):
                tipo = 'BOX'
            else:
                tipo = 'OTRO'
            
            cursor.execute("UPDATE horario_clase SET tipo_clase = ? WHERE id = ?", (tipo, horario_id))
        
        conn.commit()
        print(f"Updated {len(horarios)} class records with type classification.")
    else:
        print("Column 'tipo_clase' already exists in horario_clase table.")
    
    conn.close()
    print("Database update completed.")

def update_database():
    """
    Actualiza el esquema de la base de datos para incorporar nuevas características.
    - Agrega campo 'activo' a la tabla horario_clase si no existe
    - Agrega campo 'fecha_desactivacion' a la tabla horario_clase si no existe
    - Crea tabla 'evento_horario' si no existe
    - Crea índices para optimizar consultas
    """
    print("="*50)
    print("Actualizando esquema de base de datos...")
    print("="*50)
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gimnasio.db')
    print(f"Base de datos: {db_path}")
    
    # Verificar si el archivo existe
    if not os.path.exists(db_path):
        print("Error: No se encontró la base de datos. Asegúrate de que el archivo existe.")
        return False
    
    # Conectar directamente con sqlite3 para operaciones de esquema
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si existe la columna 'activo' en horario_clase
        cursor.execute("PRAGMA table_info(horario_clase)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Agregar columna 'activo' si no existe
        if 'activo' not in column_names:
            print("Agregando columna 'activo' a la tabla horario_clase...")
            cursor.execute("ALTER TABLE horario_clase ADD COLUMN activo BOOLEAN DEFAULT 1")
            conn.commit()
            print("Columna 'activo' agregada exitosamente.")
        else:
            print("La columna 'activo' ya existe en la tabla horario_clase.")
        
        # Agregar columna 'fecha_desactivacion' si no existe
        if 'fecha_desactivacion' not in column_names:
            print("Agregando columna 'fecha_desactivacion' a la tabla horario_clase...")
            cursor.execute("ALTER TABLE horario_clase ADD COLUMN fecha_desactivacion DATE")
            conn.commit()
            print("Columna 'fecha_desactivacion' agregada exitosamente.")
        else:
            print("La columna 'fecha_desactivacion' ya existe en la tabla horario_clase.")
        
        # Verificar si existe la tabla evento_horario
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evento_horario'")
        table_exists = cursor.fetchone()
        
        # Crear tabla evento_horario si no existe
        if not table_exists:
            print("Creando tabla 'evento_horario'...")
            cursor.execute('''
            CREATE TABLE evento_horario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                horario_id INTEGER NOT NULL,
                tipo VARCHAR(20) NOT NULL,
                fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_aplicacion DATE,
                motivo VARCHAR(255),
                datos_adicionales TEXT,
                FOREIGN KEY (horario_id) REFERENCES horario_clase (id)
            )
            ''')
            
            # Crear índices para la tabla evento_horario
            cursor.execute("CREATE INDEX idx_evento_horario_id ON evento_horario (horario_id)")
            cursor.execute("CREATE INDEX idx_evento_tipo ON evento_horario (tipo)")
            cursor.execute("CREATE INDEX idx_evento_fecha ON evento_horario (fecha)")
            conn.commit()
            print("Tabla 'evento_horario' y sus índices creados exitosamente.")
            
            # Migrar datos existentes: crear eventos iniciales basados en estado actual de horarios
            print("Migrando datos existentes a eventos...")
            cursor.execute("SELECT id, activo, fecha_desactivacion FROM horario_clase")
            horarios = cursor.fetchall()
            
            for horario in horarios:
                horario_id, activo, fecha_desactivacion = horario
                # Crear evento de creación para todos los horarios
                cursor.execute('''
                INSERT INTO evento_horario (horario_id, tipo, fecha, fecha_aplicacion, motivo)
                VALUES (?, 'creacion', datetime('now', '-1 year'), datetime('now', '-1 year'), 'Migración inicial')
                ''', (horario_id,))
                
                # Si está inactivo, crear un evento de desactivación
                if not activo:
                    fecha = fecha_desactivacion if fecha_desactivacion else 'datetime("now", "-1 month")'
                    cursor.execute(f'''
                    INSERT INTO evento_horario (horario_id, tipo, fecha, fecha_aplicacion, motivo)
                    VALUES (?, 'desactivacion', {fecha}, {fecha}, 'Migración inicial')
                    ''', (horario_id,))
            
            conn.commit()
            print(f"Migrados datos de {len(horarios)} horarios a eventos iniciales.")
        else:
            print("La tabla 'evento_horario' ya existe.")
        
        # Crear índices para optimizar consultas si no existen
        print("Verificando índices...")
        
        # Índice para optimizar consultas por horario activo
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_horario_activo'")
        if not cursor.fetchone():
            print("Creando índice para horarios activos...")
            cursor.execute("CREATE INDEX idx_horario_activo ON horario_clase (activo)")
            conn.commit()
            print("Índice 'idx_horario_activo' creado exitosamente.")
        
        # Índice para optimizar consultas por fecha de desactivación
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_fecha_desactivacion'")
        if not cursor.fetchone():
            print("Creando índice para fecha de desactivación...")
            cursor.execute("CREATE INDEX idx_fecha_desactivacion ON horario_clase (fecha_desactivacion)")
            conn.commit()
            print("Índice 'idx_fecha_desactivacion' creado exitosamente.")
        
        conn.close()
        print("="*50)
        print("Actualización de base de datos completada con éxito.")
        print("="*50)
        return True
        
    except Exception as e:
        print(f"Error al actualizar la base de datos: {str(e)}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

if __name__ == "__main__":
    # Crear explícitamente un contexto de aplicación
    try:
        # Primero intentar el método directo de SQLite que no depende del contexto Flask
        success = update_database()
        if success:
            print("Actualización completada usando SQLite directamente")
            sys.exit(0)
        
        # Si el método directo no funciona, intentar con el contexto de aplicación
        print("Intentando actualización con contexto de aplicación Flask...")
        
        # Empujar un contexto de aplicación
        ctx = app.app_context()
        ctx.push()
        
        # Importar HorarioClase dentro del contexto de aplicación
        from app import HorarioClase
        
        # Ejecutar las actualizaciones
        add_tipo_clase_column()
        
        # Liberar el contexto cuando terminemos
        ctx.pop()
        
        print("Actualización de base de datos completada")
        sys.exit(0)
    except Exception as e:
        print(f"Advertencia: Error durante la actualización de la base de datos: {e}")
        print("Este error no necesariamente indica un problema grave.")
        print("La aplicación intentará ejecutarse normalmente.")
        sys.exit(0)  # Salir con éxito para no detener el inicio