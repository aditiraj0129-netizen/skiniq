"""
Seeds the ingredients table with a starter set of common skincare ingredients.



"""
from app.db.database import SessionLocal, Base, engine
from app.models.models import Ingredient

Base.metadata.create_all(bind=engine)

STARTER_INGREDIENTS = [
    # name, inci_name, comedogenic_rating (0-5), is_common_allergen, purpose
    ("Niacinamide", "Niacinamide", 0, False, "brightening/barrier repair"),
    ("Hyaluronic Acid", "Sodium Hyaluronate", 0, False, "hydration"),
    ("Salicylic Acid", "Salicylic Acid", 0, False, "exfoliant"),
    ("Glycolic Acid", "Glycolic Acid", 0, False, "exfoliant"),
    ("Ceramides", "Ceramide NP", 0, False, "barrier repair"),
    ("Glycerin", "Glycerin", 0, False, "humectant"),
    ("Zinc Oxide", "Zinc Oxide", 0, False, "sunscreen/soothing"),
    ("Retinol", "Retinol", 1, False, "anti-aging/exfoliant"),
    ("Vitamin C", "Ascorbic Acid", 1, True, "antioxidant/brightening"),
    ("Squalane", "Squalane", 1, False, "moisturizer"),
    ("Shea Butter", "Butyrospermum Parkii Butter", 2, False, "moisturizer"),
    ("Jojoba Oil", "Simmondsia Chinensis Oil", 2, False, "moisturizer"),
    ("Dimethicone", "Dimethicone", 2, False, "silicone/smoothing"),
    ("Argan Oil", "Argania Spinosa Kernel Oil", 2, False, "moisturizer"),
    ("Lanolin", "Lanolin", 2, True, "moisturizer"),
    ("Cetyl Alcohol", "Cetyl Alcohol", 2, False, "emollient/thickener"),
    ("Isopropyl Myristate", "Isopropyl Myristate", 5, False, "emollient"),
    ("Coconut Oil", "Cocos Nucifera Oil", 4, False, "moisturizer"),
    ("Cocoa Butter", "Theobroma Cacao Seed Butter", 4, False, "moisturizer"),
    ("Lauric Acid", "Lauric Acid", 4, False, "emollient"),
    ("Algae Extract", "Algae Extract", 3, False, "antioxidant"),
    ("Sodium Lauryl Sulfate", "Sodium Lauryl Sulfate", 1, True, "surfactant/cleanser"),
    ("Fragrance", "Parfum", 0, True, "fragrance"),
    ("Essential Oil Blend", "Fragrance Oil", 0, True, "fragrance"),
    ("Alcohol Denat", "Alcohol Denat", 0, True, "solvent/astringent"),
    ("Witch Hazel", "Hamamelis Virginiana Extract", 0, True, "astringent"),
    ("Benzoyl Peroxide", "Benzoyl Peroxide", 0, True, "acne treatment"),
    ("Tea Tree Oil", "Melaleuca Alternifolia Oil", 0, True, "antimicrobial"),
    ("Aloe Vera", "Aloe Barbadensis Leaf Juice", 0, False, "soothing"),
    ("Panthenol", "Panthenol", 0, False, "soothing/hydration"),
    ("Centella Asiatica", "Centella Asiatica Extract", 0, False, "soothing/repair"),
    ("Titanium Dioxide", "Titanium Dioxide", 0, False, "sunscreen"),
    ("Octinoxate", "Ethylhexyl Methoxycinnamate", 0, True, "sunscreen"),
    ("Parabens", "Methylparaben", 0, True, "preservative"),
    ("Phenoxyethanol", "Phenoxyethanol", 0, False, "preservative"),
    ("Water", "Aqua", 0, False, "solvent/base"),
    ("Propylene Glycol", "Propylene Glycol", 0, True, "humectant/solvent"),
    ("Mineral Oil", "Paraffinum Liquidum", 1, False, "occlusive/moisturizer"),
    ("Petrolatum", "Petrolatum", 1, False, "occlusive"),
    ("Beeswax", "Cera Alba", 2, False, "emollient/thickener"),
    ("Avocado Oil", "Persea Gratissima Oil", 2, False, "moisturizer"),
    # --- Added: common ingredients found in real mainstream products (e.g. lotions) ---
    ("Glycol Distearate", "Glycol Distearate", 3, False, "pearlizing/thickener"),
    ("Glyceryl Stearate", "Glyceryl Stearate", 2, False, "emulsifier"),
    ("Dimethicone Crosspolymer", "Dimethicone Crosspolymer", 1, False, "silicone/texture"),
    ("Carbomer", "Carbomer", 0, False, "thickener/gelling agent"),
    ("Sodium Hydroxide", "Sodium Hydroxide", 0, False, "pH adjuster"),
    ("Disodium EDTA", "Disodium EDTA", 0, False, "chelating agent/stabilizer"),
    ("Citric Acid", "Citric Acid", 0, False, "pH adjuster"),
    ("Linalool", "Linalool", 0, True, "fragrance component"),
    ("Limonene", "Limonene", 0, True, "fragrance component"),
    ("Benzyl Alcohol", "Benzyl Alcohol", 0, True, "preservative/fragrance"),
    ("Alpha-Isomethyl Ionone", "Alpha-Isomethyl Ionone", 0, True, "fragrance component"),
    ("Panthenol Derivative", "Panthenyl Ethyl Ether", 0, False, "moisturizer/soothing"),
    ("PEG-100 Stearate", "PEG-100 Stearate", 2, False, "emulsifier"),
    ("Stearic Acid", "Stearic Acid", 2, False, "emulsifier/thickener"),
    ("Sodium Benzoate", "Sodium Benzoate", 0, False, "preservative"),
    ("Potassium Sorbate", "Potassium Sorbate", 0, False, "preservative"),
    ("Xanthan Gum", "Xanthan Gum", 0, False, "thickener"),
    ("Allantoin", "Allantoin", 0, False, "soothing"),
    ("Tocopherol", "Tocopherol", 0, False, "antioxidant (Vitamin E)"),
    ("Caprylic Triglyceride", "Caprylic/Capric Triglyceride", 1, False, "emollient"),
]


def seed():
    db = SessionLocal()
    added = 0
    for name, inci, rating, allergen, purpose in STARTER_INGREDIENTS:
        existing = db.query(Ingredient).filter(Ingredient.name == name).first()
        if existing:
            continue
        db.add(Ingredient(
            name=name, inci_name=inci, comedogenic_rating=rating,
            is_common_allergen=allergen, purpose=purpose,
        ))
        added += 1
    db.commit()
    total = db.query(Ingredient).count()
    db.close()
    print(f"Added {added} new ingredients. Total in database: {total}")


if __name__ == "__main__":
    seed()