"""
Recommendation Agent: content-based filtering (a real, established
recommender-systems technique) matching products to a user's resolved
skin profile.

Why content-based instead of a "two-tower neural recommender" right now:
that architecture needs a large dataset of real user-product interactions
to learn meaningful embeddings from. We don't have that data yet -- building
one anyway would just be an untrained network producing arbitrary output
dressed up as ML. Content-based scoring, using our real ingredient risk
data, is honest and will actually perform well. Noted here as the honest
engineering tradeoff it is -- upgrading to collaborative/two-tower filtering
once real usage data exists is a legitimate documented next step.
"""
from urllib.parse import quote
from sqlalchemy.orm import Session

from app.models.models import Product

ACNE_THRESHOLD = 0.5
DARKCIRCLE_THRESHOLD = 0.5


def score_product(product: Product, skin_type: str, acne_probability: float, darkcircle_probability: float) -> tuple[float, list[str]]:
    """Returns (score, reasons) -- fully interpretable, every point traces to a rule."""
    score = 0.0
    reasons = []

    if product.suitable_skin_types and skin_type in product.suitable_skin_types:
        score += 3
        reasons.append(f"Formulated for {skin_type} skin.")

    if acne_probability >= ACNE_THRESHOLD:
        if product.concerns_addressed and "acne" in product.concerns_addressed:
            score += 3
            reasons.append("Targets acne, which was detected as a concern.")
        if product.is_oil_free:
            score += 1
            reasons.append("Oil-free formula -- generally safer for acne-prone skin.")

    if darkcircle_probability >= DARKCIRCLE_THRESHOLD:
        if product.concerns_addressed and "dark_circles" in product.concerns_addressed:
            score += 3
            reasons.append("Targets dark circles, which were detected as a concern.")

    if product.is_fragrance_free:
        score += 0.5
        reasons.append("Fragrance-free -- lower irritation risk.")

    return score, reasons


def recommend_products(
    db: Session,
    skin_type: str,
    acne_probability: float = 0.0,
    darkcircle_probability: float = 0.0,
    category: str = None,
    top_n: int = 6,
) -> list[dict]:
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    products = query.all()

    scored = []
    for p in products:
        score, reasons = score_product(p, skin_type, acne_probability, darkcircle_probability)
        if score > 0:
            scored.append((score, p, reasons))

    scored.sort(key=lambda x: -x[0])
    top = scored[:top_n]

    results = []
    for score, p, reasons in top:
        search_term = f"{p.brand} {p.name}"
        results.append({
            "product_name": p.name,
            "brand": p.brand,
            "category": p.category,
            "match_score": round(score, 1),
            "match_reasons": reasons,
            "key_ingredients": p.key_ingredients,
            "price_range": p.price_range,
            "nykaa_search_url": f"https://www.nykaa.com/search/result/?q={quote(search_term)}",
            "purplle_search_url": f"https://www.purplle.com/search?q={quote(search_term)}",
            "disclaimer": "Recommendation only -- patch-test new products and consult a dermatologist for persistent issues.",
        })

    return results