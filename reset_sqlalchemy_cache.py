#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para resetear el caché de SQLAlchemy y refrescar las conexiones de base de datos
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

def reset_sqlalchemy_metadata():
    """Resetea los metadatos de SQLAlchemy y refresca las conexiones"""
    print("=== RESETEANDO METADATOS DE SQLALCHEMY ===")
    
    try:
        # Importar los modelos
        from models import db, ClaseRealizada, HorarioClase, Profesor
        
        # Crear una nueva aplicación Flask
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gimnasio.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Inicializar la base de datos
        db.init_app(app)
        
        with app.app_context():
            # Limpiar todas las conexiones existentes
            db.session.remove()
            
            # Crear un nuevo engine
            db.engine.dispose()
            
            # Reflejar la estructura de la base de datos
            db.reflect()
            
            print("✓ Metadatos de SQLAlchemy reseteados")
            
            # Probar que las consultas funcionan
            clases_count = ClaseRealizada.query.count()
            horarios_count = HorarioClase.query.count()
            profesores_count = Profesor.query.count()
            
            print(f"✓ Consultas de prueba exitosas:")
            print(f"  - Clases realizadas: {clases_count}")
            print(f"  - Horarios: {horarios_count}")
            print(f"  - Profesores: {profesores_count}")
            
            return True
            
    except Exception as e:
        print(f"Error reseteando metadatos: {e}")
        return False

def clear_python_cache():
    """Limpia el caché de Python"""
    print("\n=== LIMPIANDO CACHÉ DE PYTHON ===")
    
    try:
        # Limpiar caché de imports
        modules_to_clear = [mod for mod in sys.modules.keys() if mod.startswith('models')]
        for mod in modules_to_clear:
            if mod in sys.modules:
                del sys.modules[mod]
        
        print("✓ Caché de módulos Python limpiado")
        
        # Limpiar archivos __pycache__
        import shutil
        for root, dirs, files in os.walk('.'):
            for d in dirs:
                if d == '__pycache__':
                    cache_path = os.path.join(root, d)
                    try:
                        shutil.rmtree(cache_path)
                        print(f"✓ Eliminado: {cache_path}")
                    except:
                        pass
        
        return True
        
    except Exception as e:
        print(f"Error limpiando caché: {e}")
        return False

def main():
    """Función principal"""
    print("Reseteando caché de SQLAlchemy y Python...")
    
    # Limpiar caché de Python primero
    python_success = clear_python_cache()
    
    # Resetear metadatos de SQLAlchemy
    sqlalchemy_success = reset_sqlalchemy_metadata()
    
    print(f"\n=== RESUMEN ===")
    print(f"Caché Python: {'✓ LIMPIADO' if python_success else '✗ ERROR'}")
    print(f"SQLAlchemy: {'✓ RESETEADO' if sqlalchemy_success else '✗ ERROR'}")
    
    if python_success and sqlalchemy_success:
        print("\n✅ Cache reseteado exitosamente. Reinicie la aplicación Flask.")
    else:
        print("\n❌ Hubo errores. Es recomendable reiniciar manualmente.")

if __name__ == '__main__':
    main() 