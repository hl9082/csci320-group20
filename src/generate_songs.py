import csv
import random
from datetime import datetime, timedelta

# Number of rows to generate
NUM_SONGS = 7000

# Helper to generate random dates between 1980 and 2024
def random_date(start_year=1980, end_year=2024):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return (start + timedelta(days=random_days)).strftime("%Y-%m-%d")

# Some word lists for pseudo-random song titles
adjectives = ["Golden", "Lonely", "Midnight", "Fading", "Electric", "Broken", "Silent", "Endless", "Burning", "Hidden"]
nouns = ["Dream", "Sky", "Road", "Heart", "Light", "Shadow", "Fire", "Storm", "Ocean", "Echo"]

# Write CSV
with open("songs.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["songid", "title", "length", "releasedate"])

    for i in range(1, NUM_SONGS + 1):
        title = f"{random.choice(adjectives)} {random.choice(nouns)}"
        length = random.randint(120, 360)  # seconds
        release_date = random_date()
        writer.writerow([i, title, length, release_date])

print("✅ songs.csv generated with 7000 rows.")