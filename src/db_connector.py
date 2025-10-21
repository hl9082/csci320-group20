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
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import DictCursor
from contextlib import contextmanager
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv, find_dotenv

# Find and load environment variables from .env file
load_dotenv(find_dotenv())

CS_USERNAME = os.getenv("CS_USERNAME")
CS_PASSWORD = os.getenv("CS_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Global variables for the tunnel and the connection pool
server = None
db_pool = None

# This block ensures the tunnel and pool are created only once by the main Flask process.
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

        # Create the DSN string for psycopg2
        dsn = (
            f"dbname='{DB_NAME}' user='{CS_USERNAME}' password='{CS_PASSWORD}' "
            f"host='localhost' port='{server.local_bind_port}'"
        )

        print("Creating psycopg2 connection pool...")
        # Use a threaded pool suitable for web applications.
        # DictCursor allows accessing rows like dictionaries (e.g., row['id'])
        db_pool = ThreadedConnectionPool(minconn=1, maxconn=10, dsn=dsn, cursor_factory=DictCursor)
        
        # Test the connection to ensure the pool is valid before the app starts.
        with db_pool.getconn() as conn:
            print("Database connection successful. Pool is ready.")
        db_pool.putconn(conn) # Return the connection to the pool

    except Exception as e:
        print(f"FATAL: Failed to initialize database connection: {e}")
        if server and server.is_active:
            server.stop()
        db_pool = None # Ensure pool is None on failure

    def shutdown_hook():
        """A cleanup function to close resources when the app exits."""
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
    Gets a connection from the psycopg2 pool.
    """
    if not db_pool:
        raise ConnectionError("Database pool is not available. Check startup logs for errors.")
    
    conn = None
    try:
        conn = db_pool.getconn()
        yield conn
    except Exception as e:
        print(f"Error getting connection from psycopg2 pool: {e}")
        raise
    finally:
        if conn:
            db_pool.putconn(conn)






