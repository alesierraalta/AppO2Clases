import sqlite3

def check_activo_column():
    """Check the 'activo' column in horario_clase table"""
    try:
        # Connect to the database
        conn = sqlite3.connect('gimnasio.db')
        cursor = conn.cursor()
        
        # 1. Check if the activo column exists
        cursor.execute("PRAGMA table_info(horario_clase)")
        columns = cursor.fetchall()
        
        activo_column = next((col for col in columns if col[1] == 'activo'), None)
        
        if not activo_column:
            print("ERROR: The 'activo' column does not exist in horario_clase table")
            return False
            
        # 2. Print column details
        print(f"Column 'activo' exists:")
        print(f"  Type: {activo_column[2]}")
        print(f"  NOT NULL: {'Yes' if activo_column[3] else 'No'}")
        print(f"  Default value: {activo_column[4] if activo_column[4] else 'NULL'}")
        
        # 3. Check for NULL values
        cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo IS NULL")
        null_count = cursor.fetchone()[0]
        print(f"\nClasses with NULL 'activo' value: {null_count}")
        
        # 4. Get counts of active/inactive classes
        cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 1")
        active_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 0")
        inactive_count = cursor.fetchone()[0]
        
        print(f"Active classes: {active_count}")
        print(f"Inactive classes: {inactive_count}")
        
        # 5. List some records with NULL activo if any exist
        if null_count > 0:
            print("\nSample records with NULL 'activo':")
            cursor.execute("SELECT id, nombre FROM horario_clase WHERE activo IS NULL LIMIT 5")
            for row in cursor.fetchall():
                print(f"  ID: {row[0]}, Name: {row[1]}")
                
            # 6. Fix NULL values by setting them to 1 (active)
            print("\nFixing NULL values by setting to 1 (active)...")
            cursor.execute("UPDATE horario_clase SET activo = 1 WHERE activo IS NULL")
            conn.commit()
            print(f"Fixed {cursor.rowcount} records")
            
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Checking 'activo' column in horario_clase table...\n")
    check_activo_column() 