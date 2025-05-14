import sqlite3

# Connect to the database
conn = sqlite3.connect('gimnasio.db')
cursor = conn.cursor()

# Check if the column already exists
cursor.execute("PRAGMA table_info(horario_clase)")
columns = [column[1] for column in cursor.fetchall()]

if 'activo' not in columns:
    print("Adding 'activo' column to horario_clase table...")
    # Add the activo column with a default value of 1 (active)
    cursor.execute("ALTER TABLE horario_clase ADD COLUMN activo BOOLEAN DEFAULT 1")
    conn.commit()
    print("Column added successfully!")
else:
    print("The 'activo' column already exists in the horario_clase table.")

# Verify the column was added
cursor.execute("PRAGMA table_info(horario_clase)")
columns = cursor.fetchall()
print("\nCurrent schema of horario_clase table:")
for column in columns:
    print(f"{column[0]}: {column[1]} ({column[2]})")

# Close the connection
conn.close() 