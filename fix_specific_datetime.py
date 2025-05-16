#!/usr/bin/env python
"""
Simple script to fix the specific problematic datetime format: '2025-05-16T08:18:35.167165'
"""
import sqlite3

def fix_specific_datetime():
    print("Fixing specific problematic datetime format in the database...")
    
    conn = sqlite3.connect('gimnasio.db')
    cursor = conn.cursor()
    
    # The exact problematic value that causes the error
    problematic_date = '2025-05-16T08:18:35.167165'
    fixed_date = '2025-05-16 08:18:35'
    
    # Directly target and fix the problematic record
    cursor.execute(
        "UPDATE evento_horario SET fecha = ? WHERE fecha = ?", 
        (fixed_date, problematic_date)
    )
    
    rows_affected = cursor.rowcount
    print(f"Updated {rows_affected} records with the exact problematic date")
    
    if rows_affected == 0:
        # If no exact match found, try a more general approach
        cursor.execute(
            "UPDATE evento_horario SET fecha = ? WHERE fecha LIKE ?", 
            (fixed_date, '2025-05-16T08:18:35%')
        )
        rows_affected = cursor.rowcount
        print(f"Updated {rows_affected} records with similar problematic date pattern")
    
    # Commit changes
    conn.commit()
    
    # Verify the fix
    cursor.execute("SELECT COUNT(*) FROM evento_horario WHERE fecha LIKE '%T%'")
    remaining_t_format = cursor.fetchone()[0]
    
    if remaining_t_format > 0:
        print(f"There are still {remaining_t_format} records with 'T' format dates.")
        cursor.execute("SELECT id, fecha FROM evento_horario WHERE fecha LIKE '%T%' LIMIT 5")
        for row in cursor.fetchall():
            print(f"  - ID: {row[0]}, Date: {row[1]}")
    else:
        print("All 'T' format dates have been fixed.")
    
    conn.close()
    print("Fix completed")

if __name__ == "__main__":
    fix_specific_datetime() 