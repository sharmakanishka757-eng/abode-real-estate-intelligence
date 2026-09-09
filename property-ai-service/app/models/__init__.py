"""SQLAlchemy models for the property-ai-service."""

from app.models.preferences import UserPreference
from app.models.property import Property

__all__ = ["Property", "UserPreference"]
