import csv
import random
import datetime
from faker import Faker

# Initialize Faker to generate random data
fake = Faker()

# Define the output filename
filename = 'users.csv'

# Sets to store generated values to ensure uniqueness
generated_usernames = set()
generated_emails = set()

# [cite_start]Define date ranges based on your sample data [cite: 281]
# Let's assume accounts were created from the start of 2024 until today
start_date_creation = datetime.date(2024, 1, 1)
# Use the "current date" from your report's context
today = datetime.date(2025, 10, 27) 

print(f"Generating {filename} with 995 unique users (ID 6 to 1000)...")

# Open the CSV file for writing
with open(filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    
    # [cite_start]Write the header row based on your schema [cite: 210-211]
    writer.writerow([
        'UserID', 'Username', 'Password', 'FirstName', 'LastName', 
        'Email', 'CreationDate', 'LastAccessDate'
    ])
    
    # Loop for UserIDs from 6 to 1000 (inclusive)
    for user_id in range(6, 1001):
        
        # Generate names
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        # --- Generate Unique Username ---
        username = fake.user_name()
        # Keep trying until a unique username is found
        while username in generated_usernames:
            username = f"{first_name.lower()}_{last_name.lower()}{random.randint(0, 999)}"
        generated_usernames.add(username)
        
        # --- Generate Unique Email ---
        email = fake.email()
        # Keep trying until a unique email is found
        while email in generated_emails:
            email = f"{username}{random.randint(0, 99)}@example.com"
        generated_emails.add(email)
        
        # Generate a random password
        password = fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
        
        # --- Generate Dates ---
        # CreationDate is between 2024-01-01 and today
        creation_date = fake.date_between(start_date=start_date_creation, end_date=today)
        
        # LastAccessDate must be on or after the CreationDate
        last_access_date = fake.date_between(start_date=creation_date, end_date=today)
        
        # Write the new user row
        writer.writerow([
            user_id, username, password, first_name, last_name,
            email, creation_date, last_access_date
        ])

print(f"Successfully created {filename}.")