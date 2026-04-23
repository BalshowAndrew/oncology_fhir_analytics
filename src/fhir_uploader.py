import os
import json
import requests
from pathlib import Path
from tqdm import tqdm

FHIR_SERVER_URL = "http://localhost:8080/fhir/" 
DATA_DIR = "./data/raw_oncology" 

def clean_fhir_resource(obj):
    """Сургически удаляет только проблемные ссылки, не ломая ресурс."""
    if isinstance(obj, dict):
        # Если это объект-ссылка
        if 'reference' in obj and isinstance(obj['reference'], str):
            ref = obj['reference']
            # Оставляем только ссылки на Пациентов. 
            # Все остальные (Practitioner, Location) превращаем в заглушку, 
            # либо удаляем саму ссылку, чтобы не злить сервер.
            if not ref.startswith('Patient/'):
                return None # Удаляем только этот конкретный объект ссылки
        
        # Рекурсивно чистим все поля
        new_dict = {}
        for k, v in obj.items():
            cleaned_v = clean_fhir_resource(v)
            if cleaned_v is not None:
                new_dict[k] = cleaned_v
        return new_dict
    
    elif isinstance(obj, list):
        # Чистим элементы списка, удаляя те, что стали None
        return [res for res in (clean_fhir_resource(i) for i in obj) if res is not None]
    
    return obj

def upload_bundles():
    path = Path(DATA_DIR)
    files = list(path.glob("*.json"))
    
    if not files:
        print(f"Файлы не найдены!")
        return

    clinical_resources = ['Patient', 'Condition', 'Observation', 'Procedure', 'Encounter', 'MedicationRequest']

    print(f"Найдено {len(files)} пациентов. Начинаем ПРАВИЛЬНУЮ загрузку...")

    for file_path in tqdm(files, desc="Загрузка"):
        with open(file_path, 'r') as f:
            try:
                bundle = json.load(f)
                bundle['type'] = 'transaction'
                
                new_entries = []
                for entry in bundle.get('entry', []):
                    res = entry.get('resource')
                    if not res or res.get('resourceType') not in clinical_resources:
                        continue
                    
                    # ЧИСТИМ ТОЛЬКО ССЫЛКИ, а не весь ресурс!
                    res_type = res['resourceType']
                    res_id = res['id']
                    
                    # Для пациента чистка не нужна, для остальных — ювелирная
                    cleaned_res = clean_fhir_resource(res) if res_type != 'Patient' else res
                    
                    if cleaned_res:
                        entry['resource'] = cleaned_res
                        entry['request'] = {"method": "PUT", "url": f"{res_type}/{res_id}"}
                        new_entries.append(entry)
                
                bundle['entry'] = new_entries

                response = requests.post(
                    FHIR_SERVER_URL, 
                    json=bundle, 
                    headers={"Content-Type": "application/fhir+json"}
                )
                
                if response.status_code not in [200, 201]:
                    print(f"\nОшибка {response.status_code} в {file_path.name}")
            
            except Exception as e:
                print(f"\nСбой в файле {file_path.name}: {e}")

if __name__ == "__main__":
    upload_bundles()