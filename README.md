Вот расширенный блок для твоего `README.md` со всеми путями и командами:

---

### Раздел 1. Подготовка и генерация данных

#### 1.1 Настройка окружения Java

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

#### 1.2 Установка и сборка Synthea

Инструмент устанавливается в директорию `tools/` проекта.

```bash
mkdir -p tools && cd tools
git clone https://github.com/synthetichealth/synthea.git
cd synthea
./gradlew build -x test
```

#### 1.3 Конфигурирование параметров экспорта (FHIR R4)

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

#### 1.4 Генерация синтетической популяции

Запуск оркестрации генерации через Python-скрипт. Скрипт настроен на возрастную группу 50-90 лет для достижения необходимой превалентности рака толстой кишки.

```bash
# Из корня проекта:
python3 src/synthea_manager.py
```
*   **Параметры запуска в скрипте:**

`-p 60000` (популяция), `-a 50-90` (возраст), `-m colorectal_cancer` (модуль).

*   **Результат:** Данные в формате JSON сохраняются в `data/raw_synthea/fhir/`.

#### 1.5 Клинический аудит и профилирование данных

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

### Раздел 2. Развертывание HAPI FHIR сервера

В связи с ограничениями доступа к публичным реестрам образов и необходимостью тонкой настройки FHIR-сервера, развертывание выполняется путем локальной сборки образа из исходных кодов.

#### 2.1 Системные требования

- **ОС:** Fedora Linux 43
- **CPU:** Intel Core i7 (рекомендуется 8+ потоков)
- **RAM:** 32 GiB (под нужды HAPI FHIR выделено 12 GiB)
- **Стек:** Docker Engine, Docker Compose, Python 3.12+, PostgreSQL 15.

#### 2.2 Подготовка окружения

Перед началом убедитесь, что Docker установлен и настроен на использование зеркал (Registry Mirrors) в `/etc/docker/daemon.json` для загрузки базовых образов (Java/Maven).

#### 2.3 Развертывание инфраструктуры

Для обеспечения модульности и контроля на каждом этапе развертывания, процесс разделен на 5 скриптов. Рекомендуется запускать их последовательно из корня проекта.

##### Шаг 1: Подготовка рабочего пространства

Скрипт создает структуру директорий для данных и логов.

```bash
mkdir -p data/raw_synthea
mkdir -p data/raw_oncology
mkdir -p data/bulk_export
mkdir -p infrastructure/hapi-fhir-jpaserver-starter
```

##### Шаг 2: Получение исходного кода сервера

Загрузка актуальной версии HAPI FHIR JPA Starter с GitHub.

```bash
# Клонирование репозитория HAPI FHIR
git clone https://github.com/hapifhir/hapi-fhir-jpaserver-starter.git \
    infrastructure/hapi-fhir-jpaserver-starter
cd infrastructure/hapi-fhir-jpaserver-starter
git checkout master # Или конкретный тег
```

##### Шаг 3: Локальная сборка Docker-образа

Сборка образа из исходников. Это решает проблему блокировок Docker Hub и позволяет контролировать версию Java и Maven.

```bash
echo "--- Сборка локального образа (это займет 5-10 минут) ---"
cd infrastructure/hapi-fhir-jpaserver-starter
docker build -t hapi-fhir-local:latest . # Точка в конце обязательна - она указывает на текущий контекст сборки
```

##### Шаг 4: Запуск контейнеров

Запуск связки PostgreSQL + HAPI FHIR с использованием конфигурации из `.env`.

```bash
# Запуск PostgreSQL и HAPI FHIR
cd infrastructure
# Используем docker-compose для поднятия всей связки
docker compose up -d
```

##### Шаг 5: Верификация и проверка работы сервера

Проверка статуса контейнеров и доступности FHIR API.

```bash
# Проверка статуса системы
docker ps --filter "name=hapi"
# Проверка логов сервера (последние 5 строк)
docker logs --tail 5 hapi-fhir-server
# 1. Проверка доступности FHIR API
curl -i http://localhost:8080/fhir/metadata
# 2. Проверка счетчика пациентов (после загрузки)
curl http://localhost:8080/fhir/Patient?_summary=count
```
---

### Раздел 3. Формирование когорты и загрузка данных (ETL)

Для обучения прогностической модели из общей популяции в 60 000 синтетических пациентов была выделена целевая когорта пациентов с диагнозами колоректального рака. Это позволило повысить качество данных и оптимизировать производительность системы.

#### 3.1 Анализ и инспекция кодов

Перед фильтрацией был проведен аудит исходных данных для выявления всех используемых кодов SNOMED-CT, относящихся к опухолям толстой кишки.

```bash
# Скрипт анализирует первые 1000 файлов для выявления паттернов кодирования
python3 src/inspect_codes.py
```

#### 3.2 Селективная фильтрация когорты

На основе выявленных кодов (363406005, 109838007, 93761005, 254637007, 254632001) выполняется скрипт, который переносит релевантные истории болезни в отдельную директорию.

```bash
# Сканирование всех 60 000 файлов и отбор целевых пациентов
python3 src/cohort_filter.py
```

#### 3.3 Клиническая загрузка в FHIR-сервер

Загрузка отобранных данных выполняется в режиме **Transaction Bundle**. Скрипт производит «клиническую очистку» данных: сохраняет связи «Ресурс -> Пациент», но удаляет административные ссылки (на врачей и организации), которые могут вызвать конфликты ссылочной целостности на пустом сервере.

```bash
# Загрузка ресурсов Patient, Condition, Observation, Procedure и Encounter
python3 src/fhir_uploader.py
# Проверка результатов загрузки данных
curl -s http://localhost:8080/fhir/Patient?_summary=count | grep total # "total": 2905
curl -s http://localhost:8080/fhir/Condition?_summary=count | grep total # "total": 9694
```
Благодаря предварительной фильтрации, объем загружаемых данных сокращен с 61 000 до ~3 000 пациентов, что позволило сократить время подготовки базы данных с 20 часов до 30 минут без потери клинической значимости выборки.

---


