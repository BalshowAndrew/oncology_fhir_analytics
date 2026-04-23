USE oncology_analytics;

-- Таблица для первичных данных пациентов
CREATE TABLE IF NOT EXISTS raw_patients (
    patient_id String,
    birth_date Date,
    death_date Nullable(Date),
    gender Enum8('male' = 1, 'female' = 2, 'other' = 3, 'unknown' = 4),
    deceased Boolean
) ENGINE = MergeTree() ORDER BY patient_id;

-- Таблица для диагнозов (Conditions)
CREATE TABLE IF NOT EXISTS raw_conditions (
    patient_id String,
    condition_id String,
    code String,
    display String,
    recorded_date DateTime,
    clinical_status String
) ENGINE = MergeTree() ORDER BY (patient_id, recorded_date);

-- Таблица для клинических наблюдений (Observations: стадии, анализы)
CREATE TABLE IF NOT EXISTS raw_observations (
    patient_id String,
    obs_id String,
    code String,
    display String,
    value_string String,
    value_quantity Float64,
    effective_date DateTime
) ENGINE = MergeTree() ORDER BY (patient_id, effective_date);