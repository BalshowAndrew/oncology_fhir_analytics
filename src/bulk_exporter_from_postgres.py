import requests
import time
import os
import json

class FHIRBulkDownloader:
    def __init__(self, polling_url, output_dir="data/bulk_export"):
        self.polling_url = polling_url
        self.output_dir = output_dir
        # Создаем папку, если её нет
        os.makedirs(self.output_dir, exist_ok=True)

    def download_files(self):
        print(f"[*] Начинаю опрос статуса экспорта...")
        
        while True:
            response = requests.get(self.polling_url)
            
            if response.status_code == 202:
                # Экспорт еще выполняется
                progress = response.headers.get("X-Progress", "выполняется")
                print(f"[...] Сервер занят: {progress}. Жду 10 секунд...")
                time.sleep(10)
                
            elif response.status_code == 200:
                # Экспорт завершен, получаем манифест
                print("[+] Экспорт завершен! Получаю список файлов.")
                manifest = response.json()
                self._process_manifest(manifest)
                break
                
            else:
                print(f"[!] Ошибка сервера: {response.status_code}")
                print(response.text)
                break

    def _process_manifest(self, manifest):
        # В манифесте лежит список ссылок на файлы в поле 'output'
        files = manifest.get("output", [])
        
        if not files:
            print("[-] В экспорте нет данных.")
            return

        print(f"[*] Найдено файлов для скачивания: {len(files)}")
        
        for item in files:
            resource_type = item.get("type")
            url = item.get("url")
            
            # Формируем имя файла (например, Patient_1.ndjson)
            # Извлекаем ID бинарного ресурса из URL для уникальности
            binary_id = url.split('/')[-1]
            filename = f"{resource_type}_{binary_id}.ndjson"
            filepath = os.path.join(self.output_dir, filename)
            
            print(f"[>] Скачиваю {resource_type} -> {filename}...")
            
            self._download_file(url, filepath)
            
        print(f"\n[OK] Все файлы сохранены в папку: {self.output_dir}")

    def _download_file(self, url, save_path):
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

if __name__ == "__main__":
    # Ваш актуальный URL
    URL = "http://localhost:8080/fhir/$export-poll-status?_jobId=6adf6333-3950-4f04-9733-8ac807f912d5"
    
    downloader = FHIRBulkDownloader(URL)
    downloader.download_files()