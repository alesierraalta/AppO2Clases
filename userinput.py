"""Módulo para modificar el comportamiento de autenticación en la aplicación
Este archivo permite el acceso a todas las rutas sin necesidad de iniciar sesión
"""

import os
import sys

# Añadir el directorio actual al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar la aplicación y las funciones necesarias
from app_optimized import app, login_required
from functools import wraps
from flask import session, redirect, url_for, request

# Redefinir el decorador login_required para permitir acceso a todas las rutas sin autenticación
def custom_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Permitir acceso sin autenticación a todas las rutas
        return f(*args, **kwargs)
    return decorated_function

# Reemplazar el decorador original con nuestra versión personalizada
app.view_functions = {
    endpoint: custom_login_required(func) if hasattr(func, '__wrapped__') and func.__wrapped__.__name__ == login_required.__name__ else func
    for endpoint, func in app.view_functions.items()
}

# Mensaje de confirmación
print("\nMódulo userinput.py cargado correctamente.")
print("Se ha modificado el comportamiento de autenticación para permitir acceso a todas las rutas sin iniciar sesión.\n")