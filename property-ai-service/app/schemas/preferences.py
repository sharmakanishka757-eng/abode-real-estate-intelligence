"""Pydantic schemas for user preference profiles."""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.property import ListingType, PropertyType

WEIGHT_MAX = 10


class PreferenceBase(BaseModel):
    min_budget: Decimal = Field(..., ge=0)
    max_budget: Decimal = Field(..., ge=0)
    preferred_listing_type: ListingType
    preferred_property_types: list[PropertyType] = Field(..., min_length=1)
    min_bedrooms: Optional[int] = Field(default=None, ge=0)
    min_area: Optional[Decimal] = Field(default=None, ge=0)
    safety_weight: float = Field(default=1.0, ge=0, le=WEIGHT_MAX)
    transport_weight: float = Field(default=1.0, ge=0, le=WEIGHT_MAX)
    healthcare_weight: float = Field(default=1.0, ge=0, le=WEIGHT_MAX)
    education_weight: float = Field(default=1.0, ge=0, le=WEIGHT_MAX)
    environment_weight: float = Field(default=1.0, ge=0, le=WEIGHT_MAX)
    water_utilities_weight: float = Field(default=1.0, ge=0, le=WEIGHT_MAX)
    flood_risk_weight: float = Field(default=1.0, ge=0, le=WEIGHT_MAX)
    amenities_weight: float = Field(default=1.0, ge=0, le=WEIGHT_MAX)
    noise_connectivity_weight: float = Field(default=1.0, ge=0, le=WEIGHT_MAX)

    @field_validator("preferred_property_types")
    @classmethod
    def unique_property_types(cls, value: list[PropertyType]) -> list[PropertyType]:
        if len(set(value)) != len(value):
            raise ValueError("preferred_property_types must not contain duplicates.")
        return value

    @model_validator(mode="after")
    def validate_budget_and_weights(self) -> "PreferenceBase":
        if self.min_budget > self.max_budget:
            raise ValueError("min_budget cannot be greater than max_budget.")
        if sum(self.category_weight_map().values()) <= 0:
            raise ValueError("At least one category weight must be greater than zero.")
        return self

    def category_weight_map(self) -> dict[str, float]:
        return {
            "safety": self.safety_weight,
            "transport": self.transport_weight,
            "healthcare": self.healthcare_weight,
            "education": self.education_weight,
            "environment": self.environment_weight,
            "water_utilities": self.water_utilities_weight,
            "flood_risk": self.flood_risk_weight,
            "amenities": self.amenities_weight,
            "noise_connectivity": self.noise_connectivity_weight,
        }


class PreferenceCreate(PreferenceBase):
    user_id: str = Field(..., min_length=1, max_length=100)


class PreferenceUpdate(BaseModel):
    min_budget: Optional[Decimal] = Field(default=None, ge=0)
    max_budget: Optional[Decimal] = Field(default=None, ge=0)
    preferred_listing_type: Optional[ListingType] = None
    preferred_property_types: Optional[list[PropertyType]] = Field(default=None, min_length=1)
    min_bedrooms: Optional[int] = Field(default=None, ge=0)
    min_area: Optional[Decimal] = Field(default=None, ge=0)
    safety_weight: Optional[float] = Field(default=None, ge=0, le=WEIGHT_MAX)
    transport_weight: Optional[float] = Field(default=None, ge=0, le=WEIGHT_MAX)
    healthcare_weight: Optional[float] = Field(default=None, ge=0, le=WEIGHT_MAX)
    education_weight: Optional[float] = Field(default=None, ge=0, le=WEIGHT_MAX)
    environment_weight: Optional[float] = Field(default=None, ge=0, le=WEIGHT_MAX)
    water_utilities_weight: Optional[float] = Field(default=None, ge=0, le=WEIGHT_MAX)
    flood_risk_weight: Optional[float] = Field(default=None, ge=0, le=WEIGHT_MAX)
    amenities_weight: Optional[float] = Field(default=None, ge=0, le=WEIGHT_MAX)
    noise_connectivity_weight: Optional[float] = Field(default=None, ge=0, le=WEIGHT_MAX)


class PreferenceResponse(PreferenceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str


class PreferenceScoringInput(PreferenceBase):
    """Preference payload used by the analyze endpoint (no stored user_id required)."""
