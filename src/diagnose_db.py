'''
Author : Huy Le (hl9082)
Co authors: Jason Ting, Iris Li, Raymond Lee
Course: CSCI-320
Group: 20
Filename: diagnose_db.py
Purpose: This is a read-only diagnostic script to inspect the exact column names of the 
"user" table in the remote database. This helps resolve case-sensitivity issues.

'''

import psycopg
from psycopg.rows import dict_row
from sshtunnel import SSHTunnelForwarder
import os
from dotenv import load_dotenv, find_dotenv

def run_diagnostic():
    """Connects to the DB, inspects the 'user' table, and prints column names."""
    
    # Load credentials from .env
    load_dotenv(find_dotenv())
    CS_USERNAME = os.getenv("CS_USERNAME")
    CS_PASSWORD = os.getenv("CS_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")

    if not all([CS_USERNAME, CS_PASSWORD, DB_NAME]):
        print("ERROR: Missing database credentials in .env file. Cannot run diagnostic.")
        return

    print("Connecting to database to diagnose table schema...")
    
    try:
        with SSHTunnelForwarder(
            ('starbug.cs.rit.edu', 22),
            ssh_username=CS_USERNAME,
            ssh_password=CS_PASSWORD,
            remote_bind_address=('127.0.0.1', 5432)
        ) as server:
            params = {
                'dbname': DB_NAME, 'user': CS_USERNAME, 'password': CS_PASSWORD,
                'host': 'localhost', 'port': server.local_bind_port
            }
            with psycopg.connect(**params) as conn:
                with conn.cursor() as curs:
                    # Query the table to get its structure
                    curs.execute('SELECT * FROM "user";')
                    
                    if curs.description is None:
                        print('Could not find the user table or it is empty.')
                        return
                        
                    # Get column names from the cursor description
                    column_names = [desc[0] for desc in curs.description]
                    
                    print("\n" + "="*50)
                    print('Success! The exact column names in your "user" table are:')
                    for name in column_names:
                        print(f"- {name}")
                    print("="*50)
                    print("\nACTION: Make sure the SQL queries in 'src/backend.py' use these exact names.")

    except Exception as e:
        print("\n" + "!"*50)
        print(f"An error occurred during the diagnostic: {e}")
        print("Please check your .env credentials and network connection.")
        print("!"*50)

if __name__ == '__main__':
    run_diagnostic()