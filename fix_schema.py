import sqlite3
from sqlalchemy import create_engine, MetaData, Table, Column, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

print("Starting database validation...")

# Step 1: Check the SQLite database schema directly
print("Step 1: Checking SQLite schema directly")
conn = sqlite3.connect('gimnasio.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(horario_clase)")
columns = cursor.fetchall()

has_activo = any(col[1] == 'activo' for col in columns)
print(f"Database has 'activo' column: {has_activo}")

# Print the schema
print("Current database schema for horario_clase:")
for col in columns:
    print(f"  {col[0]}: {col[1]} ({col[2]})")

# Step 2: Set up SQLAlchemy engine and inspect
print("\nStep 2: Checking with SQLAlchemy...")
engine = create_engine('sqlite:///gimnasio.db')
metadata = MetaData()
metadata.reflect(bind=engine)

if 'horario_clase' in metadata.tables:
    horario_clase = metadata.tables['horario_clase']
    sa_has_activo = 'activo' in horario_clase.columns
    print(f"SQLAlchemy sees 'activo' column: {sa_has_activo}")
    
    if sa_has_activo:
        print("SQLAlchemy schema for horario_clase:")
        for col_name, col in horario_clase.columns.items():
            print(f"  {col_name}: {col.type}")
    else:
        print("ERROR: SQLAlchemy doesn't see the 'activo' column even though it exists in the database.")
        print("This could be due to SQLAlchemy caching or reflection issues.")
        
        # Step 3: Fix the schema if needed
        print("\nStep 3: Attempting to fix the schema...")
        
        # Add the column to the table if it doesn't exist in SQLAlchemy's view
        if not sa_has_activo and has_activo:
            # Create a new metadata object
            print("Rebuilding the SQLAlchemy metadata...")
            new_metadata = MetaData()
            new_metadata.reflect(bind=engine)
            
            # Get the table
            horario_clase = Table('horario_clase', new_metadata)
            
            # Create a temporary connection and transaction to test
            connection = engine.connect()
            trans = connection.begin()
            
            try:
                # If for some reason the column is visible to SQLAlchemy now, abort
                if 'activo' in horario_clase.columns:
                    print("Column 'activo' is now visible to SQLAlchemy")
                else:
                    print("Column still not visible to SQLAlchemy. This is likely a caching issue.")
                
                # Perform a query using the column to test if it's accessible
                print("\nTesting if we can query using the 'activo' column...")
                result = connection.execute("SELECT id, nombre, activo FROM horario_clase LIMIT 5")
                rows = result.fetchall()
                print(f"Query successful! Found {len(rows)} rows:")
                for row in rows:
                    print(f"  ID: {row[0]}, Nombre: {row[1]}, Activo: {row[2]}")
                
                print("\nThe database structure is correct, but SQLAlchemy might have cached metadata.")
                print("Potential solutions:")
                print("1. Restart your application")
                print("2. Create a fresh SQLAlchemy engine when starting your app")
                print("3. If using Flask-SQLAlchemy, try clearing the session and reattaching")
                
                trans.commit()
            except Exception as e:
                trans.rollback()
                print(f"Error during test: {str(e)}")
            finally:
                connection.close()

# Create a small test to simulate what might be failing
print("\nSimulating the query that's failing...")
try:
    connection = engine.connect()
    query = "SELECT horario_clase.id AS horario_clase_id, horario_clase.nombre AS horario_clase_nombre, " \
            "horario_clase.dia_semana AS horario_clase_dia_semana, horario_clase.hora_inicio AS horario_clase_hora_inicio, " \
            "horario_clase.duracion AS horario_clase_duracion, horario_clase.profesor_id AS horario_clase_profesor_id, " \
            "horario_clase.fecha_creacion AS horario_clase_fecha_creacion, horario_clase.capacidad_maxima AS horario_clase_capacidad_maxima, " \
            "horario_clase.tipo_clase AS horario_clase_tipo_clase, horario_clase.activo AS horario_clase_activo, " \
            "horario_clase.fecha_desactivacion AS horario_clase_fecha_desactivacion " \
            "FROM horario_clase WHERE horario_clase.dia_semana = 2 ORDER BY horario_clase.hora_inicio"
    result = connection.execute(query)
    rows = result.fetchall()
    print(f"Test query successful! Found {len(rows)} rows")
    connection.close()
    
    print("\nThe issue is likely with SQLAlchemy's model definition rather than the database itself.")
    print("Make sure your models.py definition of HorarioClase includes the 'activo' column.")
except Exception as e:
    print(f"Error during test query: {str(e)}")
    print("\nThere appears to be a discrepancy between the database schema and the SQLAlchemy model.")

# Close connections
cursor.close()
conn.close()

print("\nDatabase validation complete!") 