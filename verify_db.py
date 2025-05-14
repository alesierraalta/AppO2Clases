import sqlite3

# Connect to the database
conn = sqlite3.connect('gimnasio.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check active/inactive classes
cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 1")
active_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM horario_clase WHERE activo = 0")
inactive_count = cursor.fetchone()[0]

print(f"Active classes: {active_count}")
print(f"Inactive classes: {inactive_count}")
print(f"Total classes: {active_count + inactive_count}")

# Show examples of inactive classes
print("\nInactive class examples:")
cursor.execute("SELECT id, nombre, dia_semana FROM horario_clase WHERE activo = 0 LIMIT 5")
for row in cursor.fetchall():
    print(f"- ID: {row['id']}, Name: {row['nombre']}, Day: {row['dia_semana']}")

# Close connection
conn.close() 