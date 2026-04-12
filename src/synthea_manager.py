import subprocess
import os
from pathlib import Path

def run_generation(count=1000):
    # Используем абсолютные пути, чтобы не зависеть от того, откуда запущен скрипт
    base_dir = Path(__file__).resolve().parent.parent
    synthea_path = base_dir / "tools" / "synthea"
    output_path = base_dir / "data" / "raw_synthea"
    
    # Создаем папку, если её нет
    output_path.mkdir(parents=True, exist_ok=True)

    command = [
        "./run_synthea", 
        "-p", str(count),
        "-a", "50-90",
        "-m", "colorectal_cancer", # Твой специфичный модуль
        f"--exporter.baseDirectory={output_path}"
    ]
    
    print(f"--- Запуск генерации {count} пациентов ---")
    
    try:
        # Важно: cwd=synthea_path, чтобы ./run_synthea нашел свои jar-файлы
        subprocess.run(command, cwd=synthea_path, check=True)
        print(f"--- Готово! Данные здесь: {output_path} ---")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при генерации: {e}")

if __name__ == "__main__":
    run_generation(50000) # Для теста начни с небольшого числа
