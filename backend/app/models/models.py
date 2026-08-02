"""
Core SQL schema for SkinIQ.

Design notes (worth remembering for your interview explanation):
- Raw photos are NEVER stored as blobs in SQL. We store a reference path to encrypted
  file storage, and the actual pixel data lives outside the relational DB. This is the
  correct real-world pattern for sensitive media.
- Every agent output is logged with a confidence interval, not just a final answer.
  This audit trail is what makes the system trustworthy and debuggable.
- sensitive_symptom_reports never has an image field at all, by design -- this enforces
  the "no photo for private-area concerns" promise at the schema level, not just in the UI.
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    skin_profiles = relationship("SkinProfile", back_populates="user")
    product_usages = relationship("UserProductUsage", back_populates="user")
    family_history = relationship("FamilyHistory", back_populates="user")


class SkinProfile(Base):
    """A snapshot of the user's skin at a point in time -- longitudinal, so we can
    show trends (e.g. 'your acne severity has dropped 30% over 6 weeks')."""
    __tablename__ = "skin_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    image_ref = Column(String)  # path/key to encrypted storage, never raw bytes here
    skin_tone_ita = Column(Float, nullable=True)       # Individual Typology Angle
    skin_type = Column(String, nullable=True)          # oily / dry / combination / normal
    texture = Column(String, nullable=True)
    acne_severity = Column(Float, nullable=True)
    dark_circle_severity = Column(Float, nullable=True)
    confidence_json = Column(JSON, nullable=True)       # conformal prediction sets per trait
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="skin_profiles")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    inci_name = Column(String)
    comedogenic_rating = Column(Float, nullable=True)   # 0-5 published dermatology scale
    is_common_allergen = Column(Boolean, default=False)
    purpose = Column(String, nullable=True)              # exfoliant, moisturizer, fragrance, etc


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    brand = Column(String)
    category = Column(String)   # cleanser, serum, moisturizer, sunscreen, etc
    shade_ita = Column(Float, nullable=True)
    is_fragrance_free = Column(Boolean, default=False)
    is_oil_free = Column(Boolean, default=False)
    suitable_skin_types = Column(JSON, nullable=True)   # e.g. ["oily", "normal"]
    concerns_addressed = Column(JSON, nullable=True)     # e.g. ["acne", "dark_circles"]
    key_ingredients = Column(String, nullable=True)
    price_range = Column(String, nullable=True)


class ProductIngredient(Base):
    """Join table: which ingredients are in which product, and roughly how concentrated
    (based on label order -- see agent logic, not fabricated precise percentages)."""
    __tablename__ = "product_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"))
    list_position = Column(Integer)   # 1 = first on label = highest concentration
    tier = Column(String)             # "primary" / "moderate" / "trace"


class UserProductUsage(Base):
    __tablename__ = "user_product_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    start_date = Column(DateTime)
    still_using = Column(Boolean, default=True)

    user = relationship("User", back_populates="product_usages")


class FamilyHistory(Base):
    __tablename__ = "family_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    condition = Column(String)   # eczema, psoriasis, hormonal acne, etc
    relation = Column(String)    # mother, father, sibling

    user = relationship("User", back_populates="family_history")


class ContributionScore(Base):
    """Output of the ingredient-reasoning agent: how likely a product is contributing
    to a reported problem, with the reasoning stored as JSON for full transparency."""
    __tablename__ = "contribution_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    score = Column(Float)              # 0-1 likelihood of contribution
    reasoning_json = Column(JSON)      # human-readable factor breakdown
    computed_at = Column(DateTime, default=datetime.utcnow)


class SensitiveSymptomReport(Base):
    """Text-only, by design -- no image field exists on this table at all."""
    __tablename__ = "sensitive_symptom_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    body_area = Column(String)
    duration_days = Column(Integer)
    symptoms_text = Column(Text)
    severity = Column(Integer)  # 1-5 self-reported
    top_category = Column(String, nullable=True)   # e.g. "irritation", "allergy" -- for trend matching
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentOutputLog(Base):
    """Full audit trail: every agent decision, every confidence value, timestamped.
    This is what makes the system debuggable and trustworthy -- nothing is a black box."""
    __tablename__ = "agent_output_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    agent_name = Column(String)
    input_summary = Column(JSON)
    output_summary = Column(JSON)
    confidence = Column(Float, nullable=True)
    triggered_debate = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnownIngredientName(Base):
    """
    Large recognition gazetteer (~28k real INCI names from the EU CosIng
    database). Separate from the `ingredients` table (which holds our
    curated risk data) -- this table answers 'is this a real cosmetic
    ingredient?' while `ingredients` answers 'what do we know about its risk?'
    """
    __tablename__ = "known_ingredient_names"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)


class SymptomKnowledge(Base):
    """
    Small curated knowledge base: symptom keywords -> possible causes.
    HONESTY NOTE: this is a starter educational reference, not a diagnostic
    ruleset -- flagged clearly in every response this feeds into.
    """
    __tablename__ = "symptom_knowledge"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, index=True)
    possible_cause = Column(String)
    category = Column(String)   # "irritation", "allergy", "sun-related", "infection-signal", etc
    urgency = Column(String, default="routine")   # "routine" / "prompt" / "urgent"
    note = Column(Text, nullable=True)


class Dermatologist(Base):
    __tablename__ = "dermatologists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    address = Column(String)
    phone = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    price_range = Column(String, nullable=True)
    rating = Column(Float, nullable=True)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    dermatologist_id = Column(Integer, ForeignKey("dermatologists.id"))
    scheduled_time = Column(DateTime)
    status = Column(String, default="pending")   # pending / confirmed / cancelled