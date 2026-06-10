import os
import requests
import re
from dotenv import load_dotenv
from utils.skill_matcher import extract_skills_from_text

load_dotenv()

SUPERJOB_SECRET_KEY = os.getenv("SUPERJOB_SECRET_KEY", "")

def search_superjob(query: str, city_id: int = 0, per_page: int = 10) -> list:
    """
    Поиск вакансий на SuperJob с извлечением навыков и защитой от None
    """
    
    if not SUPERJOB_SECRET_KEY or SUPERJOB_SECRET_KEY == "ВАШ_СЕКРЕТНЫЙ_КЛЮЧ_СЮДА":
        print("⚠️ SuperJob: Не указан секретный ключ в .env")
        return []

    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {
        "X-Api-App-Id": SUPERJOB_SECRET_KEY,
        "Accept": "application/json"
    }
    
    params = {
        "keyword": query,
        "page": 0,
        "count": per_page,
    }
    
    if city_id and city_id > 0:
        params["town"] = city_id

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code in [401, 403]:
            print(f"❌ SuperJob: Ошибка авторизации ({response.status_code})")
            return []
        
        response.raise_for_status()
        data = response.json()
        objects = data.get("objects")

        if not objects:
            print(f"⚠️ SuperJob: Пустой ответ")
            return []
        
        vacancies = []
        for item in objects:
            try:
                profession = item.get("profession") or "Без названия"
                client = item.get("client") or {}
                company = client.get("title") if isinstance(client, dict) else item.get("client_name") or "Компания не указана"
                link = item.get("link") or "#"
                
                # Зарплата
                pay_from = item.get("payment_from")
                pay_to = item.get("payment_to")
                currency = item.get("currency", "RUR")
                cur_map = {
                    "RUB": "₽", "RUR": "₽",
                    "USD": "$", "EUR": "€", "KZT": "₸", "BYN": "Br"
                }

                cur_symbol = cur_map.get((currency or "RUB").upper(), "₽")
                
                if pay_from and pay_to and pay_from > 0 and pay_to > 0:
                    salary_text = f"{pay_from:,}–{pay_to:,} {cur_symbol}".replace(",", " ")
                elif pay_from and pay_from > 0:
                    salary_text = f"от {pay_from:,} {cur_symbol}".replace(",", " ")
                elif pay_to and pay_to > 0:
                    salary_text = f"до {pay_to:,} {cur_symbol}".replace(",", " ")
                else:
                    salary_text = "Не указана"
                
                # Описание
                candidat = item.get("candidat") or ""
                snippet = (candidat[:200] + "...") if len(candidat) > 200 else (candidat or "Описание не найдено")
                
                # Локация
                town = item.get("town") or {}
                location = town.get("title") if isinstance(town, dict) else str(town) if town else ""
                
                key_skills_api = item.get("skills") or []
                skills_list = []

                # 1. Если API вернул явные навыки — используем их
                if isinstance(key_skills_api, list) and len(key_skills_api) > 0:
                    skills_list = [
                        s.get("title") for s in key_skills_api 
                        if isinstance(s, dict) and s.get("title")
                    ]

                # 2. Если навыков нет или их мало — извлекаем из описания
                if len(skills_list) < 3 and candidat:
                    extracted = extract_skills_from_text(candidat)
                    # Добавляем только те, которых ещё нет в списке
                    for skill in extracted:
                        if skill.lower() not in [s.lower() for s in skills_list]:
                            skills_list.append(skill)
                
                vacancies.append({
                    "id": item.get("id"),
                    "name": profession,
                    "company": company,
                    "url": link,
                    "salary": salary_text,
                    "snippet": snippet,
                    "full_description": candidat,
                    "location": location,
                    "remote": item.get("work_format") == "Удалённая работа",
                    "source": "SuperJob",
                    "experience": (item.get("experience") or {}).get("title", "") if isinstance(item.get("experience"), dict) else "",
                    "employment": (item.get("type_of_work") or {}).get("title", "") if isinstance(item.get("type_of_work"), dict) else "",
                    "key_skills": skills_list 
                })
                
            except (KeyError, TypeError, AttributeError) as e:
                print(f"⚠️ Пропущена вакансия: {e}")
                continue
            
        print(f"✅ SuperJob: Найдено {len(vacancies)} вакансий")
        return vacancies

    except Exception as e:
        print(f"❌ SuperJob Ошибка: {e}")
        return []