# src/database_setup.py
'''
Author: Huy Le (hl9082)
Description:
This file is used to setup database.
'''
import psycopg
from sshtunnel import SSHTunnelForwarder
import os
from dotenv import load_dotenv, find_dotenv

# Find and load environment variables from .env file in the parent directory
load_dotenv(find_dotenv())

CS_USERNAME = os.getenv("CS_USERNAME")
CS_PASSWORD = os.getenv("CS_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

def get_db_connection():
    """Establishes an SSH tunnel and connects to the PostgreSQL database."""
    if not all([CS_USERNAME, CS_PASSWORD, DB_NAME]):
        print("FATAL ERROR: Missing database credentials. Please check your .env file in the project root.")
        return None, None
    try:
        server = SSHTunnelForwarder(
            ('starbug.cs.rit.edu', 22),
            ssh_username=CS_USERNAME,
            ssh_password=CS_PASSWORD,
            remote_bind_address=('127.0.0.1', 5432)
        )
        server.start()
        print("SSH tunnel established")
        params = {
            'dbname': DB_NAME, 'user': CS_USERNAME, 'password': CS_PASSWORD,
            'host': 'localhost', 'port': server.local_bind_port
        }
        conn = psycopg.connect(**params)
        print("Database connection established")
        return server, conn
    except Exception as e:
        print(f"Connection failed: {e}")
        return None, None

def setup_database():
    """Connects to the remote DB, drops old tables, creates new ones, and populates them."""
    server, conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as curs:
            print("Dropping existing tables...")
            tables_to_drop = [
                "HAS", "CONTAINS", "PERFORMS", "CONSISTS_OF", "PLAYS", "FOLLOWS", 
                "COLLECTION", "GENRES", "SONG", "ALBUM", "ARTIST", "\"USER\""
            ]
            for table in tables_to_drop:
                curs.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")

            print("Creating tables...")
            # Note: "USER" is a reserved keyword in SQL, so it must be quoted.
            curs.execute("""
            CREATE TABLE "USER" (
                UserID SERIAL PRIMARY KEY, Username TEXT NOT NULL UNIQUE, Password TEXT NOT NULL,
                FirstName TEXT, LastName TEXT, Email TEXT NOT NULL UNIQUE,
                CreationDate TIMESTAMPTZ NOT NULL, LastAccessDate TIMESTAMPTZ NOT NULL
            );""")
            curs.execute("CREATE TABLE ARTIST (ArtistID SERIAL PRIMARY KEY, Name TEXT NOT NULL);")
            curs.execute("CREATE TABLE ALBUM (AlbumID SERIAL PRIMARY KEY, Name TEXT NOT NULL, ReleaseDate DATE);")
            curs.execute("CREATE TABLE SONG (SongID SERIAL PRIMARY KEY, Title TEXT NOT NULL, Length INTEGER CHECK(Length > 0), ReleaseDate DATE);")
            curs.execute("CREATE TABLE GENRES (GenreID SERIAL PRIMARY KEY, GenreType TEXT NOT NULL UNIQUE);")
            curs.execute("""
            CREATE TABLE COLLECTION (
                UserID INTEGER NOT NULL, Title TEXT NOT NULL, NumberOfSongs INTEGER DEFAULT 0, Length INTEGER DEFAULT 0,
                PRIMARY KEY (UserID, Title), FOREIGN KEY (UserID) REFERENCES "USER" (UserID) ON DELETE CASCADE
            );""")
            curs.execute("""
            CREATE TABLE FOLLOWS (
                Follower INTEGER NOT NULL, Followee INTEGER NOT NULL, PRIMARY KEY (Follower, Followee),
                FOREIGN KEY (Follower) REFERENCES "USER" (UserID) ON DELETE CASCADE,
                FOREIGN KEY (Followee) REFERENCES "USER" (UserID) ON DELETE CASCADE,
                CHECK (Follower != Followee)
            );""")
            print("All tables created successfully.")
            
            print("Populating tables with sample data...")
            users = [('huyle', 'pass123', 'Huy', 'Le', 'huy@example.com', '2024-01-01 00:00:00', '2025-09-15 00:00:00'), ('jsmith', 'secret', 'John', 'Smith', 'john@example.com', '2024-02-10 00:00:00', '2025-09-14 00:00:00')]
            curs.executemany('INSERT INTO "USER"(Username, Password, FirstName, LastName, Email, CreationDate, LastAccessDate) VALUES (%s, %s, %s, %s, %s, %s, %s)', users)
            print("Sample data populated successfully.")
            conn.commit()

    except psycopg.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        if conn: conn.close(); print("Database connection closed")
        if server: server.stop(); print("SSH tunnel closed")

if __name__ == '__main__':
    setup_database()