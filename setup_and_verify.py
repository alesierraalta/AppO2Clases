import sys
import subprocess
import os
import pkg_resources
import sqlite3
from datetime import datetime

# Function to run shell commands with error handling
def run_command(command, shell=True):
    try:
        result = subprocess.run(command, shell=shell, check=True, text=True, capture_output=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

# Step 1: Verify Python Version
print("Checking Python version...")
python_version = sys.version
print(f"Detected Python version: {python_version}")
if sys.version_info < (3, 6):
    print("WARNING: Python version is too old. Please upgrade to at least Python 3.6.")
    sys.exit(1)

# Step 2: Instructions for Virtual Environment Activation
print("\nInstructions for activating the virtual environment:")
print("- Windows: venv\\Scripts\\activate")
print("- Linux/Mac: source venv/bin/activate")
input("Please activate the virtual environment and press Enter to continue...")

# Step 3: Check and Install setuptools
print("\nChecking for setuptools...")
try:
    pkg_resources.get_distribution("setuptools")
    print("setuptools is already installed.")
except pkg_resources.DistributionNotFound:
    print("setuptools not found. Installing...")
    output = run_command("pip install setuptools")
    print(output)

# Step 4: Install Dependencies from requirements.txt
print("\nInstalling dependencies from requirements.txt...")
failed_deps = []
if os.path.exists("requirements.txt"):
    with open("requirements.txt", "r") as file:
        deps = file.readlines()
        for dep in deps:
            dep = dep.strip()
            if dep and not dep.startswith("#"):
                print(f"Installing {dep}...")
                output = run_command(f"pip install {dep}")
                if "Error" in output:
                    failed_deps.append((dep, output))
                print(output)
else:
    print("requirements.txt not found. Skipping dependency installation.")

# Step 5: Install Critical Dependencies with Force Reinstall if Needed
critical_deps = ["Flask==2.0.1", "Flask-SQLAlchemy==2.5.1", "Flask-Login==0.5.0", "openpyxl", "numpy"]
print("\nEnsuring critical dependencies are installed...")
for dep in critical_deps:
    print(f"Checking {dep}...")
    output = run_command(f"pip install --force-reinstall {dep}")
    if "Error" in output:
        failed_deps.append((dep, output))
    print(output)

# Special handling for numpy if it fails
if any("numpy" in dep for dep, _ in failed_deps):
    print("Trying a different version of numpy...")
    output = run_command("pip install --force-reinstall numpy==1.24.3")
    if "Error" in output:
        failed_deps.append(("numpy==1.24.3", output))
    print(output)

# Step 6: Verify Critical Dependencies by Import
print("\nVerifying critical dependencies...")
critical_modules = ["flask", "flask_sqlalchemy", "sqlalchemy", "flask_login", "openpyxl"]
failed_imports = []
for module in critical_modules:
    try:
        __import__(module)
        print(f"{module} imported successfully.")
    except ImportError as e:
        failed_imports.append((module, str(e)))
        print(f"Failed to import {module}: {e}")

# Step 7: Create or Verify Database
print("\nSetting up the database...")
db_status = ""
try:
    from app import create_app, db
    app = create_app()
    with app.app_context():
        db.create_all()
    db_status = "Database tables created successfully."
    print(db_status)
except Exception as e:
    print(f"Failed to create database tables: {e}")
    db_status = f"Failed to create database tables: {e}"
    print("Creating a fallback SQLite database...")
    try:
        conn = sqlite3.connect("gimnasio.db")
        conn.close()
        db_status += "\nFallback SQLite database created."
        print("Fallback SQLite database created.")
    except Exception as e2:
        db_status += f"\nFailed to create fallback database: {e2}"
        print(f"Failed to create fallback database: {e2}")

# Step 8: Generate Final Report
report = f"Setup Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
report += "=" * 50 + "\n"
report += f"Python Version: {python_version}\n"
report += "\nFailed Dependencies:\n"
if failed_deps:
    for dep, error in failed_deps:
        report += f"- {dep}: {error}\n"
else:
    report += "None\n"
report += "\nFailed Imports:\n"
if failed_imports:
    for module, error in failed_imports:
        report += f"- {module}: {error}\n"
else:
    report += "None\n"
report += f"\nDatabase Status: {db_status}\n"
report += "\nSetup Complete. Check for any errors above."

print("\n" + report)
with open("setup_report.txt", "w") as f:
    f.write(report)

print("Report saved to setup_report.txt")
if failed_deps or failed_imports:
    print("WARNING: There are issues with some dependencies or imports. Check the report for details.")
else:
    print("All set! You can now run the application.") 