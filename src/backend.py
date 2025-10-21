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
import bcrypt
from datetime import datetime
# Import the single, authoritative connection function from the connector module
from db_connector import get_db_connection
import psycopg

# --- User Management ---

def create_user(username, password, first_name, last_name, email):
    """
    Creates a new user with a securely hashed password.
    This function is unchanged and remains secure for all new registrations.
    """
    # Hash the password using bcrypt
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
                # Store the hashed password (as a string) in the database
                curs.execute(sql, (hashed_password.decode('utf-8'), first_name, last_name, email, now, now))
                user_id = curs.fetchone()['userid']
                conn.commit()
                return user_id
    except psycopg.errors.UniqueViolation:
        # This will be caught if the username or email is not unique
        return None
    except (psycopg.Error, ConnectionError) as e:
        print(f"Error creating user: {e}")
        return None

def login_user(username, password):
    """
    Logs a user in, seamlessly upgrading their password from plaintext to a hash if needed.
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

                # A valid bcrypt hash will start with a signature like '$2b$'. Plaintext won't.
                is_hashed = stored_password.startswith('$2b$')

                if is_hashed:
                    # --- Path 1: Secure Hash ---
                    # The stored password is a hash, so we use bcrypt to check.
                    if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                        curs.execute(sql_update_access, (now, user_record['userid']))
                        conn.commit()
                        return {'userid': user_record['userid'], 'username': user_record['username']}
                    else:
                        return None  # Incorrect password
                else:
                    # --- Path 2: Plaintext Password (Lazy Migration) ---
                    # The stored password is plaintext. We compare it directly.
                    if stored_password == password:
                        # The password is correct. Now, UPGRADE it to a secure hash.
                        print(f"NOTICE: Upgrading plaintext password for user: {username}")
                        new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        curs.execute(sql_update_password, (new_hash, now, user_record['userid']))
                        conn.commit()
                        print(f"SUCCESS: Password for user '{username}' has been securely upgraded.")
                        return {'userid': user_record['userid'], 'username': user_record['username']}
                    else:
                        return None  # Incorrect password

    except (psycopg.Error, ConnectionError) as e:
        print(f"Login failed due to a database error: {e}")
        return None
    except ValueError as e:
        print(f"A password check failed unexpectedly: {e}")
        return None

# --- Collection Management ---
def get_user_collections(user_id):
    """
    Gets a user's collections. This function is unchanged.
    """
    sql = 'SELECT title, numberofsongs, length FROM "collection" WHERE userid = %s ORDER BY title ASC'
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (user_id,))
                return curs.fetchall()
    except (psycopg.Error, ConnectionError) as e:
        print(f"Failed to get collections due to a database error: {e}")
        return []