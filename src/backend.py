'''
Author: Huy Le (hl9082)
Co-authors: Jason Ting, Iris Li, Raymond Lee
 Group: 20
 Course: CSCI 320
 Filename: backend.py
Description: 
This module contains all the functions that interact with the database.
          It serves as the data access layer, separating SQL logic from the
          web application's routing logic.
'''
import psycopg
from datetime import datetime
# Import the single, authoritative connection function from the connector module
from db_connector import get_db_connection

# --- User Management ---
def create_user(username, password, first_name, last_name, email):
    '''
    Create a new user in the database.
    
    Parameters:
    - username (str): user's username.
    - password (str): the user's password.
    - first_name (str): the user's first name.
    - last_name (str): the user's last name.
    - email (str): the user's email.
    
    Returns: new user's id; None if the username or email already exists.
    '''
    now = datetime.now()
    sql = 'INSERT INTO USER(Username, Password, FirstName, LastName, Email, CreationDate, LastAccessDate) VALUES(%s, %s, %s, %s, %s, %s, %s) RETURNING UserID'
    try:
        with get_db_connection() as conn, conn.cursor() as curs:
            curs.execute(sql, (username, password, first_name, last_name, email, now, now))
            user_id = curs.fetchone()['userid']
            conn.commit()
            return user_id
    except psycopg.errors.UniqueViolation:
        return None
    except (psycopg.Error, ConnectionError) as e:
        print(f"Error creating user: {e}")
        return None

def login_user(username, password):
    
    '''
    Login with an existing username and password.
    
    Parameters:
    - username (str): the username.
    - password (str): the password.
    
    Returns: user, None if login fails.
    '''
    
    sql_select = 'SELECT userid, username FROM user WHERE username = %s AND password = %s'
    sql_update = 'UPDATE user SET lastaccessdate = %s WHERE userid = %s'
    now = datetime.now()
    try:
        with get_db_connection() as conn, conn.cursor() as curs:
            curs.execute(sql_select, (username, password))
            user = curs.fetchone()
            if user:
                curs.execute(sql_update, (now, user['userid']))
                conn.commit()
                return user
    except (psycopg.Error, ConnectionError) as e:
        print(f"Login failed due to a database error: {e}")
        return None

# --- Collection Management ---
def get_user_collections(user_id):
    
    '''
    This function gets user's collection.
    
    Parameter:
    - user_id (int): the user's id.
    
    Returns: list of songs from collection, and empty list if error.
    '''
    
    sql = "SELECT Title, NumberOfSongs, Length FROM COLLECTION WHERE UserID = %s ORDER BY Title ASC"
    try:
        with get_db_connection() as conn, conn.cursor() as curs:
            curs.execute(sql, (user_id,))
            return curs.fetchall()
    except (psycopg.Error, ConnectionError) as e:
        print(f"Failed to get collections due to a database error: {e}")
        return [] # Return an empty list on error