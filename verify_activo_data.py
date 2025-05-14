import sqlite3
import sys

def verify_activo_column():
    """Verify the activo column in the database and test deactivation"""
    try:
        # Connect to the database
        conn = sqlite3.connect('gimnasio.db')
        conn.row_factory = sqlite3.Row  # This enables accessing columns by name
        cursor = conn.cursor()
        
        print("STEP 1: Verify database schema")
        cursor.execute("PRAGMA table_info(horario_clase)")
        columns = cursor.fetchall()
        
        # Check if activo column exists
        activo_column = next((col for col in columns if col[1] == 'activo'), None)
        if not activo_column:
            print("ERROR: The 'activo' column does not exist in horario_clase table")
            return False
        
        print("✓ Column 'activo' exists")
        print(f"  Type: {activo_column[2]}")
        print(f"  NOT NULL: {'Yes' if activo_column[3] else 'No'}")
        print(f"  Default value: {activo_column[4] if activo_column[4] else 'NULL'}")
        
        # Check default value
        if activo_column[4] != '1':
            print("WARNING: Default value is not 1. This could cause issues with new classes.")
            should_fix = input("Do you want to alter the table to set default value to 1? (y/n): ")
            if should_fix.lower() == 'y':
                try:
                    # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
                    # This is complex and risky, so we'll just note it for now
                    print("NOTE: SQLite doesn't support direct ALTER COLUMN. Please modify the models.py file.")
                except Exception as e:
                    print(f"Error fixing default value: {str(e)}")
        else:
            print("✓ Default value is correctly set to 1")
        
        print("\nSTEP 2: Check for NULL values")
        cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo IS NULL")
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            print(f"WARNING: Found {null_count} classes with NULL activo value")
            
            # Fix NULL values
            cursor.execute("UPDATE horario_clase SET activo = 1 WHERE activo IS NULL")
            conn.commit()
            print(f"✓ Fixed {cursor.rowcount} records by setting activo = 1")
        else:
            print("✓ No NULL values found in activo column")
        
        print("\nSTEP 3: Current active/inactive status")
        cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 1")
        active_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 0")
        inactive_count = cursor.fetchone()[0]
        
        print(f"Active classes: {active_count}")
        print(f"Inactive classes: {inactive_count}")
        
        # List sample of classes
        print("\nSample classes:")
        cursor.execute("SELECT id, nombre, activo FROM horario_clase ORDER BY id LIMIT 5")
        for row in cursor.fetchall():
            status = "Active" if row['activo'] == 1 else "Inactive"
            print(f"  ID: {row['id']}, Name: {row['nombre']}, Status: {status}")
        
        print("\nSTEP 4: Test deactivating a class")
        if '--no-test' not in sys.argv:
            # Find a class to deactivate for testing
            cursor.execute("SELECT id, nombre FROM horario_clase WHERE activo = 1 LIMIT 1")
            test_class = cursor.fetchone()
            
            if test_class:
                class_id = test_class['id']
                class_name = test_class['nombre']
                
                print(f"Testing deactivation on class: {class_name} (ID: {class_id})")
                cursor.execute("UPDATE horario_clase SET activo = 0 WHERE id = ?", (class_id,))
                conn.commit()
                print(f"✓ Deactivated class {class_name}")
                
                # Verify the update
                cursor.execute("SELECT activo FROM horario_clase WHERE id = ?", (class_id,))
                new_status = cursor.fetchone()['activo']
                if new_status == 0:
                    print("✓ Verification successful - class is now inactive")
                else:
                    print("ERROR: Verification failed - class is still active")
                
                # Reactivate the class to avoid side effects
                cursor.execute("UPDATE horario_clase SET activo = 1 WHERE id = ?", (class_id,))
                conn.commit()
                print(f"✓ Reactivated class {class_name} to restore initial state")
            else:
                print("No active classes found to test deactivation")
        else:
            print("Test deactivation skipped (--no-test flag provided)")
        
        print("\nVerification complete")
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verify_activo_column() 