"""
Downloads and seeds the large cosmetic-ingredient recognition gazetteer
(~28k real INCI names, sourced from the EU CosIng database via the
open-licensed beauteeru/cosmetic-ingredients-dataset on GitHub, MIT license).

This is separate from seed_ingredients.py (our curated risk database) --
this one is purely for "is this a real ingredient name?" recognition,
used to make OCR matching far more robust.

Run with:  python -m app.db.seed_gazetteer
"""
import requests
import csv
import io

from app.db.database import SessionLocal, Base, engine
from app.models.models import KnownIngredientName

Base.metadata.create_all(bind=engine)

CSV_URL = "https://raw.githubusercontent.com/beauteeru/cosmetic-ingredients-dataset/main/ingredients.csv"


def seed():
    print("Downloading ingredient gazetteer (this may take a moment)...")
    response = requests.get(CSV_URL, timeout=30)
    response.raise_for_status()

    reader = csv.DictReader(io.StringIO(response.text))
    names = set()
    for row in reader:
        name = row.get("name", "").strip()
        if name and len(name) >= 3:
            names.add(name.title())  # normalize capitalization

    print(f"Parsed {len(names)} unique ingredient names. Inserting into database...")

    db = SessionLocal()
    existing = {r.name for r in db.query(KnownIngredientName.name).all()}
    to_add = names - existing

    batch = [KnownIngredientName(name=n) for n in to_add]
    db.bulk_save_objects(batch)
    db.commit()

    total = db.query(KnownIngredientName).count()
    db.close()
    print(f"Added {len(to_add)} new names. Total in gazetteer: {total}")


if __name__ == "__main__":
    seed()