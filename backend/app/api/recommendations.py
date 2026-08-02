from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.agents.recommendation_agent import recommend_products

router = APIRouter()


@router.get("/products")
def get_recommendations(
    skin_type: str = Query(..., description="oily / dry / normal"),
    acne_probability: float = Query(default=0.0, ge=0.0, le=1.0),
    darkcircle_probability: float = Query(default=0.0, ge=0.0, le=1.0),
    category: str = Query(default=None, description="optional: cleanser, moisturizer, serum, sunscreen, etc"),
    db: Session = Depends(get_db),
):
    """
    Returns ranked, content-based product recommendations for a given skin
    profile, with interpretable match reasons and purchase search links.
    """
    results = recommend_products(
        db, skin_type=skin_type, acne_probability=acne_probability,
        darkcircle_probability=darkcircle_probability, category=category,
    )
    return {"recommendations": results, "count": len(results)}