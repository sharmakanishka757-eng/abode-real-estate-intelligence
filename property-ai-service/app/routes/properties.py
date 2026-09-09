"""REST routes for property listings."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.property import Property
from app.schemas.property import (
    PropertyCreate,
    PropertyResponse,
    PropertySearchQuery,
    PropertySearchResponse,
    PropertyUpdate,
)
from app.services.property_search import search_properties

router = APIRouter(tags=["properties"])


@router.post(
    "/properties",
    response_model=PropertyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_property(payload: PropertyCreate, db: Session = Depends(get_db)) -> Property:
    property_item = Property(**payload.model_dump())
    db.add(property_item)
    db.commit()
    db.refresh(property_item)
    return property_item


@router.get("/properties", response_model=list[PropertyResponse])
def list_properties(db: Session = Depends(get_db)) -> list[Property]:
    return db.query(Property).order_by(Property.id).all()


@router.get("/properties/search", response_model=PropertySearchResponse)
def search_property_listings(
    filters: Annotated[PropertySearchQuery, Query()],
    db: Session = Depends(get_db),
) -> PropertySearchResponse:
    total, results = search_properties(db, filters)
    return PropertySearchResponse(
        total=total,
        skip=filters.skip,
        limit=filters.limit,
        results=results,
    )


@router.get("/properties/{property_id}", response_model=PropertyResponse)
def get_property(property_id: int, db: Session = Depends(get_db)) -> Property:
    property_item = db.query(Property).filter(Property.id == property_id).first()
    if property_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} was not found.",
        )
    return property_item


@router.put("/properties/{property_id}", response_model=PropertyResponse)
def update_property(
    property_id: int,
    payload: PropertyUpdate,
    db: Session = Depends(get_db),
) -> Property:
    property_item = db.query(Property).filter(Property.id == property_id).first()
    if property_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} was not found.",
        )

    updates = payload.model_dump(exclude_unset=True)
    for field_name, value in updates.items():
        setattr(property_item, field_name, value)

    db.commit()
    db.refresh(property_item)
    return property_item


@router.delete("/properties/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(property_id: int, db: Session = Depends(get_db)) -> None:
    property_item = db.query(Property).filter(Property.id == property_id).first()
    if property_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} was not found.",
        )

    db.delete(property_item)
    db.commit()
