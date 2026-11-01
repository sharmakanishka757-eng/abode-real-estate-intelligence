import json
import os
import re
import time
import requests

from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from rapidfuzz import fuzz


# ==========================================================
# 1. CONFIGURATION
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("GNEWS_API_KEY")

GNEWS_URL = "https://gnews.io/api/v4/search"

DAYS_BACK = 30
MAX_RESULTS = 10
REQUEST_DELAY = 1.2

JAIPUR_LOCALITIES = [
    "Vaishali Nagar",
    "Mansarovar",
    "Malviya Nagar",
    "Jagatpura",
    "Jhotwara",
    "Raja Park",
    "C-Scheme",
    "Sanganer",
    "Pratap Nagar",
    "Tonk Road"
]

# Additional locations that may appear in reports.
# A mention is NOT proof of the incident location.
LOCATION_NAMES_TO_DETECT = JAIPUR_LOCALITIES + [
    "Nahargarh"
]


# ==========================================================
# 2. CRIME CLASSIFICATION
# ==========================================================

CRIME_CATEGORIES = {
    "serious_crime": [
        "murder",
        "homicide",
        "shooting",
        "firing",
        "stabbing",
        "violent attack",
        "हत्या",
        "गोलीबारी"
    ],

    "property_crime": [
        "theft",
        "burglary",
        "robbery",
        "snatching",
        "housebreaking",
        "dacoity",
        "loot",
        "चोरी",
        "लूट",
        "डकैती"
    ],

    "personal_safety": [
        "kidnapping",
        "rape",
        "sexual assault",
        "molestation",
        "physical assault",
        "beaten",
        "beating",
        "अपहरण",
        "बलात्कार",
        "छेड़छाड़"
    ],

    "vehicle_crime": [
        "vehicle theft",
        "car theft",
        "bike theft",
        "motorcycle theft",
        "stolen vehicle",
        "वाहन चोरी",
        "बाइक चोरी",
        "कार चोरी"
    ]
}


EXCLUSION_KEYWORDS = [
    "consumer commission",
    "consumer court",
    "consumer complaint",
    "mental harassment",
    "product complaint",
    "political allegation",
    "alleges rising crime"
]


# ==========================================================
# 3. SEARCH QUERY
# ==========================================================

CRIME_SEARCH_TERMS = (
    'crime OR theft OR burglary OR robbery OR murder '
    'OR assault OR kidnapping OR "vehicle theft" '
    'OR rape OR harassment'
)


# ==========================================================
# 4. DATE RANGE
# ==========================================================

def get_date_range():

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=DAYS_BACK)

    start = start_date.isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")

    end = end_date.isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")

    return start, end


# ==========================================================
# 5. CRIME CLASSIFICATION
# ==========================================================

def classify_crime(article):

    title = article.get("title") or ""
    description = article.get("description") or ""

    text = f"{title} {description}".lower()

    if any(
        keyword in text
        for keyword in EXCLUSION_KEYWORDS
    ):
        return []

    categories = []

    for category, keywords in CRIME_CATEGORIES.items():

        for keyword in keywords:

            if keyword.lower() in text:
                categories.append(category)
                break

    return categories


# ==========================================================
# 6. JAIPUR RELEVANCE FILTER
# ==========================================================

OTHER_CITIES = [
    "nashik",
    "mumbai",
    "delhi",
    "gurugram",
    "gurgaon",
    "noida",
    "rishikesh",
    "chandigarh",
    "lucknow",
    "indore",
    "bhopal",
    "jodhpur",
    "udaipur",
    "kota",
    "ajmer"
]


def is_jaipur_related(article):

    title = article.get("title") or ""
    description = article.get("description") or ""

    title_text = title.lower()
    description_text = description.lower()

    if (
        "jaipur" not in title_text
        and "jaipur" not in description_text
    ):
        return False

    if "jaipur" not in title_text:

        if any(
            city in title_text
            for city in OTHER_CITIES
        ):
            return False

    return True


