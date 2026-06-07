# Спецификация маппинга данных:

## Patient Resource -> ClickHouse

**Источник:** FHIR R4 (NDJSON, US Core Profile)  
**Цель:** Таблица `oncology.patients` (ClickHouse)  
**Версия:** 1.1

### Таблица маппинга (Patient)

| FHIR Path | ClickHouse Column | Тип данных | Описание |
| :--- | :--- | :--- | :--- |
| `id` | `patient_id` | `UUID` | Идентификатор пациента (Primary Key) |
| `gender` | `gender` | `LowCardinality(String)` | Административный пол (male, female, etc.) |
| `extension[us-core-birthsex]` | `birth_sex` | `Enum8('M'=1, 'F'=2, 'UNK'=3)` | Биологический пол при рождении (US Core) |
| `birthDate` | `birth_date` | `Nullable(Date32)` | Дата рождения (поддержка дат до 1970 г.) |
| `deceasedDateTime` | `deceased_at` | `Nullable(DateTime64(3, 'UTC'))`| Дата и время смерти (точка для Survival Analysis) |
| - | `is_deceased` | `UInt8` | Флаг смерти (1 — умер, 0 — жив, вычисляется по наличию даты смерти) |
| `extension[us-core-race]` | `race` | `LowCardinality(String)` | Расовая принадлежность (поле text) |
| `extension[us-core-ethnicity]` | `ethnicity` | `LowCardinality(String)` | Этническая принадлежность (поле text) |
| `address[0].city` | `city` | `String` | Город проживания |
| `address[0].state` | `state` | `String` | Код штата проживания |
| `address[0].extension[lat]` | `lat` | `Float64` | Географическая широта (из US Core Geolocation) |
| `address[0].extension[lon]` | `lon` | `Float64` | Географическая долгота (из US Core Geolocation) |
| `maritalStatus.text` | `marital_status` | `LowCardinality(String)` | Семейное положение (текстовое описание) |