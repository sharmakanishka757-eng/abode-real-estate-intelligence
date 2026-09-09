"""Normalize user category priorities into weights that sum to 1.0."""

CATEGORY_WEIGHT_KEYS = (
    "safety",
    "transport",
    "healthcare",
    "education",
    "environment",
    "water_utilities",
    "flood_risk",
    "amenities",
    "noise_connectivity",
)


class ZeroCategoryWeightError(ValueError):
    """Raised when every category weight is zero, so priorities cannot be normalized."""


def normalize_category_weights(weights: dict[str, float]) -> dict[str, float]:
    """Convert raw priority values into fractions that sum to 1.

    Example: {safety: 5, transport: 3, healthcare: 2} -> 0.5, 0.3, 0.2
    """
    cleaned = {key: float(value) for key, value in weights.items() if float(value) >= 0}
    total = sum(cleaned.values())
    if total <= 0:
        raise ZeroCategoryWeightError(
            "All category weights are zero. Provide at least one positive weight."
        )
    return {key: value / total for key, value in cleaned.items()}
