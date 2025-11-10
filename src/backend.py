'''
Author: Huy Le (hl9082)
Co-authors: Jason Ting, Iris Li, Raymond Lee
Group: 20
Course: CSCI 320
Filename: backend.py
Description: 
This module contains all the functions that interact with the database.
It serves as the data access layer, separating SQL logic from the web application's routing logic.
'''
from datetime import datetime  # Used to generate timestamps for creation and last access dates.
from db_connector import get_db_connection  # Imports the connection manager from our connector file.
#from src.db_connector import get_db_connection                 #Used for populating_user_table
import psycopg2  # Imported specifically to catch psycopg2-related exceptions.
from psycopg2.extras import DictCursor # Ensures we can access results by column name
import bcrypt 

# --- User Management ---

def create_user(username, password, first_name, last_name, email):
    """
    Creates a new user with a PLAINTEXT password.
    Records creation and last access time.
    Schema-Compliant: Uses "users" table.
    """
    now = datetime.now()

    sql = """
        INSERT INTO "users" (Username, Password, FirstName, LastName, Email, CreationDate, LastAccessDate)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING UserID
    """

    try:
        # Use the context manager to get a connection
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (username, password, first_name, last_name, email, now, now))
                user_id = curs.fetchone()['userid']
                #curs.execute("TRUNCATE TABLE users RESTART IDENTITY CASCADE")
                print(user_id)
                conn.commit()
                return user_id
    except psycopg2.errors.UniqueViolation:
        # This error occurs if the username or email already exists
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        # Rollback and close are handled by the context manager
        return None

def login_user(username, password):
    """
    Logs a user in by checking their PLAINTEXT password.
    Updates the LastAccessDate on successful login.
    Schema-Compliant: Uses "users" table.
    """
    sql_select = 'SELECT UserID, Username, Password FROM "users" WHERE Username = %s'
    sql_update_access = 'UPDATE "users" SET LastAccessDate = %s WHERE UserID = %s'
    
    now = datetime.now()
    try:
        # Use the context manager to get a connection
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql_select, (username,))
                user_record = curs.fetchone()

                if not user_record:
                    return None  # User not found

                stored_password = user_record['password']
                
                # Direct plaintext comparison
                if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                    # Update last access time
                    curs.execute(sql_update_access, (now, user_record['userid']))
                    conn.commit()
                    return {'userid': user_record['userid'], 'username': user_record['username']}
                else:
                    return None  # Incorrect password
                    
    except Exception as e:
        print(f"Login failed due to a database error: {e}")
        # Rollback and close are handled by the context manager
        return None

# --- Collection Management ---

def get_user_collections(user_id):
    """
    Gets all collections for a specific user.
    Schema-Compliant: Uses "collection" table.
    """
    sql = 'SELECT Title, NumberOfSongs, Length FROM "collection" WHERE UserID = %s ORDER BY Title ASC'
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (user_id,))
                return curs.fetchall()
    except Exception as e:
        print(f"Failed to get collections: {e}")
        return [] # Return empty list on error
    
