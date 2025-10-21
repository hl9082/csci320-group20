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
from sqlalchemy import text
from db_connector import get_db_connection
import psycopg # Still needed for catching specific psycopg errors

# --- User Management ---

def create_user(username, password, first_name, last_name, email):
    """
    Creates a new user with a securely hashed password using SQLAlchemy.
    """
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    now = datetime.now()
    sql = text("""
        INSERT INTO "user"(username, password, firstname, lastname, email, creationdate, lastaccessdate)
        VALUES(:username, :password, :first_name, :last_name, :email, :now, :now)
        RETURNING userid
    """)
    try:
        with get_db_connection() as conn:
            params = {
                "username": username, "password": hashed_password.decode('utf-8'),
                "first_name": first_name, "last_name": last_name,
                "email": email, "now": now
            }
            result = conn.execute(sql, params)
            user_id = result.scalar_one()
            conn.commit()
            return user_id
    except psycopg.errors.UniqueViolation:
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def login_user(username, password):
    """
    Logs a user in using SQLAlchemy, with on-the-fly password migration.
    """
    sql_select = text('SELECT userid, username, password FROM "user" WHERE username = :username')
    sql_update_access = text('UPDATE "user" SET lastaccessdate = :now WHERE userid = :userid')
    sql_update_password = text('UPDATE "user" SET password = :new_hash, lastaccessdate = :now WHERE userid = :userid')
    now = datetime.now()

    try:
        with get_db_connection() as conn:
            result = conn.execute(sql_select, {"username": username})
            # .mappings().first() provides a dictionary-like row object
            user_record = result.mappings().first()

            if not user_record:
                return None

            stored_password = user_record['password']
            is_hashed = stored_password.startswith('$2b$')

            if is_hashed:
                if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                    conn.execute(sql_update_access, {"now": now, "userid": user_record['userid']})
                    conn.commit()
                    return {'userid': user_record['userid'], 'username': user_record['username']}
                else:
                    return None
            else:
                if stored_password == password:
                    print(f"NOTICE: Upgrading plaintext password for user: {username}")
                    new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    conn.execute(sql_update_password, {
                        "new_hash": new_hash,
                        "now": now,
                        "userid": user_record['userid']
                    })
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
    Gets a user's collections using SQLAlchemy.
    """
    sql = text('SELECT title, numberofsongs, length FROM "collection" WHERE userid = :user_id ORDER BY title ASC')
    try:
        with get_db_connection() as conn:
            result = conn.execute(sql, {"user_id": user_id})
            return result.mappings().all()
    except Exception as e:
        print(f"Failed to get collections due to a database error: {e}")
        return []