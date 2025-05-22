import sqlite3
from sqlalchemy import create_engine, MetaData, Table, Column, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

print("Debugging 'activo' column issue...")

# Check direct SQLite query
conn = sqlite3.connect('gimnasio.db')
cursor = conn.cursor()
print("Testing direct SQLite query...")
try:
    cursor.execute("SELECT id, nombre, activo FROM horario_clase LIMIT 5")
    rows = cursor.fetchall()
    print(f"SUCCESS! Query returned {len(rows)} rows")
    for row in rows:
        print(f"ID: {row[0]}, Nombre: {row[1]}, Activo: {row[2]}")
except Exception as e:
    print(f"ERROR: {str(e)}")

# Now try with SQLAlchemy
print("\nTesting SQLAlchemy query...")
engine = create_engine('sqlite:///gimnasio.db')
try:
    connection = engine.connect()
    query = "SELECT horario_clase.id AS horario_clase_id, horario_clase.activo AS horario_clase_activo FROM horario_clase LIMIT 5"
    result = connection.execute(query)
    rows = result.fetchall()
    print(f"SUCCESS! SQLAlchemy query returned {len(rows)} rows")
    for row in rows:
        print(f"ID: {row[0]}, Activo: {row[1]}")
    connection.close()
except Exception as e:
    print(f"ERROR: {str(e)}")

# Now try the exact query that's failing
print("\nTesting the exact failing query...")
try:
    connection = engine.connect()
    query = """
    SELECT horario_clase.id AS horario_clase_id, 
           horario_clase.nombre AS horario_clase_nombre, 
           horario_clase.dia_semana AS horario_clase_dia_semana, 
           horario_clase.hora_inicio AS horario_clase_hora_inicio, 
           horario_clase.duracion AS horario_clase_duracion, 
           horario_clase.profesor_id AS horario_clase_profesor_id, 
           horario_clase.fecha_creacion AS horario_clase_fecha_creacion, 
           horario_clase.capacidad_maxima AS horario_clase_capacidad_maxima, 
           horario_clase.tipo_clase AS horario_clase_tipo_clase, 
           horario_clase.activo AS horario_clase_activo, 
           horario_clase.fecha_desactivacion AS horario_clase_fecha_desactivacion 
    FROM horario_clase 
    WHERE horario_clase.dia_semana = 2 
    ORDER BY horario_clase.hora_inicio
    """
    result = connection.execute(query)
    rows = result.fetchall()
    print(f"SUCCESS! Exact failing query returned {len(rows)} rows")
    connection.close()
except Exception as e:
    print(f"ERROR with exact failing query: {str(e)}")

# Close connections
cursor.close()
conn.close()

print("\nProviding potential solutions for SQLAlchemy issues:")
print("1. Make sure your models.py HorarioClase model includes: activo = db.Column(db.Boolean, default=True)")
print("2. Make sure you're not using two different instances of the database or stale model instances")
print("3. Try restarting the application to clear any caching or stale model information")
print("4. Run 'python app.py' with no command line arguments to let SQLAlchemy reinitialize the models") 