def get_collection_details(user_id, collection_title):
    """
    Gets a specific collection's info AND all songs within it.
    Schema-Compliant: Identifies collection by (UserID, Title) and uses all bridge tables.
    """
    collection_info = {
        'title': collection_title,
        'songs': []
    }
   
    sql_songs = """
        SELECT 
            S.SongID, 
            S.Title AS SongTitle, 
            S.Length, 
            S.ReleaseDate,
            COALESCE(STRING_AGG(DISTINCT A.Name, ',' ORDER BY A.Name), '') AS artist_list,
            COALESCE(STRING_AGG(DISTINCT AL.Name, ',' ORDER BY AL.Name), '') AS album_list,
            COALESCE(STRING_AGG(DISTINCT G.GenreType, ',' ORDER BY G.GenreType), '') AS genre_list,
            MAX(R.Rating) AS Rating
        FROM "consists_of" AS CO
        JOIN "song" S ON S.SongID = CO.SongID
        LEFT JOIN "performs" P ON S.SongID = P.SongID
        LEFT JOIN "artist" A ON P.ArtistID = A.ArtistID
        LEFT JOIN "contains" C ON S.SongID = C.SongID
        LEFT JOIN "album" AL ON C.AlbumID = AL.AlbumID
        LEFT JOIN "has" H ON S.SongID = H.SongID
        LEFT JOIN "genres" G ON H.GenreID = G.GenreID
        LEFT JOIN "rates" R ON S.SongID = R.SongID AND R.UserID = %s
        WHERE CO.UserID = %s AND CO.Title = %s
        GROUP BY S.SongID, S.Title, S.Length, S.ReleaseDate
        ORDER BY S.Title
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql_songs, (user_id, user_id, collection_title))
                songs = curs.fetchall()
                
                if not songs:
                    # Check if the collection *exists* but is just empty
                    curs.execute('SELECT 1 FROM "collection" WHERE UserID = %s AND Title = %s', (user_id, collection_title))
                    if curs.fetchone() is None:
                        return None # Collection doesn't exist at all
                
                collection_info['songs'] = songs
                return collection_info
    except Exception as e:
        print(f"Failed to get collection details: {e}")
        return None


def create_collection(user_id, title):
    """
    Creates a new, empty collection.
    Schema-Compliant: Uses (UserID, Title) as primary key.
    """
    sql = 'INSERT INTO "collection" (UserID, Title, NumberOfSongs, Length) VALUES (%s, %s, 0, 0)'
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (user_id, title))
                conn.commit()
                return True
    except psycopg2.errors.UniqueViolation:
        # Collection with this (UserID, Title) already exists
        return False
    except Exception as e:
        print(f"Failed to create collection: {e}")
        return False

def rename_collection(user_id, old_title, new_title):
    """
    Renames a user's collection.
    Schema-Compliant: Updates "collection" table based on (UserID, OldTitle).
    """
    sql = 'UPDATE "collection" SET Title = %s WHERE UserID = %s AND Title = %s'
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (new_title, user_id, old_title))
                conn.commit()
                return curs.rowcount > 0 # Returns True if a row was updated
    except psycopg2.errors.UniqueViolation:
        # A collection with the new name (UserID, NewTitle) already exists
        return False
    except Exception as e:
        print(f"Failed to rename collection: {e}")
        return False

def delete_collection(user_id, title):
    """
    Deletes a user's collection.
    Schema-Compliant: Deletes from "collection" using (UserID, Title).
    """
    sql = 'DELETE FROM "collection" WHERE UserID = %s AND Title = %s'
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (user_id, title))
                conn.commit()
                return True
    except Exception as e:
        print(f"Failed to delete collection: {e}")
        return False

# --- Song and Search Management ---

def _update_collection_stats(curs, user_id, collection_title):
    """
    Private helper function to update a collection's song count and total length.
    This should be called *within* a transaction, passing the cursor.
    """
    sql_update_stats = """
        WITH Stats AS (
            SELECT
                COUNT(S.SongID) AS SongCount,
                COALESCE(SUM(S.Length), 0) AS TotalLength
            FROM "consists_of" CO
            JOIN "song" S ON CO.SongID = S.SongID
            WHERE CO.UserID = %s AND CO.Title = %s
        )
        UPDATE "collection" C
        SET
            NumberOfSongs = S.SongCount,
            Length = S.TotalLength
        FROM Stats S
        WHERE C.UserID = %s AND C.Title = %s;
    """
    curs.execute(sql_update_stats, (user_id, collection_title, user_id, collection_title))


def add_song_to_collection(user_id, collection_title, song_id):
    """
    Adds a single song to a collection.
    Schema-Compliant: Inserts into "consists_of" and updates "collection" stats.
    """
    sql_insert = 'INSERT INTO "consists_of" (UserID, Title, SongID) VALUES (%s, %s, %s)'
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                # Insert the song into the bridge table
                curs.execute(sql_insert, (user_id, collection_title, song_id))
                
                # Update the collection stats in the same transaction
                _update_collection_stats(curs, user_id, collection_title)
                
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
        return False

def add_album_to_collection(user_id, collection_title, album_id):
    """
    Adds all songs from a given album to a collection.
    Ignores songs that are already in the collection.
    Returns the number of *new* songs added.
    """
    sql_insert_album = """
        INSERT INTO "consists_of" (UserID, Title, SongID)
        SELECT %s, %s, C.SongID
        FROM "contains" C
        WHERE C.AlbumID = %s
        AND NOT EXISTS (
            SELECT 1
            FROM "consists_of" CO
            WHERE CO.UserID = %s
            AND CO.Title = %s
            AND CO.SongID = C.SongID
        )
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql_insert_album, (user_id, collection_title, album_id, user_id, collection_title))
                added_count = curs.rowcount # Get how many songs were inserted
                
                # Update the collection stats in the same transaction
                _update_collection_stats(curs, user_id, collection_title)
                
                conn.commit()
                return added_count
    except Exception as e:
        print(f"Failed to add album to collection: {e}")
        return 0


