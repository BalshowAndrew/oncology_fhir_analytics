# Спецификация маппинга данных:

## Encounter Resource -> ClickHouse

**Источник:** FHIR R4 (NDJSON, US Core Profile)  
**Цель:** Таблица `oncology.encounters` (ClickHouse)  
**Версия:** 1.1

### 1. Таблица маппинга (Encounter)

| FHIR Path | ClickHouse Column | Тип данных | Описание |
| :--- | :--- | :--- | :--- |
| `id` | `encounter_id` | `UUID` | Идентификатор визита |
| `subject.reference` | `patient_id` | `UUID` | Ссылка на пациента |
| `period.start` | `start_at` | `DateTime64(3, 'UTC')`| Время начала (ключ сортировки) |
| `period.end` | `end_at` | `DateTime64(3, 'UTC')`| Время окончания |
| `class.code` | `class_code` | `LowCardinality(String)`| AMB (амбулаторно), IMP (стационар) и т.д. |
| `type[0].coding[0].display`| `display` | `String` | Описание типа визита |
| `reasonCode[0]...display`| `reason_display` | `Nullable(String)` | Причина визита (например, Скрининг) |
| `status` | `status` | `LowCardinality(String)`| finished, arrived и т.д. |