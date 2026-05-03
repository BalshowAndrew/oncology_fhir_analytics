# Спецификация маппинга данных:

## Patient Resource -> ClickHouse

**Источник:** FHIR R4 (NDJSON, US Core Profile)  
**Цель:** Таблица `oncology.patients` (ClickHouse)  
**Версия:** 1.1

### 1. Основные демографические данные

| Целевая колонка (ClickHouse) | Тип данных (CH) | Путь в FHIR (JSON Path) | Логика трансформации / Комментарий |
| :--- | :--- | :--- | :--- |
| **patient_id** | `UUID` | `$.id` | Первичный ключ. Конвертация String -> UUID. |
| **gender** | `LowCardinality(String)` | `$.gender` | Административный пол (male, female, other, unknown). |
| **birth_sex** | `Enum8` | `$.extension[?(@.url=='...us-core-birthsex')].valueCode` | Биологический пол (M, F, UNK). Критичен для онкологического прогноза. |
| **birth_date** | `Nullable(Date32)` | `$.birthDate` | Поддержка дат до 1970 года. Конвертация String -> Date. |
| **deceased_at** | `Nullable(DateTime64)` | `$.deceasedDateTime` | Точка завершения наблюдения для анализа выживаемости. |
| **is_deceased** | `UInt8` | - | `1` если `deceasedDateTime` присутствует, иначе `0`. |
| **marital_status** | `LowCardinality(String)`| `$.maritalStatus.text` | Семейное положение на момент выгрузки. |

### 2. Социально-демографические детерминанты (US Core Extensions)

| Целевая колонка (ClickHouse) | Тип данных (CH) | Путь в FHIR (JSON Path) | Логика трансформации / Комментарий |
| :--- | :--- | :--- | :--- |
| **race** | `LowCardinality(String)` | `$.extension[?(@.url=='http://hl7.org/fhir/us/core/StructureDefinition/us-core-race')].extension[?(@.url=='text')].valueString` | Расовая принадлежность. |
| **ethnicity** | `LowCardinality(String)` | `$.extension[?(@.url=='http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity')].extension[?(@.url=='text')].valueString` | Этническая принадлежность. |

### 3. Географические данные (Address & Geolocation)

| Целевая колонка (ClickHouse) | Тип данных (CH) | Путь в FHIR (JSON Path) | Логика трансформации / Комментарий |
| :--- | :--- | :--- | :--- |
| **city** | `String` | `$.address[0].city` | Город проживания. |
| **state** | `String` | `$.address[0].state` | Штат (код). Используется для территориального анализа заболеваемости. |
| **lat** | `Float64` | `$.address[0].extension[?(@.url=='...geolocation')].extension[?(@.url=='latitude')].valueDecimal` | Широта. Для анализа доступности медпомощи. |
| **lon** | `Float64` | `$.address[0].extension[?(@.url=='...geolocation')].extension[?(@.url=='longitude')].valueDecimal` | Долгота. |

### 4. Служебные поля

| Целевая колонка (ClickHouse) | Тип данных (CH) | Источник | Комментарий |
| :--- | :--- | :--- | :--- |
| **updated_at** | `DateTime` | `now()` | Время фактической загрузки записи в ClickHouse. |

---

### Примечания по реализации:
1. **Обработка пустых значений:** Все даты помечены как `Nullable`, так как FHIR не гарантирует их наличие (например, для живых пациентов).
2. **Оптимизация:** Поля с низкой кардинальностью (Race, Ethnicity, Gender) используют тип `LowCardinality` для ускорения агрегационных запросов в 5-10 раз.
3. **Геокодирование:** Координаты извлекаются из расширения `geolocation` внутри первого элемента массива `address`.