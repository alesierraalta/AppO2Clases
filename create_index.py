from app import db

def create_indexes():
    """Create necessary indexes for optimized queries"""
    print("Creating indexes for database optimization...")
    
    # Create index on horario_clase.activo for faster queries
    try:
        db.engine.execute('CREATE INDEX IF NOT EXISTS idx_horario_activo ON horario_clase (activo)')
        print("✅ Created index on horario_clase.activo")
    except Exception as e:
        print(f"❌ Error creating index on horario_clase.activo: {str(e)}")
    
    print("Index creation completed")

if __name__ == "__main__":
    create_indexes() 