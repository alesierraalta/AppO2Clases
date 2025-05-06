#!/bin/bash

set -e

echo "Checking for Python 3..."
if ! command -v python3 &> /dev/null
then
    echo "Error: Python 3 could not be found."
    echo "Please install Python 3."
    exit 1
fi

PYTHON_EXE=$(command -v python3)
echo "Using Python at: $PYTHON_EXE"

echo "Checking for virtual environment (venv)..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment in 'venv' directory..."
    $PYTHON_EXE -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        exit 1
    fi
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

echo "Activating virtual environment..."
# shellcheck source=/dev/null
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment. Check if 'venv/bin/activate' exists."
    exit 1
fi

echo "Upgrading build tools..."
python -m pip install --upgrade pip setuptools wheel || echo "Warning: Failed to upgrade build tools. Installation might fail."

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies. Please check requirements.txt and your internet connection."
    deactivate
    exit 1
fi
echo "Dependencies installed successfully."

echo "Verifying dependencies..."
python check_dependencies.py
if [ $? -ne 0 ]; then
    echo "Warning: Dependency check reported issues. The application might not run correctly."
else
    echo "Dependency check successful."
fi

echo "Initializing database..."
python create_db.py
if [ $? -ne 0 ]; then
    echo "Error: Failed to initialize the database using create_db.py."
    deactivate
    exit 1
fi
echo "Database initialized successfully."

echo "Installation complete."
echo "You can now run the application using start.sh."

deactivate

exit 0 