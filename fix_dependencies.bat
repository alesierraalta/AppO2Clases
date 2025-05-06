@echo off
echo Reparando dependencias para Python 3.12...

:: Activar el entorno virtual
call venv\Scripts\activate

:: Instalar setuptools primero (incluye distutils)
pip install setuptools

:: Instalar dependencias principales
echo Instalando dependencias principales...
pip install Flask==2.0.1
pip install Jinja2==3.0.1
pip install Werkzeug==2.0.1
pip install click==8.0.1
pip install Flask-Login==0.5.0
pip install Flask-SQLAlchemy==2.5.1
pip install SQLAlchemy==1.4.23
pip install WTForms==2.3.3
pip install flask-wtf==0.15.1
pip install cryptography==3.4.8
pip install openpyxl==3.0.9
pip install APScheduler==3.9.1
pip install pywhatkit==5.4
pip install pyautogui==0.9.54
pip install numpy==1.24.3
pip install pandas==2.0.3

:: Estas dependencias pueden ser problemáticas, instalar si es necesario
echo Instalando dependencias opcionales...
pip install matplotlib==3.10.1 || echo "Advertencia: No se pudo instalar matplotlib"
pip install librosa==0.11.0 || echo "Advertencia: No se pudo instalar librosa"

echo.
echo Dependencias instaladas. Ahora puede intentar ejecutar la aplicación con run.bat
echo.

pause 