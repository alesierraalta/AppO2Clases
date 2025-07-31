#!/usr/bin/env python3
"""
Script para verificar que todas las dependencias estén instaladas correctamente.
"""

import sys
import importlib

# Lista de todas las dependencias críticas de la aplicación
DEPENDENCIES = [
    # Flask y extensiones
    ('flask', 'Flask'),
    ('flask_sqlalchemy', 'Flask-SQLAlchemy'),
    ('flask_wtf', 'Flask-WTF'),
    ('werkzeug', 'Werkzeug'),
    ('jinja2', 'Jinja2'),
    ('wtforms', 'WTForms'),
    ('click', 'Click'),
    
    # Base de datos y ORM
    ('sqlalchemy', 'SQLAlchemy'),
    
    # Análisis de datos
    ('pandas', 'Pandas'),
    ('numpy', 'NumPy'),
    
    # Gráficos y visualización
    ('matplotlib', 'Matplotlib'),
    
    # Audio
    ('librosa', 'Librosa'),
    
    # PDF
    ('reportlab', 'ReportLab'),
    
    # Imágenes
    ('PIL', 'Pillow'),
    
    # Excel
    ('openpyxl', 'OpenPyXL'),
    
    # Programación de tareas
    ('apscheduler', 'APScheduler'),
    
    # WhatsApp (opcional)
    ('pywhatkit', 'PyWhatKit'),
    ('pyautogui', 'PyAutoGUI'),
    
    # Seguridad
    ('cryptography', 'Cryptography'),
    
    # Utilidades estándar (incluidas con Python)
    ('os', 'OS'),
    ('sys', 'Sys'),
    ('datetime', 'DateTime'),
    ('sqlite3', 'SQLite3'),
    ('io', 'IO'),
    ('re', 'RegEx'),
    ('calendar', 'Calendar'),
    ('logging', 'Logging'),
    ('traceback', 'Traceback'),
    ('functools', 'Functools'),
    ('glob', 'Glob'),
    ('shutil', 'Shutil'),
    ('base64', 'Base64'),
    ('time', 'Time'),
]

def check_dependency(module_name, display_name):
    """Verificar si un módulo se puede importar."""
    try:
        importlib.import_module(module_name)
        return True, None
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"

def main():
    """Función principal."""
    print("=" * 60)
    print("VERIFICADOR DE DEPENDENCIAS - CLASES O2")
    print("=" * 60)
    print()
    
    missing_dependencies = []
    optional_missing = []
    
    for module_name, display_name in DEPENDENCIES:
        success, error = check_dependency(module_name, display_name)
        
        if success:
            print(f"✓ {display_name:<20} OK")
        else:
            print(f"✗ {display_name:<20} ERROR: {error}")
            
            # Clasificar dependencias opcionales vs críticas
            if module_name in ['pywhatkit', 'pyautogui']:
                optional_missing.append((module_name, display_name, error))
            else:
                missing_dependencies.append((module_name, display_name, error))
    
    print()
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    if not missing_dependencies and not optional_missing:
        print("✓ TODAS LAS DEPENDENCIAS ESTÁN INSTALADAS CORRECTAMENTE")
        print("✓ La aplicación debería funcionar sin problemas")
        return 0
    
    if missing_dependencies:
        print("✗ DEPENDENCIAS CRÍTICAS FALTANTES:")
        for module_name, display_name, error in missing_dependencies:
            print(f"  - {display_name} ({module_name})")
        print()
        print("Para instalar las dependencias faltantes, ejecute:")
        print("  pip install -r requirements.txt")
        print("  O ejecute: install.bat")
    
    if optional_missing:
        print("⚠ DEPENDENCIAS OPCIONALES FALTANTES:")
        for module_name, display_name, error in optional_missing:
            print(f"  - {display_name} ({module_name})")
        print("Estas dependencias son opcionales. La aplicación funcionará sin ellas,")
        print("pero algunas funcionalidades (como notificaciones WhatsApp) no estarán disponibles.")
    
    return 1 if missing_dependencies else 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)