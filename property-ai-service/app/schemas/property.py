"""Request and response schemas for property listings."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PropertyType(str, Enum):
    apartment = "apartment"
    house = "house"
    land = "land"


class ListingType(str, Enum):
    buy = "buy"
    rent = "rent"


class PropertyCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    property_type: PropertyType
    listing_type: ListingType
    price: Decimal = Field(..., ge=0)
    address: str = Field(..., min_length=1, max_length=500)
    city: str = Field(..., min_length=1, max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    area: Optional[Decimal] = Field(default=None, ge=0)
    bedrooms: Optional[int] = Field(default=None, ge=0)
    bathrooms: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = None


class PropertyUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    property_type: Optional[PropertyType] = None
    listing_type: Optional[ListingType] = None
    price: Optional[Decimal] = Field(default=None, ge=0)
    address: Optional[str] = Field(default=None, min_length=1, max_length=500)
    city: Optional[str] = Field(default=None, min_length=1, max_length=100)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    area: Optional[Decimal] = Field(default=None, ge=0)
    bedrooms: Optional[int] = Field(default=None, ge=0)
    bathrooms: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = None


class PropertyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    property_type: PropertyType
    listing_type: ListingType
    price: Decimal
    address: str
    city: str
    latitude: float
    longitude: float
    area: Optional[Decimal] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime


class PropertySearchQuery(BaseModel):
    city: Optional[str] = None
    listing_type: Optional[ListingType] = None
    property_type: Optional[PropertyType] = None
    min_price: Optional[Decimal] = Field(default=None, ge=0)
    max_price: Optional[Decimal] = Field(default=None, ge=0)
    min_bedrooms: Optional[int] = Field(default=None, ge=0)
    max_bedrooms: Optional[int] = Field(default=None, ge=0)
    min_area: Optional[Decimal] = Field(default=None, ge=0)
    max_area: Optional[Decimal] = Field(default=None, ge=0)
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class PropertySearchResponse(BaseModel):
    total: int
    skip: int
    limit: int
    results: list[PropertyResponse]
