import csv
from faker import Faker

# Initialize Faker to generate random data
fake = Faker()

# A set to store generated names to ensure uniqueness
generated_names = set()

# Define the output filename
filename = 'artists.csv'

print(f"Generating {filename} with 995 unique artists (ID 6 to 1000)...")

# Open the CSV file for writing
with open(filename, 'w', newline='', encoding='utf-8') as f:
    # Create a CSV writer object
    writer = csv.writer(f)
    
    # Write the header row
    writer.writerow(['ArtistID', 'Name'])
    
    # Loop for ArtistIDs from 6 to 1000 (inclusive)
    for artist_id in range(6, 1001):
        
        # Generate a new name
        name = fake.name()
        
        # Ensure the name is unique
        while name in generated_names:
            name = fake.name()
            
        # Add the new unique name to our set
        generated_names.add(name)
        
        # Write the new row [ArtistID, Name] to the file
        writer.writerow([artist_id, name])

print(f"Successfully created {filename}.")