def remove_song_from_collection(user_id, collection_title, song_id):
    """
    Removes a single song from a collection.
    Schema-Compliant: Deletes from "consists_of" and updates "collection" stats.
    """
    sql_delete = 'DELETE FROM "consists_of" WHERE UserID = %s AND Title = %s AND SongID = %s'
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                # Delete the song from the bridge table
                curs.execute(sql_delete, (user_id, collection_title, song_id))
                deleted_count = curs.rowcount
                
                if deleted_count > 0:
                    # Update stats only if a song was actually deleted
                    _update_collection_stats(curs, user_id, collection_title)
                
                conn.commit()
                return deleted_count > 0
    except Exception as e:
        print(f"Failed to remove song from collection: {e}")
        return False

def search_songs(user_id, search_term, search_type, sort_by, sort_order):
    """
    Searches for songs based on various criteria and sorting options.
    Schema-Compliant: Uses LEFT JOINs and dynamically
    calculates listencount from "plays".
    """
    # Whitelist sort options to prevent SQL injection
    sort_columns_map = {
        'song_name': 'S.Title',
        'artist_name': 'artist_list',
        'album_name' : 'album_list',
        'genre_name': 'G.GenreType',
        'ReleaseDate': 'S.ReleaseDate'
    }
    sort_order_map = {'ASC': 'ASC', 'DESC': 'DESC'}

    # Default to safe values if inputs are invalid
    sort_column = sort_columns_map.get(sort_by, 'S.Title')
    sort_direction = sort_order_map.get(sort_order, 'ASC')
    
    base_query = f"""
        SELECT 
            S.SongID, 
            S.Title AS song_name, 
            COALESCE(STRING_AGG(DISTINCT A.Name, ',' ORDER BY A.Name), '') AS artist_list,
            COALESCE(STRING_AGG(DISTINCT AL.Name, ',' ORDER BY AL.Name), '') AS album_list,
            COALESCE(STRING_AGG(DISTINCT G.GenreType, ',' ORDER BY G.GenreType), '') AS genre_list, 
            (SELECT COUNT(*) FROM "plays" P WHERE P.SongID = S.SongID AND P.UserID = %s) AS listencount, 
            S.Length, 
            S.ReleaseDate
        FROM song S
        LEFT JOIN performs P ON S.SongID = P.SongID
        LEFT JOIN artist A ON P.ArtistID = A.ArtistID
        LEFT JOIN contains C ON S.SongID = C.SongID
        LEFT JOIN album AL ON C.AlbumID = AL.AlbumID
        LEFT JOIN has H ON S.SongID = H.SongID
        LEFT JOIN genres G ON H.GenreID = G.GenreID
    """

    params = [user_id]
    where_clause = ""

    if search_term and search_type:
        search_pattern = f"%{search_term}%"
        if search_type == 'song':
            where_clause = "WHERE S.Title ILIKE %s"
            params.append(search_pattern,)
        elif search_type == 'artist':
            where_clause = """
                WHERE EXISTS(
                    SELECT 1
                    FROM performs P2
                    JOIN artist A2 ON P2.ArtistID = A2.ArtistID
                    WHERE P2.SongID = S.SongID AND A2.Name ILIKE %s)
            """
            params.append(search_pattern,)
        elif search_type == 'album':
            where_clause = """
                WHERE EXISTS(
                    SELECT 1
                    FROM contains C2
                    JOIN album AL2 ON C2.AlbumID = AL2.AlbumID
                    WHERE C2.SongID = S.SongID AND AL2.Name ILIKE %s
                )
            """
            params.append(search_pattern,)
        elif search_type == 'genre':
            where_clause = """
                WHERE EXISTS(
                    SELECT 1
                    FROM has H2
                    JOIN genres G2 ON H2.GenreID = G2.GenreID
                    WHERE H2.SongID = S.SongID AND G2.GenreType ILIKE %s)
            """
            params.append(search_pattern,)


    group_by_clause = """
        GROUP BY 
            S.SongID,
            S.Title,
            S.Length,
            S.ReleaseDate
    """

    if not search_term and not search_type:
        order_by_clause = """
            ORDER BY 
                S.Title ASC,
                COALESCE(STRING_AGG(DISTINCT A.Name, ',' ORDER BY A.Name), '') ASC
        """
    else:
        order_by_clause = f"ORDER BY {sort_column} {sort_direction}"
        if sort_by == 'song_name':
            order_by_clause += ', artist_list ASC'
        elif sort_by == 'artist_name':
            order_by_clause += ', S.Title ASC'
        elif sort_by == 'genre_name':
            order_by_clause = f"ORDER BY SPLIT_PART(COALESCE(STRING_AGG(DISTINCT G.GenreType, ',' ORDER BY G.GenreType), ''), ',', 1) {sort_direction}"
        elif sort_by == 'song.releasedate':
            order_by_clause = f"ORDER BY releasedate {sort_direction}"

    sql = f"{base_query} {where_clause} {group_by_clause} {order_by_clause}"

    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, params)
                return curs.fetchall()
    except Exception as e:
        print(f"Failed to search songs: {e}")
        return []

