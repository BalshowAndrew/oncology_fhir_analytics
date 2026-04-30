import subprocess
from pathlib import Path

def run_generation(total_population=5000):
    base_dir = Path(__file__).resolve().parent.parent
    synthea_path = base_dir / "tools" / "synthea"
    output_path = base_dir / "data" / "raw_synthea"
    
    output_path.mkdir(parents=True, exist_ok=True)

    # Упрощенная команда: без фильтра -k, но с модулем онкологии
    command = [
        "./run_synthea", 
        "-p", str(total_population), # Генерируем 5000 человек
        "-a", "45-90",               # Возраст риска
        "-m", "colorectal_cancer",   # Обязательный модуль
        "-s", "123",                 # Seed для воспроизводимости
        "Massachusetts",
    ]
    
    command.extend([
        f"--exporter.baseDirectory={output_path}",
        "--exporter.fhir.export=true",
        "--exporter.hospital.fhir.export=true",
        "--exporter.practitioner.fhir.export=true",
        "--exporter.fhir.transaction_bundle=true",
        "--exporter.years_of_history=0",
        "--generate.append_numbers_to_person_names=false"
    ])

    print(f"--- Запуск генерации {total_population} человек ---")
    
    try:
        subprocess.run(command, cwd=synthea_path, check=True)
        print(f"--- Успех! Проверь папку: {output_path} ---")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    run_generation(50000)