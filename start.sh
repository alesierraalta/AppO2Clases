#!/bin/bash

set -e

echo "Activating virtual environment..."
if [ ! -f "venv/bin/activate" ]; then
    echo "Error: Virtual environment not found. Please run install.sh first."
    exit 1
fi

# shellcheck source=/dev/null
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment."
    exit 1
fi

echo "Checking database connection..."
python check_db.py || echo "Warning: Database check failed. Attempting to start anyway..."

echo "Updating database schema..."
python update_db.py
if [ $? -ne 0 ]; then
    echo "Warning: Database schema update failed. Some features might not work correctly."
else
    echo "Database schema updated successfully."
fi

export FLASK_APP=app.py
export FLASK_ENV=development

echo "Starting Flask application..."
echo "Open http://127.0.0.1:5000 in your browser."

# Try to open the browser automatically (optional)
# Check for macOS
if [[ "$(uname)" == "Darwin" ]]; then 
  open http://127.0.0.1:5000
# Check for Linux 
elif command -v xdg-open &> /dev/null; then
  xdg-open http://127.0.0.1:5000
fi

flask run

DEACTIVATE_EXIT_CODE=$?

deactivate

exit $DEACTIVATE_EXIT_CODE 