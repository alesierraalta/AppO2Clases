import sqlite3
import sys
from datetime import datetime

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

def print_separator():
    print("-" * 80)

def check_db_status():
    """Check the status of active/inactive classes in the database"""
    print("DATABASE STATUS:")
    
    # Check column exists
    cursor.execute("PRAGMA table_info(horario_clase)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'activo' not in columns:
        print("ERROR: 'activo' column doesn't exist in horario_clase table")
        return False
    
    # Count active classes
    cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 1")
    active_count = cursor.fetchone()[0]
    
    # Count inactive classes
    cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 0")
    inactive_count = cursor.fetchone()[0]
    
    # Count null activo values
    cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo IS NULL")
    null_count = cursor.fetchone()[0]
    
    print(f"Active classes: {active_count}")
    print(f"Inactive classes: {inactive_count}")
    print(f"Classes with NULL activo value: {null_count}")
    print(f"Total classes: {active_count + inactive_count + null_count}")
    
    return True

def check_power_bike_classes():
    """Check the status of POWER BIKE classes specifically"""
    print_separator()
    print("POWER BIKE CLASSES STATUS:")
    
    cursor.execute("""
        SELECT id, nombre, dia_semana, hora_inicio, tipo_clase, activo
        FROM horario_clase 
        WHERE nombre LIKE '%POWER BIKE%'
        ORDER BY dia_semana, hora_inicio
    """)
    
    classes = cursor.fetchall()
    if not classes:
        print("No POWER BIKE classes found")
        return
    
    days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    print(f"Found {len(classes)} POWER BIKE classes:")
    for cls in classes:
        day = days[cls['dia_semana']] if 0 <= cls['dia_semana'] < len(days) else f"Day {cls['dia_semana']}"
        hora = cls['hora_inicio'] if cls['hora_inicio'] else "N/A"
        status = "ACTIVE" if cls['activo'] else "INACTIVE"
        print(f"ID: {cls['id']}, Name: {cls['nombre']}, Day: {day}, Time: {hora}, Status: {status}")

def check_attendance_view_filters():
    """Check the attendance view's active class filtering"""
    print_separator()
    print("ANALYZING ATTENDANCE VIEW FILTERING:")
    
    # Get today's weekday (0-6, Monday is 0)
    today_weekday = datetime.now().weekday()
    
    # Get all classes for today
    cursor.execute("""
        SELECT id, nombre, hora_inicio, tipo_clase, activo
        FROM horario_clase 
        WHERE dia_semana = ?
        ORDER BY hora_inicio
    """, (today_weekday,))
    
    classes = cursor.fetchall()
    if not classes:
        print(f"No classes scheduled for today (weekday {today_weekday})")
        return
    
    print(f"Today is weekday {today_weekday}")
    
    # Count active and inactive classes
    active_count = sum(1 for cls in classes if cls['activo'])
    inactive_count = sum(1 for cls in classes if not cls['activo'])
    
    print(f"Total classes for today: {len(classes)}")
    print(f"Active classes: {active_count}")
    print(f"Inactive classes: {inactive_count}")
    
    # Check if app.py has proper filtering
    print_separator()
    print("CHECKING CODE FILTERING:")
    
    # 1. Check control_asistencia route
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            app_code = f.read()
        
        # Search for relevant patterns
        if "HorarioClase.query.filter_by(dia_semana=dia_semana, activo=True)" in app_code:
            print("✅ control_asistencia route correctly filters by activo=True")
        elif "horario.activo" in app_code:
            print("✅ control_asistencia route has some filtering on activo field")
        else:
            print("❌ control_asistencia route might not filter inactive classes")
        
        # Check clases_no_registradas route
        if "WHERE h.activo = 1" in app_code:
            print("✅ clases_no_registradas SQL query filters by activo=1")
        else:
            print("❌ clases_no_registradas might not filter inactive classes")
    except Exception as e:
        print(f"Error checking app.py: {str(e)}")

def check_inactive_classes_today():
    """Specific test for inactive classes that would show today"""
    print_separator()
    print("CHECKING INACTIVE CLASSES FOR TODAY:")
    
    # Get today's weekday
    today_weekday = datetime.now().weekday()
    
    # Get inactive classes for today
    cursor.execute("""
        SELECT id, nombre, hora_inicio
        FROM horario_clase 
        WHERE dia_semana = ? AND activo = 0
        ORDER BY hora_inicio
    """, (today_weekday,))
    
    inactive_classes = cursor.fetchall()
    
    if not inactive_classes:
        print("No inactive classes scheduled for today.")
        return
    
    print(f"Found {len(inactive_classes)} inactive classes for today:")
    for cls in inactive_classes:
        print(f"ID: {cls['id']}, Name: {cls['nombre']}, Time: {cls['hora_inicio']}")
    
    print("\nThese classes should NOT appear in the attendance view.")

def deactivate_power_bike_classes():
    """Deactivate all POWER BIKE classes for testing"""
    print_separator()
    print("DEACTIVATING POWER BIKE CLASSES:")
    
    # Find POWER BIKE classes
    cursor.execute("SELECT id, nombre, activo FROM horario_clase WHERE nombre LIKE '%POWER BIKE%'")
    classes = cursor.fetchall()
    
    if not classes:
        print("No POWER BIKE classes found")
        return
    
    # Count active classes
    active_classes = [cls for cls in classes if cls['activo']]
    
    if not active_classes:
        print("No active POWER BIKE classes found. They are all already inactive.")
        return
    
    print(f"Found {len(active_classes)} active POWER BIKE classes to deactivate:")
    for cls in active_classes:
        print(f"ID: {cls['id']}, Name: {cls['nombre']}")
    
    # Deactivate all POWER BIKE classes
    cursor.execute("UPDATE horario_clase SET activo = 0 WHERE nombre LIKE '%POWER BIKE%' AND activo = 1")
    conn.commit()
    
    print(f"\n✅ Successfully deactivated {cursor.rowcount} POWER BIKE classes.")

def main():
    print("=== VERIFICATION OF ACTIVO COLUMN USAGE ===")
    
    if not check_db_status():
        print("Cannot proceed due to database issues")
        return
    
    check_power_bike_classes()
    check_attendance_view_filters()
    check_inactive_classes_today()
    
    # Check command line arguments
    auto_deactivate = False
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['deactivate', '-d', '--deactivate']:
        auto_deactivate = True
    
    if auto_deactivate:
        print("Auto-deactivation enabled via command line argument")
        deactivate_power_bike_classes()
        check_power_bike_classes()  # Show updated status
    
    conn.close()
    print_separator()
    print("Verification complete. Database connection closed.")

if __name__ == "__main__":
    main() 