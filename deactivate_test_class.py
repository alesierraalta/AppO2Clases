import sqlite3
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('gimnasio.db')
conn.row_factory = sqlite3.Row  # To access columns by name
cursor = conn.cursor()

def deactivate_class(class_name):
    """Deactivate a class by name and show confirmation"""
    print(f"\n=== Attempting to deactivate class: {class_name} ===")
    
    # Find the class ID
    cursor.execute("SELECT id, nombre, tipo_clase, activo FROM horario_clase WHERE nombre LIKE ?", 
                   (f"%{class_name}%",))
    classes = cursor.fetchall()
    
    if not classes:
        print(f"No classes found matching '{class_name}'")
        return
    
    print(f"Found {len(classes)} matching classes:")
    for idx, cls in enumerate(classes):
        active_status = "ACTIVE" if cls['activo'] else "INACTIVE"
        print(f"{idx+1}. ID: {cls['id']}, Name: {cls['nombre']}, Type: {cls['tipo_clase']}, Status: {active_status}")
    
    if len(classes) > 1:
        try:
            choice = int(input("\nEnter the number of the class to deactivate (or 0 to cancel): "))
            if choice == 0:
                print("Operation cancelled")
                return
            if choice < 1 or choice > len(classes):
                print("Invalid choice")
                return
            class_id = classes[choice-1]['id']
        except ValueError:
            print("Invalid input")
            return
    else:
        class_id = classes[0]['id']
    
    # Confirm class is active before deactivating
    cursor.execute("SELECT activo FROM horario_clase WHERE id = ?", (class_id,))
    result = cursor.fetchone()
    
    if not result:
        print("Error retrieving class information")
        return
    
    if not result['activo']:
        print(f"Class with ID {class_id} is already inactive.")
        should_activate = input("Would you like to activate it instead? (y/n): ").lower() == 'y'
        if not should_activate:
            return
        
        # Activate the class
        cursor.execute("UPDATE horario_clase SET activo = 1 WHERE id = ?", (class_id,))
        conn.commit()
        print(f"Class with ID {class_id} has been activated successfully!")
    else:
        # Deactivate the class
        cursor.execute("UPDATE horario_clase SET activo = 0 WHERE id = ?", (class_id,))
        conn.commit()
        print(f"Class with ID {class_id} has been deactivated successfully!")

def verify_active_status():
    """Show current count of active and inactive classes"""
    cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 1")
    active_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 0")
    inactive_count = cursor.fetchone()[0]
    
    print(f"\n=== Database Status ===")
    print(f"Active classes: {active_count}")
    print(f"Inactive classes: {inactive_count}")
    print(f"Total classes: {active_count + inactive_count}")

def show_inactive_classes():
    """Display all inactive classes"""
    print("\n=== Inactive Classes ===")
    cursor.execute("""
        SELECT id, nombre, dia_semana, hora_inicio, tipo_clase 
        FROM horario_clase 
        WHERE activo = 0
        ORDER BY nombre
    """)
    
    inactive_classes = cursor.fetchall()
    if not inactive_classes:
        print("No inactive classes found")
        return
    
    days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    for cls in inactive_classes:
        day = days[cls['dia_semana']] if 0 <= cls['dia_semana'] < len(days) else f"Day {cls['dia_semana']}"
        hora = cls['hora_inicio'] if cls['hora_inicio'] else "N/A"
        print(f"ID: {cls['id']}, Name: {cls['nombre']}, Day: {day}, Time: {hora}, Type: {cls['tipo_clase']}")

def show_classes_in_attendance_view():
    """Show which classes would appear in today's attendance view"""
    print("\n=== Classes in Today's Attendance View ===")
    # Get today's weekday (0-6, Monday is 0)
    today_weekday = datetime.now().weekday()
    
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
    print("Classes that would appear in attendance view (active only):")
    
    active_classes = []
    inactive_classes = []
    
    for cls in classes:
        is_active = bool(cls['activo'])
        status = "ACTIVE" if is_active else "INACTIVE"
        class_info = f"ID: {cls['id']}, Name: {cls['nombre']}, Time: {cls['hora_inicio']}, Status: {status}"
        
        if is_active:
            active_classes.append(class_info)
        else:
            inactive_classes.append(class_info)
    
    if active_classes:
        for cls in active_classes:
            print(f"✅ {cls}")
    else:
        print("No active classes for today")
    
    if inactive_classes:
        print("\nInactive classes for today (should NOT appear):")
        for cls in inactive_classes:
            print(f"❌ {cls}")

# Main execution
if __name__ == "__main__":
    print("Database Utility - Class Deactivation Test")
    
    verify_active_status()
    
    while True:
        print("\n--- MENU ---")
        print("1. Deactivate a class")
        print("2. Show inactive classes")
        print("3. Show classes in today's attendance view")
        print("0. Exit")
        
        choice = input("Enter your choice: ")
        
        if choice == "1":
            class_name = input("Enter class name to search for (e.g., 'POWER BIKE'): ")
            deactivate_class(class_name)
            verify_active_status()
        elif choice == "2":
            show_inactive_classes()
        elif choice == "3":
            show_classes_in_attendance_view()
        elif choice == "0":
            break
        else:
            print("Invalid choice")
    
    conn.close()
    print("\nConnection closed. Exiting program.") 