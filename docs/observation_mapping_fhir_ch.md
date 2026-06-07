# Спецификация маппинга данных:

## Observation Resource -> ClickHouse

**Источник:** FHIR R4 (NDJSON, US Core Profile)  
**Цель:** Таблица `oncology.observations` (ClickHouse)  
**Версия:** 1.1

### 1. Таблица маппинга (Observation)

| FHIR Path | ClickHouse Column | Тип данных | Комментарий |
| :--- | :--- | :--- | :--- |
| `id` | `observation_id` | `UUID` | |
| `subject.reference` | `patient_id` | `UUID` | Убираем префикс 'Patient/' |
| `encounter.reference` | `encounter_id` | `Nullable(UUID)`| Убираем префикс 'Encounter/' |
| `category[0].coding[0].code`| `category` | `LowCardinality(String)`| vital-signs, laboratory, procedure |
| `code.coding[0].code` | `code` | `String` | LOINC код |
| `code.coding[0].display` | `display` | `String` | Название (например, "Glucose") |
| `valueQuantity.value` | `value_number` | `Nullable(Float64)` | Для анализов и веса |
| `valueQuantity.unit` | `unit` | `LowCardinality(String)`| mg/dL, mm, % и т.д. |
| `valueCodeableConcept.text` | `value_string` | `Nullable(String)` | Для стадий рака и текстовых ответов |
| `effectiveDateTime` | `effective_at` | `DateTime64(3, 'UTC')` | Ключ сортировки (не Nullable) |
