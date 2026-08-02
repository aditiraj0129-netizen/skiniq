"""
Pydantic schemas: define exactly what shape of data the API accepts and returns.
Keeping these separate from the SQLAlchemy models (in models.py) is a real backend
best practice -- it lets your API contract evolve independently of your DB schema.
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Dict, Any


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class SkinAnalysisResult(BaseModel):
    """What the vision agent returns after analyzing a photo. Note every trait
    comes with a confidence value -- never a bare, unqualified prediction."""
    skin_tone_ita: float
    skin_type: str
    skin_type_confidence: float
    texture: str
    acne_severity: float
    acne_severity_confidence_interval: List[float]   # e.g. [0.4, 0.6] = conformal set
    dark_circle_severity: float
    disclaimer: str = (
        "This is an automated estimate, not a medical diagnosis. "
        "Please verify with a licensed dermatologist before making treatment decisions."
    )


class ProductUsageIn(BaseModel):
    product_name: str
    brand: Optional[str] = None
    start_date: datetime
    still_using: bool = True


class ContributionScoreOut(BaseModel):
    product_name: str
    score: float
    reasoning: Dict[str, Any]
    disclaimer: str = (
        "This score is a statistical estimate based on ingredient data and your "
        "reported profile. It is not a clinical finding."
    )


class SensitiveSymptomIn(BaseModel):
    """No image field exists here -- enforced by design, not just by convention."""
    body_area: str
    duration_days: int
    symptoms_text: str
    severity: int  # 1-5


class RecommendationOut(BaseModel):
    product_name: str
    category: str
    match_reason: str
    confidence: float
    disclaimer: str = "Recommendation only -- patch-test new products and consult a dermatologist for persistent issues."


class DermatologistOut(BaseModel):
    name: str
    address: str
    phone: str
    distance_km: Optional[float] = None
    price_range: Optional[str] = None
    rating: Optional[float] = None


class SkinSelfReport(BaseModel):
    """
    Optional user self-report, used to override low-confidence model
    predictions rather than presenting an uncertain guess as fact.
    tone_category maps to a Fitzpatrick range: bright(1-2) / mid(3-4) / brown(4-5) / black(5-6)
    """
    tone_category: Optional[str] = None   # "bright" / "mid" / "brown" / "black"
    skin_type: Optional[str] = None        # "oily" / "dry" / "normal"