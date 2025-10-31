import os
import sys
import csv

# Ensure access to src/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.db_connector import get_db_connection

CSV_FILE = "fake_artists_5000.csv"
START_ID = 1001

def load_artists():
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return [row[0] for row in csv.reader(f) if row]

def main():
    artists = load_artists()
    print("🔌 Connecting to the database through SSH tunnel...")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for i, name in enumerate(artists, START_ID):
                    # Match the actual table column names
                    cur.execute(
                        "INSERT INTO artist (artistid, name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (i, name)
                    )
            conn.commit()
        print(f"✅ Successfully inserted {len(artists)} artists starting at ID {START_ID}")
    except Exception as e:
        print(f"❌ Error inserting artists: {e}")

if __name__ == "__main__":
    main()
