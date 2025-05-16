#!/usr/bin/env python
"""
Direct fix for the specific problematic record in the database
"""
import sqlite3

def fix_date_record():
    print("Fixing specific problematic date record...")
    
    conn = sqlite3.connect('gimnasio.db')
    cursor = conn.cursor()
    
    # Directly fix the problematic record with the exact date
    cursor.execute("""
    UPDATE evento_horario 
    SET fecha = '2025-05-16 08:18:35' 
    WHERE fecha = '2025-05-16T08:18:35.167165'
    """)
    
    rows_affected = cursor.rowcount
    print(f"Updated {rows_affected} rows with the specific problematic date")
    
    # Backup approach: fix any date with the T format
    cursor.execute("""
    SELECT id, fecha FROM evento_horario 
    WHERE fecha LIKE '%T%'
    """)
    
    t_format_dates = cursor.fetchall()
    print(f"Found {len(t_format_dates)} records with 'T' in date format")
    
    if t_format_dates:
        print("Fixing records with 'T' in date format...")
        fixed = 0
        
        for row_id, date_str in t_format_dates:
            fixed_date = date_str.replace('T', ' ')
            if '.' in fixed_date:
                fixed_date = fixed_date.split('.')[0]
                
            cursor.execute(
                "UPDATE evento_horario SET fecha = ? WHERE id = ?", 
                (fixed_date, row_id)
            )
            fixed += 1
        
        print(f"Fixed {fixed} records with 'T' format dates")
    
    # Commit changes
    conn.commit()
    
    # Verify no problematic dates remain
    cursor.execute("SELECT COUNT(*) FROM evento_horario WHERE fecha LIKE '%T%'")
    remaining = cursor.fetchone()[0]
    
    if remaining > 0:
        print(f"Warning: {remaining} problematic records still remain")
    else:
        print("All problematic records have been fixed")
    
    conn.close()
    print("Fix completed")

if __name__ == "__main__":
    fix_date_record() 