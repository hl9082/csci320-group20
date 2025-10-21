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
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv, find_dotenv

# Find and load environment variables from .env file
load_dotenv(find_dotenv())

CS_USERNAME = os.getenv("CS_USERNAME")
CS_PASSWORD = os.getenv("CS_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Global variables for the tunnel and the SQLAlchemy engine
server = None
engine = None

# This block ensures the tunnel and engine are created only once by the main Flask process.
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

        # Create the connection URI for SQLAlchemy
        db_uri = (
            f"postgresql+psycopg://{CS_USERNAME}:{CS_PASSWORD}@localhost:{server.local_bind_port}/{DB_NAME}"
        )

        print("Creating SQLAlchemy engine and connection pool...")
        # create_engine automatically handles connection pooling.
        engine = create_engine(db_uri, pool_pre_ping=True) # pool_pre_ping checks connection validity

        # Test the connection to ensure everything is working before the app starts.
        with engine.connect() as connection:
            print("Database connection successful. Engine is ready.")

    except Exception as e:
        print(f"FATAL: Failed to initialize database connection: {e}")
        if server and server.is_active:
            server.stop()
        engine = None # Ensure engine is None on failure

    def shutdown_hook():
        """A cleanup function to close resources when the app exits."""
        print("Executing shutdown hook...")
        if engine:
            engine.dispose()
            print("SQLAlchemy engine disposed.")
        if server and server.is_active:
            server.stop()
            print("SSH tunnel closed.")

    atexit.register(shutdown_hook)

@contextmanager
def get_db_connection():
    """
    Gets a connection from the SQLAlchemy engine's pool.
    """
    if not engine:
        raise ConnectionError("Database engine is not available. Check startup logs for errors.")
    
    connection = None
    try:
        connection = engine.connect()
        yield connection
    except Exception as e:
        print(f"Error getting connection from SQLAlchemy pool: {e}")
        raise
    finally:
        if connection:
            connection.close()






