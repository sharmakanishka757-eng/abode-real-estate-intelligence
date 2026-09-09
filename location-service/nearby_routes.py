from overpass_client import find_nearby_places
from ors_client import get_route


def find_nearby_places_with_routes(
    latitude: float,
    longitude: float,
    radius: int,
    category: str,
    limit: int,
    profile: str = "driving-car",
) -> list[dict]:
    places = find_nearby_places(
        latitude,
        longitude,
        radius,
        category,
    )

    results = []

    for place in places[:limit]:
        route = get_route(
            latitude,
            longitude,
            place["latitude"],
            place["longitude"],
            profile,
        )

        results.append(
            {
                "name": place["name"],
                "category": place["category"],
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "distance_meters": place["distance_meters"],
                "travel_distance_meters": route["distance_meters"],
                "travel_time_minutes": route["duration_minutes"],
                "profile": profile,
            }
        )

    return results