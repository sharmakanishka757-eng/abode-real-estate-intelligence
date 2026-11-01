import csv
from pathlib import Path
from datetime import date

from environment_service.database import get_connection


CSV_PATH = Path(
    "environment_service/data/water_supply/processed/"
    "malviya_nagar_water_supply_cleaned.csv"
)

REQUIRED_COLUMNS = {
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
    "source_document",
    "source_status_date",
    "record_status",
}


def clean(value):
    value = value.strip() if value else ""
    return value if value else None


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("CSV has no column headers.")

        missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing_columns:
            raise ValueError(f"Missing CSV columns: {sorted(missing_columns)}")

        rows = list(reader)

    if len(rows) != 24:
        raise ValueError(
            f"Expected 24 pilot records, but found {len(rows)}."
        )

    source_document = "Jaipur City.pdf"
    source_date = date(2024, 3, 12)

    conn = get_connection()

    try:
        inserted = 0
        skipped = 0

        with conn.cursor() as cur:

            # Register the source document only if it does not already exist.
            cur.execute(
                """
                INSERT INTO water_supply_sources (
                    source_document,
                    issuing_department,
                    source_status_date,
                    source_type,
                    notes
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (source_document) DO NOTHING
                """,
                (
                    source_document,
                    "Public Health Engineering Department (PHED), Rajasthan",
                    source_date,
                    "historical_water_supply_schedule",
                    "Jaipur City PHED schedule. Historical source data; "
                    "24-record Malviya Nagar pilot dataset. "
                    "Not confirmation of current supply timings."
                )
            )

            cur.execute(
                """
                SELECT source_id
                FROM water_supply_sources
                WHERE source_document = %s
                """,
                (source_document,)
            )

            result = cur.fetchone()

            if result is None:
                raise RuntimeError("Could not register or find source document.")

            source_id = result[0]

            # Validate serial numbers before inserting.
            serial_numbers = [
                int(row["phed_serial_no"])
                for row in rows
            ]

            if len(serial_numbers) != len(set(serial_numbers)):
                raise ValueError("Duplicate PHED serial numbers in CSV.")

            for row in rows:
                row_source = clean(row["source_document"])

                if row_source != source_document:
                    raise ValueError(
                        f"Unexpected source document: {row_source}"
                    )

                row_date = date.fromisoformat(
                    clean(row["source_status_date"])
                )

                if row_date != source_date:
                    raise ValueError(
                        f"Unexpected source date for serial "
                        f"{row['phed_serial_no']}: {row_date}"
                    )

                cur.execute(
                    """
                    INSERT INTO water_supply_records (
                        source_id,
                        phed_serial_no,
                        district,
                        circle,
                        division,
                        uwss,
                        service_level_lpcd,
                        water_supply_zone,
                        major_areas_colonies_covered,
                        ohsr_supply,
                        direct_boosting_from_cwr,
                        direct_boosting_from_tubewells,
                        water_supply_timings,
                        duration_of_supply,
                        supply_as_per_schedule,
                        record_status
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (source_id, phed_serial_no)
                    DO NOTHING
                    RETURNING record_id
                    """,
                    (
                        source_id,
                        int(row["phed_serial_no"]),
                        clean(row["district"]),
                        clean(row["circle"]),
                        clean(row["division"]),
                        clean(row["uwss"]),
                        (
                            float(clean(row["service_level_lpcd"]))
                            if clean(row["service_level_lpcd"])
                            else None
                        ),
                        clean(row["water_supply_zone"]),
                        clean(row["major_areas_colonies_covered"]),
                        clean(row["ohsr_supply"]),
                        clean(row["direct_boosting_from_cwr"]),
                        clean(row["direct_boosting_from_tubewells"]),
                        clean(row["water_supply_timings"]),
                        clean(row["duration_of_supply"]),
                        clean(row["supply_as_per_schedule"]),
                        clean(row["record_status"]),
                    )
                )

                if cur.fetchone():
                    inserted += 1
                else:
                    skipped += 1

        conn.commit()

        print("\nWATER SUPPLY IMPORT SUCCESSFUL")
        print("--------------------------------")
        print("Source ID:", source_id)
        print("Source document:", source_document)
        print("Source date:", source_date)
        print("CSV records:", len(rows))
        print("New records inserted:", inserted)
        print("Existing records skipped:", skipped)
        print("Total records processed:", inserted + skipped)

    except Exception as error:
        conn.rollback()
        print("\nIMPORT FAILED. ALL CHANGES ROLLED BACK.")
        print(type(error).__name__, ":", error)
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
