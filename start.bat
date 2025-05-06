@echo off
setlocal

echo Activating virtual environment...
if not exist venv\Scripts\activate.bat (
    echo Error: Virtual environment not found. Please run install.bat first.
    exit /b 1
)
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment.
    exit /b 1
)

echo Checking database connection...
python check_db.py
if %errorlevel% neq 0 (
    echo Warning: Database check failed. Attempting to start anyway...
)

set FLASK_APP=app.py
set FLASK_ENV=development

echo Starting Flask application...
echo Open http://127.0.0.1:5000 in your browser.

:: Try to open the browser automatically (optional)
start "" http://127.0.0.1:5000

flask run

deactivate
endlocal 