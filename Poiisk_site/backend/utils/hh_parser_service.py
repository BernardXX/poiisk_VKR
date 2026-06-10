import sys
import os
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from hhparser.scrapper import VacancyScrapper
    from hhparser.api import Api
    from hhparser.template_parser import DumpParser
except ImportError:
    print(f"⚠️ ОШИБКА ИМПОРТА: Не удалось найти папку 'hhparser'.")
    print(f"   Убедитесь, что файлы (scrapper.py и др.) лежат в: {current_dir}/hhparser/")
    raise


def search_vacancies_hhparser(
    query: str,
    per_page: int = 10,
    remote: bool = False,
    location: str = None
) -> list:
    """
    Поиск вакансий через hhparser (веб-скрейпинг)
    """
    try:
        params = {
            "text": query,
            "per_page": per_page,
            "page": 0,
            "enable_snippets": True,
            "clusters": False
        }
        
        if remote and "удаленн" not in query.lower():
            params["text"] += " удалённо"
        
        scrapper = VacancyScrapper(params=params)
        hh_api = Api(scrapper)
        
        # Получаем вакансии с "благословением" полей (дозагрузка полного описания)
        # Это может занять время, так как парсер ходит на каждую страницу вакансии
        vacancies = hh_api.get_vacancies(
            search_text=query,
            bless_fields=["description", "key_skills", "salary", "experience"]
        )
        
        result = []
        for vac in vacancies[:per_page]: 
            salary = vac.get("salary")
            salary_text = "Не указана"
            if salary and isinstance(salary, dict):
                fr, to = salary.get("from"), salary.get("to")
                
                cur_map = {
                    "RUB": "₽",
                    "RUR": "₽",  
                    "USD": "$",
                    "EUR": "€",
                    "KZT": "₸",
                    "BYN": "Br"
                }
                
                cur = cur_map.get(salary.get("currency"), salary.get("currency", "₽"))
                
                if fr and to:
                    salary_text = f"{fr:,}–{to:,} {cur}".replace(",", " ")
                elif fr:
                    salary_text = f"от {fr:,} {cur}".replace(",", " ")
                elif to:
                    salary_text = f"до {to:,} {cur}".replace(",", " ")
            
            
            result.append({
                "name": vac.get("title") or vac.get("name"),
                "company": vac.get("company_name") or vac.get("employer", {}).get("name"),
                "url": vac.get("url"),
                "snippet": (vac.get("description", "")[:200] + "...") if vac.get("description") else "Без описания",
                "salary": salary_text,
                "full_description": vac.get("description", "")[:1200],
                "location": vac.get("adress") or vac.get("area", {}).get("name"),
                "experience": vac.get("experience"),
                "key_skills": vac.get("key_skills") or vac.get("tag", []),
                "published_at": vac.get("creation-time")
            })
        
        print(f"✅ Найдено {len(result)} вакансий через hhparser")
        return result
        
    except Exception as e:
        print(f"❌ Ошибка hhparser: {e}")
        import traceback
        traceback.print_exc()
        return []