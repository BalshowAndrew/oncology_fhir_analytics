-- DROP TABLE IF EXISTS oncology.procedures;

CREATE TABLE oncology.procedures (
    procedure_id UUID,
    patient_id UUID,
    encounter_id Nullable(UUID),
    reason_condition_id Nullable(UUID),
    code String,
    display String,
    performed_at DateTime64(3, 'UTC') DEFAULT '1900-01-01 00:00:00',
    end_at Nullable(DateTime64(3, 'UTC')),
    status LowCardinality(String),
    updated_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (patient_id, performed_at);