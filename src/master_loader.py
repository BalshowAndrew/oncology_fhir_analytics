import json
import uuid
import glob
import os
import logging
from pathlib import Path
from datetime import date, datetime # ДОБАВИЛИ ДЛЯ КОНВЕРТАЦИИ
from clickhouse_connect import get_client
from dotenv import load_dotenv

base_path = Path(__file__).resolve().parent.parent
env_path = base_path / 'infrastructure' / '.env'
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FhirParsers:
    @staticmethod
    def parse_date(d_str):
        if not d_str: return None
        try:
            # Превращаем строку в объект date
            dt = date.fromisoformat(d_str)
            # Защита от дат ранее 1900 года (Date32 их не любит)
            if dt.year < 1900: return None
            return dt
        except:
            return None

    @staticmethod
    def parse_datetime(dt_str):
        if not dt_str: return None
        try:
            if dt_str.endswith('Z'):
                dt_str = dt_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(dt_str)
            if dt.year < 1900: return None
            return dt
        except:
            return None

    @staticmethod
    def parse_datetime(dt_str):
        """Конвертация ISO строки в объект datetime"""
        if not dt_str: return None
        try:
            # FHIR datetime может содержать 'Z' или смещение
            if dt_str.endswith('Z'):
                dt_str = dt_str.replace('Z', '+00:00')
            return datetime.fromisoformat(dt_str)
        except:
            return None

    @staticmethod
    def get_extension_text(res, url):
        for ext in res.get('extension', []):
            if ext.get('url') == url:
                for sub_ext in ext.get('extension', []):
                    if sub_ext.get('url') == 'text':
                        return sub_ext.get('valueString')
        return "Unknown"

    @classmethod
    def patient(cls, res):
        """Парсер с конвертацией типов данных"""
        birth_sex = "UNK"
        for ext in res.get('extension', []):
            if 'us-core-birthsex' in ext.get('url', ''):
                val = ext.get('valueCode')
                if val in ['M', 'F']: birth_sex = val
                break

        row = {
            "patient_id": uuid.UUID(res['id']),
            "gender": res.get('gender', 'unknown'),
            "birth_sex": birth_sex,
            # КОНВЕРТИРУЕМ СТРОКИ В ОБЪЕКТЫ
            "birth_date": cls.parse_date(res.get('birthDate')),
            "deceased_at": cls.parse_datetime(res.get('deceasedDateTime')),
            "is_deceased": 1 if 'deceasedDateTime' in res else 0,
            "race": cls.get_extension_text(res, "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race"),
            "ethnicity": cls.get_extension_text(res, "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity"),
            "city": "Unknown",
            "state": "Unknown",
            "lat": 0.0,
            "lon": 0.0,
            "marital_status": res.get('maritalStatus', {}).get('text', 'Unknown')
        }

        if 'address' in res and res['address']:
            addr = res['address'][0]
            row["city"] = addr.get('city', 'Unknown')
            row["state"] = addr.get('state', 'Unknown')
            for addr_ext in addr.get('extension', []):
                if 'geolocation' in addr_ext.get('url', ''):
                    for geo in addr_ext.get('extension', []):
                        if geo.get('url') == 'latitude': row["lat"] = float(geo.get('valueDecimal', 0.0))
                        if geo.get('url') == 'longitude': row["lon"] = float(geo.get('valueDecimal', 0.0))
        
        return row

class ClickHouseLoader:
    def __init__(self):
        host = os.getenv('CLICKHOUSE_HOST', 'localhost')
        port = int(os.getenv('CLICKHOUSE_PORT', 8123))
        user = os.getenv('CLICKHOUSE_USER', 'default')
        password = os.getenv('CLICKHOUSE_PASSWORD', '')
        
        self.registry = {
            'Patient': (FhirParsers.patient, 'patients'),
        }
        
        try:
            self.client = get_client(host=host, port=port, username=user, password=password)
            logger.info(f"Connected to ClickHouse at {host}:{port}")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise

    def load_resource(self, resource_type, data_dir='data/fhir_export'):
        parse_func, table_name = self.registry[resource_type]
        full_table_name = f"oncology.{table_name}"
        
        files = sorted(glob.glob(os.path.join(data_dir, f"{resource_type}_*.ndjson")))

        for file_path in files:
            batch_dicts = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    parsed = parse_func(json.loads(line))
                    if parsed: batch_dicts.append(parsed)

                if batch_dicts:
                    cols = list(batch_dicts[0].keys())
                    # ПРЕВРАЩАЕМ В КОРТЕЖИ
                    data_as_tuples = [tuple(row[col] for col in cols) for row in batch_dicts]
                    
                    try:
                        self.client.insert(full_table_name, data_as_tuples, column_names=cols)
                        logger.info(f"Loaded {len(data_as_tuples)} rows from {os.path.basename(file_path)}")
                    except Exception as e:
                        logger.error(f"Insert failed: {e}")
                        raise 

if __name__ == "__main__":
    loader = ClickHouseLoader()
    loader.load_resource('Patient')