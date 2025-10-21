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
import time
import socket # Import the socket module
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

        # --- FIX: Actively probe the tunnel port to ensure it's ready ---
        print("Waiting for tunnel to become ready...")
        tunnel_ready = False
        wait_start_time = time.monotonic()
        wait_timeout = 15  # seconds

        while time.monotonic() - wait_start_time < wait_timeout:
            try:
                # Attempt to create a brief connection to the tunnel's local port
                with socket.create_connection(('127.0.0.1', server.local_bind_port), timeout=1):
                    tunnel_ready = True
                    print("Tunnel is ready and accepting connections.")
                    break
            except (ConnectionRefusedError, socket.timeout):
                # Port is not open yet, wait a moment and retry
                time.sleep(0.2)
        
        if not tunnel_ready:
            raise ConnectionError(f"SSH tunnel failed to become ready on port {server.local_bind_port} within {wait_timeout} seconds.")

        # --- Proceed only after tunnel is confirmed to be ready ---
        print("Creating database connection pool...")
        conninfo_uri = (
            f"postgresql://{CS_USERNAME}:{CS_PASSWORD}@localhost:{server.local_bind_port}/{DB_NAME}"
        )
        db_pool = ConnectionPool(
            conninfo=conninfo_uri,
            min_size=1,
            max_size=10,
            kwargs={'row_factory': dict_row}
        )
        print("Database connection pool created.")

        # Final verification
        print("Checking pool health...")
        db_pool.check()
        print("Database connection pool is healthy and ready.")

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

    atexit.register(shutdown_hook)

@contextmanager
def get_db_connection():
    """
    Gets a connection from the pre-established pool.
    """
    if not db_pool:
        raise ConnectionError("Database connection pool is not available. Check startup logs for errors.")
    try:
        with db_pool.connection() as conn:
            yield conn
    except Exception as e:
        print(f"Error getting connection from pool: {e}")
        raise






