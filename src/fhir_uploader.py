import os
import json
import requests
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

FHIR_SERVER_URL = "http://localhost:8080/fhir/"
DATA_DIR = "./data/raw_synthea/fhir"
TARGET_CODES = ["363406005", "109838007", "93761005", "254637007", "254632001"]
MAX_WORKERS = 20  # Количество параллельных потоков загрузки
CONTROL_GROUP_SIZE = 5000 # Сколько здоровых пациентов добавить к 5673 больным

def upload_bundle(file_path):
    """Загружает один файл на сервер"""
    with open(file_path, 'r') as f:
        try:
            bundle = json.load(f)
            # Убеждаемся, что тип Bundle - transaction
            bundle['type'] = 'transaction'
            for entry in bundle.get('entry', []):
                res = entry.get('resource')
                if res:
                    # Настраиваем UPSERT (создать или обновить по ID)
                    entry['request'] = {
                        "method": "PUT",
                        "url": f"{res['resourceType']}/{res['id']}"
                    }
            
            response = requests.post(
                FHIR_SERVER_URL,
                json=bundle,
                headers={"Content-Type": "application/fhir+json"},
                timeout=30
            )
            return response.status_code in [200, 201]
        except Exception as e:
            return False

def prepare_file_lists():
    path = Path(DATA_DIR)
    all_files = list(path.glob("*.json"))
    
    infra_files = []
    target_files = []
    other_files = []

    print("Сортировка файлов...")
    for f in tqdm(all_files):
        if "Information" in f.name:
            infra_files.append(f)
        else:
            # Быстрая проверка на онкологию
            with open(f, 'r') as file:
                content = file.read()
                if any(code in content for code in TARGET_CODES):
                    target_files.append(f)
                else:
                    other_files.append(f)
    
    # Формируем итоговый список: инфраструктура + все больные + часть здоровых
    random.seed(123)
    selected_control = random.sample(other_files, min(len(other_files), CONTROL_GROUP_SIZE))
    
    return infra_files, target_files + selected_control

def main():
    infra_files, clinical_files = prepare_file_lists()
    
    # 1. Сначала загружаем инфраструктуру (строго последовательно)
    print(f"\nЗагрузка инфраструктуры ({len(infra_files)} файлов)...")
    for f in tqdm(infra_files):
        upload_bundle(f)

    # 2. Загружаем клинические данные (многопоточно)
    print(f"\nЗагрузка пациентов ({len(clinical_files)} файлов) в {MAX_WORKERS} потоков...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        list(tqdm(executor.map(upload_bundle, clinical_files), total=len(clinical_files)))

    print("\n--- Загрузка завершена! ---")

if __name__ == "__main__":
    main()