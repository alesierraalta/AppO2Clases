from app import db, HorarioClase
import sqlite3
import os
from app import app

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
        # Use SQLAlchemy to create all tables
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
    
    # Conectar directamente con sqlite3 para operaciones de bajo nivel
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Verificar si existe la columna 'activo' en horario_clase
        cursor.execute("PRAGMA table_info(horario_clase)")
        columnas = cursor.fetchall()
        
        tiene_activo = any(col[1] == 'activo' for col in columnas)
        
        if not tiene_activo:
            print("Agregando columna 'activo' a la tabla horario_clase...")
            try:
                cursor.execute("ALTER TABLE horario_clase ADD COLUMN activo BOOLEAN DEFAULT 1")
                conn.commit()
                print("✅ Columna 'activo' agregada con éxito")
            except sqlite3.Error as e:
                print(f"❌ Error al agregar columna 'activo': {str(e)}")
                conn.rollback()
        else:
            print("✅ La columna 'activo' ya existe en la tabla horario_clase")
        
        # 2. Crear índice para mejorar rendimiento
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_horario_activo ON horario_clase (activo)")
            conn.commit()
            print("✅ Índice idx_horario_activo creado o verificado")
        except sqlite3.Error as e:
            print(f"❌ Error al crear índice en 'activo': {str(e)}")
            conn.rollback()
        
        # 3. Asegurarse de que todos los horarios tengan un valor para 'activo'
        if tiene_activo:
            try:
                cursor.execute("UPDATE horario_clase SET activo = 1 WHERE activo IS NULL")
                conn.commit()
                filas_actualizadas = cursor.rowcount
                if filas_actualizadas > 0:
                    print(f"✅ Se actualizaron {filas_actualizadas} horarios sin valor en 'activo'")
                else:
                    print("✅ Todos los horarios tienen valor en 'activo'")
            except sqlite3.Error as e:
                print(f"❌ Error al actualizar valores nulos en 'activo': {str(e)}")
                conn.rollback()
        
        # 4. Mostrar estadísticas
        cursor.execute("SELECT COUNT(*) FROM horario_clase")
        total_horarios = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 1")
        horarios_activos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 0")
        horarios_inactivos = cursor.fetchone()[0]
        
        print("\nEstadísticas de la base de datos:")
        print(f"Total de horarios: {total_horarios}")
        print(f"Horarios activos: {horarios_activos}")
        print(f"Horarios inactivos: {horarios_inactivos}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Actualización de base de datos completada con éxito")
        print("="*50)
        return True
        
    except Exception as e:
        print(f"❌ Error al actualizar la base de datos: {str(e)}")
        print("="*50)
        return False

if __name__ == "__main__":
    with app.app_context():
        update_database() 