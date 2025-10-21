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

import atexit
import psycopg
from psycopg.rows import dict_row
from psycopg.pool import ConnectionPool
from sshtunnel import SSHTunnelForwarder
from contextlib import contextmanager
import os
from dotenv import load_dotenv, find_dotenv

# 1. Find and load environment variables from .env file
load_dotenv(find_dotenv())

CS_USERNAME = os.getenv("CS_USERNAME")
CS_PASSWORD = os.getenv("CS_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Global variables for the tunnel and the pool
server = None
db_pool = None

if not all([CS_USERNAME, CS_PASSWORD, DB_NAME]):
    raise ConnectionError("Missing database credentials. Please check your .env file.")

# 2. Define the SSH tunnel configuration
# 
print("Configuring SSH tunnel to starbug.cs.rit.edu...")
server = SSHTunnelForwarder(
    ('starbug.cs.rit.edu', 22),
    ssh_username=CS_USERNAME,
    ssh_password=CS_PASSWORD,
    remote_bind_address=('127.0.0.1', 5432)
)

try:
    # 3. Start the SSH tunnel
    print("Establishing SSH tunnel...")
    server.start()
    print(f"SSH tunnel established on local port {server.local_bind_port}.")

    # 4. Create the connection pool through the tunnel
    # This pool is created only ONCE.
    print("Creating database connection pool...")
    conninfo = (
        f"dbname={DB_NAME} user={CS_USERNAME} password={CS_PASSWORD} "
        f"host=localhost port={server.local_bind_port}"
    )
    db_pool = ConnectionPool(conninfo, min_size=1, max_size=10, open=True)
    # Set the row_factory for all connections in the pool
    db_pool.connection_kwargs['row_factory'] = dict_row
    print("Database connection pool created successfully.")

except Exception as e:
    print(f"FATAL: Failed to initialize database connection: {e}")
    if server and server.is_active:
        server.stop()
    # Setting the pool to None ensures that any attempt to use it will fail clearly
    db_pool = None


@contextmanager
def get_db_connection():
    """
    A context manager to get a connection from the pre-established pool.
    This is now extremely fast as the tunnel and connections are already open.
    """
    if not db_pool:
        raise ConnectionError("Database connection pool is not available.")

    conn = None
    try:
        # Get a connection from the pool
        conn = db_pool.getconn()
        yield conn
    finally:
        if conn:
            # Return the connection to the pool
            db_pool.putconn(conn)


def shutdown_hook():
    """
    A cleanup function to close the pool and tunnel when the app exits.
    """
    print("Executing shutdown hook...")
    if db_pool:
        db_pool.close()
        print("Database connection pool closed.")
    if server and server.is_active:
        server.stop()
        print("SSH tunnel closed.")

# 5. Register the shutdown hook to be called when the application exits
atexit.register(shutdown_hook)# Find and load environment variables from .env file in the project root
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