# ==========================================================
# 7. FETCH NEWS FROM GNEWS
# ==========================================================

def fetch_news(query):

    if not API_KEY:
        raise ValueError(
            "GNEWS_API_KEY not found in root .env file."
        )

    if len(query) > 200:
        raise ValueError(
            f"GNews query exceeds 200 characters: {len(query)}"
        )

    start_date, end_date = get_date_range()

    headers = {
        "X-Api-Key": API_KEY
    }

    params = {
        "q": query,
        "lang": "en",
        "country": "in",
        "from": start_date,
        "to": end_date,
        "max": MAX_RESULTS,
        "sortby": "publishedAt"
    }

    response = requests.get(
        GNEWS_URL,
        headers=headers,
        params=params,
        timeout=30
    )

    if response.status_code != 200:

        print("GNews status code:", response.status_code)
        print("GNews error details:", response.text[:1000])

        response.raise_for_status()

    return response.json().get("articles", [])


# ==========================================================
# 8. LOCATION MENTION EXTRACTION
# ==========================================================

def extract_location_mentions(article):

    title = article.get("title") or ""
    description = article.get("description") or ""

    text = f"{title} {description}".lower()

    mentions = []

    for location in LOCATION_NAMES_TO_DETECT:

        if location.lower() in text:
            mentions.append(location)

    return sorted(set(mentions))


# ==========================================================
# 9. PROCESS INDIVIDUAL ARTICLES
# ==========================================================

def process_article(article, searched_locality):

    title = article.get("title") or ""
    description = article.get("description") or ""
    url = article.get("url") or ""

    if not is_jaipur_related(article):
        return None

    categories = classify_crime(article)

    if not categories:
        return None

    source = article.get("source") or {}

    return {
        "title": title,
        "description": description,
        "url": url,

        "published_at": article.get("publishedAt"),

        "source_name": source.get("name"),
        "source_url": source.get("url"),

        # Search provenance, not incident location.
        "searched_locality": searched_locality,

        # Jaipur is mentioned, but incident city is not confirmed.
        "incident_city": None,
        "incident_locality": None,
        "incident_coordinates": None,

        # Locations mentioned in the article text.
        "reported_location_mentions": (
            extract_location_mentions(article)
        ),

        "jaipur_relevance": "jaipur_mentioned_unverified",

        "crime_categories": categories,

        "location_verification": "pending",
        "verification_status": "unverified_news_report",

        "collected_at": datetime.now(
            timezone.utc
        ).isoformat()
    }


# ==========================================================
# 10. COLLECT JAIPUR CRIME NEWS
# ==========================================================

def collect_jaipur_crime_news():

    all_articles = {}

    searches = [
        (
            "Jaipur",
            f"Jaipur AND ({CRIME_SEARCH_TERMS})"
        )
    ]

    for locality in JAIPUR_LOCALITIES:

        query = (
            f'"{locality}" AND Jaipur AND '
            f'({CRIME_SEARCH_TERMS})'
        )

        searches.append((locality, query))

    print("\nABODE JAIPUR CRIME NEWS COLLECTOR")
    print("=" * 60)

    print(f"Search period: Last {DAYS_BACK} days")
    print("Total searches:", len(searches))

    for locality, query in searches:

        print(f"\nSearching: {locality}")
        print("Query length:", len(query))

        try:

            raw_articles = fetch_news(query)

            print(
                "Articles received:",
                len(raw_articles)
            )

            for article in raw_articles:

                processed = process_article(
                    article,
                    locality
                )

                if not processed:
                    continue

                url = processed["url"]

                if not url:
                    continue

                if url not in all_articles:

                    processed["matched_searches"] = [
                        locality
                    ]

                    all_articles[url] = processed

                else:

                    matches = all_articles[url][
                        "matched_searches"
                    ]

                    if locality not in matches:
                        matches.append(locality)

        except requests.exceptions.HTTPError:

            print(
                "Skipping this search due to API error."
            )

        except requests.exceptions.RequestException as error:

            print("Connection error:", error)

        time.sleep(REQUEST_DELAY)

    return list(all_articles.values())

