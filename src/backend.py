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
from db_connector import get_db_connection
import psycopg2 # Import psycopg2 for its specific error types

# --- User Management ---

def create_user(username, password, first_name, last_name, email):
    """
    Creates a new user with a securely hashed password using psycopg2.
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
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def login_user(username, password):
    """
    Logs a user in using psycopg2, with on-the-fly password migration.
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
                    return None

                stored_password = user_record['password']
                is_hashed = stored_password.startswith('$2b$')

                if is_hashed:
                    if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                        curs.execute(sql_update_access, (now, user_record['userid']))
                        conn.commit()
                        return {'userid': user_record['userid'], 'username': user_record['username']}
                    else:
                        return None
                else:
                    if stored_password == password:
                        print(f"NOTICE: Upgrading plaintext password for user: {username}")
                        new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        curs.execute(sql_update_password, (new_hash, now, user_record['userid']))
                        conn.commit()
                        print(f"SUCCESS: Password for user '{username}' has been securely upgraded.")
                        return {'userid': user_record['userid'], 'username': user_record['username']}
                    else:
                        return None
    except Exception as e:
        print(f"Login failed due to a database error: {e}")
        return None

# --- Collection Management ---
def get_user_collections(user_id):
    """
    Gets a user's collections using psycopg2.
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