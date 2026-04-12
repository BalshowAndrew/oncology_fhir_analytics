import json
import os
from pathlib import Path

def find_stage_in_data():
    data_path = Path("./data/raw_synthea/fhir")
    
    # Используем итератор, чтобы не перегружать память
    print("--- Начинаю поиск структуры стадии в данных ---")
    
    count = 0
    for file_path in data_path.iterdir():
        if not file_path.suffix == '.json':
            continue
            
        with open(file_path, 'r') as f:
            # Читаем файл как текст для быстрого поиска
            content = f.read()
            if "Malignant neoplasm of colon" in content and "tage" in content:
                # Если нашли и рак, и слово Stage (или stage)
                bundle = json.loads(content)
                print(f"\n[!] Нашли подходящего пациента: {file_path.name}")
                
                # Ищем, в каком ресурсе и поле лежит стадия
                for entry in bundle.get('entry', []):
                    res = entry.get('resource', {})
                    res_str = json.dumps(res, indent=2)
                    
                    if "tage" in res_str:
                        print(f"\n--- Ресурс: {res.get('resourceType')} ---")
                        # Выводим кусок JSON, где есть слово stage
                        for line in res_str.split('\n'):
                            if "tage" in line:
                                print(f"Найденная строка: {line.strip()}")
                
                return # Выходим после первого найденного примера

        count += 1
        if count % 5000 == 0:
            print(f"Проверено {count} файлов...")

if __name__ == "__main__":
    find_stage_in_data()