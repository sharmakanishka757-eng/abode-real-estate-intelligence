"""Personalized property analysis routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.property import Property
from app.schemas.property import PropertyResponse
from app.schemas.scoring import PropertyAnalyzeRequest, PropertyAnalyzeResponse
from app.services.intelligence_integration import resolve_intelligence
from app.services.property_scoring import score_property

router = APIRouter(tags=["analysis"])


@router.post(
    "/properties/{property_id}/analyze",
    response_model=PropertyAnalyzeResponse,
)
def analyze_property(
    property_id: int,
    payload: PropertyAnalyzeRequest,
    db: Session = Depends(get_db),
) -> PropertyAnalyzeResponse:
    property_item = db.query(Property).filter(Property.id == property_id).first()
    if property_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} was not found.",
        )

    area = float(property_item.area) if property_item.area is not None else None
    intelligence = resolve_intelligence(
        property_item,
        location_scores=payload.location_scores,
        environment_scores=payload.environment_scores,
    )
    result = score_property(
        price=float(property_item.price),
        listing_type=property_item.listing_type,
        property_type=property_item.property_type,
        bedrooms=property_item.bedrooms,
        area=area,
        preferences=payload.user_preferences,
        location_scores=intelligence.location_scores(),
        environment_scores=intelligence.environment_scores(),
    )
    return PropertyAnalyzeResponse(
        property_id=property_item.id,
        property=PropertyResponse.model_validate(property_item),
        match_score=result.match_score,
        recommendation=result.recommendation,
        summary=result.summary,
        positive_factors=result.positive_factors,
        caution_factors=result.caution_factors,
        category_scores=result.category_scores,
    )
