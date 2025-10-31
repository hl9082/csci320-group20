#!/usr/bin/env python3
"""
generate_fake_artists.py

Generate fake artist/stage names and save to a CSV file.
Creates a mix of mononyms, full-name style, adjective+noun, band-like names, and stylized names.

Usage:
    python generate_fake_artists.py
    python generate_fake_artists.py --count 1000 --out my_artists.csv --seed 42
"""

import csv
import random
import argparse
from itertools import product

# --- Configurable pools of name parts ---
FIRSTS = [
    "Ari", "Nova", "Mika", "Luca", "Zane", "Kai", "Juno", "Remy", "Sage", "Eden",
    "Rory", "Nia", "Rex", "Tess", "Mara", "Finn", "Noa", "Skye", "Beau", "Lina",
    "Zuri", "Oli", "Theo", "Cleo", "Lola", "Vera", "Ivo", "Kira", "Maya", "Jai",
    "Lia", "Rin", "Zed", "Hugo", "Esme", "Nova", "Pax", "Rhea", "Silas", "Orin"
]

LASTS = [
    "Hollow", "Marley", "Winslow", "Carter", "Vance", "Monroe", "Hayes", "Frost",
    "Willow", "Cross", "Bell", "Sable", "Quinn", "Lane", "Bennett", "Hart", "Gray",
    "Voss", "Stone", "Day", "Rowe", "Blake", "Ash", "Noel", "Reid", "Fox", "Dunne"
]

ADJECTIVES = [
    "Silver", "Neon", "Crimson", "Velvet", "Golden", "Hidden", "Lonely", "Frozen",
    "Burning", "Blue", "Electric", "Silent", "Wandering", "Wild", "Gentle", "Broken",
    "Luminous", "Midnight", "Paper", "Royal", "Tender", "Rapid", "Sour", "Urban"
]

NOUNS = [
    "Skies", "Hearts", "Echoes", "Machines", "Roses", "Ghosts", "Harbor", "Empire",
    "Waves", "Thorns", "Tide", "Diamonds", "Road", "Garden", "Noise", "Signal",
    "Mirrors", "Lanterns", "Crows", "Fires", "Sundays", "Atlas", "Comet", "Voyage"
]

COLORS = [
    "Crimson", "Indigo", "Amber", "Emerald", "Saffron", "Onyx", "Ivory", "Azure",
    "Coral", "Teal"
]

ANIMALS = [
    "Fox", "Crow", "Wolf", "Raven", "Tiger", "Panther", "Deer", "Sparrow", "Otter",
    "Hawk"
]

VERBS = [
    "Chasing", "Dancing", "Hiding", "Falling", "Rising", "Wandering", "Floating",
    "Breaking", "Holding", "Calling"
]

CONNECTORS = ["&", "and", "x", "with", "feat.", "featuring"]

STYLES = ["™", "°", "☆", "x", "!" ]

BAND_SUFFIXES = ["Collective", "Trio", "Quartet", "Orchestra", "Ensemble", "Syndicate", "Project"]

# Some templates to generate names
TEMPLATES = [
    ("mononym", lambda: random.choice(FIRSTS)),
    ("full_name", lambda: f"{random.choice(FIRSTS)} {random.choice(LASTS)}"),
    ("first_last_joined", lambda: random.choice(FIRSTS) + random.choice(LASTS)),
    ("adj_noun", lambda: f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)}"),
    ("color_animal", lambda: f"{random.choice(COLORS)} {random.choice(ANIMALS)}"),
    ("verb_the_noun", lambda: f"{random.choice(VERBS)} the {random.choice(NOUNS)}"),
    ("the_noun", lambda: f"The {random.choice(NOUNS)}"),
    ("noun_project", lambda: f"{random.choice(NOUNS)} {random.choice(BAND_SUFFIXES)}"),
    ("first_x_first", lambda: f"{random.choice(FIRSTS)} {random.choice(CONNECTORS)} {random.choice(FIRSTS)}"),
    ("stylized", lambda: stylized_name()),
]

# Helper stylized name generator
def stylized_name():
    # picks a short base and randomly appends a style char or number
    base_choices = [
        f"{random.choice(FIRSTS)}", f"{random.choice(ADJECTIVES)}{random.choice(NOUNS)}",
        f"{random.choice(COLORS)}{random.choice(ANIMALS)}", f"{random.choice(NOUNS)}"
    ]
    base = random.choice(base_choices)
    # maybe add a digit or symbol
    r = random.random()
    if r < 0.25:
        return base + random.choice(STYLES)
    elif r < 0.5:
        return base + str(random.randint(2,99))
    elif r < 0.75:
        return base + "-" + random.choice(LASTS)
    else:
        return base

def generate_one():
    # Weighted selection of templates so output is varied but plausible
    weights = [8, 8, 4, 7, 4, 3, 6, 2, 3, 3]
    template = random.choices(TEMPLATES, weights=weights, k=1)[0][1]
    name = template().strip()
    # clean some double spaces
    name = " ".join(name.split())
    return name

def generate_unique_names(count=5000, seed=None):
    if seed is not None:
        random.seed(seed)

    names = set()
    attempts = 0
    max_attempts = count * 50  # safety: avoid infinite loop

    # To increase variety, pre-generate combos from parts where useful
    # Ensure uniqueness by sampling both generated and combinatorial permutations
    # Add some deterministic combos first
    for a, b in product(ADJECTIVES, NOUNS):
        if len(names) >= count:
            break
        names.add(f"{a} {b}")
    for c, a in product(COLORS, ANIMALS):
        if len(names) >= count:
            break
        names.add(f"{c} {a}")

    # Now random-generate until we reach desired count
    while len(names) < count and attempts < max_attempts:
        name = generate_one()
        # Filters: remove purely numeric or tiny junk
        if len(name) < 2:
            attempts += 1
            continue
        if any(x in name.lower() for x in ("category:", "list of", "http", "wiki")):
            attempts += 1
            continue
        # Normalize capitalization: keep intended casing but strip leading/trailing punctuation
        name = name.strip().strip(" -_.,;:")
        # Avoid names that are duplicates ignoring case
        if name.lower() in (n.lower() for n in names):
            attempts += 1
            continue
        names.add(name)
        attempts += 1

    if len(names) < count:
        # fallback deterministic generation to fill the rest
        i = 1
        while len(names) < count:
            names.add(f"Artist {i}")
            i += 1

    # return a stable list but shuffled
    result = list(names)
    random.shuffle(result)
    return result[:count]

def save_to_csv(names, out_file="fake_artists_5000.csv"):
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Artist Name"])
        for n in names:
            writer.writerow([n])

def main():
    parser = argparse.ArgumentParser(description="Generate fake artist names and save to CSV.")
    parser.add_argument("--count", type=int, default=5000, help="Number of artist names to generate (default 5000).")
    parser.add_argument("--out", type=str, default="fake_artists_5000.csv", help="Output CSV file name.")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed for reproducible output.")
    args = parser.parse_args()

    print(f"Generating {args.count} fake artist names...")
    names = generate_unique_names(count=args.count, seed=args.seed)
    print(f"Generated {len(names)} names. Saving to {args.out} ...")
    save_to_csv(names, args.out)
    print("Done!")

if __name__ == "__main__":
    main()
