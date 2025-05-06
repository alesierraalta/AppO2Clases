import subprocess
import sys
import os
import platform

def run_command(command):
    """Run a command and return its output"""
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def ensure_setuptools():
    """Make sure setuptools is installed (required for distutils)"""
    print("Verificando setuptools (necesario para Python 3.12+)...")
    
    try:
        import setuptools
        print("✓ setuptools ya está instalado")
        return True
    except ImportError:
        print("✗ setuptools no está instalado. Instalando...")
        success, output = run_command(f"{sys.executable} -m pip install setuptools")
        if success:
            print("✓ setuptools instalado con éxito")
            return True
        else:
            print(f"✗ Error instalando setuptools: {output}")
            return False

def install_dependencies():
    """Install all required dependencies"""
    dependencies = [
        "Flask==2.0.1",
        "Flask-SQLAlchemy==2.5.1",
        "Jinja2==3.0.1",
        "SQLAlchemy==1.4.23",
        "Werkzeug==2.0.1",
        "WTForms==2.3.3",
        "flask-wtf==0.15.1",
        "click==8.0.1",
        "cryptography==3.4.8",
        "Flask-Login==0.5.0",
        "openpyxl==3.0.9",
        "APScheduler==3.9.1",
        "pywhatkit==5.4",
        "pyautogui==0.9.54"
    ]
    
    optional_dependencies = [
        "numpy==1.24.3",
        "pandas==2.0.3",
        "matplotlib==3.10.1",
        "librosa==0.11.0"
    ]
    
    print("\nInstalando dependencias principales...")
    for dep in dependencies:
        print(f"Instalando {dep}...")
        success, output = run_command(f"{sys.executable} -m pip install {dep}")
        if not success:
            print(f"✗ Error instalando {dep}: {output}")
        else:
            print(f"✓ {dep} instalado")
    
    print("\nInstalando dependencias opcionales...")
    for dep in optional_dependencies:
        print(f"Intentando instalar {dep}...")
        success, output = run_command(f"{sys.executable} -m pip install {dep}")
        if not success:
            print(f"⚠ No se pudo instalar {dep} (puede no ser necesario)")
        else:
            print(f"✓ {dep} instalado")

def verify_critical_dependencies():
    """Verify if critical dependencies are properly installed"""
    critical_modules = [
        'flask',
        'flask_sqlalchemy',
        'sqlalchemy',
        'flask_login',
        'openpyxl'
    ]
    
    print("\nVerificando dependencias críticas...")
    all_ok = True
    
    for module in critical_modules:
        try:
            __import__(module)
            print(f"✓ {module} - Instalado correctamente")
        except ImportError:
            print(f"✗ {module} - NO INSTALADO")
            all_ok = False
            
            # Try to reinstall
            print(f"  Reintentando instalación de {module}...")
            module_name = module.replace('_', '-')
            run_command(f"{sys.executable} -m pip install {module_name} --force-reinstall")
    
    return all_ok

def main():
    """Main function"""
    print("==== REPARADOR DE DEPENDENCIAS ====")
    print(f"Python {platform.python_version()} en {platform.system()}")
    
    # Check if we're in a virtual environment
    in_venv = sys.prefix != sys.base_prefix
    if not in_venv:
        print("⚠ ADVERTENCIA: No estás en un entorno virtual. Se recomienda usar un entorno virtual.")
        choice = input("¿Deseas continuar de todas formas? (s/n): ")
        if choice.lower() != 's' and choice.lower() != 'y':
            print("Operación cancelada.")
            return
    
    # Ensure setuptools is installed
    if not ensure_setuptools():
        print("Error crítico: No se pudo instalar setuptools. No se puede continuar.")
        return
    
    # Install dependencies
    install_dependencies()
    
    # Verify critical dependencies
    if verify_critical_dependencies():
        print("\n✅ Todas las dependencias críticas están instaladas correctamente.")
    else:
        print("\n⚠ Algunas dependencias críticas no se pudieron instalar correctamente.")
    
    print("\n==== FINALIZADO ====")
    print("Ahora puedes intentar ejecutar la aplicación con:\n")
    
    if platform.system() == "Windows":
        print("  run.bat")
        print("  o")
        print("  flask run --host=0.0.0.0 --port=5000")
    else:
        print("  flask run --host=0.0.0.0 --port=5000")
        print("  o")
        print("  python -m flask run --host=0.0.0.0 --port=5000")

if __name__ == "__main__":
    main()
    
    # Keep console open on Windows
    if platform.system() == "Windows":
        input("\nPresiona Enter para salir...") 