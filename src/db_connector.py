'''
Author: Huy Le (hl9082)
Co-authors: Jason Ting, Iris Li, Raymond Lee
Group: 20
Course: CSCI 320
Filename: db_connector.py 
Purpose: 
This module centralizes the database connection logic. It handles establishing an SSH tunnel 
to starbug.cs.rit.edu and connecting to the PostgreSQL database. 
It is the single source of truth for all DB connections.

'''

import os  # Used to access environment variables.
import atexit  # Allows registering functions to be called upon script exit for cleanup.
import psycopg2  # The main Python adapter for PostgreSQL.
from psycopg2.pool import ThreadedConnectionPool  # A connection pool suitable for multi-threaded apps like Flask.
from psycopg2.extras import DictCursor  # A cursor that returns rows as dictionary-like objects.
from contextlib import contextmanager  # A utility to create context managers for 'with' statements.
from sshtunnel import SSHTunnelForwarder  # Manages the SSH tunnel to the remote database server.
from dotenv import load_dotenv, find_dotenv  # Loads variables from a .env file into the environment.

# Find and load environment variables from .env file
load_dotenv(find_dotenv())

# --- Global Variables ---
# Database credentials loaded from the .env file.
CS_USERNAME = os.getenv("CS_USERNAME")
CS_PASSWORD = os.getenv("CS_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Global placeholders for the SSH tunnel and database pool objects.
# They are initialized once when the application starts.
server = None
db_pool = None

# This block ensures the tunnel and pool are created only once by the main Flask process.
# The 'WERKZEUG_RUN_MAIN' check prevents this code from running in the reloader's subprocess.
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or os.environ.get("FLASK_ENV") == "production":
    if not all([CS_USERNAME, CS_PASSWORD, DB_NAME]):
        raise ConnectionError("Missing database credentials. Please check your .env file.")

    print("Configuring SSH tunnel to starbug.cs.rit.edu...")
    server = SSHTunnelForwarder(
        ('starbug.cs.rit.edu', 22),
        ssh_username=CS_USERNAME,
        ssh_password=CS_PASSWORD,
        remote_bind_address=('127.0.0.1', 5432)
    )

    try:
        print("Establishing SSH tunnel...")
        server.start()
        print(f"SSH tunnel established on local port {server.local_bind_port}.")

        # The Data Source Name (DSN) is a string containing all connection parameters for psycopg2.
        dsn = (
            f"dbname='{DB_NAME}' user='{CS_USERNAME}' password='{CS_PASSWORD}' "
            f"host='localhost' port='{server.local_bind_port}'"
        )

        print("Creating psycopg2 connection pool...")
        # A threaded pool is ideal for web apps where each request might be in a different thread.
        # DictCursor makes row access convenient (e.g., row['column_name']).
        db_pool = ThreadedConnectionPool(minconn=1, maxconn=10, dsn=dsn, cursor_factory=DictCursor)
        
        # Test the connection to ensure the pool is valid before the app starts handling requests.
        with db_pool.getconn() as conn:
            print("Database connection successful. Pool is ready.")
        db_pool.putconn(conn) # Return the connection immediately to the pool.

    except Exception as e:
        print(f"FATAL: Failed to initialize database connection: {e}")
        if server and server.is_active:
            server.stop()
        db_pool = None # Ensure pool is set to None on failure.

    def shutdown_hook():
        """
        A cleanup function registered with atexit to close resources when the app shuts down.
        """
        print("Executing shutdown hook...")
        if db_pool:
            db_pool.closeall()
            print("psycopg2 connection pool closed.")
        if server and server.is_active:
            server.stop()
            print("SSH tunnel closed.")

    atexit.register(shutdown_hook)

@contextmanager
def get_db_connection():
    """
    A context manager to safely get a connection from the global pool and ensure it's returned.
    
    Yields:
        conn: A database connection object from the pool.
    
    Raises:
        ConnectionError: If the database pool was never initialized or failed to initialize.
        Exception: Re-raises any other exception that occurs while getting a connection.
    """
    if not db_pool:
        raise ConnectionError("Database pool is not available. Check startup logs for errors.")
    
    conn = None
    try:
        # Get a connection from the pool.
        conn = db_pool.getconn()
        yield conn
    except Exception as e:
        print(f"Error getting connection from psycopg2 pool: {e}")
        raise
    finally:
        # This block ensures the connection is ALWAYS returned to the pool,
        # even if errors occurred in the 'with' block.
        if conn:
            db_pool.putconn(conn)






