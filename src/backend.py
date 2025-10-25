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
    collection_info = {
        'title': collection_id,
        'songs': []
    }
    
    # Get all songs in that collection
    sql_songs = """
        SELECT 
            S.songid, S.title AS SongTitle, S.length, S.releasedate,
            A.name AS ArtistName,
            AL.title AS AlbumTitle, AL.albumid,
            G.genretype AS GenreName,
            R.rating
        FROM "song" S
        JOIN "consists_of" CO ON S.songid = CO.songid
        JOIN "performs" P ON S.songid = P.songid
        JOIN "artist" A ON P.artistid = A.artistid
        JOIN "contains" C ON S.songid = C.songid
        JOIN "album" AL ON C.albumid = AL.albumid
        JOIN "has" H ON S.songid = H.songid
        JOIN "genre" G ON H.genreid = G.genreid
        LEFT JOIN "rates" R ON S.songid = R.songid AND R.songid = %s
        WHERE CO.userid = %s AND CO.title = %s
        ORDER BY S.title
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql_songs, (user_id, user_id, collection_title))
                songs = curs.fetchall()
                
                if not songs:
                    # Check if the collection *exists* but is just empty
                    curs.execute('SELECT 1 FROM "COLLECTION" WHERE UserID = %s AND Title = %s', (user_id, collection_title))
                    if curs.fetchone() is None:
                        return None # Collection doesn't exist at all
                
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
    sql = 'UPDATE "collection" SET title = %s WHERE title = %s AND userid = %s'
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
    sql = 'DELETE FROM "collection" where userid = %s AND title = %s'
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (user_id, title))
                conn.commit()
                return True
    except Exception as e:
        print(f"Failed to delete collection: {e}")
        conn.rollback() # Rollback on error
        return False
    
def update_collection_stats(conn, user_id, collection_id):
    """
    Private helper function to update a collection's song count and total length.
    This should be called *within* a transaction.
    """
    sql_update_stats = """
        WITH Stats AS (
            SELECT
                COUNT(S.songiD) AS SongCount,
                COALESCE(SUM(S.length), 0) AS TotalLength
            FROM "consists_of" CO
            JOIN "song" S ON CO.songid = S.songid
            WHERE CO.userid = %s AND CO.title = %s
        )
        UPDATE "collection" C
        SET
            numberofsongs = S.SongCount,
            length = S.TotalLength
        FROM Stats S
        WHERE C.userid = %s AND C.title = %s;
    """
    with conn.cursor() as curs:
        curs.execute(sql_update_stats, (user_id, collection_id, user_id, collection_id))

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
    
    sql_insert = 'INSERT INTO "consists_of" (userid, title, songid) VALUES (%s, %s, %s)'
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                # Insert the song into the bridge table
                curs.execute(sql_insert, (user_id, collection_id, song_id))
            
            # Update the collection stats in the same transaction
            update_collection_stats(conn, user_id, collection_id)
            
            conn.commit()
            return True
    except psycopg2.errors.UniqueViolation:
        # Song is already in the collection
        return False
    except psycopg2.errors.ForeignKeyViolation:
        # User doesn't own this collection, or song doesn't exist
        return False
    except Exception as e:
        print(f"Failed to add song to collection: {e}")
        conn.rollback()
        return False
    
def add_album_to_collection(user_id, collection_id, album_id):
    """
    Adds all songs from a given album to a collection.
    Ignores songs that are already in the collection.
    Returns the number of *new* songs added.
    """
    # This query finds all songs from the album that are NOT already
    # in the user's collection, then inserts them.
    sql_insert_album = """
        INSERT INTO "consists_of" (userid, title, songid)
        SELECT %s, %s, C.songid
        FROM "contains" C
        WHERE C.albumid = %s
        AND NOT EXISTS (
            SELECT 1
            FROM "consists_of" CO
            WHERE CO.userid = %s
            AND CO.title = %s
            AND CO.songid = C.songid
        )
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql_insert_album, (user_id, collection_id, album_id, user_id, collection_id))
                added_count = curs.rowcount # Get how many songs were inserted
            
            # Update the collection stats in the same transaction
            _update_collection_stats(conn, user_id, collection_title)
            
            conn.commit()
            return added_count
    except Exception as e:
        print(f"Failed to add album to collection: {e}")
        conn.rollback()
        return 0

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
    sql_delete = 'DELETE FROM "consists_of" WHERE userid = %s AND title = %s AND songid = %s'
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                # Delete the song from the bridge table
                curs.execute(sql_delete, (user_id, collection_id, song_id))
                deleted_count = curs.rowcount
            
            if deleted_count > 0:
                # Update stats only if a song was actually deleted
                update_collection_stats(conn, user_id, collection_id)
            
            conn.commit()
            return deleted_count > 0
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
        'song_name': 'S.title',
        'artist_name': 'A.name',
        'genre_name': 'G.genretype',
        'releaseyear': 'S.releaseyear'
    }
    sort_order_map = {'ASC': 'ASC', 'DESC': 'DESC'}

    # Default to safe values if inputs are invalid
    sort_column = sort_columns_map.get(sort_by, 'S.title')
    sort_direction = sort_order_map.get(sort_order, 'ASC')
    
    # Base sort
    order_by_clause = f"ORDER BY {sort_column} {sort_direction}"
    # Add secondary sort for song name
    if sort_by == 'song_name':
        order_by_clause += ", A.name ASC"
    elif sort_by == 'artist_name':
        order_by_clause += ", S.title ASC"
        
    # This subquery calculates the listen count for each song
    listen_count_subquery = """
        (SELECT COUNT(*) FROM "plays" P WHERE P.songid = S.songid) AS listencount
    """
    
    # This query is complex because it must join all M-M tables
    base_query = f"""
        SELECT DISTINCT
            S.songid, 
            S.title AS song_name, 
            S.length, 
            S.releaseyear,
            A.name AS artist_name, 
            AL.title AS album_name, 
            AL.albumid,
            G.genretype AS genre_name,
            {listen_count_subquery}
        FROM "sonh" S
        JOIN "performs" P ON S.songid = P.songid
        JOIN "artist" A ON P.artistid = A.artistid
        JOIN "contains" C ON S.songid = C.songid
        JOIN "album" AL ON C.albumid = AL.albumid
        JOIN "has" H ON S.songid = H.songid
        JOIN "genre" G ON H.genreid = G.genreid
    """
    
    where_clause = ""
    params = ()
    search_pattern = f"%{search_term}%" # ILIKE is case-insensitive

    if search_type == 'song':
        where_clause = "WHERE S.title ILIKE %s"
        params = (search_pattern,)
    elif search_type == 'artist':
        where_clause = "WHERE A.name ILIKE %s"
        params = (search_pattern,)
    elif search_type == 'album':
        where_clause = "WHERE AL.title ILIKE %s"
        params = (search_pattern,)
    elif search_type == 'genre':
        where_clause = "WHERE G.genretype ILIKE %s"
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
    sql_log = 'INSERT INTO "plays" (userid, songid, playtimestamp) VALUES (%s, %s, %s)'
    
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

    # Log plays for all songs in the collection
    sql_log_all = """
        INSERT INTO "plays" (userid, songid, playdate)
        SELECT %s, songid, %s
        FROM "consists_of"
        WHERE userid = %s AND title = %s
    """
    now = datetime.now()
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql_log_all, (user_id, now, user_id, collection_id))
                played_count = curs.rowcount # Get how many songs were logged
                conn.commit()
                return played_count
    except Exception as e:
        print(f"Failed to play collection: {e}")
        return 0

