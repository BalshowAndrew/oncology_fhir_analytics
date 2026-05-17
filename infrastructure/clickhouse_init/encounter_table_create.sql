-- DROP TABLE IF EXISTS oncology.encounters;

CREATE TABLE oncology.encounters (
    encounter_id UUID,
    patient_id UUID,
    start_at DateTime64(3, 'UTC') DEFAULT '1900-01-01 00:00:00',
    end_at DateTime64(3, 'UTC') DEFAULT '1900-01-01 00:00:00',
    class_code LowCardinality(String),
    display String,
    reason_display Nullable(String),
    status LowCardinality(String),
    updated_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (patient_id, start_at);