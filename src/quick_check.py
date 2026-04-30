import os
import json
from pathlib import Path

# Учитываем твой путь fhir/
DATA_DIR = "./data/raw_synthea/fhir" 
TARGET_CODES = ["363406005", "109838007", "93761005", "254637007", "254632001"]

def fast_analyze():
    path = Path(DATA_DIR)
    if not path.exists():
        print(f"Путь {path} не найден!")
        return

    oncology_count = 0
    total_files = 0

    print("Начинаю сканирование... Это может занять пару минут для 50к файлов.")
    
    # rglob не боится длинных списков аргументов
    for file_path in path.glob("*.json"):
        if "Information" in file_path.name: # Пропускаем провайдеров
            continue
            
        total_files += 1
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                # Быстрая проверка текста перед парсингом JSON (экономит CPU)
                if any(code in content for code in TARGET_CODES):
                    oncology_count += 1
        except Exception:
            continue
        
        if total_files % 5000 == 0:
            print(f"Обработано {total_files} файлов...")

    print("\n--- Результат ---")
    print(f"Всего проанализировано пациентов: {total_files}")
    print(f"Найдено пациентов с нужными кодами: {oncology_count}")
    if total_files > 0:
        print(f"Доля целевой группы: {(oncology_count/total_files)*100:.2f}%")

if __name__ == "__main__":
    fast_analyze()