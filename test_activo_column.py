import sqlite3
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('gimnasio.db')
conn.row_factory = sqlite3.Row  # To access columns by name
cursor = conn.cursor()

print("Testing query with horario_clase.activo column...")

# Test the exact query that was causing the error
try:
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
           horario_clase.activo AS horario_clase_activo 
    FROM horario_clase 
    WHERE horario_clase.dia_semana = ? 
    ORDER BY horario_clase.hora_inicio
    """
    cursor.execute(query, (2,))  # 2 corresponds to Wednesday
    results = cursor.fetchall()
    
    print(f"Query executed successfully! Found {len(results)} results.")
    
    # Show first few results
    print("\nSample results:")
    for i, row in enumerate(results[:3]):
        print(f"Row {i+1}:")
        print(f"  ID: {row['horario_clase_id']}")
        print(f"  Nombre: {row['horario_clase_nombre']}")
        print(f"  Activo: {row['horario_clase_activo']}")
        print()

except Exception as e:
    print(f"Error executing query: {str(e)}")

# Now check how many active and inactive classes we have
try:
    cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 1")
    active_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 0")
    inactive_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo IS NULL")
    null_count = cursor.fetchone()[0]
    
    print(f"Active classes: {active_count}")
    print(f"Inactive classes: {inactive_count}")
    print(f"Classes with NULL activo value: {null_count}")
    
except Exception as e:
    print(f"Error counting active/inactive classes: {str(e)}")

conn.close() 