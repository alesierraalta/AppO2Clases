import sqlite3
import os
import sys

def create_db():
    """Crear la estructura básica de la base de datos"""
    db_path = 'gimnasio.db'
    
    try:
        # Método 1: SQLite directo (independiente de Flask)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tablas existentes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        existing_tables = [table[0] for table in tables]
        
        # Si ya existen tablas básicas, no es necesario crear la estructura
        required_tables = ['profesor', 'horario_clase', 'clase_realizada', 'evento_horario']
        if all(table in existing_tables for table in required_tables):
            print(f"Base de datos {db_path} ya contiene las tablas requeridas")
            conn.close()
            return True
        
        print("Creando estructura básica de la base de datos...")
        
        # Tabla profesor
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS profesor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            tarifa_por_clase REAL NOT NULL,
            telefono TEXT,
            email TEXT
        )
        ''')
        
        # Tabla horario_clase
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS horario_clase (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            dia_semana INTEGER NOT NULL,
            hora_inicio TIME NOT NULL,
            duracion INTEGER DEFAULT 60,
            profesor_id INTEGER NOT NULL,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            capacidad_maxima INTEGER DEFAULT 20,
            tipo_clase TEXT DEFAULT 'OTRO',
            activo BOOLEAN DEFAULT 1,
            fecha_desactivacion DATE,
            FOREIGN KEY (profesor_id) REFERENCES profesor (id)
        )
        ''')
        
        # Tabla clase_realizada
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clase_realizada (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            horario_id INTEGER NOT NULL,
            profesor_id INTEGER NOT NULL,
            hora_llegada_profesor TIME,
            cantidad_alumnos INTEGER DEFAULT 0,
            observaciones TEXT,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            audio_file TEXT,
            FOREIGN KEY (horario_id) REFERENCES horario_clase (id),
            FOREIGN KEY (profesor_id) REFERENCES profesor (id)
        )
        ''')
        
        # Tabla evento_horario
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS evento_horario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            horario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            fecha_aplicacion DATE,
            motivo TEXT,
            datos_adicionales TEXT,
            FOREIGN KEY (horario_id) REFERENCES horario_clase (id)
        )
        ''')
        
        # Crear índices para optimizar consultas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_horario_profesor ON horario_clase (profesor_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_horario_dia ON horario_clase (dia_semana)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_horario_activo ON horario_clase (activo)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clase_fecha ON clase_realizada (fecha)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clase_horario ON clase_realizada (horario_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clase_profesor ON clase_realizada (profesor_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evento_horario_id ON evento_horario (horario_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evento_tipo ON evento_horario (tipo)")
        
        # Confirmar cambios
        conn.commit()
        conn.close()
        
        print("Base de datos creada exitosamente con SQLite directo")
        return True
        
    except Exception as e:
        print(f"Error al crear la base de datos directamente: {str(e)}")
        
        # Método 2: Intentar con Flask-SQLAlchemy si el método directo falla
        try:
            from app import app, db
            print("Intentando crear la base de datos con SQLAlchemy...")
            
            # Crear un contexto de aplicación
            with app.app_context():
                db.create_all()
                print("Base de datos creada exitosamente con SQLAlchemy")
                return True
        except Exception as e_flask:
            print(f"Error al crear la base de datos con SQLAlchemy: {str(e_flask)}")
            print("Ambos métodos de creación de base de datos fallaron.")
            return False

if __name__ == "__main__":
    if create_db():
        print("Creación de base de datos completada")
        sys.exit(0)
    else:
        print("Error al crear la base de datos")
        sys.exit(1) 
