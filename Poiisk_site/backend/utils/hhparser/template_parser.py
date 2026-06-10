import json
import re
from .vacancy_decorator import SearchedVacancyDecorator, ViewVacancyDecorator

class DumpParser:
    @classmethod
    def __parse_template(cls, page):
        """Безопасное извлечение JSON из скрытого шаблона"""
        if not page:
            return {}
        
        noindex_tag = page.find('noindex')
        if not noindex_tag:
            script_tag = page.find('script', type='application/ld+json')
            if script_tag and script_tag.string:
                try:
                    return json.loads(script_tag.string)
                except:
                    pass
            qa_tag = page.find(attrs={'data-qa': 'vacancy-json-data'})
            if qa_tag and qa_tag.get('data-qa'):
                try:
                    return json.loads(qa_tag.get('data-qa'))
                except:
                    pass
            return {}
        
        raw_json = None
        for ch in noindex_tag.children:
            if hasattr(ch, 'contents') and ch.contents:
                try:
                    raw_json = ch.contents[0]
                    break
                except (IndexError, AttributeError):
                    continue
        
        if not raw_json:
            return {}
        
        try:
            return json.loads(json.dumps(
                json.loads(raw_json), 
                indent=4, 
                ensure_ascii=False
            ))
        except json.JSONDecodeError:
            try:
                clean = re.sub(r'[\x00-\x1F\x7F]', '', raw_json)
                return json.loads(clean)
            except:
                return {}

    @classmethod
    def parse_vacancy_page(cls, page):
        """Парсинг страницы конкретной вакансии"""
        if not page:
            return {"error": "Страница не загружена"}
        
        try:
            json_obj = cls.__parse_template(page)
            vacancy = json_obj.get("vacancyView", {})
            if vacancy:
                ViewVacancyDecorator(vacancy)
            return vacancy or {"error": "Данные вакансии не найдены"}
        except Exception as e:
            print(f"⚠️ Ошибка парсинга вакансии: {e}")
            return {"error": str(e)}

    @classmethod
    def parse_search_page(cls, searching_page):
        """Парсинг страницы поиска вакансий"""
        if not searching_page:
            return []
        
        try:
            json_obj = cls.__parse_template(searching_page)
            vacancies = json_obj.get("vacancySearchResult", {}).get("vacancies", [])
            if vacancies:
                SearchedVacancyDecorator(vacancies)
            return vacancies or []
        except Exception as e:
            print(f"⚠️ Ошибка парсинга поиска: {e}")
            return []