import requests
import uuid
from config import get_token
import urllib3

urllib3.disable_warnings()

def get_access_token():
    """Получение access token для GigaChat API"""
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {get_token()}"
    }
    data = {
        "scope": "GIGACHAT_API_PERS"
    }
    
    response = requests.post(url, headers=headers, data=data, verify=False)
    if response.status_code != 200:
        print("Ошибка получения токена: ", response.text)
        return None
    
    return response.json()["access_token"]

def ask_gigachat(messages: list) -> str:
    """Отправка запроса к GigaChat API"""
    token = get_access_token()
    if not token:
        return "⚠️ Не удалось подключиться к GigaChat. Проверь token.txt"
    
    API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "GigaChat",
        "messages": messages,
        "temperature": 0.3
    }
    
    res = requests.post(API_URL, headers=headers, json=data, verify=False)
    if res.status_code != 200:
        return "⚠️ Ошибка ответа от нейросети"
    
    try:
        return res.json()["choices"][0]["message"]["content"]
    except:
        return "⚠️ Не удалось обработать ответ"