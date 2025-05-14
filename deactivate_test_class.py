import sqlite3

def deactivate_class(class_name='POWER BIKE'):
    """Deactivate a specific class by name"""
    conn = None
    try:
        # Connect to the database
        conn = sqlite3.connect('gimnasio.db')
        cursor = conn.cursor()
        
        # Find classes with the given name
        cursor.execute("SELECT id, nombre, activo FROM horario_clase WHERE nombre LIKE ?", (f'%{class_name}%',))
        classes = cursor.fetchall()
        
        if not classes:
            print(f"No classes found matching: {class_name}")
            return False
        
        print(f"Found {len(classes)} classes matching '{class_name}':")
        for i, cls in enumerate(classes):
            status = "Active" if cls[2] == 1 else "Inactive"
            print(f"{i+1}. ID: {cls[0]}, Name: {cls[1]}, Status: {status}")
        
        # Deactivate all matching classes
        cursor.execute("UPDATE horario_clase SET activo = 0 WHERE nombre LIKE ?", (f'%{class_name}%',))
        conn.commit()
        
        print(f"\n✓ Deactivated {cursor.rowcount} classes matching '{class_name}'")
        
        # Verify the update
        cursor.execute("SELECT id, nombre, activo FROM horario_clase WHERE nombre LIKE ?", (f'%{class_name}%',))
        classes = cursor.fetchall()
        
        print("\nUpdated status:")
        for i, cls in enumerate(classes):
            status = "Active" if cls[2] == 1 else "Inactive"
            print(f"{i+1}. ID: {cls[0]}, Name: {cls[1]}, Status: {status}")
        
        # Get updated counts
        cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 1")
        active_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 0")
        inactive_count = cursor.fetchone()[0]
        
        print(f"\nUpdated counts:")
        print(f"Active classes: {active_count}")
        print(f"Inactive classes: {inactive_count}")
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        class_name = sys.argv[1]
    else:
        class_name = 'POWER BIKE'
        
    print(f"Deactivating classes matching: {class_name}\n")
    deactivate_class(class_name) 