import sqlite3

# Connect to the database
conn = sqlite3.connect('gimnasio.db')
cursor = conn.cursor()

print("Deactivating POWER BIKE classes...")

# Check current counts
cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 1")
active_before = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 0")
inactive_before = cursor.fetchone()[0]

print(f"Before update: {active_before} active, {inactive_before} inactive classes")

# Get POWER BIKE classes that are active
cursor.execute("SELECT id, nombre FROM horario_clase WHERE nombre LIKE '%POWER BIKE%' AND activo = 1")
power_bike_classes = cursor.fetchall()

if not power_bike_classes:
    print("No active POWER BIKE classes found.")
else:
    print(f"Found {len(power_bike_classes)} active POWER BIKE classes:")
    for class_id, name in power_bike_classes:
        print(f"ID: {class_id}, Name: {name}")
    
    # Deactivate all POWER BIKE classes
    cursor.execute("UPDATE horario_clase SET activo = 0 WHERE nombre LIKE '%POWER BIKE%' AND activo = 1")
    conn.commit()
    
    print(f"\nSuccessfully deactivated {cursor.rowcount} POWER BIKE classes.")

# Check updated counts
cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 1")
active_after = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 0")
inactive_after = cursor.fetchone()[0]

print(f"After update: {active_after} active, {inactive_after} inactive classes")
print(f"Change: {active_before - active_after} classes deactivated")

conn.close()
print("Done.") 