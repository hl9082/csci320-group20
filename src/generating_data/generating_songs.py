import csv
import time
import requests

# Example: MusicBrainz open API (no auth needed)
BASE_URL = "https://musicbrainz.org/ws/2/recording/"

songs = []
offset = 0
limit = 100  # MusicBrainz max per query
total_needed = 5000

while len(songs) < total_needed:
    params = {
        "query": "date:[2000 TO 2025]",  # limit by year range if you want
        "fmt": "json",
        "limit": limit,
        "offset": offset
    }
    r = requests.get(BASE_URL, params=params)
    data = r.json()
    for rec in data.get("recordings", []):
        title = rec.get("title")
        length_ms = rec.get("length")
        artist_credit = rec.get("artist-credit", [{}])[0].get("name", "Unknown Artist")
        release_date = rec.get("first-release-date", "Unknown")
        length_sec = round(length_ms / 1000, 2) if length_ms else "Unknown"
        songs.append({
            "title": title,
            "artist": artist_credit,
            "length_seconds": length_sec,
            "release_date": release_date
        })
        if len(songs) >= total_needed:
            break
    offset += limit
    time.sleep(1)  # be nice to API

with open("songs_5000.csv", "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["title", "artist", "length_seconds", "release_date"])
    writer.writeheader()
    writer.writerows(songs)

print(f"Wrote {len(songs)} songs to songs_5000.csv")
