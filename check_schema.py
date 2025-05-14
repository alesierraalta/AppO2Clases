import sqlite3

try:
    # Connect to the database
    conn = sqlite3.connect('gimnasio.db')
    cursor = conn.cursor()
    
    # Check if the horario_clase table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='horario_clase'")
    if cursor.fetchone():
        print("Table horario_clase exists")
        
        # Get table schema
        cursor.execute("PRAGMA table_info(horario_clase)")
        columns = cursor.fetchall()
        print("\nTable schema:")
        for column in columns:
            print(f"Column: {column[1]}, Type: {column[2]}, NotNull: {column[3]}, DefaultValue: {column[4]}, PK: {column[5]}")
        
        # Check if 'activo' column exists
        activo_exists = any(col[1] == 'activo' for col in columns)
        print(f"\nColumn 'activo' exists: {activo_exists}")
        
        if activo_exists:
            # Check sample data
            cursor.execute("SELECT id, nombre, activo FROM horario_clase LIMIT 5")
            rows = cursor.fetchall()
            print("\nSample data:")
            for row in rows:
                print(f"ID: {row[0]}, Nombre: {row[1]}, Activo: {row[2]}")
    else:
        print("Table horario_clase does not exist")
    
    # Close the connection
    conn.close()
    
except Exception as e:
    print(f"Error: {str(e)}") 