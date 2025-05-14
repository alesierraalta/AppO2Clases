import sqlite3

# Connect to the database
conn = sqlite3.connect('gimnasio.db')
cursor = conn.cursor()

try:
    print("Creating index on horario_clase.activo column...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_horario_activo ON horario_clase (activo)')
    conn.commit()
    print("Index created successfully!")
except Exception as e:
    print(f"Error creating index: {str(e)}")

# Verify indices in the database
cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='horario_clase'")
indices = cursor.fetchall()

print("\nIndices on horario_clase table:")
for index in indices:
    print(f"- {index[0]}")

conn.close() 