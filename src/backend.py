# src/backend.py
'''
Author: Huy Le (hl9082)
Description: this is for sign up, log in, and collection display.
'''
import psycopg
from psycopg.rows import dict_row
from sshtunnel import SSHTunnelForwarder
from datetime import datetime
from contextlib import contextmanager
import os
from dotenv import load_dotenv, find_dotenv

# Find and load environment variables from .env file in the parent directory
load_dotenv(find_dotenv())

CS_USERNAME = os.getenv("CS_USERNAME")
CS_PASSWORD = os.getenv("CS_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

@contextmanager
def get_db_connection():
    """A context manager to handle the SSH tunnel and DB connection lifecycle."""
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
        server.start()
        params = {
            'dbname': DB_NAME, 'user': CS_USERNAME, 'password': CS_PASSWORD,
            'host': 'localhost', 'port': server.local_bind_port
        }
        conn = psycopg.connect(**params)
        conn.row_factory = dict_row
        yield conn
    finally:
        if conn:
            conn.close()
        server.stop()

# --- User Management ---
def create_user(username, password, first_name, last_name, email):
    now = datetime.now()
    sql = 'INSERT INTO "USER"(Username, Password, FirstName, LastName, Email, CreationDate, LastAccessDate) VALUES(%s, %s, %s, %s, %s, %s, %s) RETURNING UserID'
    try:
        with get_db_connection() as conn, conn.cursor() as curs:
            curs.execute(sql, (username, password, first_name, last_name, email, now, now))
            user_id = curs.fetchone()['userid']
            conn.commit()
            return user_id
    except psycopg.errors.UniqueViolation:
        return None

def login_user(username, password):
    sql_select = 'SELECT UserID, Username FROM "USER" WHERE Username = %s AND Password = %s'
    sql_update = 'UPDATE "USER" SET LastAccessDate = %s WHERE UserID = %s'
    now = datetime.now()
    try:
        with get_db_connection() as conn, conn.cursor() as curs:
            curs.execute(sql_select, (username, password))
            user = curs.fetchone()
            if user:
                curs.execute(sql_update, (now, user['userid']))
                conn.commit()
                return user
    except Exception:
        return None

# --- Collection Management ---
def get_user_collections(user_id):
    sql = "SELECT Title, NumberOfSongs, Length FROM COLLECTION WHERE UserID = %s ORDER BY Title ASC"
    with get_db_connection() as conn, conn.cursor() as curs:
        curs.execute(sql, (user_id,))
        return curs.fetchall()