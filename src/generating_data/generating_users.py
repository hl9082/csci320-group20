import csv
import secrets
import string

# Increase rows to 6000 (1000 original + ~5000 more)
NUM_ROWS = 6000
PASSWORD_LEN = 12  # keep desired password length

FIRST_NAMES = [
    "Liam","Noah","Oliver","Elijah","William","James","Benjamin","Lucas","Henry","Alexander",
    "Olivia","Emma","Ava","Charlotte","Sophia","Amelia","Isabella","Mia","Evelyn","Harper"
]
LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
    "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin"
]

digits = string.digits
symbols = "!@#$%^&*"
letters = string.ascii_letters

def rand_digits(n):
    return ''.join(secrets.choice(digits) for _ in range(n))

def rand_chars(n):
    pool = letters + digits + symbols
    return ''.join(secrets.choice(pool) for _ in range(n))

def make_username(first, last, existing_usernames):
    # base like firstname.lastname (lowercase)
    base = f"{first.lower()}.{last.lower()}"
    # try short numeric suffixes to avoid collisions
    for suffix_len in (2, 3, 4):
        suffix = rand_digits(suffix_len)
        candidate = f"{base}{suffix}"
        if candidate not in existing_usernames:
            return candidate
    # fallback: append a longer random string
    while True:
        candidate = f"{base}{rand_chars(6)}"
        if candidate not in existing_usernames:
            return candidate

def make_password(first, last, length=PASSWORD_LEN):
    # Build a password that is recognizably similar to the name but padded with random chars
    # Use first 3 letters of first name + last 3 of last name (or fewer if short)
    part1 = first[:3].lower()
    part2 = last[-3:].capitalize()
    core = part1 + part2  # e.g., "liaSmith"
    # make sure we include at least one digit and one symbol
    remaining_len = max(0, length - len(core) - 2)  # keep room for 1 digit + 1 symbol
    tail = rand_chars(remaining_len)
    digit = rand_digits(1)
    symbol = secrets.choice(symbols)
    # shuffle the tail elements a bit by concatenating in varied order
    password = core + digit + symbol + tail
    # if somehow too long/truncated, slice to exact length
    if len(password) > length:
        password = password[:length]
    return password

output_file = "users.csv"
existing_usernames = set()

with open(output_file, "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["username","password","firstname","lastname","email"])
    for i in range(NUM_ROWS):
        firstname = FIRST_NAMES[i % len(FIRST_NAMES)]
        lastname = LAST_NAMES[(i // len(FIRST_NAMES)) % len(LAST_NAMES)]
        username = make_username(firstname, lastname, existing_usernames)
        existing_usernames.add(username)
        password = make_password(firstname, lastname, PASSWORD_LEN)
        email = f"{username}@example.com"
        writer.writerow([username, password, firstname, lastname, email])

print(f"Generated {NUM_ROWS} rows and wrote to {output_file}")
