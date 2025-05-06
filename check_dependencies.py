import pkg_resources
import sys
import platform

print("Python version:", platform.python_version())
print("PATH:", sys.path)
print("\nInstalled packages:")

try:
    installed_packages = pkg_resources.working_set
    installed_packages_list = sorted(["%s==%s" % (i.key, i.version) for i in installed_packages])
    
    for package in installed_packages_list:
        print("  ", package)
    
    # Check specifically for critical packages
    critical_packages = [
        'flask', 
        'flask_sqlalchemy', 
        'sqlalchemy',
        'setuptools',
        'flask_login',
        'openpyxl',
        'apscheduler',
        'pywhatkit',
        'pyautogui'
    ]
    
    print("\nCritical packages status:")
    for package in critical_packages:
        try:
            __import__(package)
            print(f"  ✓ {package} - Installed")
        except ImportError:
            print(f"  ✗ {package} - MISSING")

except Exception as e:
    print(f"Error checking packages: {e}") 