
import json
from pathlib import Path

file_path = (
    Path(__file__).parent
    / "data"
    / "crime_articles.json"
)

if not file_path.exists():
    print("Crime articles file not found.")
else:

    with open(file_path, "r", encoding="utf-8") as file:
        articles = json.load(file)

    print("CRIME DATASET SUMMARY")
    print("=" * 40)

    print("Total articles:", len(articles))

    for index, article in enumerate(articles, start=1):
        print(f"\nArticle {index}")
        print("Title:", article.get("title"))
        print("Source:", article.get("source_name"))
        print("Published:", article.get("published_at"))
