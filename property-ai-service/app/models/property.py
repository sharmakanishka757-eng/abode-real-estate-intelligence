"""Property listing model used for listings and future analysis."""

from sqlalchemy import CheckConstraint, Column, DateTime, Float, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Property(Base):
    """A property listing that can later hold analysis results."""

    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    property_type = Column(String(50), nullable=False)
    listing_type = Column(String(20), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    area = Column(Numeric(12, 2), nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "property_type IN ('apartment', 'house', 'land')",
            name="ck_property_type",
        ),
        CheckConstraint(
            "listing_type IN ('buy', 'rent')",
            name="ck_listing_type",
        ),
        CheckConstraint("price >= 0", name="ck_price_non_negative"),
        CheckConstraint("area IS NULL OR area >= 0", name="ck_area_non_negative"),
        CheckConstraint(
            "bedrooms IS NULL OR bedrooms >= 0",
            name="ck_bedrooms_non_negative",
        ),
        CheckConstraint(
            "bathrooms IS NULL OR bathrooms >= 0",
            name="ck_bathrooms_non_negative",
        ),
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="ck_latitude_range",
        ),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="ck_longitude_range",
        ),
    )
