"""Add four sample animal records when the animals table is empty."""

from pawmatch_animals import seed_demo_animals

inserted = seed_demo_animals()
print(f"Added {inserted} demonstration records." if inserted else "The animals table is not empty, so no demo records were added.")
