import os
import json
from pathlib import Path
from collections import Counter

DATA_DIR = "./data/raw_synthea/fhir"

def inspect_codes():
    path = Path(DATA_DIR)
    files = list(path.glob("*.json"))[:1000] # Проверим первую тысячу
    found_codes = []

    for file_path in files:
        with open(file_path, 'r') as f:
            bundle = json.load(f)
            for entry in bundle.get('entry', []):
                res = entry.get('resource')
                if res and res.get('resourceType') == 'Condition':
                    for coding in res.get('code', {}).get('coding', []):
                        display = coding.get('display', '').lower()
                        # Ищем упоминания рака кишечника
                        if 'colon' in display or 'rectum' in display or 'malignant' in display:
                            found_codes.append(f"{coding.get('code')} | {coding.get('display')}")

    # Считаем частоту встретившихся кодов
    stats = Counter(found_codes)
    print("Найденные коды по теме онкологии кишечника:")
    for code, count in stats.most_common():
        print(f"{count} раз(а): {code}")

if __name__ == "__main__":
    inspect_codes()