# --- "Play" and "Follow" Functions ---

def play_song(song_id, user_id):
    """
    Logs that a user played a song.
    Schema-Compliant: Inserts a record into "plays".
    """
    sql_log = 'INSERT INTO "plays" (UserID, SongID, PlayDate) VALUES (%s, %s, %s)'
    now = datetime.now()
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql_log, (user_id, song_id, now))
                conn.commit()
                return True
    except Exception as e:
        print(f"Failed to play song: {e}")
        return False

def play_collection(user_id, collection_title):
    """
    Logs a play event for *every* song in a collection.
    Schema-Compliant: Inserts multiple rows into "plays".
    """
    sql_log_all = """
        INSERT INTO "plays" (UserID, SongID, PlayDate)
        SELECT %s, SongID, %s
        FROM "consists_of"
        WHERE UserID = %s AND Title = %s
    """
    now = datetime.now()
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql_log_all, (user_id, now, user_id, collection_title))
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

    sql = """
        INSERT INTO "rates" (UserID, SongID, Rating)
        VALUES (%s, %s, %s)
        ON CONFLICT (UserID, SongID)
        DO UPDATE SET Rating = EXCLUDED.Rating
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
        SELECT U.UserID, U.Username, U.Email,
        CASE WHEN F.Follower IS NOT NULL THEN true ELSE false END as is_following
        FROM "users" U
        LEFT JOIN "follows" F ON U.UserID = F.Followee AND F.Follower = %s
        WHERE U.UserID != %s
        ORDER BY U.Username
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
        SELECT U.UserID, U.Username, U.Email,
        CASE WHEN F.Follower IS NOT NULL THEN true ELSE false END as is_following
        FROM "users" U
        LEFT JOIN "follows" F ON U.UserID = F.Followee AND F.Follower = %s
        WHERE U.UserID != %s AND U.Email ILIKE %s
        ORDER BY U.Username
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
    Adds a record to the "follows" table.
    """
    # Prevent users from following themselves
    if follower_id == followee_id:
        return False
        
    sql = 'INSERT INTO "follows" (Follower, Followee) VALUES (%s, %s) ON CONFLICT DO NOTHING'
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
    Removes a record from the "follows" table.
    """
    sql = 'DELETE FROM "follows" WHERE Follower = %s AND Followee = %s'
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (follower_id, followee_id))
                conn.commit()
                return True
    except Exception as e:
        print(f"Failed to unfollow user: {e}")
        return False

def get_top_50_popular_songs():
    """
    Finds the top 50 most popular songs in the last 30 days.
    """
    sql = """
        SELECT
            S.SongID,
            S.Title AS song_name,
            COALESCE(STRING_AGG(DISTINCT A.Name, ',' ORDER BY A.Name), '') AS artist_list,
            COUNT(P.SongID) AS play_count
        FROM "plays" P
        JOIN "song" S ON P.SongID = S.SongID
        LEFT JOIN "performs" PRF ON S.SongID = PRF.SongID
        LEFT JOIN "artist" A ON PRF.ArtistID = A.ArtistID
        WHERE P.PlayDate >= NOW() - INTERVAL '30 days'
        GROUP BY S.SongID, S.Title
        ORDER BY play_count DESC
        LIMIT 50;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql)
                return curs.fetchall()
    except Exception as e:
        print(f"Error getting top 50 popular songs: {e}")
        return []

