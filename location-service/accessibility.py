from ors_client import get_route


ACCESSIBILITY_CATEGORIES = [
    "school",
    "hospital",
    "police",
    "bank",
    "atm",
    "college",
    "restaurant",
    "park",
]


def build_accessibility_data(
    nearby_places: list[dict],
    latitude: float,
    longitude: float,
) -> dict:
    """
    Build accessibility information for the nearest place
    in each accessibility category.

    For each category:
    - Find the nearest place using straight-line distance.
    - Calculate road distance and driving time using OpenRouteService.
    """

    accessibility_data = {}

    for category in ACCESSIBILITY_CATEGORIES:

        category_places = [
            place
            for place in nearby_places
            if place.get("category") == category
        ]

        if category_places:

            nearest_place = min(
                category_places,
                key=lambda place: place["distance_meters"],
            )

            route = get_route(
                latitude,
                longitude,
                nearest_place["latitude"],
                nearest_place["longitude"],
                "driving-car",
            )

            accessibility_data[category] = {
                "nearest_distance_meters": nearest_place[
                    "distance_meters"
                ],
                "nearest_travel_distance_meters": route[
                    "distance_meters"
                ],
                "nearest_travel_time_minutes": route[
                    "duration_minutes"
                ],
            }

        else:

            accessibility_data[category] = {
                "nearest_distance_meters": None,
                "nearest_travel_distance_meters": None,
                "nearest_travel_time_minutes": None,
            }

    return accessibility_data