# ==========================================================
# SAVE COLLECTED CRIME ARTICLES
# ==========================================================

def save_articles_to_json(articles):

    data_folder = Path(__file__).parent / "data"

    data_folder.mkdir(exist_ok=True)

    file_path = data_folder / "crime_articles.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            articles,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"\nArticles saved successfully: {file_path}")


# ==========================================================
# 11. INCIDENT MATCHING HELPERS
# ==========================================================

MAX_PUBLICATION_DATE_GAP_DAYS = 3

# These are distinctive clues, not generic crime words.
EVENT_CLUES = [
    "kachori",
    "scooter",
    "scooter-borne",
    "thieves",
    "two thieves",
    "two men",
    "cash bag",
    "cash",
    "chase",
    "chased",
    "snack break",
    "businessman",
    "collection agent",
    "cctv",
    "nahargarh"
]

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90
}


def get_published_datetime(article):

    published_at = article.get("published_at")

    if not published_at:
        return None

    try:
        parsed = datetime.fromisoformat(
            published_at.replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed

    except (ValueError, TypeError):
        return None


def get_article_text(article):

    title = article.get("title") or ""
    description = article.get("description") or ""

    return f"{title} {description}"


# ==========================================================
# 12. EXTRACT STOLEN AMOUNTS
# ==========================================================

def extract_money_amounts(article):

    text = get_article_text(article).lower()

    amounts = set()

    numeric_pattern = (
        r"(?:₹\s*|rs\.?\s*)?"
        r"(\d+(?:\.\d+)?)\s*"
        r"(lakh|lac|crore|cr)\b"
    )

    for match in re.finditer(numeric_pattern, text):

        value = float(match.group(1))
        unit = match.group(2)

        multiplier = (
            1000000
            if unit in ("crore", "cr")
            else 100000
        )

        amounts.add(round(value * multiplier))

    word_pattern = (
        r"\b(one|two|three|four|five|six|seven|eight|nine|ten|"
        r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
        r"seventeen|eighteen|nineteen|twenty|thirty|forty|"
        r"fifty|sixty|seventy|eighty|ninety)\s+"
        r"(lakh|lac|crore|cr)\b"
    )

    for match in re.finditer(word_pattern, text):

        number = NUMBER_WORDS[match.group(1)]
        unit = match.group(2)

        multiplier = (
            1000000
            if unit in ("crore", "cr")
            else 100000
        )

        amounts.add(number * multiplier)

    return amounts


# ==========================================================
# 13. EXTRACT NAMED PERSON CLUES
# ==========================================================



def extract_person_names(article):

    text = get_article_text(article)

    patterns = [
        r"\bnamed\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"\bidentified\s+as\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"\bidentified\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"\b(?:businessman|businesswoman|trader|victim|accused|suspect)\s+([A-Z][a-z]+)",
        r"\b(?:Mr|Mrs|Ms|Shri|Smt)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
    ]

    names = set()

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for name in matches:
            names.add(name.lower().strip())

    return names



# ==========================================================
# 14. EXTRACT DISTINCTIVE EVENT CLUES
# ==========================================================

def extract_event_clues(article):

    text = get_article_text(article).lower()

    return {
        clue
        for clue in EVENT_CLUES
        if clue in text
    }


# ==========================================================
# 15. COMPARE TWO ARTICLES
# ==========================================================

def get_incident_match_evidence(article1, article2):

    categories1 = set(
        article1.get("crime_categories", [])
    )

    categories2 = set(
        article2.get("crime_categories", [])
    )

    common_categories = categories1.intersection(
        categories2
    )

    if not common_categories:
        return None

    date1 = get_published_datetime(article1)
    date2 = get_published_datetime(article2)

    if date1 is None or date2 is None:
        return None

    date_gap = abs(
        (date1 - date2).total_seconds()
    )

    date_gap_days = date_gap / 86400

    if date_gap > MAX_PUBLICATION_DATE_GAP_DAYS * 86400:
        return None

    title1 = article1.get("title") or ""
    title2 = article2.get("title") or ""

    description1 = article1.get("description") or ""
    description2 = article2.get("description") or ""

    title_similarity = fuzz.token_set_ratio(
        title1,
        title2
    )

    description_similarity = fuzz.token_set_ratio(
        description1,
        description2
    )

    amounts1 = extract_money_amounts(article1)
    amounts2 = extract_money_amounts(article2)

    common_amounts = amounts1.intersection(amounts2)

    names1 = extract_person_names(article1)
    names2 = extract_person_names(article2)

    common_names = names1.intersection(names2)

    clues1 = extract_event_clues(article1)
    clues2 = extract_event_clues(article2)

    common_event_clues = clues1.intersection(clues2)

    # Matching evidence rules.
    amount_match = bool(common_amounts)
    person_match = bool(common_names)
    event_match = len(common_event_clues) >= 2

    is_match = False
    reasons = []

    if amount_match:
        reasons.append("matching_stolen_amount")

    if person_match:
        reasons.append("matching_named_person")

    if event_match:
        reasons.append("matching_distinctive_event_details")

    if title_similarity >= 75:
        reasons.append("strong_title_similarity")

    if description_similarity >= 60:
        reasons.append("description_similarity")

    # Rule 1: Same amount plus at least one additional clue.
    if amount_match and (
        person_match
        or event_match
        or title_similarity >= 70
        or description_similarity >= 60
    ):
        is_match = True

    # Rule 2: Same named person plus another supporting clue.
    elif person_match and (
        event_match
        or title_similarity >= 65
        or description_similarity >= 60
    ):
        is_match = True

    # Rule 3: Strong title and description similarity.
    elif (
        title_similarity >= 85
        and description_similarity >= 50
    ):
        is_match = True

    # Rule 4: Strong title match plus distinctive event clues.
    elif (
        title_similarity >= 80
        and event_match
    ):
        is_match = True

    if not is_match:
        return None

    # Conservative confidence label.
    if amount_match and (person_match or event_match):
        confidence = "high"

    elif person_match and event_match:
        confidence = "high"

    else:
        confidence = "medium"

    return {
        "match": True,
        "confidence": confidence,
        "reasons": reasons,
        "common_categories": sorted(common_categories),
        "common_amounts_inr": sorted(common_amounts),
        "common_person_names": sorted(common_names),
        "common_event_clues": sorted(common_event_clues),
        "title_similarity": round(title_similarity, 2),
        "description_similarity": round(
            description_similarity,
            2
        ),
        "publication_date_gap_days": round(
            date_gap_days,
            2
        )
    }


def is_same_potential_incident(article1, article2):

    return get_incident_match_evidence(
        article1,
        article2
    ) is not None


# ==========================================================
# 16. GROUP POTENTIAL INCIDENTS
# ==========================================================

def group_potential_incidents(articles):

    incident_groups = []

    for article in articles:

        matching_group = None
        best_evidence = None
        best_matched_article = None

        # Compare the new article with existing groups.
        for group in incident_groups:

            for existing_article in group["source_articles"]:

                evidence = get_incident_match_evidence(
                    article,
                    existing_article
                )

                if evidence:

                    if (
                        best_evidence is None
                        or evidence["confidence"] == "high"
                        and best_evidence["confidence"] != "high"
                        or (
                            evidence["confidence"]
                            == best_evidence["confidence"]
                            and evidence["title_similarity"]
                            > best_evidence["title_similarity"]
                        )
                    ):

                        matching_group = group
                        best_evidence = evidence
                        best_matched_article = existing_article
        if matching_group:

            matching_group["source_articles"].append(
                article
            )

            matching_group["matching_evidence"].append({
                "new_article_url": article["url"],
                "matched_with_url": (
                    best_matched_article["url"]
                ),
                "evidence": best_evidence
            })

        else:

            incident_groups.append({
                "source_articles": [article],
                "matching_evidence": []
            })

    # Assign IDs and aggregate information.
    for index, group in enumerate(
        incident_groups,
        start=1
    ):

        group["incident_id"] = f"INC-{index:03d}"

        group["crime_categories"] = sorted({
            category
            for article in group["source_articles"]
            for category in article.get(
                "crime_categories", []
            )
        })

        group["source_count"] = len(
            group["source_articles"]
        )

        confidences = [
            item["evidence"]["confidence"]
            for item in group["matching_evidence"]
        ]

        if "high" in confidences:
            group["match_confidence"] = "high"

        elif confidences:
            group["match_confidence"] = "medium"

        else:
            group["match_confidence"] = "not_assessed_single_source"

        group["verification_status"] = (
            "potential_incident_unverified"
        )

    return incident_groups


# ==========================================================
# 17. DISPLAY INCIDENT GROUPS
# ==========================================================

def display_results(incident_groups):

    print("\n" + "=" * 60)
    print("ABODE INCIDENT GROUPING SUMMARY")
    print("=" * 60)

    print(
        "Potential incidents:",
        len(incident_groups)
    )

    total_articles = sum(
        group["source_count"]
        for group in incident_groups
    )

    print("Original articles retained:", total_articles)

    for group in incident_groups:

        representative = group["source_articles"][0]

        print("\n" + "-" * 60)

        print("INCIDENT ID:", group["incident_id"])
        print("Title:", representative["title"])

        print(
            "Categories:",
            group["crime_categories"]
        )

        print(
            "Number of source articles:",
            group["source_count"]
        )

        print(
            "Match confidence:",
            group["match_confidence"]
        )

        print(
            "Incident city:",
            "Not independently verified"
        )

        print(
            "Incident locality:",
            "Not independently verified"
        )

        print(
            "Reported location mentions:",
            sorted({
                location
                for article in group["source_articles"]
                for location in article.get(
                    "reported_location_mentions", []
                )
            })
        )

        print(
            "Verification:",
            group["verification_status"]
        )

        print("SOURCES:")

        for index, article in enumerate(
            group["source_articles"],
            start=1
        ):

            print(f"\n  Source {index}")
            print("  Publisher:", article["source_name"])
            print("  Published:", article["published_at"])

            print(
                "  Reported locations:",
                article["reported_location_mentions"]
            )

            print("  URL:", article["url"])

        if group["matching_evidence"]:

            print("\nMATCHING EVIDENCE:")

            for evidence_item in group["matching_evidence"]:

                evidence = evidence_item["evidence"]

                print(
                    "  Confidence:",
                    evidence["confidence"]
                )

                print(
                    "  Reasons:",
                    evidence["reasons"]
                )

                print(
                    "  Common amounts (INR):",
                    evidence["common_amounts_inr"]
                )

                print(
                    "  Common names:",
                    evidence["common_person_names"]
                )

                print(
                    "  Common event clues:",
                    evidence["common_event_clues"]
                )

                print(
                    "  Title similarity:",
                    evidence["title_similarity"]
                )

                print(
                    "  Description similarity:",
                    evidence["description_similarity"]
                )


# ==========================================================
# 18. PROGRAM ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    articles = collect_jaipur_crime_news()

    # Save original collected articles
    save_articles_to_json(articles)

    incident_groups = group_potential_incidents(
        articles
    )

    display_results(incident_groups)

    print("\nIncident collection and grouping completed.")