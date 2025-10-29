import os
import sys
import csv
import importlib
import bcrypt

# --- Ensure access to src/ ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src import db_connector, backend

# --- Initialize DB connection ---
if db_connector.db_pool is None:
    print("Initializing DB connection...")
    os.environ["WERKZEUG_RUN_MAIN"] = "true"
    importlib.reload(db_connector)

# --- Read CSV and create users ---
with open('users.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)  # Use DictReader for named access
    for row in reader:
        password = row['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        backend.create_user(
            username=row['username'],
            password=hashed_password,
            first_name=row['firstname'],
            last_name=row['lastname'],
            email=row['email']
        )
        print(f"✅ Created user: {row['username']}")
