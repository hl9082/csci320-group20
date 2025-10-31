from datetime import datetime  # Used to generate timestamps for creation and last access dates.
from db_connector import get_db_connection  # Imports the connection manager from our connector file.
import psycopg2  # Imported specifically to catch psycopg2-related exceptions.
from psycopg2.extras import DictCursor # Ensures we can access results by column name

def create_song(songID, title, length, releasedate):
    """
    Creates a new song entry in the database.
    Schema-Compliant: Uses "songs" table.
    """
    now = datetime.now()

    sql = """
        INSERT INTO "songs" (songID, Title, Length, ReleaseDate)
        VALUES (%s, %s, %s, %s)
        RETURNING SongID
    """

    try:
        # Use the context manager to get a connection
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (songID, title, length, releasedate))
                song_id = curs.fetchone()['songid']
                conn.commit()
                return song_id
    except psycopg2.errors.UniqueViolation:
        # This error occurs if the song title already exists
        return None
    except Exception as e:
        print(f"Error creating song: {e}")
        # Rollback and close are handled by the context manager
        return None

    now = datetime.now()

    sql = """
        INSERT INTO "songs" (SongID, Title, Length, ReleaseDate)
        VALUES (%s, %s, %s, %s)
        RETURNING songID
    """

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as curs:
                curs.execute(sql, (songID, title, length, releasedate))
                song_id = curs.fetchone()['songid']
                conn.commit()
                return song_id
    except psycopg2.errors.UniqueViolation:
        # This error occurs if the song title already exists
        return None
    except Exception as e:
        print(f"Error creating song: {e}")
        # Rollback and close are handled by the context manager
        return None
    