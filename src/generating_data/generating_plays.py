import random
import csv
from datetime import datetime, timedelta

# Parameters
num_users = 7007
num_songs = 1000
plays_per_user = 100

# Create song IDs and user IDs
songs = [f"{i+1}" for i in range(num_songs)]
users = [f"{i+1}" for i in range(num_users)]

# Define a start date for play history (e.g., Jan 1, 2025)
start_date = datetime(2025, 1, 1)

# Open CSV file for writing
with open("user_song_data.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["userid", "songid", "playdate"])  # header

    for user in users:
        for _ in range(plays_per_user):
            song = random.choice(songs)

            # Generate a random play date within 2025
            random_days = random.randint(0, 364)
            random_seconds = random.randint(0, 86399)
            playdate = start_date + timedelta(days=random_days, seconds=random_seconds)

            # Write to CSV
            writer.writerow([user, song, playdate.strftime("%Y-%m-%d %H:%M:%S")])

print("✅ Simulation complete! Data saved to 'user_song_data.csv'")
