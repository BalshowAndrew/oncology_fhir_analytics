Вот расширенный блок для твоего `README.md` со всеми путями и командами:

---

### Инструкция по подготовке и генерации данных

#### 1. Настройка окружения Java

Первоначально на моей ОС (Fedora 43) была установлена Java 25. Но для корректной работы генератора Synthea требуется Java 21 (LTS).

```bash
# Установка JDK 21 (инструменты разработки)
sudo dnf install java-21-openjdk-devel -y

# Переключение версии Java (выберите номер, соответствующий java-21-openjdk)
sudo alternatives --config java
sudo alternatives --config javac

# Проверка версии
java -version  # Ожидается: openjdk version "21.x.x"
```

#### 2. Установка и сборка Synthea

Инструмент устанавливается в директорию `tools/` проекта.

```bash
mkdir -p tools && cd tools
git clone https://github.com/synthetichealth/synthea.git
cd synthea
./gradlew build -x test
```

#### 3. Конфигурирование параметров экспорта (FHIR R4)

Отредактируйте файл `tools/synthea/src/main/resources/synthea.properties` для соответствия спецификации проекта:

```properties
# Путь: tools/synthea/src/main/resources/synthea.properties
exporter.base_version = R4
exporter.fhir.export = true
exporter.fhir.transaction_bundle = true
exporter.ccda.export = false
exporter.csv.export = false
exporter.text.export = false
```

#### 4. Генерация синтетической популяции

Запуск оркестрации генерации через Python-скрипт. Скрипт настроен на возрастную группу 50-90 лет для достижения необходимой превалентности рака толстой кишки.

```bash
# Из корня проекта:
python3 src/synthea_manager.py
```
*   **Параметры запуска в скрипте:**

`-p 60000` (популяция), `-a 50-90` (возраст), `-m colorectal_cancer` (модуль).

*   **Результат:** Данные в формате JSON сохраняются в `data/raw_synthea/fhir/`.

#### 5. Клинический аудит и профилирование данных

Проверка качества выборки и поиск диагностических меток (стадий) перед загрузкой в БД.

```bash
# Запуск инспектора (проверка структуры ресурсов и кодов SNOMED-CT)
python3 src/data_inspector.py
```
**Результаты анализа выборки:**
*   Общая популяция: ~61 000 пациентов.
*   Целевая группа (Рак толстой кишки): 1141 пациент.
*   Доступные маркеры: `Condition` (Primary malignant neoplasm of colon), `Procedure` (Chemotherapy, Colectomy), `Observation` (Hemoglobin, Pain score).

---

### Развертывание среды:


