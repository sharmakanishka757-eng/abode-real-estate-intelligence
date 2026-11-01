from fastapi import APIRouter, HTTPException, Query

from environment_service.database import get_connection


router = APIRouter(
    prefix="/water-supply",
    tags=["Water Supply Intelligence"]
)


@router.get("/sources")
def get_water_supply_sources():
    """List registered water supply source documents."""

    query = """
        SELECT
            s.source_id,
            s.source_document,
            s.issuing_department,
            s.source_status_date,
            s.source_type,
            s.source_url,
            s.imported_at,
            s.notes,
            COUNT(r.record_id) AS total_records
        FROM water_supply_sources s
        LEFT JOIN water_supply_records r
            ON s.source_id = r.source_id
        GROUP BY s.source_id
        ORDER BY s.source_status_date DESC NULLS LAST;
    """

    columns = [
        "source_id",
        "source_document",
        "issuing_department",
        "source_status_date",
        "source_type",
        "source_url",
        "imported_at",
        "notes",
        "total_records"
    ]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

    sources = [dict(zip(columns, row)) for row in rows]

    return {
        "total_sources": len(sources),
        "sources": sources
    }


@router.get("/records")
def get_water_supply_records(
    source_id: int | None = Query(default=None, ge=1),
    locality: str | None = Query(default=None, min_length=1),
    zone: str | None = Query(default=None, min_length=1),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0)
):
    """Retrieve historical PHED water supply records with optional filters."""

    conditions = []
    parameters = []

    if source_id is not None:
        conditions.append("r.source_id = %s")
        parameters.append(source_id)

    if locality:
        conditions.append(
            "r.major_areas_colonies_covered ILIKE %s"
        )
        parameters.append(f"%{locality.strip()}%")

    if zone:
        conditions.append(
            "r.water_supply_zone ILIKE %s"
        )
        parameters.append(f"%{zone.strip()}%")

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions
        else ""
    )

    count_query = f"""
        SELECT COUNT(*)
        FROM water_supply_records r
        {where_clause};
    """

    records_query = f"""
        SELECT
            r.record_id,
            r.source_id,
            r.phed_serial_no,
            r.district,
            r.circle,
            r.division,
            r.uwss,
            r.service_level_lpcd,
            r.water_supply_zone,
            r.major_areas_colonies_covered,
            r.ohsr_supply,
            r.direct_boosting_from_cwr,
            r.direct_boosting_from_tubewells,
            r.water_supply_timings,
            r.duration_of_supply,
            r.supply_as_per_schedule,
            r.record_status,
            s.source_document,
            s.source_status_date
        FROM water_supply_records r
        JOIN water_supply_sources s
            ON r.source_id = s.source_id
        {where_clause}
        ORDER BY r.phed_serial_no
        LIMIT %s OFFSET %s;
    """

    columns = [
        "record_id",
        "source_id",
        "phed_serial_no",
        "district",
        "circle",
        "division",
        "uwss",
        "service_level_lpcd",
        "water_supply_zone",
        "major_areas_colonies_covered",
        "ohsr_supply",
        "direct_boosting_from_cwr",
        "direct_boosting_from_tubewells",
        "water_supply_timings",
        "duration_of_supply",
        "supply_as_per_schedule",
        "record_status",
        "source_document",
        "source_status_date"
    ]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(count_query, parameters)
            total_records = cursor.fetchone()[0]

            cursor.execute(
                records_query,
                parameters + [limit, offset]
            )
            rows = cursor.fetchall()

    records = [dict(zip(columns, row)) for row in rows]

    return {
        "total_matching_records": total_records,
        "total_returned": len(records),
        "limit": limit,
        "offset": offset,
        "filters": {
            "source_id": source_id,
            "locality": locality,
            "zone": zone
        },
        "data_status": "historical_source_data",
        "records": records
    }


@router.get("/records/{record_id}")
def get_water_supply_record(record_id: int):
    """Retrieve one water supply record with its source information."""

    query = """
        SELECT
            r.record_id,
            r.source_id,
            r.phed_serial_no,
            r.district,
            r.circle,
            r.division,
            r.uwss,
            r.service_level_lpcd,
            r.water_supply_zone,
            r.major_areas_colonies_covered,
            r.ohsr_supply,
            r.direct_boosting_from_cwr,
            r.direct_boosting_from_tubewells,
            r.water_supply_timings,
            r.duration_of_supply,
            r.supply_as_per_schedule,
            r.record_status,
            r.created_at,
            s.source_document,
            s.issuing_department,
            s.source_status_date,
            s.source_type,
            s.source_url,
            s.notes
        FROM water_supply_records r
        JOIN water_supply_sources s
            ON r.source_id = s.source_id
        WHERE r.record_id = %s;
    """

    columns = [
        "record_id",
        "source_id",
        "phed_serial_no",
        "district",
        "circle",
        "division",
        "uwss",
        "service_level_lpcd",
        "water_supply_zone",
        "major_areas_colonies_covered",
        "ohsr_supply",
        "direct_boosting_from_cwr",
        "direct_boosting_from_tubewells",
        "water_supply_timings",
        "duration_of_supply",
        "supply_as_per_schedule",
        "record_status",
        "created_at",
        "source_document",
        "issuing_department",
        "source_status_date",
        "source_type",
        "source_url",
        "notes"
    ]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (record_id,))
            row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Water supply record not found"
        )

    return {
        "data_status": "historical_source_data",
        "record": dict(zip(columns, row))
    }


@router.get("/summary")
def get_water_supply_summary():
    """Return water supply dataset statistics."""

    query = """
        SELECT
            COUNT(DISTINCT r.record_id),
            COUNT(DISTINCT s.source_id),
            COUNT(DISTINCT r.uwss),
            COUNT(DISTINCT r.water_supply_zone),
            MIN(s.source_status_date),
            MAX(s.source_status_date)
        FROM water_supply_records r
        JOIN water_supply_sources s
            ON r.source_id = s.source_id;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

    return {
        "total_records": row[0],
        "total_sources": row[1],
        "total_uwss": row[2],
        "total_named_zones": row[3],
        "earliest_source_date": row[4],
        "latest_source_date": row[5],
        "data_status": "historical_source_data",
        "data_note": (
            "These records represent historical PHED water supply "
            "schedules. They do not confirm current supply timings, "
            "actual household availability, or water quality."
        )
    }
