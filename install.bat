@echo off
setlocal

echo Checking for Python 3...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python 3 is not installed or not found in PATH.
    echo Please install Python 3 and ensure it's added to your PATH.
    exit /b 1
)

echo Checking for virtual environment (venv)...
if not exist venv\ (
    echo Creating virtual environment in 'venv' directory...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment.
        exit /b 1
    )
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment. Check if 'venv\Scripts\activate.bat' exists.
    exit /b 1
)

echo Upgrading build tools...
python -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
    echo Warning: Failed to upgrade build tools. Installation might fail.
)

echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies. Please check requirements.txt and your internet connection.
    deactivate
    exit /b 1
)
echo Dependencies installed successfully.

echo Verifying dependencies...
python check_dependencies.py
if %errorlevel% neq 0 (
    echo Warning: Dependency check reported issues. The application might not run correctly.
) else (
    echo Dependency check successful.
)

echo Initializing database...
python create_db.py
if %errorlevel% neq 0 (
    echo Error: Failed to initialize the database using create_db.py.
    deactivate
    exit /b 1
)
echo Database initialized successfully.

echo Updating database schema...
python update_db.py
if %errorlevel% neq 0 (
    echo Warning: Failed to update database schema. Some features might not work correctly.
) else (
    echo Database schema updated successfully.
)

echo Installation complete.
echo You can now run the application using start.bat.

deactivate
endlocal 