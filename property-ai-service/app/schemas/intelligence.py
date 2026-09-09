"""Internal contracts for Location and Environment Intelligence.

These models describe the data Member 3's scoring engine expects.
HTTP clients for Member 1 / Member 2 are not implemented in this milestone.

Score meaning (every category):
- 0 = poor / unfavorable for a buyer
- 100 = strong / favorable for a buyer

flood_risk is inverted from raw hazard:
- 100 = low flood/waterlogging risk (favorable)
- 0 = high flood/waterlogging risk (unfavorable)
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.scoring import EnvironmentScores, LocationScores


class LocationIntelligence(BaseModel):
    """Complete location-intelligence payload. All values are 0-100."""

    safety: float = Field(..., ge=0, le=100)
    transport: float = Field(..., ge=0, le=100)
    healthcare: float = Field(..., ge=0, le=100)
    education: float = Field(..., ge=0, le=100)
    amenities: float = Field(..., ge=0, le=100)
    noise_connectivity: float = Field(..., ge=0, le=100)

    def to_location_scores(self) -> LocationScores:
        return LocationScores.model_validate(self.model_dump())


class EnvironmentIntelligence(BaseModel):
    """Complete environment-intelligence payload. All values are 0-100."""

    environment: float = Field(..., ge=0, le=100)
    water_utilities: float = Field(..., ge=0, le=100)
    flood_risk: float = Field(..., ge=0, le=100)

    def to_environment_scores(self) -> EnvironmentScores:
        return EnvironmentScores.model_validate(self.model_dump())


class CombinedIntelligence(BaseModel):
    location: LocationIntelligence | LocationScores
    environment: EnvironmentIntelligence | EnvironmentScores
    location_source: Literal["explicit", "mock"]
    environment_source: Literal["explicit", "mock"]

    def location_scores(self) -> LocationScores:
        if isinstance(self.location, LocationIntelligence):
            return self.location.to_location_scores()
        return self.location

    def environment_scores(self) -> EnvironmentScores:
        if isinstance(self.environment, EnvironmentIntelligence):
            return self.environment.to_environment_scores()
        return self.environment


class PropertyIntelligenceInput(BaseModel):
    """Minimum property fields the mock (and later HTTP) layer needs."""

    city: str
    latitude: float
    longitude: float
    address: str = ""
    property_type: str = ""
    listing_type: str = ""
    id: Optional[int] = None