def get_top_50_popular_songs_from_followed_users(user_id):
    """
    Finds the top 50 most popular songs among users followed by the current user.
    """
    sql = """
        SELECT
            S.SongID,
            S.Title AS song_name,
            COALESCE(STRING_AGG(DISTINCT A.Name, ',' ORDER BY A.Name), '') AS artist_list,
            COUNT(P.SongID) AS play_count
        FROM "plays" P
        JOIN "song" S ON P.SongID = S.SongID
        LEFT JOIN "performs" PRF ON S.SongID = PRF.SongID
        LEFT JOIN "artist" A ON PRF.ArtistID = A.ArtistID
        WHERE P.UserID IN (SELECT Followee FROM "follows" WHERE Follower = %s)
        GROUP BY S.SongID, S.Title
        ORDER BY play_count DESC
        LIMIT 50;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (user_id,))
                return curs.fetchall()
    except Exception as e:
        print(f"Error getting top 50 popular songs from followed users: {e}")
        return []

def get_top_5_genres_of_the_month():
    """
    Finds the top 5 most popular genres of the month.
    """
    sql = """
        SELECT
            G.GenreType,
            COUNT(*) as play_count
        FROM "plays" P
        JOIN "has" H ON P.SongID = H.SongID
        JOIN "genres" G ON H.GenreID = G.GenreID
        WHERE P.PlayDate >= DATE_TRUNC('month', NOW())
        GROUP BY G.GenreType
        ORDER BY play_count DESC
        LIMIT 5;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql)
                return curs.fetchall()
    except Exception as e:
        print(f"Error getting top 5 genres of the month: {e}")
        return []

def get_user_profile_data(user_id):
    """
    Gathers all data for the user profile page.
    """
    profile_data = {}
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                # Get collection count
                curs.execute('SELECT COUNT(*) AS count FROM "collection" WHERE UserID = %s', (user_id,))
                profile_data['collection_count'] = curs.fetchone()['count']

                # Get followers count
                curs.execute('SELECT COUNT(*) AS count FROM "follows" WHERE Followee = %s', (user_id,))
                profile_data['followers_count'] = curs.fetchone()['count']

                # Get following count
                curs.execute('SELECT COUNT(*) AS count FROM "follows" WHERE Follower = %s', (user_id,))
                profile_data['following_count'] = curs.fetchone()['count']

                # Get top 10 artists by play count
                sql_top_artists = """
                    SELECT A.Name, COUNT(*) as play_count
                    FROM plays P
                    JOIN song S ON P.SongID = S.SongID
                    JOIN performs PRF ON S.SongID = PRF.SongID
                    JOIN artist A ON PRF.ArtistID = A.ArtistID
                    WHERE P.UserID = %s
                    GROUP BY A.Name
                    ORDER BY play_count DESC
                    LIMIT 10;
                """
                curs.execute(sql_top_artists, (user_id,))
                profile_data['top_artists'] = curs.fetchall()
        return profile_data
    except Exception as e:
        print(f"Error getting user profile data: {e}")
        return None