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

-- Таблица для диагнозов (Conditions)
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

-- Таблица для клинических наблюдений (Observations)
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

-- Таббица для визитов к врачу (Encounter)
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

-- Талбица для процедур (Procedure) - оперативные всешательства, курсы химиотерапии
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