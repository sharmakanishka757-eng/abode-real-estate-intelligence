
from environment_service.crime_data_processor import load_crime_articles
from environment_service.crime_news_client import (
    group_potential_incidents,
    extract_money_amounts
)
from environment_service.crime_database import (
    save_crime_incident,
    save_crime_source
)


def import_crime_data():
    # Load previously collected articles.
    # This does NOT make any GNews API requests.
    articles = load_crime_articles()

    if not articles:
        print("No crime articles found.")
        return

    print(f"Loaded {len(articles)} saved articles.")

    # Group articles that may describe the same incident.
    incident_groups = group_potential_incidents(articles)

    print(f"Found {len(incident_groups)} potential incident groups.")

    for group in incident_groups:
        source_articles = group.get("source_articles", [])

        if not source_articles:
            continue

        first_article = source_articles[0]

        # Collect reported location mentions.
        location_mentions = set()
        searched_localities = set()
        reported_amounts = set()

        for article in source_articles:
            mentions = article.get("reported_location_mentions", [])

            if isinstance(mentions, list):
                location_mentions.update(
                    str(item) for item in mentions if item
                )

            locality = article.get("searched_locality")
            if locality:
                searched_localities.add(locality)

            reported_amounts.update(extract_money_amounts(article))

        # Store an amount only when the group has one
        # unambiguous distinct amount.
        reported_amount = (
            next(iter(reported_amounts))
            if len(reported_amounts) == 1
            else None
        )

        incident = {
            "incident_id": group["incident_id"],
            "title": first_article.get("title") or "Untitled incident",
            "description": first_article.get("description"),
            "crime_categories": group.get("crime_categories", []),
            "reported_location": ", ".join(sorted(location_mentions)) or None,
            "searched_locality": ", ".join(sorted(searched_localities)) or None,

            # Do not treat publication date as incident date.
            "incident_date": None,

            # This is the earliest article publication date,
            # not a verified incident date.
            "publication_date": min(
                (
                    article.get("published_at")
                    for article in source_articles
                    if article.get("published_at")
                ),
                default=None
            ),

            "reported_amount_inr": reported_amount,
            "verification_status": group.get(
                "verification_status",
                "potential_incident_unverified"
            ),
            "match_confidence": group.get("match_confidence")
        }

        save_crime_incident(incident)

        # Save every original article as a separate source.
        for article in source_articles:
            source_url = article.get("url")

            if not source_url:
                continue

            source = {
                "incident_id": group["incident_id"],
                "source_name": article.get("source_name"),
                "source_url": source_url,
                "article_title": article.get("title"),
                "article_publication_date": article.get("published_at")
            }

            save_crime_source(source)

        print(
            f"Saved {group['incident_id']} "
            f"with {len(source_articles)} source article(s)."
        )

    print("\nCrime data import finished.")


if __name__ == "__main__":
    import_crime_data()
