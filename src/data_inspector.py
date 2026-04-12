import json
import os
from pathlib import Path
from collections import Counter

def inspect_fhir_data():
    data_path = Path("./data/raw_synthea/fhir")
    files = list(data_path.glob("*.json"))
    
    stats = {
        "total_patients": len(files),
        "with_cancer": 0,
        "conditions": Counter(),
        "observations": Counter(),
        "procedures": Counter(),
        "stages": Counter()
    }

    # Ключевые коды (SNOMED-CT / LOINC)
    CRC_CODE = "363406005" # Malignant tumor of colon
    STAGE_CODES = ["Stage I", "Stage II", "Stage III", "Stage IV"]
    # Основные коды стадий
    STAGE_MAPPING = {
        "258215001": "Stage 1",
        "258219007": "Stage 2",
        "258224005": "Stage 3",
        "258228008": "Stage 4"
    }

    # Коды операций
    SURGERY_CODES = ["43075005", "397394009", "2615000"] # Коды резекции кишки

    for file_path in files:
        with open(file_path, 'r') as f:
            bundle = json.load(f)
            has_cancer = False
            
            for entry in bundle.get('entry', []):
                resource = entry.get('resource', {})
                res_type = resource.get('resourceType')

                # Проверка диагнозов
                if res_type == "Condition":
                    coding = resource.get('code', {}).get('coding', [{}])[0]
                    code = str(coding.get('code'))
                    display = coding.get('display', '')

                    # Ищем стадию в кодах
                    if code in STAGE_MAPPING:
                        stats["stages"][STAGE_MAPPING[code]] += 1
                    elif "stage" in display.lower():
                        stats["stages"][display] += 1
            
                    if "Malignant neoplasm of colon" in display:
                        has_cancer = True               
                # Проверка процедур (Хирургия)
                elif res_type == "Procedure":
                    display = resource.get('code', {}).get('coding', [{}])[0].get('display', 'Unknown')
                    stats["procedures"][display] += 1
                # Проверка стадирования и анализов
                elif res_type == "Observation":
                    display = resource.get('code', {}).get('coding', [{}])[0].get('display')
                    value = resource.get('valueCodeableConcept', {}).get('coding', [{}])[0].get('display')
                    
                    if "Stage" in str(value):
                        stats["stages"][value] += 1
                    else:
                        stats["observations"][display] += 1
            
            if has_cancer:
                stats["with_cancer"] += 1

    # Печать отчета
    print("=== КЛИНИЧЕСКИЙ АУДИТ ВЫБОРКИ ===")
    print(f"Всего пациентов: {stats['total_patients']}")
    print(f"Пациентов с раком толстой кишки: {stats['with_cancer']}")
    
    print("\n--- Топ процедур (Surgery) ---")
    for proc, count in stats["procedures"].most_common(5):
        print(f"- {proc}: {count}")

    print("\n--- Стадирование (для Главы 3) ---")
    for stage, count in sorted(stats["stages"].items()):
        print(f"- {stage}: {count}")

    print("\n--- Топ анализов/наблюдений ---")
    for obs, count in stats["observations"].most_common(5):
        print(f"- {obs}: {count}")

if __name__ == "__main__":
    inspect_fhir_data()
