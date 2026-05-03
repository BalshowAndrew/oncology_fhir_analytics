USE oncology_analytics;

-- Таблица для первичных данных пациентов
CREATE TABLE oncology.patients (
    patient_id UUID,
    gender LowCardinality(String),
    birth_sex Enum8('M' = 1, 'F' = 2, 'UNK' = 3),
    birth_date Nullable(Date32),                   -- Использовать Date32 для дат до 1970 года
    deceased_at Nullable(DateTime64(3, 'UTC')),    -- DateTime64 поддерживает даты с 1900 года
    is_deceased UInt8,
    race LowCardinality(String),
    ethnicity LowCardinality(String),
    city String,
    state String,
    lat Float64,
    lon Float64,
    marital_status LowCardinality(String),
    updated_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (patient_id);

-- -- Таблица для диагнозов (Conditions)
-- CREATE TABLE IF NOT EXISTS raw_conditions (
--     patient_id String,
--     condition_id String,
--     code String,
--     display String,
--     recorded_date DateTime,
--     clinical_status String
-- ) ENGINE = MergeTree() ORDER BY (patient_id, recorded_date);

-- -- Таблица для клинических наблюдений (Observations: стадии, анализы)
-- CREATE TABLE IF NOT EXISTS raw_observations (
--     patient_id String,
--     obs_id String,
--     code String,
--     display String,
--     value_string String,
--     value_quantity Float64,
--     effective_date DateTime
-- ) ENGINE = MergeTree() ORDER BY (patient_id, effective_date);