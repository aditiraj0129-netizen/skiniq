"""
Seeds a starter product catalog for the recommendation engine.

HONESTY NOTE for your README: suitability tags here are based on how these
products are commonly marketed/formulated (publicly known attributes), not
lab-verified data. A production version would need this validated -- worth
saying upfront in your writeup, same principle as the ingredient database.

Run with:  python -m app.db.seed_products
"""
from app.db.database import SessionLocal, Base, engine
from app.models.models import Product

Base.metadata.create_all(bind=engine)

STARTER_PRODUCTS = [
    # name, brand, category, fragrance_free, oil_free, skin_types, concerns, key_ingredients, price_range
    ("Ultra Facial Cream", "Kiehl's", "moisturizer", True, False, ["dry", "normal"], ["hydration"], "Squalane, Glycerin", "$$"),
    ("Toleriane Double Repair Moisturizer", "La Roche-Posay", "moisturizer", True, True, ["oily", "normal", "dry"], ["barrier repair"], "Ceramides, Niacinamide", "$$"),
    ("Oil-Free Moisturizer", "Neutrogena", "moisturizer", True, True, ["oily", "normal"], ["acne"], "Glycerin", "$"),
    ("Hyaluronic Acid 2% + B5", "The Ordinary", "serum", True, True, ["oily", "dry", "normal"], ["hydration"], "Hyaluronic Acid", "$"),
    ("Niacinamide 10% + Zinc 1%", "The Ordinary", "serum", True, True, ["oily", "combination"], ["acne"], "Niacinamide", "$"),
    ("Effaclar Duo Acne Treatment", "La Roche-Posay", "treatment", True, True, ["oily"], ["acne"], "Niacinamide, Salicylic Acid", "$$"),
    ("Clear Improvement Charcoal Cleanser", "Origins", "cleanser", False, True, ["oily"], ["acne"], "Charcoal, Salicylic Acid", "$$"),
    ("Gentle Skin Cleanser", "Cetaphil", "cleanser", True, False, ["dry", "normal", "oily"], ["sensitivity"], "Glycerin", "$"),
    ("Foaming Facial Cleanser", "CeraVe", "cleanser", True, True, ["oily", "normal"], ["acne"], "Ceramides, Niacinamide", "$"),
    ("Hydrating Facial Cleanser", "CeraVe", "cleanser", True, False, ["dry", "normal"], ["hydration"], "Ceramides, Hyaluronic Acid", "$"),
    ("Ultra Light Daily UV Defense Sunscreen SPF50", "Neutrogena", "sunscreen", False, True, ["oily", "normal"], ["sun protection"], "Zinc Oxide", "$"),
    ("Anthelios Melt-in Milk Sunscreen SPF60", "La Roche-Posay", "sunscreen", True, False, ["dry", "normal"], ["sun protection"], "Zinc Oxide, Titanium Dioxide", "$$"),
    ("Watery Essence Sunscreen SPF50", "Biore UV", "sunscreen", True, True, ["oily", "combination"], ["sun protection"], "Titanium Dioxide", "$"),
    ("Retinol 0.5% in Squalane", "The Ordinary", "treatment", True, False, ["normal", "dry"], ["anti-aging"], "Retinol, Squalane", "$"),
    ("Dark Spot Correcting Serum", "Good Molecules", "serum", True, True, ["oily", "dry", "normal"], ["dark_spots"], "Niacinamide, Tranexamic Acid", "$"),
    ("Caffeine Solution 5% + EGCG", "The Ordinary", "eye_care", True, True, ["oily", "dry", "normal"], ["dark_circles"], "Caffeine", "$"),
    ("Eye Balm", "Kiehl's", "eye_care", True, False, ["dry", "normal"], ["dark_circles"], "Avocado, Shea Butter", "$$"),
    ("Vitamin C Suspension 23% + HA Spheres 2%", "The Ordinary", "serum", True, True, ["normal", "oily"], ["dark_spots"], "Vitamin C", "$"),
    ("Squalane Cleanser", "The Ordinary", "cleanser", True, False, ["dry", "normal"], ["hydration"], "Squalane", "$"),
    ("Redness Relief Soothing Gel Cream", "Aveeno", "moisturizer", True, True, ["oily", "normal"], ["sensitivity"], "Feverfew, Colloidal Oatmeal", "$"),
    ("Micellar Cleansing Water", "Bioderma", "cleanser", True, False, ["dry", "normal", "oily"], ["sensitivity"], "Micelle Technology", "$"),
    ("Blue Herbal Acne Cleansing Gel", "Origins", "cleanser", False, True, ["oily"], ["acne"], "Salicylic Acid, Tea Tree", "$$"),
    ("Water Cream Oil-Free Moisturizer", "Tatcha", "moisturizer", True, True, ["oily", "combination"], ["hydration"], "Japanese Wild Rose", "$$$"),
    ("Ultra Repair Cream", "First Aid Beauty", "moisturizer", True, False, ["dry"], ["barrier repair"], "Colloidal Oatmeal, Shea Butter", "$$"),
    ("Clear Skin Max Salicylic Acid Cleanser", "Simple", "cleanser", True, True, ["oily"], ["acne"], "Salicylic Acid", "$"),
]


def seed():
    db = SessionLocal()
    added = 0
    for (name, brand, category, frag_free, oil_free, types, concerns, key_ing, price) in STARTER_PRODUCTS:
        existing = db.query(Product).filter(Product.name == name, Product.brand == brand).first()
        if existing:
            continue
        db.add(Product(
            name=name, brand=brand, category=category,
            is_fragrance_free=frag_free, is_oil_free=oil_free,
            suitable_skin_types=types, concerns_addressed=concerns,
            key_ingredients=key_ing, price_range=price,
        ))
        added += 1
    db.commit()
    total = db.query(Product).count()
    db.close()
    print(f"Added {added} new products. Total in catalog: {total}")


if __name__ == "__main__":
    seed()