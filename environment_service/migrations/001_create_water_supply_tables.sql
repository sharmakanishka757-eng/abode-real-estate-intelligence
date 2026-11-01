CREATE TABLE IF NOT EXISTS water_supply_sources (
    source_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_document VARCHAR(255) NOT NULL UNIQUE,
    issuing_department VARCHAR(255),
    source_status_date DATE,
    source_type VARCHAR(100),
    source_url TEXT,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS water_supply_records (
    record_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_id BIGINT NOT NULL
        REFERENCES water_supply_sources(source_id)
        ON DELETE RESTRICT,

    phed_serial_no INTEGER NOT NULL,

    district VARCHAR(150),
    circle VARCHAR(150),
    division VARCHAR(150),
    uwss VARCHAR(255),

    service_level_lpcd NUMERIC(10, 2),

    water_supply_zone TEXT,
    major_areas_colonies_covered TEXT,

    ohsr_supply TEXT,
    direct_boosting_from_cwr TEXT,
    direct_boosting_from_tubewells TEXT,

    water_supply_timings TEXT,
    duration_of_supply TEXT,
    supply_as_per_schedule VARCHAR(50),

    record_status VARCHAR(100) NOT NULL DEFAULT 'historical_source_record',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_water_supply_source_record
        UNIQUE (source_id, phed_serial_no),

    CONSTRAINT valid_service_level
        CHECK (service_level_lpcd IS NULL OR service_level_lpcd >= 0)
);

CREATE INDEX IF NOT EXISTS idx_water_supply_records_source_id
    ON water_supply_records(source_id);

CREATE INDEX IF NOT EXISTS idx_water_supply_records_zone
    ON water_supply_records(water_supply_zone);

CREATE INDEX IF NOT EXISTS idx_water_supply_records_uwss
    ON water_supply_records(uwss);
