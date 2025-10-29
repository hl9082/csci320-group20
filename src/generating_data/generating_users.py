import csv
import secrets
import string

"THIS CODE WAS TAKEN DIRECTLY FROM CHATGPT AND IS NOT MINE"
"IT IS JUST BEING USED TO GET SOME RANDOM DATA"

NUM_ROWS = 1000
USERNAME_LEN = 8
PASSWORD_LEN = 12

FIRST_NAMES = [
    "Liam","Noah","Oliver","Elijah","William","James","Benjamin","Lucas","Henry","Alexander",
    "Olivia","Emma","Ava","Charlotte","Sophia","Amelia","Isabella","Mia","Evelyn","Harper"
]
LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
    "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin"
]

alphabet = string.ascii_letters + string.digits

def rand_string(n):
    return ''.join(secrets.choice(alphabet) for _ in range(n))

output_file = "users.csv"
with open(output_file, "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["username","password","firstname","lastname","email"])
    for i in range(NUM_ROWS):
        username = rand_string(USERNAME_LEN)
        password = rand_string(PASSWORD_LEN)
        firstname = FIRST_NAMES[i % len(FIRST_NAMES)]
        lastname = LAST_NAMES[(i // len(FIRST_NAMES)) % len(LAST_NAMES)]
        email = f"{username}@example.com"
        writer.writerow([username, password, firstname, lastname, email])

print(f"Generated {NUM_ROWS} rows and wrote to {output_file}")
