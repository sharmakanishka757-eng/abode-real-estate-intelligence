"""REST routes for user preference profiles."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.preferences import UserPreference
from app.schemas.preferences import PreferenceCreate, PreferenceResponse, PreferenceUpdate

router = APIRouter(tags=["preferences"])

WEIGHT_FIELDS = (
    "safety_weight",
    "transport_weight",
    "healthcare_weight",
    "education_weight",
    "environment_weight",
    "water_utilities_weight",
    "flood_risk_weight",
    "amenities_weight",
    "noise_connectivity_weight",
)


def _get_preference_or_404(db: Session, user_id: str) -> UserPreference:
    preference = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if preference is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preferences for user {user_id} were not found.",
        )
    return preference


@router.post("/preferences", response_model=PreferenceResponse, status_code=status.HTTP_201_CREATED)
def create_preferences(payload: PreferenceCreate, db: Session = Depends(get_db)) -> UserPreference:
    existing = db.query(UserPreference).filter(UserPreference.user_id == payload.user_id).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Preferences for user {payload.user_id} already exist.",
        )
    data = payload.model_dump()
    data["preferred_listing_type"] = payload.preferred_listing_type.value
    data["preferred_property_types"] = [
        item.value for item in payload.preferred_property_types
    ]
    preference = UserPreference(**data)
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference


@router.get("/preferences/{user_id}", response_model=PreferenceResponse)
def get_preferences(user_id: str, db: Session = Depends(get_db)) -> UserPreference:
    return _get_preference_or_404(db, user_id)


@router.put("/preferences/{user_id}", response_model=PreferenceResponse)
def update_preferences(
    user_id: str,
    payload: PreferenceUpdate,
    db: Session = Depends(get_db),
) -> UserPreference:
    preference = _get_preference_or_404(db, user_id)
    updates = payload.model_dump(exclude_unset=True)
    if "preferred_listing_type" in updates and updates["preferred_listing_type"] is not None:
        listing = updates["preferred_listing_type"]
        updates["preferred_listing_type"] = listing.value if hasattr(listing, "value") else listing
    if "preferred_property_types" in updates and updates["preferred_property_types"] is not None:
        updates["preferred_property_types"] = [
            item.value if hasattr(item, "value") else item
            for item in updates["preferred_property_types"]
        ]

    merged_min = updates.get("min_budget", preference.min_budget)
    merged_max = updates.get("max_budget", preference.max_budget)
    if merged_min is not None and merged_max is not None and merged_min > merged_max:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_budget cannot be greater than max_budget.",
        )

    weight_values = []
    for field_name in WEIGHT_FIELDS:
        if field_name in updates:
            weight_values.append(updates[field_name])
        else:
            weight_values.append(getattr(preference, field_name))
    if sum(float(value) for value in weight_values) <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one category weight must be greater than zero.",
        )

    for field_name, value in updates.items():
        setattr(preference, field_name, value)
    db.commit()
    db.refresh(preference)
    return preference


@router.delete("/preferences/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_preferences(user_id: str, db: Session = Depends(get_db)) -> None:
    preference = _get_preference_or_404(db, user_id)
    db.delete(preference)
    db.commit()