def rate_song(user_id, song_id, rating):
    """
    Inserts or updates a user's rating for a song.
    Enforces that the rating must be between 1 and 5.
    """
    try:
        rating_val = int(rating)
        if not 1 <= rating_val <= 5:
            print("Invalid rating value. Must be 1-5.")
            return False
    except ValueError:
        print("Invalid rating value. Must be an integer.")
        return False

    # Use ON CONFLICT to either INSERT a new rating or UPDATE an existing one
    sql = """
        INSERT INTO "rates" (userid, songid, rating)
        VALUES (%s, %s, %s)
        ON CONFLICT (userid, songid)
        DO UPDATE SET rating = EXCLUDED.rating
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (user_id, song_id, rating_val))
                conn.commit()
                return True
    except Exception as e:
        print(f"Failed to rate song: {e}")
        return False
    
def get_all_users_to_follow(user_id):
    """
    Gets a list of all users *except* the currently logged-in one.
    Also checks if the logged-in user is already following each user.
    """
    sql = """
        SELECT U.userid, U.username, U.email,
               CASE WHEN F.follower IS NOT NULL THEN true ELSE false END as is_following
        FROM "users" U
        LEFT JOIN "follows" F ON U.userid = F.followee AND F.follower = %s
        WHERE U.userid != %s
        ORDER BY U.username
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (user_id, user_id))
                return curs.fetchall()
    except Exception as e:
        print(f"Failed to get all users: {e}")
        return []

def search_users_by_email(user_id, email_term):
    """
    Searches for users by email, excluding the logged-in user.
    """
    sql = """
        SELECT U.userid, U.username, U.email,
               CASE WHEN F.follower IS NOT NULL THEN true ELSE false END as is_following
        FROM "users" U
        LEFT JOIN "follows" F ON U.userid = F.followee AND F.follower = %s
        WHERE U.userid != %s AND U.email ILIKE %s
        ORDER BY U.username
    """
    search_pattern = f"%{email_term}%"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (user_id, user_id, search_pattern))
                return curs.fetchall()
    except Exception as e:
        print(f"Failed to search users: {e}")
        return []

def follow_user(follower_id, followee_id):
    """
Additional-Instructions: 
    Adds a record to the "FOLLOWS" table.
    """
    # Prevent users from following themselves
    if follower_id == followee_id:
        return False
        
    sql = 'INSERT INTO "follows" (follower, followee) VALUES (%s, %s) ON CONFLICT DO NOTHING'
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (follower_id, followee_id))
                conn.commit()
                return True
    except Exception as e:
        print(f"Failed to follow user: {e}")
        return False

def unfollow_user(follower_id, followee_id):
    """
    Removes a record from the "FOLLOWS" table.
    """
    sql = 'DELETE FROM "followers" WHERE follower = %s AND followee = %s'
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (follower_id, followee_id))
                conn.commit()
                return True
    except Exception as e:
        print(f"Failed to unfollow user: {e}")
        return False