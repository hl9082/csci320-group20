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
import bcrypt

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
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    now = datetime.now()
    # Note: Using "user" as a table name can be problematic. Consider "users" instead.
    sql = 'INSERT INTO "user"(username, password, firstname, lastname, email, creationdate, lastaccessdate) VALUES(%s, %s, %s, %s, %s, %s, %s) RETURNING userid'
    user_id = None

    try:
        # Use our new pooled connection function, which is now very fast.
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                # Store the decoded hash string, not the plaintext password.
                curs.execute(sql, (username, hashed_password.decode('utf-8'), first_name, last_name, email, now, now))
                user_id_row = curs.fetchone()
                if user_id_row:
                    user_id = user_id_row['userid']
                conn.commit()
    except psycopg.errors.UniqueViolation:
        print(f"Attempted to create a user with a duplicate username or email: {username}")
        # conn.rollback() happens automatically when the 'with' block exits on error.
    except (psycopg.Error, ConnectionError) as e:
        print(f"Error creating user: {e}")

    return user_id

def login_user(username, password):
    
    '''
    Login with an existing username and password.
    
    Parameters:
    - username (str): the username.
    - password (str): the password.
    
    Returns: user, None if login fails.
    '''
    
    user_data = None
    # 1. Fetch the user's record, including the hashed password, by their username.
    sql_select = 'SELECT userid, username, password FROM "user" WHERE username = %s'

    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql_select, (username,))
                user_record = curs.fetchone()

                # 2. If a user is found, check if the provided password matches the stored hash.
                if user_record and bcrypt.checkpw(password.encode('utf-8'), user_record['password'].encode('utf-8')):
                    # Password is correct!
                    now = datetime.now()
                    sql_update = 'UPDATE "user" SET lastaccessdate = %s WHERE userid = %s'
                    curs.execute(sql_update, (now, user_record['userid']))
                    conn.commit()

                    # Don't send the password hash back to the web app.
                    user_data = {
                        'userid': user_record['userid'],
                        'username': user_record['username']
                    }
    except (psycopg.Error, ConnectionError) as e:
        print(f"Login failed due to a database error: {e}")

    return user_data

# --- Collection Management ---
def get_user_collections(user_id):
    
    '''
    This function gets user's collection.
    
    Parameter:
    - user_id (int): the user's id.
    
    Returns: list of songs from collection, and empty list if error.
    '''
  
    sql = 'SELECT title, numberofsongs, length FROM "collection" WHERE userid = %s ORDER BY title ASC'
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (user_id,))
                return curs.fetchall()
    except (psycopg.Error, ConnectionError) as e:
        print(f"Failed to get collections due to a database error: {e}")
        return [] # Return an empty list on error