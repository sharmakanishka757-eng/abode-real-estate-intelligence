
import json
import re
from pathlib import Path
from datetime import datetime


# Dataset location
DATA_FILE = (
    Path(__file__).parent
    / "data"
    / "crime_articles.json"
)


def load_crime_articles():
    """Load collected crime news articles from JSON."""

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Crime dataset not found: {DATA_FILE}"
        )

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        articles = json.load(file)

    if not isinstance(articles, list):
        raise ValueError(
            "Crime dataset must contain a list of articles."
        )

    print(f"Successfully loaded {len(articles)} articles.")

    return articles


def extract_basic_information(article):
    """Extract basic information from an article."""

    return {
        "title": article.get("title"),
        "description": article.get("description"),
        "published_at": article.get("published_at"),
        "source_name": article.get("source_name"),
        "source_url": article.get("url"),
        "searched_locality": article.get("searched_locality"),
        "crime_categories": article.get("crime_categories", []),
        "reported_location_mentions": article.get(
            "reported_location_mentions", []
        ),
        "verification_status": article.get(
            "verification_status", "unknown"
        )
    }


def extract_money_amounts(article):
    """Extract monetary amounts expressed in lakh or crore."""

    text = " ".join([
        article.get("title") or "",
        article.get("description") or ""
    ])

    patterns = [
        r"(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)\s*(lakh|lac|crore|cr)\b",
        r"([\d,]+(?:\.\d+)?)\s*(lakh|lac|crore|cr)\b"
    ]

    amounts = set()

    for pattern in patterns:
        matches = re.findall(
            pattern, text, re.IGNORECASE
        )

        for number, unit in matches:
            value = float(number.replace(",", ""))
            unit = unit.lower()

            if unit in ("lakh", "lac"):
                value *= 100000
            elif unit in ("crore", "cr"):
                value *= 10000000

            amounts.add(int(value))

    return sorted(amounts)


def extract_incident_date(article):
    """
    Extract a possible date mentioned in the article.

    This is only a candidate date, not a verified
    incident date.
    """

    text = " ".join([
        article.get("title") or "",
        article.get("description") or ""
    ])

    date_patterns = [
        r"\b\d{1,2}\s+"
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{4}\b",

        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2},?\s+\d{4}\b",

        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b"
    ]

    formats = [
        "%d %B %Y",
        "%B %d, %Y",
        "%B %d %Y",
        "%d/%m/%Y",
        "%d-%m-%Y"
    ]

    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            date_text = match.group()

            for date_format in formats:
                try:
                    return datetime.strptime(
                        date_text, date_format
                    ).date().isoformat()
                except ValueError:
                    continue

    return None


if __name__ == "__main__":

    articles = load_crime_articles()

    print("\nEXTRACTED INCIDENT INFORMATION")
    print("=" * 45)

    for index, article in enumerate(articles, start=1):

        incident = extract_basic_information(article)

        amounts = extract_money_amounts(article)

        possible_incident_date = extract_incident_date(article)

        print(f"\nArticle {index}")
        print("Title:", incident["title"])
        print("Category:", incident["crime_categories"])
        print("Source:", incident["source_name"])
        print("Locations:", incident["reported_location_mentions"])
        print("Reported amounts (INR):", amounts)
        print("Verification:", incident["verification_status"])
        print("Publication date:", incident["published_at"])
        print("Possible incident date:", possible_incident_date)
