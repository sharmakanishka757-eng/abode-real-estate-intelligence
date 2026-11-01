
from environment_service.database import get_connection


def verify_crime_data():
    with get_connection() as connection:
        with connection.cursor() as cursor:

            # Count incident records.
            cursor.execute("""
                SELECT COUNT(*)
                FROM crime_incidents;
            """)
            incident_count = cursor.fetchone()[0]

            # Count original news articles.
            cursor.execute("""
                SELECT COUNT(*)
                FROM crime_sources;
            """)
            source_count = cursor.fetchone()[0]

            # Display each incident and its linked sources.
            cursor.execute("""
                SELECT
                    i.incident_id,
                    i.title,
                    i.verification_status,
                    i.match_confidence,
                    COUNT(s.source_id) AS source_count
                FROM crime_incidents i
                LEFT JOIN crime_sources s
                    ON i.incident_id = s.incident_id
                GROUP BY
                    i.incident_id,
                    i.title,
                    i.verification_status,
                    i.match_confidence
                ORDER BY i.incident_id;
            """)

            incidents = cursor.fetchall()

    print("\n========== CRIME DATABASE VERIFICATION ==========")
    print(f"Total incidents: {incident_count}")
    print(f"Total news sources: {source_count}")

    print("\nIncident details:\n")

    for incident in incidents:
        print(f"ID: {incident[0]}")
        print(f"Title: {incident[1]}")
        print(f"Status: {incident[2]}")
        print(f"Match confidence: {incident[3]}")
        print(f"Linked sources: {incident[4]}")
        print("-" * 50)


if __name__ == "__main__":
    verify_crime_data()
