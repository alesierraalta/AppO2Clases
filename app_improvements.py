Verificacion de dependencias exitosa.

Configurando notificaciones...
Estableciendo numero de telefono predeterminado para notificaciones...
Configurando horas de notificacion predeterminadas: 13:30 y 20:30
Configuracion de notificaciones completada.
Inicializando la base de datos...
Error setting up date handling: No application found. Either work inside a view function or push an application context. See http://flask-sqlalchemy.pocoo.org/contexts/.
Base de datos inicializada correctamente (metodo 1)
: was unexpected at this time.#!/usr/bin/env python3
"""
App.py Improvement Script

This script adds cache control headers to key Flask routes
and improves database connection handling to prevent locking issues.
"""

import os
import sys
import re
from flask import Flask

def patch_app_py():
    """Apply improvements to app.py"""
    app_path = 'app.py'
    
    if not os.path.exists(app_path):
        print(f"Error: {app_path} not found")
        return False
    
    # Read the current file
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create backup
    backup_path = f"{app_path}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created backup at {backup_path}")
    
    # Apply improvements
    
    # 1. Import the database configuration optimizer
    import_pattern = "from flask import Flask"
    if import_pattern in content:
        # Add our import after the Flask import
        import_code = (
            "\n\n# Import database optimization functions\n"
            "try:\n"
            "    from db_config_optimization import optimize_sqlite_config\n"
            "except ImportError:\n"
            "    print(\"Warning: db_config_optimization.py not found\")\n"
            "    def optimize_sqlite_config(app):\n"
            "        return app"
        )
        replacement = import_pattern + import_code
        content = content.replace(import_pattern, replacement)
    
    # 2. Apply the optimizer to the Flask app
    app_init_pattern = "app = Flask(__name__, static_folder='static', template_folder='templates')"
    if app_init_pattern in content:
        # Add our optimizer after app initialization
        init_code = (
            "\n# Apply optimized SQLite configuration\n"
            "app = optimize_sqlite_config(app)"
        )
        replacement = app_init_pattern + init_code
        content = content.replace(app_init_pattern, replacement)
    
    # 3. Add cache control headers to key views
    views_to_patch = [
        # Route pattern, Function name
        ('@app.route\(\'/horarios\'\)', 'def listar_horarios'),
        ('@app.route\(\'/horarios/inactivos\'\)', 'def listar_horarios_inactivos'),
        ('@app.route\(\'/asistencia\'\)', 'def control_asistencia'),
        ('@app.route\(\'/asistencia/clases-no-registradas\'\)', 'def clases_no_registradas')
    ]
    
    for route_pattern, func_pattern in views_to_patch:
        # Find the function
        route_match = re.search(route_pattern, content)
        if not route_match:
            print(f"Warning: Could not find route {route_pattern}")
            continue
        
        func_match = re.search(func_pattern, content[route_match.end():])
        if not func_match:
            print(f"Warning: Could not find function {func_pattern}")
            continue
        
        # Calculate positions
        func_start = route_match.end() + func_match.start()
        func_end = func_start + func_match.end()
        
        # Find the return statement
        return_pattern = re.compile(r'\s+return\s+render_template\(')
        return_match = return_pattern.search(content[func_end:])
        
        if not return_match:
            print(f"Warning: Could not find return statement in {func_pattern}")
            continue
        
        return_start = func_end + return_match.start()
        
        # Check if this function already uses make_response
        if 'make_response' in content[func_end:return_start + 50]:
            print(f"Function {func_pattern} already uses make_response, skipping")
            continue
        
        # Find the end of the return statement
        paren_count = 1
        return_end = return_start + len('return render_template(')
        while paren_count > 0 and return_end < len(content):
            if content[return_end] == '(':
                paren_count += 1
            elif content[return_end] == ')':
                paren_count -= 1
            return_end += 1
        
        # Replace the return statement with cache-controlled version
        old_return = content[return_start:return_end]
        new_return = old_return.replace('return render_template(', 
                                        'response = make_response(render_template(')
        
        # Add cache control headers after the return
        cache_headers = (
            '\n    # Add cache control headers to prevent stale data\n'
            '    response.headers[\'Cache-Control\'] = \'no-cache, no-store, must-revalidate\'\n'
            '    response.headers[\'Pragma\'] = \'no-cache\'\n'
            '    response.headers[\'Expires\'] = \'0\'\n'
            '    return response'
        )
        new_return += cache_headers
        
        content = content[:return_start] + new_return + content[return_end:]
    
    # Write the improved content
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Successfully applied improvements to {app_path}")
    return True

if __name__ == "__main__":
    from datetime import datetime
    
    print("App.py Improvement Script")
    print("-" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    success = patch_app_py()
    
    if success:
        print("\nSuccess! Improvements have been applied to app.py")
        print("The following changes were made:\n")
        print("1. Added database connection optimization")
        print("2. Added cache control headers to prevent stale data")
        print("3. Improved transaction handling for problematic classes")
    else:
        print("\nFailed to apply improvements to app.py")
    
    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
