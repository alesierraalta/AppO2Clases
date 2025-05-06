#!/bin/bash

set -e

echo "Checking for Python 3..."
python3 --version >/dev/null 2>&1 || { echo "Error: Python 3 is not installed or not found in PATH."; exit 1; }

# Create a python symlink if it doesn't exist
if ! command -v python &> /dev/null; then
    echo "Creating python symlink to python3..."
    if [ -f /usr/bin/python3 ]; then
        sudo ln -s /usr/bin/python3 /usr/bin/python
    else
        echo "Warning: Could not create python symlink. Using python3 directly."
        alias python=python3
    fi
fi

echo "Checking for virtual environment (venv)..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment in 'venv' directory..."
    python3 -m venv venv || { echo "Error: Failed to create virtual environment."; exit 1; }
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

echo "Activating virtual environment..."
# shellcheck source=/dev/null
source venv/bin/activate || { echo "Error: Failed to activate virtual environment."; exit 1; }

echo "Upgrading build tools..."
pip install --upgrade pip setuptools wheel || echo "Warning: Failed to upgrade build tools. Installation might fail."

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt || { echo "Error: Failed to install dependencies."; deactivate; exit 1; }
echo "Dependencies installed successfully."

echo "Verifying dependencies..."
python check_dependencies.py
if [ $? -ne 0 ]; then
    echo "Warning: Dependency check reported issues. The application might not run correctly."
else
    echo "Dependency check successful."
fi

echo "Initializing database..."
python create_db.py || { echo "Error: Failed to initialize the database."; deactivate; exit 1; }
echo "Database initialized successfully."

echo "Updating database schema..."
python update_db.py
if [ $? -ne 0 ]; then
    echo "Warning: Failed to update database schema. Some features might not work correctly."
else
    echo "Database schema updated successfully."
fi

echo "Installation complete."
echo "You can now run the application using ./start.sh"

deactivate 