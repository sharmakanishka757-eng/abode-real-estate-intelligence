"""User preference profile for personalized property scoring."""

from sqlalchemy import CheckConstraint, Column, Float, Integer, JSON, Numeric, String

from app.database import Base


class UserPreference(Base):
    """One active preference profile per user_id for this milestone."""

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    min_budget = Column(Numeric(12, 2), nullable=False)
    max_budget = Column(Numeric(12, 2), nullable=False)
    preferred_listing_type = Column(String(20), nullable=False)
    preferred_property_types = Column(JSON, nullable=False)
    min_bedrooms = Column(Integer, nullable=True)
    min_area = Column(Numeric(12, 2), nullable=True)
    safety_weight = Column(Float, nullable=False, default=1.0)
    transport_weight = Column(Float, nullable=False, default=1.0)
    healthcare_weight = Column(Float, nullable=False, default=1.0)
    education_weight = Column(Float, nullable=False, default=1.0)
    environment_weight = Column(Float, nullable=False, default=1.0)
    water_utilities_weight = Column(Float, nullable=False, default=1.0)
    flood_risk_weight = Column(Float, nullable=False, default=1.0)
    amenities_weight = Column(Float, nullable=False, default=1.0)
    noise_connectivity_weight = Column(Float, nullable=False, default=1.0)

    __table_args__ = (
        CheckConstraint("min_budget >= 0", name="ck_pref_min_budget_non_negative"),
        CheckConstraint("max_budget >= 0", name="ck_pref_max_budget_non_negative"),
        CheckConstraint("min_budget <= max_budget", name="ck_pref_budget_range"),
        CheckConstraint(
            "preferred_listing_type IN ('buy', 'rent')",
            name="ck_pref_listing_type",
        ),
        CheckConstraint(
            "min_bedrooms IS NULL OR min_bedrooms >= 0",
            name="ck_pref_min_bedrooms_non_negative",
        ),
        CheckConstraint(
            "min_area IS NULL OR min_area >= 0",
            name="ck_pref_min_area_non_negative",
        ),
    )
