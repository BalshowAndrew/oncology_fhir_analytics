import requests
import time
import os
from datetime import datetime

FHIR_SERVER_URL = "http://localhost:8080/fhir/"
EXPORT_SAVE_DIR = "./data/fhir_export/"

def download_ndjson(output_list):
    """Скачивает сформированные файлы с сервера в локальную папку"""
    if not os.path.exists(EXPORT_SAVE_DIR):
        os.makedirs(EXPORT_SAVE_DIR)

    print(f"\n[{datetime.now()}] Начинаю скачивание файлов...")
    
    # Счетчик для одинаковых типов ресурсов (например, несколько файлов Patient)
    counters = {}

    for item in output_list:
        res_type = item['type']
        file_url = item['url']
        
        # Считаем файлы одного типа
        counters[res_type] = counters.get(res_type, 0) + 1
        file_name = f"{res_type}_{counters[res_type]}.ndjson"
        target_path = os.path.join(EXPORT_SAVE_DIR, file_name)

        print(f"Скачивание {file_name}...")
        
        response = requests.get(file_url, stream=True)
        if response.status_code == 200:
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Успешно сохранено: {target_path} ({os.path.getsize(target_path)} байт)")
        else:
            print(f"Ошибка при скачивании {file_url}: {response.status_code}")

def run_bulk_pipeline():
    # 1. Инициируем экспорт
    resource_types = "Patient,Condition,Observation,Procedure,Encounter,MedicationRequest"
    headers = {"Prefer": "respond-async", "Accept": "application/fhir+json"}
    
    print(f"[{datetime.now()}] Инициирую Bulk Export...")
    init_res = requests.get(f"{FHIR_SERVER_URL}$export?_type={resource_types}", headers=headers)
    
    if init_res.status_code != 202:
        print(f"Ошибка старта: {init_res.status_code}")
        return

    status_url = init_res.headers.get("Content-Location")
    
    # 2. Опрос готовности
    print(f"[{datetime.now()}] Ожидание формирования данных (Polling)...")
    while True:
        status_res = requests.get(status_url)
        if status_res.status_code == 200:
            print(f"[{datetime.now()}] Сервер подготовил данные.")
            output = status_res.json().get("output", [])
            # 3. Скачиваем результат
            download_ndjson(output)
            break
        elif status_res.status_code == 202:
            time.sleep(5)
            print(".", end="", flush=True)
        else:
            print(f"Ошибка мониторинга: {status_res.status_code}")
            break

if __name__ == "__main__":
    run_bulk_pipeline()