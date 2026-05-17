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
    
    @staticmethod
    def clean_ref(ref_str):
        """Удаляет префиксы 'Patient/' или 'Encounter/' из ссылок"""
        if not ref_str: return None
        return uuid.UUID(ref_str.split('/')[-1])

    @classmethod
    def condition(cls, res):
        code_coding = res.get('code', {}).get('coding', [{}])[0]
        
        # Пытаемся получить дату начала, если её нет - берем дату записи, 
        # если и её нет - используем "эпоху" (1900 год)
        onset_val = cls.parse_datetime(res.get('onsetDateTime'))
        recorded_val = cls.parse_datetime(res.get('recordedDate'))
        
        # Гарантируем отсутствие None для колонки в ORDER BY
        final_onset = onset_val or recorded_val or datetime(1900, 1, 1)

        row = {
            "condition_id": uuid.UUID(res['id']),
            "patient_id": cls.clean_ref(res.get('subject', {}).get('reference')),
            "encounter_id": cls.clean_ref(res.get('encounter', {}).get('reference')),
            "code": code_coding.get('code', 'Unknown'),
            "display": code_coding.get('display', 'Unknown'),
            "clinical_status": res.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', 'unknown'),
            "verification_status": res.get('verificationStatus', {}).get('coding', [{}])[0].get('code', 'unknown'),
            "onset_at": final_onset, # Здесь теперь точно не None
            "abatement_at": cls.parse_datetime(res.get('abatementDateTime')),
            "recorded_at": recorded_val
        }
        return row

    @classmethod
    def observation(cls, res):
        code_coding = res.get('code', {}).get('coding', [{}])[0]
        category = res.get('category', [{}])[0].get('coding', [{}])[0].get('code', 'unknown')
        effective_at = cls.parse_datetime(res.get('effectiveDateTime')) or datetime(1900, 1, 1)

        val_num = None
        val_str = None
        unit = ""
        
        # 1. Если это число (Quantity)
        if 'valueQuantity' in res:
            val_num = float(res['valueQuantity'].get('value', 0))
            unit = res['valueQuantity'].get('unit', '')
            
        # 2. Если это код (CodeableConcept)
        elif 'valueCodeableConcept' in res:
            # Пытаемся взять человекочитаемый текст или display кода
            val_str = res['valueCodeableConcept'].get('text')
            if not val_str and 'coding' in res['valueCodeableConcept']:
                val_str = res['valueCodeableConcept']['coding'][0].get('display')
        
        # 3. Если это просто строка
        elif 'valueString' in res:
            val_str = res['valueString']
            
        # 4. Если это логическое значение
        elif 'valueBoolean' in res:
            val_str = str(res['valueBoolean'])

        row = {
            "observation_id": uuid.UUID(res['id']),
            "patient_id": cls.clean_ref(res.get('subject', {}).get('reference')),
            "encounter_id": cls.clean_ref(res.get('encounter', {}).get('reference')),
            "category": category,
            "code": code_coding.get('code', 'Unknown'),
            "display": code_coding.get('display', 'Unknown'),
            "value_number": val_num,
            "value_string": val_str,
            "unit": unit,
            "effective_at": effective_at
        }
        return row

    @classmethod
    def encounter(cls, res):
        """Парсер для ресурса Encounter"""
        # Тип визита
        type_info = res.get('type', [{}])[0].get('coding', [{}])[0]
        
        # Причина визита (reasonCode) - может отсутствовать
        reason = None
        if 'reasonCode' in res and res['reasonCode']:
            reason = res['reasonCode'][0].get('coding', [{}])[0].get('display')

        return {
            "encounter_id": uuid.UUID(res['id']),
            "patient_id": cls.clean_ref(res.get('subject', {}).get('reference')),
            "start_at": cls.parse_datetime(res.get('period', {}).get('start')) or datetime(1900, 1, 1),
            "end_at": cls.parse_datetime(res.get('period', {}).get('end')) or datetime(1900, 1, 1),
            "class_code": res.get('class', {}).get('code', 'unknown'),
            "display": type_info.get('display', 'Unknown'),
            "reason_display": reason,
            "status": res.get('status', 'unknown')
        }

    @classmethod
    def procedure(cls, res):
        """Парсер для ресурса Procedure с обработкой ссылок на причины"""
        code_coding = res.get('code', {}).get('coding', [{}])[0]
        
        # Ссылка на причину (Condition)
        reason_id = None
        if 'reasonReference' in res and res['reasonReference']:
            reason_ref = res['reasonReference'][0].get('reference', '')
            if 'Condition/' in reason_ref:
                reason_id = uuid.UUID(reason_ref.split('/')[-1])

        # Время проведения (может быть DateTime или Period)
        start_dt = res.get('performedDateTime') or res.get('performedPeriod', {}).get('start')
        end_dt = res.get('performedPeriod', {}).get('end') if 'performedPeriod' in res else None

        return {
            "procedure_id": uuid.UUID(res['id']),
            "patient_id": cls.clean_ref(res.get('subject', {}).get('reference')),
            "encounter_id": cls.clean_ref(res.get('encounter', {}).get('reference')),
            "reason_condition_id": reason_id,
            "code": code_coding.get('code', 'Unknown'),
            "display": code_coding.get('display', 'Unknown'),
            "performed_at": cls.parse_datetime(start_dt) or datetime(1900, 1, 1),
            "end_at": cls.parse_datetime(end_dt),
            "status": res.get('status', 'unknown')
        }  

class ClickHouseLoader:
    def __init__(self):
        host = os.getenv('CLICKHOUSE_HOST', 'localhost')
        port = int(os.getenv('CLICKHOUSE_PORT', 8123))
        user = os.getenv('CLICKHOUSE_USER', 'default')
        password = os.getenv('CLICKHOUSE_PASSWORD', '')
        
        self.registry = {
            'Patient': (FhirParsers.patient, 'patients'),
            'Condition': (FhirParsers.condition, 'conditions'),
            'Observation': (FhirParsers.observation, 'observations'),
            'Encounter': (FhirParsers.encounter, 'encounters'),
            'Procedure': (FhirParsers.procedure, 'procedures'),
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
    # loader.load_resource('Patient')
    # loader.load_resource('Condition')
    # loader.load_resource('Observation')
    # loader.load_resource('Encounter')
    loader.load_resource('Procedure')