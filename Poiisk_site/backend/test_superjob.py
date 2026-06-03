# backend/test_superjob.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SUPERJOB_SECRET_KEY", "")

if not API_KEY or API_KEY == "ВАШ_СЕКРЕТНЫЙ_КЛЮЧ_СЮДА":
    print("❌ Ошибка: Ключ SuperJob не найден или не задан в .env")
    exit()

url = "https://api.superjob.ru/2.0/vacancies/"
headers = {
    "X-Api-App-Id": API_KEY,
    "Accept": "application/json"
}


params = {
    "keyword": "Python senior",
    "page": 0,
    "count": 3,
    "town": 4  # 4 = Москва, 14 = СПб. SuperJob часто не возвращает ничего при town=0
}

print(f"🔍 Тест SuperJob API...")
print(f"🔑 Используемый ключ: {API_KEY[:20]}...")
print(f"📍 town параметр: {params['town']}")
print(f" URL: {url}")
print(f"⚙️ Параметры: {params}\n")

try:
    response = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"📡 HTTP Статус: {response.status_code}")
    
    if response.status_code == 200:
        print(f"🔍 SuperJob Response Status: {response.status_code}")

        data = response.json()
        objects = data.get("objects", [])

        print(f"✅ Успешно! Найдено вакансий: {len(objects)}")
        for i, vac in enumerate(objects[:2], 1):
            print(f"  {i}. {vac.get('profession')} @ {vac.get('client', {}).get('title')} — {vac.get('payment_from', '?')}–{vac.get('payment_to', '?')} {vac.get('currency', '')}")
    elif response.status_code == 401 or response.status_code == 403:
        print("❌ Ошибка авторизации. Проверь ключ (должен быть типа Secret Code, а не Client ID)")
        print(f"Ответ сервера: {response.text}")
    else:
        print(f"⚠️ Неожиданный статус: {response.status_code}")
        print(f"Ответ: {response.text[:300]}")
        
except requests.exceptions.Timeout:
    print("⏳ Таймаут: SuperJob не отвечает за 10 сек")
except Exception as e:
    print(f"💥 Ошибка: {e}")