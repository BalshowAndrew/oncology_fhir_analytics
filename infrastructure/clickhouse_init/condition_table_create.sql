-- DROP TABLE IF EXISTS oncology.conditions;

CREATE TABLE oncology.conditions (
    condition_id UUID,
    patient_id UUID,
    encounter_id Nullable(UUID),
    code String,
    display String,
    clinical_status LowCardinality(String),
    verification_status LowCardinality(String),
    onset_at DateTime64(3, 'UTC') DEFAULT '1900-01-01 00:00:00', 
    abatement_at Nullable(DateTime64(3, 'UTC')),
    recorded_at Nullable(DateTime64(3, 'UTC')),
    updated_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (patient_id, onset_at);