@echo off
echo Restarting application to clear SQLAlchemy caching...

echo 1. Stopping any running Flask instances...
taskkill /f /im python.exe 2>nul

echo 2. Clearing any __pycache__ directories...
for /d /r %%d in (__pycache__) do (
    echo Removing %%d
    rd /s /q "%%d" 2>nul
)

echo 3. Confirming database schema has activo column...
python check_db_activo.py

echo 4. Starting application...
start python app.py

echo Application restart complete. Please try your operation again.
pause 