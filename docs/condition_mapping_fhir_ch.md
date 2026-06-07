# Спецификация маппинга данных:

## Condition Resource -> ClickHouse

**Источник:** FHIR R4 (NDJSON, US Core Profile)  
**Цель:** Таблица `oncology.conditions` (ClickHouse)  
**Версия:** 1.1

### 1. Таблица маппинга (FHIR Condition -> ClickHouse)

| FHIR Path | ClickHouse Column | Тип данных | Описание |
| :--- | :--- | :--- | :--- |
| `id` | `condition_id` | `UUID` | Идентификатор записи |
| `subject.reference` | `patient_id` | `UUID` | Ссылка на пациента (без префикса Patient/) |
| `encounter.reference` | `encounter_id` | `UUID` (Nullable) | Ссылка на визит (без префикса Encounter/) |
| `code.coding[0].code` | `code` | `String` | Код SNOMED-CT |
| `code.coding[0].display` | `display` | `String` | Текстовое описание диагноза |
| `clinicalStatus.coding[0].code`| `clinical_status` | `LowCardinality(String)`| Статус: active, resolved и т.д. |
| `verificationStatus...code` | `verification_status`| `LowCardinality(String)`| Статус подтверждения: confirmed |
| `onsetDateTime` | `onset_at` | `Nullable(DateTime64(3, 'UTC'))`| Дата и время начала заболевания |
| `abatementDateTime` | `abatement_at` | `Nullable(DateTime64(3, 'UTC'))`| Дата и время завершения/ремиссии |
| `recordedDate` | `recorded_at` | `Nullable(DateTime64(3, 'UTC'))`| Дата записи в систему |

---

