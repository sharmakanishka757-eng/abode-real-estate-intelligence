
import requests


# ============================================================
# ABODE - CRIME INTELLIGENCE SERVICE
# Jaipur Locality-Wise Crime News Collection
# ============================================================


GDELT_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

REQUEST_TIMEOUT = 30

# Start with a small number of localities.
# We can expand coverage after validating the source.

JAIPUR_LOCALITIES = [
    "Vaishali Nagar",
    "Mansarovar",
    "Malviya Nagar",
    "Jagatpura",
    "Jhotwara",
    "Sanganer",
    "Raja Park",
    "C-Scheme",
    "Sitapura",
    "Sodala",
    "Bani Park",
    "Pratap Nagar",
    "Tonk Road",
    "Vidhyadhar Nagar"
]

CRIME_KEYWORDS = [
    "theft",
    "robbery",
    "murder",
    "assault",
    "burglary",
    "snatching",
    "shooting",
    "firing",
    "kidnapping",
    "rape",
    "हत्या",
    "चोरी",
    "लूट",
    "पथराव",
    "मारपीट",
    "अपराध"
]


# ============================================================
# BUILD QUERY
# ============================================================

def build_crime_query(locality):

    crime_query = " OR ".join(
        f'"{keyword}"' if " " in keyword else keyword
        for keyword in CRIME_KEYWORDS
    )

    return (
        f'"{locality}" AND '
        f'({crime_query})'
    )


# ============================================================
# FETCH NEWS FOR ONE LOCALITY
# ============================================================

def fetch_locality_crime_news(
    locality,
    days=7,
    max_records=10
):

    params = {
        "query": build_crime_query(locality),
        "mode": "artlist",
        "format": "json",
        "maxrecords": max_records,
        "timespan": f"{days}d",
        "sort": "datedesc"
    }

    try:

        response = requests.get(
            GDELT_API_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "ABODE-Crime-Intelligence/0.1"
            }
        )

        # Handle rate limiting without repeated retries.
        if response.status_code == 429:

            print(
                f"Rate limit reached while searching "
                f"{locality}. Skipping this locality."
            )

            return []

        response.raise_for_status()

        data = response.json()

        articles = data.get("articles", [])

        cleaned_articles = []

        for article in articles:

            title = article.get("title")
            url = article.get("url")

            if not title or not url:
                continue

            headline = title.lower()

            # Check whether locality appears in headline.
            headline_has_locality = (
                locality.lower() in headline
            )

            # Identify crime-related headline keywords.
            headline_has_crime = any(
                keyword.lower() in headline
                for keyword in CRIME_KEYWORDS
            )

            if not headline_has_locality:
                location_status = "locality_not_confirmed"
                location_confidence = "none"

            else:
                location_status = "headline_locality_match"
                location_confidence = "low"

            cleaned_articles.append({

                "title": title,

                "url": url,

                "source": article.get("domain"),

                "source_seen_at": article.get("seendate"),

                "language": article.get("language"),

                "source_country": article.get("sourcecountry"),

                "searched_locality": locality,

                "headline_has_locality": headline_has_locality,

                "headline_has_crime_keyword": headline_has_crime,

                "location_status": location_status,

                "location_confidence": location_confidence,

                "verification_status": "unverified_news_report"

            })

        return cleaned_articles

    except requests.Timeout:

        print(f"Request timed out for {locality}.")
        return []

    except requests.RequestException as error:

        print(
            f"Request failed for {locality}: {error}"
        )

        return []

    except ValueError as error:

        print(
            f"Invalid JSON response for {locality}: {error}"
        )

        return []


# ============================================================
# FETCH NEWS FOR ALL JAIPUR LOCALITIES
# ============================================================

def fetch_jaipur_crime_news(
    days=7,
    max_records=10
):

    all_articles = []

    seen_urls = set()

    print("\nStarting Jaipur locality-wise crime collection...")

    for locality in JAIPUR_LOCALITIES:

        print(f"\nSearching: {locality}")

        articles = fetch_locality_crime_news(
            locality=locality,
            days=days,
            max_records=max_records
        )

        for article in articles:

            url = article["url"]

            # Prevent duplicate articles across localities.
            if url in seen_urls:
                continue

            seen_urls.add(url)

            # Only retain articles with crime-related headlines
            # for this initial prototype.
            if not article["headline_has_crime_keyword"]:
                continue

            all_articles.append(article)

        print(
            f"Relevant articles collected for "
            f"{locality}: "
            f"{len(articles)}"
        )

    return all_articles


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("=" * 60)
    print("       ABODE - CRIME INTELLIGENCE")
    print("       JAIPUR AREA-WISE NEWS COLLECTION")
    print("=" * 60)

    news = fetch_jaipur_crime_news(
        days=7,
        max_records=10
    )

    print("\n")
    print("=" * 60)

    print("TOTAL RELEVANT ARTICLES:", len(news))

    print("=" * 60)

    for index, article in enumerate(news, start=1):

        print(f"\nARTICLE {index}")

        print("Title:", article["title"])

        print("Searched locality:", article["searched_locality"])

        print("Source:", article["source"])

        print("Seen at:", article["source_seen_at"])

        print("Location status:", article["location_status"])

        print("Location confidence:", article["location_confidence"])

        print("Verification:", article["verification_status"])

        print("URL:", article["url"])

        print("-" * 60)

    print("\nCollection completed.")

