import requests
import time

def bulk_export(base_url):
    headers = {
        "Prefer": "respond-async",
        "Accept": "application/fhir+json"
    }
    # Мы запрашиваем экспорт только нужных нам типов ресурсов
    url = f"{base_url}/$export?_type=Patient,Condition,Observation,Procedure"
    # url = f"{base_url}/$export?_type=Procedure"

    
    print(f"Запуск экспорта: {url}")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 202:
        poll_url = response.headers.get("Content-Location")
        print(f"Экспорт запущен. Статус можно проверить тут: {poll_url}")
        
        # Цикл ожидания готовности
        while True:
            status_res = requests.get(poll_url)
            if status_res.status_code == 200:
                print("HAPI FHIR подтвердил завершение экспорта!")
                break
            else:
                print("Сервер всё еще обрабатывает данные... (статус 202)")
                time.sleep(5)
    else:
        print(f"Ошибка старта: {response.status_code} {response.text}")

if __name__ == "__main__":
    bulk_export("http://localhost:8080/fhir")