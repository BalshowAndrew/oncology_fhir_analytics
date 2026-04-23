import os
import json
import shutil
from pathlib import Path
from tqdm import tqdm

# Целевые коды первичного рака (Colon + Rectum)
TARGET_ONCO_CODES = [
    "363406005", # Malignant neoplasm of colon
    "109838007", # Overlapping malignant neoplasm of colon
    "93761005",  # Primary malignant neoplasm of colon
    "254637007", # Malignant neoplasm of rectum
    "254632001"  # Malignant neoplasm of cecum
]

# Настройки
SOURCE_DIR = "./data/raw_synthea/fhir" 
TARGET_DIR = "./data/raw_oncology" 

def filter_cohort():
    source_path = Path(SOURCE_DIR)
    target_path = Path(TARGET_DIR)
    
    if not source_path.exists():
        print(f"Ошибка: Директория {SOURCE_DIR} не найдена!")
        return

    target_path.mkdir(parents=True, exist_ok=True)
    
    all_files = list(source_path.glob("*.json"))
    print(f"Сканируем {len(all_files)} файлов...")

    count = 0
    # Используем tqdm для визуализации прогресса
    for file_path in tqdm(all_files, desc="Фильтрация"):
        try:
            with open(file_path, 'r') as f:
                bundle = json.load(f)
                is_target = False
                
                # Ищем диагноз в ресурсах Condition
                for entry in bundle.get('entry', []):
                    res = entry.get('resource')
                    if res and res.get('resourceType') == 'Condition':
                        codings = res.get('code', {}).get('coding', [])
                        # ИСПРАВЛЕНО: используем 'in TARGET_ONCO_CODES'
                        if any(c.get('code') in TARGET_ONCO_CODES for c in codings):
                            is_target = True
                            break
                
                if is_target:
                    # Копируем файл
                    shutil.copy(file_path, target_path / file_path.name)
                    count += 1
        except Exception as e:
            # Если файл битый, просто идем дальше
            continue

    print(f"\nГотово! Найдено {count} пациентов с целевыми диагнозами.")
    print(f"Целевые файлы скопированы в: {TARGET_DIR}")

if __name__ == "__main__":
    filter_cohort()