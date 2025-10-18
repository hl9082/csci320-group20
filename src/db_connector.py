'''
 Author: Huy Le (hl9082)
 Co-authors: Jason Ting, Iris Li, Raymond Lee
 Group: 20
 Course: CSCI 320
 Filename: db_connector.py 
 Purpose: 
 This module centralizes the database connection logic. It handles
          establishing an SSH tunnel to starbug.cs.rit.edu and connecting to the
          PostgreSQL database. It is the single source of truth for all DB connections.

'''

import psycopg
from psycopg.rows import dict_row
from sshtunnel import SSHTunnelForwarder
from contextlib import contextmanager
import os
from dotenv import load_dotenv, find_dotenv

# Find and load environment variables from .env file in the project root
load_dotenv(find_dotenv())

CS_USERNAME = os.getenv("CS_USERNAME")
CS_PASSWORD = os.getenv("CS_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

@contextmanager
def get_db_connection():
    """
    A context manager to handle the SSH tunnel and DB connection lifecycle.
    """
    if not all([CS_USERNAME, CS_PASSWORD, DB_NAME]):
        raise ConnectionError("Missing database credentials. Please check your .env file.")

    server = SSHTunnelForwarder(
        ('starbug.cs.rit.edu', 22),
        ssh_username=CS_USERNAME,
        ssh_password=CS_PASSWORD,
        remote_bind_address=('127.0.0.1', 5432)
    )
    conn = None
    try:
        print("Establishing SSH tunnel...")
        server.start()
        print("SSH tunnel established.")
        params = {
            'dbname': DB_NAME, 'user': CS_USERNAME, 'password': CS_PASSWORD,
            'host': 'localhost', 'port': server.local_bind_port
        }
        print("Connecting to database...")
        conn = psycopg.connect(**params)
        conn.row_factory = dict_row
        print("Database connection successful.")
        yield conn
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")
        server.stop()
        print("SSH tunnel closed.")