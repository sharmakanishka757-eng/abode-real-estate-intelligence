
from environment_service.database import get_connection


def create_crime_tables():
    """Create crime incident and news source tables."""

    create_incidents_table = """
    CREATE TABLE IF NOT EXISTS crime_incidents (
        incident_id VARCHAR(50) PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        crime_categories TEXT[],
        reported_location TEXT,
        searched_locality TEXT,
        incident_date DATE,
        publication_date TIMESTAMPTZ,
        reported_amount_inr NUMERIC(15, 2),
        verification_status VARCHAR(50)
            DEFAULT 'unverified_news_report',
        match_confidence VARCHAR(50),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """

    create_sources_table = """
    CREATE TABLE IF NOT EXISTS crime_sources (
        source_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        incident_id VARCHAR(50) NOT NULL,
        source_name TEXT,
        source_url TEXT NOT NULL UNIQUE,
        article_title TEXT,
        article_publication_date TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_crime_incident
            FOREIGN KEY (incident_id)
            REFERENCES crime_incidents(incident_id)
            ON DELETE CASCADE
    );
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(create_incidents_table)
            cursor.execute(create_sources_table)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_crime_incident_date
                ON crime_incidents(incident_date);
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_crime_publication_date
                ON crime_incidents(publication_date);
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_crime_searched_locality
                ON crime_incidents(searched_locality);
            """)
            cursor.execute("""
                ALTER TABLE crime_incidents
                ALTER COLUMN match_confidence TYPE VARCHAR(50);
            """)
        connection.commit()

    print("Crime database tables created successfully!")


def verify_crime_tables():
    """Verify that the required crime tables exist."""

    query = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('crime_incidents', 'crime_sources')
    ORDER BY table_name;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            tables = cursor.fetchall()

    print("Tables found:", tables)

    return tables


def save_crime_incident(incident):
    """Insert or update a potential crime incident."""

    query = """
    INSERT INTO crime_incidents (
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
    )
    VALUES (
        %(incident_id)s,
        %(title)s,
        %(description)s,
        %(crime_categories)s,
        %(reported_location)s,
        %(searched_locality)s,
        %(incident_date)s,
        %(publication_date)s,
        %(reported_amount_inr)s,
        %(verification_status)s,
        %(match_confidence)s
    )
    ON CONFLICT (incident_id)
    DO UPDATE SET
        title = EXCLUDED.title,
        description = EXCLUDED.description,
        crime_categories = EXCLUDED.crime_categories,
        reported_location = EXCLUDED.reported_location,
        searched_locality = EXCLUDED.searched_locality,
        incident_date = EXCLUDED.incident_date,
        publication_date = EXCLUDED.publication_date,
        reported_amount_inr = EXCLUDED.reported_amount_inr,
        verification_status = EXCLUDED.verification_status,
        match_confidence = EXCLUDED.match_confidence,
        updated_at = CURRENT_TIMESTAMP;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, incident)

        connection.commit()


def save_crime_source(source):
    """Save an original news article linked to an incident."""

    query = """
    INSERT INTO crime_sources (
        incident_id,
        source_name,
        source_url,
        article_title,
        article_publication_date
    )
    VALUES (
        %(incident_id)s,
        %(source_name)s,
        %(source_url)s,
        %(article_title)s,
        %(article_publication_date)s
    )
    ON CONFLICT (source_url)
    DO UPDATE SET
        source_name = EXCLUDED.source_name,
        article_title = EXCLUDED.article_title,
        article_publication_date = EXCLUDED.article_publication_date;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, source)

        connection.commit()


if __name__ == "__main__":
    create_crime_tables()
    verify_crime_tables()
