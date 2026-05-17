-- DROP TABLE IF EXISTS oncology.observations;

CREATE TABLE oncology.observations (
    observation_id UUID,
    patient_id UUID,
    encounter_id Nullable(UUID),
    category LowCardinality(String),
    code String,
    display String,
    value_number Nullable(Float64),
    value_string Nullable(String),
    unit LowCardinality(String),
    effective_at DateTime64(3, 'UTC') DEFAULT '1900-01-01 00:00:00',
    updated_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (patient_id, effective_at);