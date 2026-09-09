"""Request and response schemas for personalized property analysis."""

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.preferences import PreferenceScoringInput
from app.schemas.property import PropertyResponse


class LocationScores(BaseModel):
    """Location intelligence scores. Higher is always better. Range 0-100."""

    safety: Optional[float] = Field(default=None, ge=0, le=100)
    transport: Optional[float] = Field(default=None, ge=0, le=100)
    healthcare: Optional[float] = Field(default=None, ge=0, le=100)
    education: Optional[float] = Field(default=None, ge=0, le=100)
    amenities: Optional[float] = Field(default=None, ge=0, le=100)
    noise_connectivity: Optional[float] = Field(default=None, ge=0, le=100)


class EnvironmentScores(BaseModel):
    """Environment intelligence scores. Higher is always better. Range 0-100.

    flood_risk: 100 = low flood/waterlogging risk (favorable).
    flood_risk: 0 = high flood/waterlogging risk (unfavorable).
    """

    environment: Optional[float] = Field(default=None, ge=0, le=100)
    water_utilities: Optional[float] = Field(default=None, ge=0, le=100)
    flood_risk: Optional[float] = Field(default=None, ge=0, le=100)


class PropertyAnalyzeRequest(BaseModel):
    user_preferences: PreferenceScoringInput
    location_scores: Optional[LocationScores] = None
    environment_scores: Optional[EnvironmentScores] = None


class PropertyAnalyzeResponse(BaseModel):
    property_id: int
    property: PropertyResponse
    match_score: float
    recommendation: str
    summary: str
    positive_factors: list[str]
    caution_factors: list[str]
    category_scores: dict[str, float]
