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

import os
import atexit
import psycopg
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from sshtunnel import SSHTunnelForwarder
from contextlib import contextmanager
from dotenv import load_dotenv, find_dotenv

# Find and load environment variables from .env file
load_dotenv(find_dotenv())

CS_USERNAME = os.getenv("CS_USERNAME")
CS_PASSWORD = os.getenv("CS_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Global variables for the tunnel and the pool
server = None
db_pool = None

# --- INITIALIZATION FIX ---
# This block now checks for an environment variable that Flask's reloader sets.
# This ensures that the SSH tunnel and database pool are created ONLY ONCE in
# the main application process, preventing conflicts with the reloader.
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or os.environ.get("FLASK_ENV") == "production":
    if not all([CS_USERNAME, CS_PASSWORD, DB_NAME]):
        raise ConnectionError("Missing database credentials. Please check your .env file.")

    # Define the SSH tunnel configuration
    print("Configuring SSH tunnel to starbug.cs.rit.edu...")
    server = SSHTunnelForwarder(
        ('starbug.cs.rit.edu', 22),
        ssh_username=CS_USERNAME,
        ssh_password=CS_PASSWORD,
        remote_bind_address=('127.0.0.1', 5432)
    )

    try:
        # Start the SSH tunnel
        print("Establishing SSH tunnel...")
        server.start()
        print(f"SSH tunnel established on local port {server.local_bind_port}.")

        # Create the connection pool through the tunnel
        print("Creating database connection pool...")
        conninfo = (
            f"dbname={DB_NAME} user={CS_USERNAME} password={CS_PASSWORD} "
            f"host=localhost port={server.local_bind_port}"
        )
        # --- FIX FOR 'connection_kwargs' ERROR ---
        # The row_factory must be passed directly into the constructor.
        db_pool = ConnectionPool(
            conninfo,
            min_size=1,
            max_size=10,
            open=True,
            row_factory=dict_row  # Pass row_factory directly here
        )
        print("Database connection pool created successfully.")

    except Exception as e:
        print(f"FATAL: Failed to initialize database connection: {e}")
        if server and server.is_active:
            server.stop()
        db_pool = None

    def shutdown_hook():
        """A cleanup function to close resources when the app exits."""
        print("Executing shutdown hook...")
        if db_pool:
            db_pool.close()
            print("Database connection pool closed.")
        if server and server.is_active:
            server.stop()
            print("SSH tunnel closed.")

    # Register the shutdown hook to be called when the application exits
    atexit.register(shutdown_hook)

@contextmanager
def get_db_connection():
    """
    Gets a connection from the pre-established pool.
    """
    if not db_pool:
        # This will now provide a clearer error if the pool failed to initialize.
        raise ConnectionError("Database connection pool is not available. Check startup logs for errors.")

    conn = None
    try:
        conn = db_pool.getconn()
        yield conn
    finally:
        if conn:
            db_pool.putconn(conn)