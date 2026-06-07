# Спецификация маппинга данных:

## Prodedure Resource -> ClickHouse

**Источник:** FHIR R4 (NDJSON, US Core Profile)  
**Цель:** Таблица `oncology.procedures` (ClickHouse)  
**Версия:** 1.1

### 1. Таблица маппинга (Procedure)

| FHIR Path | ClickHouse Column | Тип данных | Описание |
| :--- | :--- | :--- | :--- |
| `id` | `procedure_id` | `UUID` | Идентификатор процедуры |
| `subject.reference` | `patient_id` | `UUID` | Ссылка на пациента |
| `encounter.reference` | `encounter_id` | `Nullable(UUID)`| Ссылка на визит |
| `code.coding[0].code` | `code` | `String` | Код процедуры (SNOMED-CT) |
| `code.coding[0].display` | `display` | `String` | Название (например, Колэктомия) |
| `performedDateTime` | `performed_at` | `DateTime64(3, 'UTC')`| Дата и время проведения |
| `status` | `status` | `LowCardinality(String)`| Статус: completed, aborted и т.д. |