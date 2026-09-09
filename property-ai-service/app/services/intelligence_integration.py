"""Boundary between Member 3 scoring and Location / Environment intelligence.

This milestone does not call Member 1 or Member 2 over HTTP.
It returns deterministic mock scores so analyze/scoring can be tested end to end.

Later, get_location_intelligence / get_environment_intelligence can be switched
to HTTP clients without changing property_scoring.py.

Mock intelligence is for development/testing only. It is not real location
or environmental data.
"""

from __future__ import annotations

from typing import Optional, Union

from app.models.property import Property
from app.schemas.intelligence import (
    CombinedIntelligence,
    EnvironmentIntelligence,
    LocationIntelligence,
    PropertyIntelligenceInput,
)
from app.schemas.scoring import EnvironmentScores, LocationScores


def _clip_score(value: float) -> float:
    return float(max(0, min(100, round(value, 2))))


def _stable_score(base: float, latitude: float, longitude: float, salt: float) -> float:
    """Map coordinates to a repeatable 0-100 score. Not random."""
    mixed = abs(latitude) * 12.7 + abs(longitude) * 8.3 + salt
    offset = (mixed % 31.0) - 10.0
    return _clip_score(base + offset)


def _to_input(
    property_data: Union[Property, PropertyIntelligenceInput],
) -> PropertyIntelligenceInput:
    if isinstance(property_data, PropertyIntelligenceInput):
        return property_data
    return PropertyIntelligenceInput(
        id=property_data.id,
        city=property_data.city,
        latitude=float(property_data.latitude),
        longitude=float(property_data.longitude),
        address=property_data.address or "",
        property_type=property_data.property_type or "",
        listing_type=property_data.listing_type or "",
    )


def get_location_intelligence(
    property_data: Union[Property, PropertyIntelligenceInput],
) -> LocationIntelligence:
    """Return location scores for a property.

    Today: deterministic mock.
    Later: Member 1 GET /api/location/{property_id}.
    """
    item = _to_input(property_data)
    city_salt = float(sum(ord(char) for char in item.city.lower()) % 17)
    return LocationIntelligence(
        safety=_stable_score(78, item.latitude, item.longitude, 1.0 + city_salt),
        transport=_stable_score(72, item.latitude, item.longitude, 4.0 + city_salt),
        healthcare=_stable_score(80, item.latitude, item.longitude, 7.0 + city_salt),
        education=_stable_score(70, item.latitude, item.longitude, 11.0 + city_salt),
        amenities=_stable_score(76, item.latitude, item.longitude, 14.0 + city_salt),
        noise_connectivity=_stable_score(68, item.latitude, item.longitude, 18.0 + city_salt),
    )


def get_environment_intelligence(
    property_data: Union[Property, PropertyIntelligenceInput],
) -> EnvironmentIntelligence:
    """Return environment scores for a property.

    Today: deterministic mock.
    Later: Member 2 GET /api/environment/{property_id}.

    flood_risk: 100 = low risk / favorable; 0 = high risk / unfavorable.
    """
    item = _to_input(property_data)
    city_salt = float(sum(ord(char) for char in item.city.lower()) % 17)
    return EnvironmentIntelligence(
        environment=_stable_score(74, item.latitude, item.longitude, 21.0 + city_salt),
        water_utilities=_stable_score(71, item.latitude, item.longitude, 25.0 + city_salt),
        flood_risk=_stable_score(82, item.latitude, item.longitude, 29.0 + city_salt),
    )


def resolve_intelligence(
    property_data: Union[Property, PropertyIntelligenceInput],
    location_scores: Optional[LocationScores] = None,
    environment_scores: Optional[EnvironmentScores] = None,
) -> CombinedIntelligence:
    """Use explicit analyze-request scores when provided; otherwise mock data."""
    if location_scores is None:
        location = get_location_intelligence(property_data)
        location_source = "mock"
    else:
        location = location_scores
        location_source = "explicit"

    if environment_scores is None:
        environment = get_environment_intelligence(property_data)
        environment_source = "mock"
    else:
        environment = environment_scores
        environment_source = "explicit"

    return CombinedIntelligence(
        location=location,
        environment=environment,
        location_source=location_source,
        environment_source=environment_source,
    )
