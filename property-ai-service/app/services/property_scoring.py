"""Deterministic, rule-based personalized property scoring.

This engine is not an LLM. Location and environment scores are optional
structured inputs so Member 1 / Member 2 services can be wired in later.

Scoring rules
-------------
Budget:
  - Inside the preferred min/max range → 100
  - Within 10% of the range (slightly outside) → 50
  - Farther outside → 0

Listing type:
  - Exact match → 100
  - Mismatch → 0

Property type:
  - In the preferred list → 100
  - Not preferred → 0

Bedrooms:
  - Meets or exceeds min_bedrooms → 100
  - One bedroom below → 40
  - More than one below, or unknown when a minimum is set → 0

Area:
  - Meets or exceeds min_area → 100
  - Within 10% below minimum → 50
  - Farther below, or unknown when a minimum is set → 0

Neighborhood categories:
  - Each provided 0-100 score is multiplied by the user's normalized weight
  - flood_risk is already "higher = more favorable" (100 = low risk)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from app.schemas.preferences import PreferenceScoringInput
from app.schemas.scoring import EnvironmentScores, LocationScores
from app.services.preference_weights import normalize_category_weights

# Share of the final 0-100 score.
BUDGET_SHARE = 0.25
LISTING_TYPE_SHARE = 0.10
PROPERTY_TYPE_SHARE = 0.10
BEDROOM_SHARE = 0.075
AREA_SHARE = 0.075
CATEGORY_SHARE = 0.40

BUDGET_NEAR_FACTOR = 0.10
AREA_NEAR_FACTOR = 0.10

EXCELLENT_MATCH_MIN = 90.0
GOOD_MATCH_MIN = 75.0
MODERATE_MATCH_MIN = 60.0

STRONG_CATEGORY_MIN = 75.0
WEAK_CATEGORY_MAX = 50.0

NEUTRAL_CATEGORY_SCORE = 50.0

RECOMMENDATION_EXCELLENT = "Excellent Match"
RECOMMENDATION_GOOD = "Good Match"
RECOMMENDATION_MODERATE = "Moderate Match"
RECOMMENDATION_LOW = "Low Match"

CATEGORY_LABELS = {
    "safety": "Safety",
    "transport": "Transport",
    "healthcare": "Healthcare",
    "education": "Education",
    "environment": "Environment",
    "water_utilities": "Water and utilities",
    "flood_risk": "Flood-risk conditions",
    "amenities": "Amenities",
    "noise_connectivity": "Noise and connectivity",
}


@dataclass
class ScoreBreakdown:
    budget: float
    listing_type: float
    property_type: float
    bedrooms: float
    area: float
    categories: float
    category_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class PropertyScoreResult:
    match_score: float
    recommendation: str
    summary: str
    positive_factors: list[str]
    caution_factors: list[str]
    category_scores: dict[str, float]
    breakdown: ScoreBreakdown


def score_budget(price: float, min_budget: Decimal, max_budget: Decimal) -> float:
    minimum = float(min_budget)
    maximum = float(max_budget)
    if minimum <= price <= maximum:
        return 100.0
    span = max(maximum - minimum, maximum * BUDGET_NEAR_FACTOR, 1.0)
    near = span * BUDGET_NEAR_FACTOR
    if price > maximum and (price - maximum) <= near:
        return 50.0
    if price < minimum and (minimum - price) <= near:
        return 50.0
    return 0.0


def score_listing_type(listing_type: str, preferred: str) -> float:
    return 100.0 if listing_type == preferred else 0.0


def score_property_type(property_type: str, preferred: list[str]) -> float:
    return 100.0 if property_type in preferred else 0.0


def score_bedrooms(bedrooms: Optional[int], min_bedrooms: Optional[int]) -> float:
    if min_bedrooms is None:
        return 100.0
    if bedrooms is None:
        return 0.0
    if bedrooms >= min_bedrooms:
        return 100.0
    if bedrooms == min_bedrooms - 1:
        return 40.0
    return 0.0


def score_area(area: Optional[float], min_area: Optional[Decimal]) -> float:
    if min_area is None:
        return 100.0
    if area is None:
        return 0.0
    minimum = float(min_area)
    if area >= minimum:
        return 100.0
    if area >= minimum * (1.0 - AREA_NEAR_FACTOR):
        return 50.0
    return 0.0


def merge_category_scores(
    location_scores: Optional[LocationScores],
    environment_scores: Optional[EnvironmentScores],
) -> dict[str, float]:
    merged: dict[str, float] = {}
    if location_scores is not None:
        merged.update(
            {
                key: value
                for key, value in location_scores.model_dump().items()
                if value is not None
            }
        )
    if environment_scores is not None:
        merged.update(
            {
                key: value
                for key, value in environment_scores.model_dump().items()
                if value is not None
            }
        )
    return merged


def score_categories(
    raw_weights: dict[str, float],
    category_scores: dict[str, float],
) -> float:
    """Weighted average of available category scores, 0-100.

    Missing category inputs are skipped and remaining weights are re-normalized.
    If no category scores are provided, a neutral 50 is used.
    """
    normalized = normalize_category_weights(raw_weights)
    usable = {
        key: score
        for key, score in category_scores.items()
        if key in normalized
    }
    if not usable:
        return NEUTRAL_CATEGORY_SCORE

    present_weights = {key: normalized[key] for key in usable}
    present_total = sum(present_weights.values())
    if present_total <= 0:
        return NEUTRAL_CATEGORY_SCORE

    weighted = 0.0
    for key, score in usable.items():
        weighted += score * (present_weights[key] / present_total)
    return weighted


def recommendation_from_score(match_score: float) -> str:
    if match_score >= EXCELLENT_MATCH_MIN:
        return RECOMMENDATION_EXCELLENT
    if match_score >= GOOD_MATCH_MIN:
        return RECOMMENDATION_GOOD
    if match_score >= MODERATE_MATCH_MIN:
        return RECOMMENDATION_MODERATE
    return RECOMMENDATION_LOW


def generate_explanation(
    match_score: float,
    recommendation: str,
    breakdown: ScoreBreakdown,
    preferences: PreferenceScoringInput,
) -> tuple[str, list[str], list[str]]:
    """Rule-based explanation. Replaceable by an AI service later."""
    if recommendation == RECOMMENDATION_EXCELLENT:
        summary = "Strong match based on your selected preferences."
    elif recommendation == RECOMMENDATION_GOOD:
        summary = "Good overall match based on your selected preferences."
    elif recommendation == RECOMMENDATION_MODERATE:
        summary = "Moderate match. Some preferences align, but review the caution factors."
    else:
        summary = (
            "Low match against your selected preferences. "
            "Review the caution factors before proceeding."
        )

    positive: list[str] = []
    caution: list[str] = []

    if breakdown.budget == 100:
        positive.append("Property fits within your preferred budget.")
    elif breakdown.budget == 50:
        caution.append("Property is slightly outside your preferred budget.")
    else:
        caution.append("Property is outside your preferred budget.")

    if breakdown.listing_type == 100:
        positive.append("Listing type matches your preference.")
    else:
        caution.append("Listing type does not match your preference.")

    if breakdown.property_type == 100:
        positive.append("Property type matches your preference.")
    else:
        caution.append("Property type is not in your preferred list.")

    if preferences.min_bedrooms is not None:
        if breakdown.bedrooms == 100:
            positive.append("Property meets your minimum bedroom requirement.")
        else:
            caution.append("Property is below your minimum bedroom requirement.")

    if preferences.min_area is not None:
        if breakdown.area == 100:
            positive.append("Property meets your minimum area requirement.")
        else:
            caution.append("Property is below your minimum area requirement.")

    for key, score in breakdown.category_scores.items():
        label = CATEGORY_LABELS.get(key, key.replace("_", " ").title())
        if key == "flood_risk":
            if score >= STRONG_CATEGORY_MIN:
                positive.append("Flood-risk conditions are favorable.")
            elif score <= WEAK_CATEGORY_MAX:
                caution.append(
                    "Flood-risk conditions are relatively high and may require further consideration."
                )
            continue
        if score >= STRONG_CATEGORY_MIN:
            positive.append(f"{label} is a strong match.")
        elif score <= WEAK_CATEGORY_MAX:
            caution.append(
                f"{label} score is relatively low and may require further consideration."
            )

    return summary, positive, caution


def score_property(
    *,
    price: float,
    listing_type: str,
    property_type: str,
    bedrooms: Optional[int],
    area: Optional[float],
    preferences: PreferenceScoringInput,
    location_scores: Optional[LocationScores] = None,
    environment_scores: Optional[EnvironmentScores] = None,
) -> PropertyScoreResult:
    """Return a personalized match score between 0 and 100."""
    category_scores = merge_category_scores(location_scores, environment_scores)
    breakdown = ScoreBreakdown(
        budget=score_budget(price, preferences.min_budget, preferences.max_budget),
        listing_type=score_listing_type(
            listing_type,
            preferences.preferred_listing_type.value,
        ),
        property_type=score_property_type(
            property_type,
            [item.value for item in preferences.preferred_property_types],
        ),
        bedrooms=score_bedrooms(bedrooms, preferences.min_bedrooms),
        area=score_area(area, preferences.min_area),
        categories=score_categories(preferences.category_weight_map(), category_scores),
        category_scores=category_scores,
    )

    raw_score = (
        breakdown.budget * BUDGET_SHARE
        + breakdown.listing_type * LISTING_TYPE_SHARE
        + breakdown.property_type * PROPERTY_TYPE_SHARE
        + breakdown.bedrooms * BEDROOM_SHARE
        + breakdown.area * AREA_SHARE
        + breakdown.categories * CATEGORY_SHARE
    )
    match_score = round(min(100.0, max(0.0, raw_score)), 2)
    recommendation = recommendation_from_score(match_score)
    summary, positive, caution = generate_explanation(
        match_score,
        recommendation,
        breakdown,
        preferences,
    )
    return PropertyScoreResult(
        match_score=match_score,
        recommendation=recommendation,
        summary=summary,
        positive_factors=positive,
        caution_factors=caution,
        category_scores=category_scores,
        breakdown=breakdown,
    )
