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
from psycopg2.extras import DictCursor # Ensures we can access results by column name

# --- User Management ---

def create_user(username, password, first_name, last_name, email):
    """
    Creates a new user using psycopg2.

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
    
    now = datetime.now()
    sql = """
        INSERT INTO "users"(username, password, firstname, lastname, email, creationdate, lastaccessdate)
        VALUES(%s, %s, %s, %s, %s, %s, %s)
        RETURNING userid
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (username, password, first_name, last_name, email, now, now))
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
    Logs a user in using psycopg2.

    Parameters:
        username (str): The username of the user trying to log in.
        password (str): The plaintext password provided by the user.

    Returns:
        dict: A dictionary containing 'userid' and 'username' on successful login.
        None: If the username is not found or the password does not match.
        
    Exceptions:
        Catches and prints any database-related exceptions, returning None.
    """
    sql_select = 'SELECT userid, username, password FROM "users" WHERE username = %s'
    sql_update_access = 'UPDATE "users" SET lastaccessdate = %s WHERE userid = %s'
    
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
                        
                        curs.execute(sql_update_access, ( now, user_record['userid']))
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
    
def get_collection_details(collection_id, user_id):
    """
    Gets a specific collection's info AND all songs within it.
    Ensures the user owns the collection.
    
    Parameters:
    - collection_id (int): collection's ID
    - user_id (int): user's ID.
    
    Returns collection's details, and None if not exists.
    """
    # First, get collection info and verify ownership
    sql_collection = 'SELECT collectionid, title FROM "collection" WHERE collectionid = %s AND userid = %s'
    
    # Then, get all songs in that collection
    sql_songs = """
        SELECT s.songid, s.title as song_title, ar.name as artist_name, al.title as album_title, s.length, g.name as genre_name
        FROM "song" s
        JOIN "collection_song" cs ON s.songid = cs.songid
        JOIN "artist" ar ON s.artistid = ar.artistid
        JOIN "album" al ON s.albumid = al.albumid
        JOIN "genre" g ON s.genreid = g.genreid
        WHERE cs.collectionid = %s
        ORDER BY s.title
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql_collection, (collection_id, user_id))
                collection_info = curs.fetchone()
                
                if not collection_info:
                    return None # User does not own this or it doesn't exist

                curs.execute(sql_songs, (collection_id,))
                songs = curs.fetchall()
                
                collection_info['songs'] = songs
                return collection_info
    except Exception as e:
        print(f"Failed to get collection details: {e}")
        return None


def create_collection(user_id, title):
    """
    Creates a new, empty collection for a user.
    
    Parameters:
    - user_id (int): user's ID.
    - title (string): collection's title
    
    Returns True if collection is created, and False if otherwise.
    """
    sql = 'INSERT INTO "collection" (userid, title, numberofsongs, length) VALUES (%s, %s, 0, 0)'
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (user_id, title))
                conn.commit()
                return True
    except Exception as e:
        print(f"Failed to create collection: {e}")
        return False

def rename_collection(collection_id, new_title, user_id):
    """
    Renames a user's collection, verifying ownership.
    
    Parameters:
    - collection_id (int): collection's ID
    - new_title (string): collection's new name
    - user_id (int): user's ID.
    
    Returns True if a row was updated, and False if otherwise.
    """
    sql = 'UPDATE "collection" SET title = %s WHERE collectionid = %s AND userid = %s'
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (new_title, collection_id, user_id))
                conn.commit()
                return curs.rowcount > 0 # Returns True if a row was updated
    except Exception as e:
        print(f"Failed to rename collection: {e}")
        return False

def delete_collection(collection_id, user_id):
    """
    Deletes a user's collection and all song mappings. Must be in a transaction.
    
    Parameters:
    - collection_id (int): collection's ID
    - user_id (int): user's ID.
    
    Returns True if the collection is removed, and False if otherwise.
    """
    # Verify ownership before deleting
    sql_check = 'SELECT 1 FROM "collection" WHERE collectionid = %s AND userid = %s'
    sql_delete_songs = 'DELETE FROM "collection_song" WHERE collectionid = %s'
    sql_delete_collection = 'DELETE FROM "collection" WHERE collectionid = %s'
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql_check, (collection_id, user_id))
                if curs.fetchone() is None:
                    return False # User does not own this
                
                # Run deletes
                curs.execute(sql_delete_songs, (collection_id,))
                curs.execute(sql_delete_collection, (collection_id,))
                conn.commit()
                return True
    except Exception as e:
        print(f"Failed to delete collection: {e}")
        conn.rollback() # Rollback on error
        return False

# --- Song and Search Management ---

def add_song_to_collection(collection_id, song_id, user_id):
    """
    Adds a single song to a collection, after verifying the user owns the collection.
    
    
    Parameters:
    - collection_id (int): collection's ID
    - song_id (int): song's ID
    - user_id (int): user's ID.
    
    Returns True if the song is added, and False if otherwise.
    """
    # Check if user owns the collection
    sql_check = 'SELECT 1 FROM "collection" WHERE collectionid = %s AND userid = %s'
    sql_insert = 'INSERT INTO "collection_song" (collectionid, songid) VALUES (%s, %s)'
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql_check, (collection_id, user_id))
                if curs.fetchone() is None:
                    return False # User does not own this
                
                curs.execute(sql_insert, (collection_id, song_id))
                conn.commit()
                # Here you would also update collection.numberofsongs and collection.length
                return True
    except psycopg2.errors.UniqueViolation:
        # Song is already in the collection
        conn.rollback()
        return False
    except Exception as e:
        print(f"Failed to add song to collection: {e}")
        conn.rollback()
        return False

