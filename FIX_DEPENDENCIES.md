# Solución a problemas de dependencias

## Problema detectado
Se está produciendo un error al instalar dependencias en Python 3.12:
- Error: `ModuleNotFoundError: No module named 'distutils'`
- Error: `ModuleNotFoundError: No module named 'flask_sqlalchemy'`

Esto ocurre porque Python 3.12 ha eliminado el módulo `distutils` del núcleo de Python, y ahora es necesario instalarlo a través de `setuptools`.

## Solución

### Método 1: Script automático para Windows
1. Ejecutar el archivo `fix_dependencies.bat` haciendo doble clic sobre él.
2. Una vez completado, ejecutar `run_fixed.bat` para iniciar la aplicación.

### Método 2: Script Python (compatible con cualquier sistema operativo)
1. Activar el entorno virtual:
   - En Windows: `venv\Scripts\activate`
   - En Linux/Mac: `source venv/bin/activate`
2. Ejecutar: `python fix_dependencies.py`
3. Una vez completado, ejecutar la aplicación con `flask run --host=0.0.0.0 --port=5000`

### Método 3: Instalación manual
Si los métodos anteriores no funcionan, puedes realizar estos pasos manualmente:

1. Activar el entorno virtual:
   - En Windows: `venv\Scripts\activate`
   - En Linux/Mac: `source venv/bin/activate`

2. Instalar setuptools (contiene distutils):
   ```
   pip install setuptools
   ```

3. Instalar las dependencias principales:
   ```
   pip install Flask==2.0.1
   pip install Flask-SQLAlchemy==2.5.1
   pip install SQLAlchemy==1.4.23
   pip install Flask-Login==0.5.0
   pip install openpyxl==3.0.9
   pip install pywhatkit==5.4
   pip install pyautogui==0.9.54
   ```

4. Ejecutar la aplicación:
   ```
   flask run --host=0.0.0.0 --port=5000
   ```

## Verificación
Para verificar que todas las dependencias se han instalado correctamente, ejecuta:
```
python check_dependencies.py
```

Este script mostrará las dependencias instaladas y las críticas que faltan. 