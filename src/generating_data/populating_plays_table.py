import os
import sys
import csv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.db_connector import get_db_connection, db_pool, initialize_db_pool

# Ensure access to src/

# Update the CSV file name and path
CSV_FILE = "user_song_data.csv"

def load_song_data():
    """Load user_song_data.csv and return as a list of tuples, skipping the first line."""
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # Skip the first line (header)
        return [(row[0], row[1], row[2]) for row in reader if row]  # Exclude empty rows


def main():
    # Ensure the database pool is initialized before proceeding
    if not db_pool:
        print("❌ Database pool is not initialized. Initializing now...")
        if not initialize_db_pool():
            print("❌ Failed to initialize the database pool. Exiting.")
            return  # Exit if the pool couldn't be initialized

    # Load the song data from CSV
    song_data = load_song_data()
    print(f"🔌 Connecting to the database through SSH tunnel...")

    try:
        # Open database connection and perform insertion
        with get_db_connection() as conn:
            print("Connected to the database.")
            with conn.cursor() as cur:
                for row in song_data:
                    # Insert data into plays table
                    print(f"Inserting row: {row}")  # Debug print
                    cur.execute(
                        "INSERT INTO plays (userid, songid, playdate) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                        (row[0], row[1], row[2])
                    )
            conn.commit()  # Commit the transaction
        print(f"✅ Successfully inserted {len(song_data)} rows into the plays table.")
    except Exception as e:
        print(f"❌ Error inserting data: {e}")

if __name__ == "__main__":
    main()
