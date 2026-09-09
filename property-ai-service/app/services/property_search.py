"""SQLAlchemy filters for property search."""

from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from app.models.property import Property
from app.schemas.property import PropertySearchQuery


def apply_property_filters(query: Query, filters: PropertySearchQuery) -> Query:
    """Apply optional search filters in the database, not in Python."""
    if filters.city and filters.city.strip():
        query = query.filter(func.lower(Property.city) == filters.city.strip().lower())

    if filters.listing_type is not None:
        query = query.filter(Property.listing_type == filters.listing_type.value)

    if filters.property_type is not None:
        query = query.filter(Property.property_type == filters.property_type.value)

    if filters.min_price is not None:
        query = query.filter(Property.price >= filters.min_price)

    if filters.max_price is not None:
        query = query.filter(Property.price <= filters.max_price)

    if filters.min_bedrooms is not None:
        query = query.filter(Property.bedrooms >= filters.min_bedrooms)

    if filters.max_bedrooms is not None:
        query = query.filter(Property.bedrooms <= filters.max_bedrooms)

    if filters.min_area is not None:
        query = query.filter(Property.area >= filters.min_area)

    if filters.max_area is not None:
        query = query.filter(Property.area <= filters.max_area)

    return query


def search_properties(
    db: Session,
    filters: PropertySearchQuery,
) -> tuple[int, list[Property]]:
    """Return (total matching rows, one page of results)."""
    query = apply_property_filters(db.query(Property), filters)
    total = query.count()
    results = (
        query.order_by(Property.id)
        .offset(filters.skip)
        .limit(filters.limit)
        .all()
    )
    return total, results
