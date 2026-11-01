
from environment_service.database import get_connection


def add_crime_location_columns():

    query = """
    ALTER TABLE crime_incidents
    ADD COLUMN IF NOT EXISTS incident_latitude NUMERIC(9, 6);

    ALTER TABLE crime_incidents
    ADD COLUMN IF NOT EXISTS incident_longitude NUMERIC(9, 6);

    ALTER TABLE crime_incidents
    ADD COLUMN IF NOT EXISTS location_precision VARCHAR(30)
        DEFAULT 'unknown';

    ALTER TABLE crime_incidents
    ADD COLUMN IF NOT EXISTS location_verification_status VARCHAR(50)
        DEFAULT 'unverified';
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)

        connection.commit()

    print("Crime location columns added successfully!")

def verify_crime_location_columns():

    query = """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'crime_incidents'
    AND column_name IN (
        'incident_latitude',
        'incident_longitude',
        'location_precision',
        'location_verification_status'
    )
    ORDER BY column_name;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = cursor.fetchall()

    print("\nCrime location columns:")
    for column in columns:
        print(column)

    print(f"\nTotal columns verified: {len(columns)}")

def verify_existing_incident_locations():

    query = """
    SELECT
        incident_id,
        reported_location,
        searched_locality,
        incident_latitude,
        incident_longitude,
        location_precision,
        location_verification_status
    FROM crime_incidents
    ORDER BY incident_id;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            records = cursor.fetchall()

    print("\nExisting incident location details:")

    for record in records:
        print("\n------------------------------")
        print("Incident ID:", record[0])
        print("Reported location:", record[1])
        print("Searched locality:", record[2])
        print("Latitude:", record[3])
        print("Longitude:", record[4])
        print("Location precision:", record[5])
        print("Verification status:", record[6])

    print(f"\nTotal incidents checked: {len(records)}")


if __name__ == "__main__":
    add_crime_location_columns()
    verify_crime_location_columns()
    verify_existing_incident_locations()