def remove_song_from_collection(collection_id, song_id, user_id):
    """
    Removes a single song from a collection, verifying ownership first.
    
    Parameters:
    - collection_id (int): collection's ID
    - song_id (int): song's ID
    - user_id (int): user's ID.
    
    Returns True if the song is removed, and False if otherwise.
    """
    # We join with the collection table to ensure the user_id matches.
    sql = """
        DELETE FROM "collection_song" cs
        USING "collection" c
        WHERE cs.collectionid = c.collectionid
          AND c.collectionid = %s
          AND cs.songid = %s
          AND c.userid = %s
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (collection_id, song_id, user_id))
                conn.commit()
                # Here you would also update collection.numberofsongs and collection.length
                return curs.rowcount > 0
    except Exception as e:
        print(f"Failed to remove song from collection: {e}")
        conn.rollback()
        return False

def search_songs(search_term, search_type, sort_by, sort_order):
    """
    Searches for songs based on various criteria and sorting options.
    
    Parameters:
    - search_term (str): The term to search for.
    - search_type (str): song, artist, album, or genre.
    - sort_by (str): the criteria by which we sort the list.
    - sort_order (str): ascending or descending.
    """
    # Whitelist sort options to prevent SQL injection
    sort_columns_map = {
        'song_name': 's.title',
        'artist_name': 'ar.name',
        'genre_name': 'g.name',
        'releaseyear': 's.releaseyear'
    }
    sort_order_map = {'ASC': 'ASC', 'DESC': 'DESC'}

    # Default to safe values if inputs are invalid
    sort_column = sort_columns_map.get(sort_by, 's.title')
    sort_direction = sort_order_map.get(sort_order, 'ASC')
    
    # Default sort
    order_by_clause = f"ORDER BY {sort_column} {sort_direction}"
    if sort_by == 'song_name':
        order_by_clause += ", ar.name ASC" # Add secondary sort
        
    base_query = """
        SELECT s.songid, s.title as song_name, ar.name as artist_name, al.title as album_name, 
               g.name as genre_name, s.length, s.releaseyear, s.listencount
        FROM "song" s
        JOIN "artist" ar ON s.artistid = ar.artistid
        JOIN "album" al ON s.albumid = al.albumid
        JOIN "genre" g ON s.genreid = g.genreid
    """
    
    where_clause = ""
    params = ()
    search_pattern = f"%{search_term}%"

    if search_type == 'song':
        where_clause = "WHERE s.title ILIKE %s"
        params = (search_pattern,)
    elif search_type == 'artist':
        where_clause = "WHERE ar.name ILIKE %s"
        params = (search_pattern,)
    elif search_type == 'album':
        where_clause = "WHERE al.title ILIKE %s"
        params = (search_pattern,)
    elif search_type == 'genre':
        where_clause = "WHERE g.name ILIKE %s"
        params = (search_pattern,)
    else:
        return [] # Invalid search type

    sql = f"{base_query} {where_clause} {order_by_clause}"
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, params)
                return curs.fetchall()
    except Exception as e:
        print(f"Failed to search songs: {e}")
        return []

# --- "Play" Functions ---

def play_song(song_id, user_id):
    """
    Logs that a user played a song and increments the song's global play count.
    
    Parameters:
    - song_id (int): song's ID.
    - user_id (int): user's ID.
    
    Returns: True if the song is played, and False otherwise.
    """
    sql_log = 'INSERT INTO "user_song_play" (userid, songid, playtimestamp) VALUES (%s, %s, %s)'
    sql_count = 'UPDATE "song" SET listencount = listencount + 1 WHERE songid = %s'
    now = datetime.now()
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql_log, (user_id, song_id, now))
                curs.execute(sql_count, (song_id,))
                conn.commit()
                return True
    except Exception as e:
        print(f"Failed to play song: {e}")
        conn.rollback()
        return False

def play_collection(collection_id, user_id):
    """
    Logs a play event for *every* song in a collection and increments their counts.
    
    Parameters:
    - collection_id (int): collection's ID
    - user_id (int): user's ID
    
    Returns: number of songs played in the collection.
    """
    # Check if user owns the collection
    sql_check = 'SELECT 1 FROM "collection" WHERE collectionid = %s AND userid = %s'
    
    # Log plays for all songs in the collection
    sql_log_all = """
        INSERT INTO "user_song_play" (userid, songid, playtimestamp)
        SELECT %s, songid, %s
        FROM "collection_song"
        WHERE collectionid = %s
    """
    # Increment counts for all songs in the collection
    sql_count_all = """
        UPDATE "song"
        SET listencount = listencount + 1
        WHERE songid IN (SELECT songid FROM "collection_song" WHERE collectionid = %s)
    """
    now = datetime.now()
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql_check, (collection_id, user_id))
                if curs.fetchone() is None:
                    return 0 # User does not own this
                
                curs.execute(sql_log_all, (user_id, now, collection_id))
                played_count = curs.rowcount # Get how many songs were logged
                
                curs.execute(sql_count_all, (collection_id,))
                conn.commit()
                
                return played_count
    except Exception as e:
        print(f"Failed to play collection: {e}")
        conn.rollback()
        return 0