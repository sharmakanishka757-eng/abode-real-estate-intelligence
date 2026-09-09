"""Insert demo property listings for local development and search testing.

This data is fictional and for ABODE development/demo use only.
It is not real property inventory, and prices are not market quotes.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database import Base, SessionLocal, engine
from app.models.property import Property

DEMO_NOTE = (
    "Demo listing for ABODE development and search testing. "
    "Not a real property and not an offer to sell or rent."
)

DEMO_PROPERTIES = [
    {
        "title": "2BHK apartment in Vaishali Nagar",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 18000,
        "address": "Sector 4, Vaishali Nagar",
        "city": "Jaipur",
        "latitude": 26.9126,
        "longitude": 75.7435,
        "area": 950,
        "bedrooms": 2,
        "bathrooms": 2,
        "description": f"Two-bedroom apartment near local shops. {DEMO_NOTE}",
    },
    {
        "title": "1BHK apartment in Mansarovar",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 12000,
        "address": "Agarwal Farm, Mansarovar",
        "city": "Jaipur",
        "latitude": 26.8570,
        "longitude": 75.7623,
        "area": 620,
        "bedrooms": 1,
        "bathrooms": 1,
        "description": f"Compact one-bedroom apartment. {DEMO_NOTE}",
    },
    {
        "title": "3BHK apartment in Malviya Nagar",
        "property_type": "apartment",
        "listing_type": "buy",
        "price": 4500000,
        "address": "Near Gaurav Tower, Malviya Nagar",
        "city": "Jaipur",
        "latitude": 26.8540,
        "longitude": 75.8047,
        "area": 1450,
        "bedrooms": 3,
        "bathrooms": 2,
        "description": f"Three-bedroom apartment on a mid floor. {DEMO_NOTE}",
    },
    {
        "title": "Independent house in Jagatpura",
        "property_type": "house",
        "listing_type": "buy",
        "price": 8500000,
        "address": "Mahal Road, Jagatpura",
        "city": "Jaipur",
        "latitude": 26.8372,
        "longitude": 75.8505,
        "area": 2200,
        "bedrooms": 4,
        "bathrooms": 3,
        "description": f"Independent house with parking space. {DEMO_NOTE}",
    },
    {
        "title": "3BHK house for rent in C-Scheme",
        "property_type": "house",
        "listing_type": "rent",
        "price": 35000,
        "address": "Ashok Marg, C-Scheme",
        "city": "Jaipur",
        "latitude": 26.9056,
        "longitude": 75.7938,
        "area": 1800,
        "bedrooms": 3,
        "bathrooms": 3,
        "description": f"House available on rent in C-Scheme. {DEMO_NOTE}",
    },
    {
        "title": "Residential plot on Ajmer Road",
        "property_type": "land",
        "listing_type": "buy",
        "price": 2500000,
        "address": "Ajmer Road, near Vaishali Nagar extension",
        "city": "Jaipur",
        "latitude": 26.9124,
        "longitude": 75.7200,
        "area": 1500,
        "bedrooms": None,
        "bathrooms": None,
        "description": f"Open residential plot. {DEMO_NOTE}",
    },
    {
        "title": "2BHK apartment in Pratap Nagar",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 15000,
        "address": "Sector 8, Pratap Nagar",
        "city": "Jaipur",
        "latitude": 26.8015,
        "longitude": 75.8180,
        "area": 880,
        "bedrooms": 2,
        "bathrooms": 2,
        "description": f"Two-bedroom apartment close to the main road. {DEMO_NOTE}",
    },
    {
        "title": "House on Tonk Road",
        "property_type": "house",
        "listing_type": "buy",
        "price": 6200000,
        "address": "Near Sanganer, Tonk Road",
        "city": "Jaipur",
        "latitude": 26.8500,
        "longitude": 75.8100,
        "area": 1950,
        "bedrooms": 3,
        "bathrooms": 2,
        "description": f"Independent house along Tonk Road. {DEMO_NOTE}",
    },
    {
        "title": "Studio apartment in C-Scheme",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 9000,
        "address": "Mirza Ismail Road, C-Scheme",
        "city": "Jaipur",
        "latitude": 26.9120,
        "longitude": 75.7873,
        "area": 420,
        "bedrooms": 1,
        "bathrooms": 1,
        "description": f"Small studio-style apartment. {DEMO_NOTE}",
    },
    {
        "title": "3BHK apartment for sale in Vaishali Nagar",
        "property_type": "apartment",
        "listing_type": "buy",
        "price": 5200000,
        "address": "Nemi Nagar, Vaishali Nagar",
        "city": "Jaipur",
        "latitude": 26.9158,
        "longitude": 75.7390,
        "area": 1380,
        "bedrooms": 3,
        "bathrooms": 2,
        "description": f"Three-bedroom apartment listed for purchase. {DEMO_NOTE}",
    },
]


def seed_demo_properties() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        inserted = 0
        skipped = 0
        for item in DEMO_PROPERTIES:
            exists = (
                db.query(Property)
                .filter(Property.title == item["title"])
                .first()
            )
            if exists is not None:
                skipped += 1
                continue
            db.add(Property(**item))
            inserted += 1
        db.commit()
        print(
            f"Demo seed complete. Inserted {inserted} listing(s), "
            f"skipped {skipped} existing title(s)."
        )
        print("These records are fictional demo data, not real inventory.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_properties()
