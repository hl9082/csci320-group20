import csv
import random

# --- Define lists of musical terms ---

# Prefixes or descriptors
prefixes = [
    "Alternative", "Indie", "Progressive", "Psychedelic", "Experimental", "Dark",
    "Minimal", "Deep", "Afro", "Latin", "Future", "Synth", "Electro", "Neo", "Acid",
    "Hard", "Gothic", "Industrial", "Celtic", "Vapor", "Lo-Fi", "Chill", "Aggro",
    "Free", "Modern", "Post", "Nu", "Ethno", "Urban", "Glitch"
]

# Core musical genres
main_genres = [
    "Rock", "Pop", "Jazz", "Electronic", "Hip-Hop", "Classical", "Folk", "Reggae",
    "Blues", "Metal", "Country", "R&B", "Soul", "Funk", "Punk", "Techno", "House",
    "Trance", "Ambient", "Disco", "Gospel", "Ska", "Salsa", "Bossa Nova", "Dub",
    "Grime", "Garage", "Industrial", "Noise", "World"
]

# Suffixes or sub-styles
suffixes = [
    "Wave", "Core", "Fusion", "Step", "Trap", "Beat", "Roots", "Swing", "Bop", "Gaze",
    "Drone", "Bounce", "Revival", "Hop", "Clash", "Stomp", "Groove", "Phonk",
    "Folk", "Billy", "Break", "Gaze", "Rap", "Core"
]

# A set to store generated genres to ensure uniqueness
generated_genres = set()

# Define the output filename
filename = 'genres.csv'

print(f"Generating {filename} with 995 unique music genres (ID 6 to 1000)...")

# Open the CSV file for writing
with open(filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    
    # Write the header row
    writer.writerow(['GenreID', 'GenreType'])
    
    # Loop for GenreIDs from 6 to 1000 (inclusive)
    for genre_id in range(6, 1001):
        
        genre_type = ""
        # Keep generating until a unique genre is found
        while not genre_type or genre_type in generated_genres:
            
            # Randomly choose a structure (2-word or 3-word)
            structure = random.randint(1, 4)
            
            if structure == 1:
                # e.g., "Indie Pop"
                genre_type = f"{random.choice(prefixes)} {random.choice(main_genres)}"
            elif structure == 2:
                # e.g., "Jazz Fusion"
                genre_type = f"{random.choice(main_genres)} {random.choice(suffixes)}"
            elif structure == 3:
                # e.g., "Deep House Beat"
                genre_type = f"{random.choice(prefixes)} {random.choice(main_genres)} {random.choice(suffixes)}"
            else:
                # e.g., "Synth Wave"
                genre_type = f"{random.choice(prefixes)} {random.choice(suffixes)}"
        
        # Add the new unique genre to our set
        generated_genres.add(genre_type)
        
        # Write the new row [GenreID, GenreType]
        writer.writerow([genre_id, genre_type])

print(f"Successfully created {filename}.")