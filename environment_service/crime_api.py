
from fastapi import APIRouter, HTTPException, Query

from environment_service.database import get_connection


router = APIRouter(prefix="/crime", tags=["Crime Intelligence"])


@router.get("/incidents")
def get_crime_incidents(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0)
):
    """Retrieve potential crime incidents with their source counts."""

    query = """
        SELECT
            i.incident_id,
            i.title,
            i.description,
            i.crime_categories,
            i.reported_location,
            i.searched_locality,
            i.incident_date,
            i.publication_date,
            i.reported_amount_inr,
            i.verification_status,
            i.match_confidence,
            COUNT(s.source_id) AS source_count
        FROM crime_incidents i
        LEFT JOIN crime_sources s
            ON i.incident_id = s.incident_id
        GROUP BY i.incident_id
        ORDER BY i.publication_date DESC NULLS LAST
        LIMIT %s OFFSET %s;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (limit, offset))
            rows = cursor.fetchall()

    columns = [
        "incident_id",
        "title",
        "description",
        "crime_categories",
        "reported_location",
        "searched_locality",
        "incident_date",
        "publication_date",
        "reported_amount_inr",
        "verification_status",
        "match_confidence",
        "source_count"
    ]

    incidents = [
        dict(zip(columns, row))
        for row in rows
    ]

    return {
        "total_returned": len(incidents),
        "limit": limit,
        "offset": offset,
        "incidents": incidents
    }


@router.get("/incidents/{incident_id}")
def get_crime_incident(incident_id: str):
    """Retrieve one potential incident and its original news sources."""

    incident_query = """
        SELECT
            incident_id,
            title,
            description,
            crime_categories,
            reported_location,
            searched_locality,
            incident_date,
            publication_date,
            reported_amount_inr,
            verification_status,
            match_confidence
        FROM crime_incidents
        WHERE incident_id = %s;
    """

    source_query = """
        SELECT
            source_name,
            source_url,
            article_title,
            article_publication_date
        FROM crime_sources
        WHERE incident_id = %s
        ORDER BY article_publication_date DESC NULLS LAST;
    """

    incident_columns = [
        "incident_id",
        "title",
        "description",
        "crime_categories",
        "reported_location",
        "searched_locality",
        "incident_date",
        "publication_date",
        "reported_amount_inr",
        "verification_status",
        "match_confidence"
    ]

    source_columns = [
        "source_name",
        "source_url",
        "article_title",
        "article_publication_date"
    ]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(incident_query, (incident_id,))
            incident_row = cursor.fetchone()

            if incident_row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Crime incident not found"
                )

            cursor.execute(source_query, (incident_id,))
            source_rows = cursor.fetchall()

    incident = dict(zip(incident_columns, incident_row))

    incident["sources"] = [
        dict(zip(source_columns, row))
        for row in source_rows
    ]

    return incident


@router.get("/summary")
def get_crime_summary():
    """Return incident counts by verification status and crime category."""

    status_query = """
        SELECT verification_status, COUNT(*)
        FROM crime_incidents
        GROUP BY verification_status
        ORDER BY verification_status;
    """

    category_query = """
        SELECT category, COUNT(DISTINCT incident_id)
        FROM crime_incidents,
             UNNEST(crime_categories) AS category
        GROUP BY category
        ORDER BY category;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(status_query)
            status_rows = cursor.fetchall()

            cursor.execute(category_query)
            category_rows = cursor.fetchall()

    return {
        "total_incidents": sum(row[1] for row in status_rows),
        "by_verification_status": {
            row[0]: row[1] for row in status_rows
        },
        "by_crime_category": {
            row[0]: row[1] for row in category_rows
        },
        "data_note": (
            "Counts represent collected potential incident reports, "
            "not independently verified crime statistics."
        )
    }
