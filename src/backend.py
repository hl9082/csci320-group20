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
import bcrypt  # Used for securely hashing and verifying passwords.
from datetime import datetime  # Used to generate timestamps for creation and last access dates.
from db_connector import get_db_connection  # Imports the connection manager from our connector file.
import psycopg2  # Imported specifically to catch psycopg2-related exceptions like UniqueViolation.

# --- User Management ---

def create_user(username, password, first_name, last_name, email):
    """
    Creates a new user with a securely hashed password using psycopg2.

    Parameters:
        username (str): The new user's desired username.
        password (str): The user's plaintext password.
        first_name (str): The user's first name.
        last_name (str): The user's last name.
        email (str): The user's email address.

    Returns:
        int: The new user's 'userid' from the database if creation is successful.
        None: If the username or email already exists, or if any other database error occurs.
    
    Exceptions:
        Handles psycopg2.errors.UniqueViolation internally to return None.
        Catches and prints any other Exception, returning None.
    """
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    now = datetime.now()
    sql = """
        INSERT INTO "user"(username, password, firstname, lastname, email, creationdate, lastaccessdate)
        VALUES(%s, %s, %s, %s, %s, %s, %s)
        RETURNING userid
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (username, hashed_password.decode('utf-8'), first_name, last_name, email, now, now))
                user_id = curs.fetchone()['userid']
                conn.commit()
                return user_id
    except psycopg2.errors.UniqueViolation:
        # This error occurs if the username or email already exists in the database.
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def login_user(username, password):
    """
    Logs a user in using psycopg2, with on-the-fly password migration.
    If the stored password is plaintext, it verifies it and upgrades it to a hash.

    Parameters:
        username (str): The username of the user trying to log in.
        password (str): The plaintext password provided by the user.

    Returns:
        dict: A dictionary containing 'userid' and 'username' on successful login.
        None: If the username is not found or the password does not match.
        
    Exceptions:
        Catches and prints any database-related exceptions, returning None.
    """
    sql_select = 'SELECT userid, username, password FROM "user" WHERE username = %s'
    sql_update_access = 'UPDATE "user" SET lastaccessdate = %s WHERE userid = %s'
    sql_update_password = 'UPDATE "user" SET password = %s, lastaccessdate = %s WHERE userid = %s'
    now = datetime.now()

    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql_select, (username,))
                user_record = curs.fetchone()

                if not user_record:
                    return None  # User not found

                stored_password = user_record['password']
                is_hashed = stored_password.startswith('$2b$') # bcrypt hashes start with this prefix.

                if is_hashed:
                    # Stored password is a hash, perform a secure check.
                    if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                        curs.execute(sql_update_access, (now, user_record['userid']))
                        conn.commit()
                        return {'userid': user_record['userid'], 'username': user_record['username']}
                    else:
                        return None # Incorrect password
                else:
                    # Stored password is plaintext, perform a direct comparison and upgrade.
                    if stored_password == password:
                        print(f"NOTICE: Upgrading plaintext password for user: {username}")
                        new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        curs.execute(sql_update_password, (new_hash, now, user_record['userid']))
                        conn.commit()
                        print(f"SUCCESS: Password for user '{username}' has been securely upgraded.")
                        return {'userid': user_record['userid'], 'username': user_record['username']}
                    else:
                        return None # Incorrect password
    except Exception as e:
        print(f"Login failed due to a database error: {e}")
        return None

# --- Collection Management ---
def get_user_collections(user_id):
    """
    Gets a user's collections from the database using psycopg2.

    Parameters:
        user_id (int): The ID of the user whose collections are to be fetched.

    Returns:
        list: A list of dictionary-like rows representing the user's collections.
        list: An empty list if the user has no collections or if a database error occurs.

    Exceptions:
        Catches and prints any database-related exceptions, returning an empty list.
    """
    sql = 'SELECT title, numberofsongs, length FROM "collection" WHERE userid = %s ORDER BY title ASC'
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (user_id,))
                return curs.fetchall()
    except Exception as e:
        print(f"Failed to get collections due to a database error: {e}")
        return []