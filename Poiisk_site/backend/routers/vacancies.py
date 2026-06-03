from fastapi import APIRouter, HTTPException, Query, Form
from typing import List, Dict, Optional
from database import get_db_connection
import json
import re
from utils.hh_parser_service import search_vacancies_hhparser
from utils.superjob_service import search_superjob
from utils.gigachat import ask_gigachat

router = APIRouter(prefix="/api/vacancies", tags=["Vacancies"])

# Список слов для функционала фильтрации вакансий
STOP_KEYWORDS = []

def is_vacancy_filtered(vacancy: Dict) -> bool:
    """
    Проверяет вакансию на наличие стоп-слов.
    Возвращает True, если вакансию нужно исключить.
    """
    text_to_check = " ".join([
        str(vacancy.get("name", "")).lower(),
        str(vacancy.get("company", "")).lower(),
        str(vacancy.get("snippet", "")).lower(),
        str(vacancy.get("full_description", "")).lower()
    ])
    
    for word in STOP_KEYWORDS:
        if word in text_to_check:
            print(f"Отфильтрована вакансия: {vacancy.get('name')} (найдено: {word})")
            return True
    return False

def extract_level_from_vacancy(vacancy: Dict) -> str:
    """
    Извлекает уровень позиции (junior/middle/senior) из названия или описания вакансии
    """
    text = f"{vacancy.get('name', '')} {vacancy.get('snippet', '')}".lower()
    
    if any(word in text for word in ['senior', 'lead', 'team lead', 'архитектор', 'главный', 'ведущий']):
        return 'senior'
    elif any(word in text for word in ['middle', 'мидл', 'mid']):
        return 'middle'
    elif any(word in text for word in ['junior', 'стажер', 'intern', 'начинающий', 'стажёр']):
        return 'junior'
    else:
        return 'unknown'  # Неизвестный уровень


def extract_requirements_with_ai(vacancy_text: str, max_skills: int = 15) -> List[str]:
    """
    Использует ИИ для извлечения технических требований из описания вакансии
    """
    if not vacancy_text or len(vacancy_text) < 50:
        return []
    
    try:
        truncated_text = vacancy_text[:2000]
        prompt = f"""
        Ты — технический рекрутер. Проанализируй описание вакансии и извлеки ВСЕ технические требования.

        ОПИСАНИЕ ВАКАНСИИ:
        {truncated_text}

        ВЕРНИ ТОЛЬКО JSON-МАССИВ СТРОК. Без комментариев, без объяснений, без markdown.
        Формат: ["Python", "Django", "PostgreSQL", "Docker", "Git"]

        Важно:
        - Включай только технические требования (не "коммуникабельность", "опыт работы")
        - Если навык упомянут косвенно — всё равно включи (например, "работа с БД" → "SQL")
        - Не дублируй синонимы (Vue.js и Vue — оставь один вариант)
        - Максимум {max_skills} позиций
        - ТОЛЬКО JSON, ничего больше
        """
        raw_response = ask_gigachat([{"role": "user", "content": prompt}])
        
        # Очистка ответа
        clean = raw_response.strip()
        json_match = re.search(r'\[\s*["\'].*?\]', clean, re.DOTALL)
        if json_match:
            clean = json_match.group()
        else:
            clean = re.sub(r'```(?:json)?\s*', '', clean).replace('```', '').strip()
        
        try:
            skills = json.loads(clean)
        except json.JSONDecodeError:
            return extract_skills_fallback(vacancy_text)
        
        if isinstance(skills, list):
            result = [s.strip() for s in skills if isinstance(s, str) and s.strip()]
            return result[:max_skills]
        return []
    except Exception as e:
        print(f"⚠️ Ошибка извлечения требований через ИИ: {e}")
        return extract_skills_fallback(vacancy_text)

def extract_skills_fallback(text: str) -> List[str]:
    """
    Простой fallback-метод извлечения навыков, если ИИ не сработал
    """
    if not text: return []
    common_skills = [
        'python', 'javascript', 'typescript', 'java', 'c#', 'c++', 'php', 'ruby', 'go', 'rust',
        'vue', 'vue.js', 'react', 'react.js', 'angular', 'node.js', 'django', 'flask', 'fastapi',
        'postgresql', 'mysql', 'mongodb', 'redis', 'docker', 'kubernetes', 'git', 'linux',
        'aws', 'azure', 'gcp', 'terraform', 'jenkins', 'ci/cd', 'rest', 'graphql',
        'html', 'css', 'scss', 'sass', 'webpack', 'vite', 'npm', 'yarn',
        'sql', 'nosql', 'elasticsearch', 'rabbitmq', 'kafka', 'nginx', 'apache'
    ]
    text_lower = text.lower()
    found_skills = []
    for skill in common_skills:
        if '/' in skill or ' ' in skill:
            if skill in text_lower: found_skills.append(skill)
        else:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower): found_skills.append(skill)
    return list(set(found_skills))[:15]

# Логика матчинга 
def calculate_match_score_detailed(
    vacancy: Dict,
    desired_role: str,
    location: str,
    priority_skills: List[str],
    all_skills: List[str],
    user_level: str = 'middle'  # По умолчанию middle
) -> tuple:
    """
    Расчет релевантности вакансии (0-100)
    Возвращает: (score, matched_skills, missing_skills)
    """
    score = 0
    matched_skills = []
    
    # 1. Соответствие должности 
    vacancy_name = vacancy.get("name", "").lower()
    role_keywords = (desired_role or "").lower().split()
    for keyword in role_keywords:
        if len(keyword) > 3 and keyword in vacancy_name:
            score += 10
    score = min(score, 25)
    
    # 2. Соответствие уровня квалификации
    vacancy_level = extract_level_from_vacancy(vacancy)
    level_score = 0
    
    user_level_norm = user_level.lower()
    if user_level_norm == 'junior':
        if vacancy_level == 'junior': level_score = 30
        elif vacancy_level == 'middle': level_score = 10
        else: level_score = 0
    elif user_level_norm == 'middle':
        if vacancy_level == 'middle': level_score = 30
        elif vacancy_level in ['junior', 'senior']: level_score = 10
    elif user_level_norm == 'senior':
        if vacancy_level == 'senior': level_score = 30
        elif vacancy_level == 'middle': level_score = 10
        else: level_score = 0
            
    score += level_score
    
    # 3. Соответствие локации
    if location:
        vac_location = vacancy.get("location", "").lower() if vacancy.get("location") else ""
        if location.lower() in vac_location or vac_location in location.lower():
            score += 5
        elif 'удален' in location.lower() and vacancy.get('remote'):
            score += 5
    
    # 4. Матчинг навыков 
    vacancy_text = (
        f"{vacancy.get('name', '')} {vacancy.get('snippet', '')} "
        f"{vacancy.get('full_description', '')}"
    )
    
    ai_requirements = extract_requirements_with_ai(vacancy_text, max_skills=15)
    
    if not ai_requirements:
        vacancy_skills_text = vacancy.get("key_skills", [])
        if isinstance(vacancy_skills_text, list):
            ai_requirements = [s.lower() for s in vacancy_skills_text if isinstance(s, str)]
        elif isinstance(vacancy_skills_text, str):
            ai_requirements = [s.strip().lower() for s in vacancy_skills_text.split(',') if s.strip()]
    
    vacancy_reqs_lower = {r.lower() for r in ai_requirements if r}
    
    # Словарь синонимов
    skill_aliases = {
        'vue': ['vue.js', 'vuejs'], 'react': ['react.js', 'reactjs'],
        'node.js': ['nodejs', 'node'], 'postgresql': ['postgres', 'psql'],
        'javascript': ['js', 'ecmascript'], 'typescript': ['ts'],
        'ci/cd': ['cicd', 'ci cd'], 'rest api': ['rest', 'restful']
    }
    
    # Находим совпавшие навыки
    for user_skill in all_skills:
        u_skill = user_skill.lower()
        is_matched = False
        
        # Прямое совпадение
        if u_skill in vacancy_reqs_lower: is_matched = True
        # Проверка синонимов
        elif u_skill in skill_aliases:
            if any(s in vacancy_reqs_lower for s in [u_skill] + skill_aliases[u_skill]): is_matched = True
        elif any(u_skill in aliases for aliases in skill_aliases.values()):
            if any(req in [u_skill] + skill_aliases.get(u_skill, []) for req in vacancy_reqs_lower): is_matched = True
            
        if is_matched:
            matched_skills.append(user_skill)
            score += 5 if u_skill in priority_skills else 3
    
    score = min(score, 100)
    
    # Извлекаем недостающие навыки
    user_skills_lower = {s.lower() for s in all_skills}
    missing_skills = []
    for req in ai_requirements:
        req_lower = req.lower()
        user_has = (req_lower in user_skills_lower or
                    any(req_lower in aliases or any(a in req_lower for a in aliases) 
                        for aliases in skill_aliases.values()))
        if not user_has and req_lower not in {m.lower() for m in matched_skills}:
            missing_skills.append(req)
    
    return score, matched_skills, missing_skills[:10]

def location_match_score(vacancy: Dict, user_location: str) -> str:
    """Определить тип соответствия локации (только для UI-бейджей)"""
    if not user_location: return "unknown"
    vac_location = vacancy.get("location", "").lower() if vacancy.get("location") else ""
    user_loc = user_location.lower()
    
    if 'удален' in user_loc and vacancy.get('remote'): return "remote_match"
    elif user_loc in vac_location or vac_location in user_loc: return "location_match"
    else: return "no_match"


@router.get("/search")
def search_vacancies(user_id: int = Query(...)):
    """
    Поиск вакансий с интеллектуальным матчингом (HH + SuperJob)
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Получаем данные профиля
        cur.execute("""
            SELECT desired_role, location, level, skills, full_name
            FROM user_profiles WHERE user_id = %s
        """, (user_id,))
        profile = cur.fetchone()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Профиль не найден")
        
        desired_role, location, user_level, skills_json, full_name = profile
        user_level = (user_level or "middle").lower()  # По умолчанию middle
        
        # 2. Извлекаем приоритетные навыки
        priority_skills = []
        all_skills = []
        
        if skills_json:
            skills = json.loads(skills_json) if isinstance(skills_json, str) else skills_json
            for skill_name, skill_data in skills.items():
                all_skills.append(skill_name)
                if isinstance(skill_data, dict) and skill_data.get('is_priority'):
                    priority_skills.append(skill_name.lower())
                elif isinstance(skill_data, bool) and skill_data:
                    priority_skills.append(skill_name.lower())
        
        # 3. Ищем вакансии на сайтах
        print("🔍 Начинаем поиск вакансий...")
        hh_vacancies = search_vacancies_hhparser(
            query=desired_role or "разработчик",
            per_page=15,
            remote=('удален' in location.lower() if location else False),
            location=location
        )
        
        city_id = 0
        if location:
            location_lower = location.lower()
            if 'москва' in location_lower: city_id = 4
            elif 'санкт-петербург' in location_lower or 'питер' in location_lower: city_id = 14
            
        sj_vacancies = search_superjob(
            query=desired_role or "разработчик",
            city_id=city_id,
            per_page=15
        )
        
        all_vacancies = hh_vacancies + sj_vacancies
        print(f"📊 Получено {len(all_vacancies)} вакансий с обоих сайтов")
        
        if not all_vacancies:
            return {"vacancies": [], "message": "Вакансии не найдены"}
        
        # 4. Фильтрация
        clean_vacancies = [v for v in all_vacancies if not is_vacancy_filtered(v)]
        print(f"✅ После фильтрации осталось {len(clean_vacancies)} вакансий")
        
        if not clean_vacancies:
            return {"vacancies": [], "message": "Все вакансии отфильтрованы по ключевым словам"}
        
        # 5. Матчинг и ранжирование
        matched_vacancies = []
        
        for vacancy in clean_vacancies:
            score, matched, missing = calculate_match_score_detailed(
                vacancy=vacancy,
                desired_role=desired_role,
                location=location,
                priority_skills=priority_skills,
                all_skills=all_skills,
                user_level=user_level
            )
            
            if score >= 10:  
                vacancy_with_score = {
                    **vacancy,
                    "relevance_score": score,
                    "matched_skills": matched,
                    "missing_skills": missing,
                    "location_match": location_match_score(vacancy, location),
                    "matched_count": len(matched)  # 🔥 Для сортировки
                }
                matched_vacancies.append(vacancy_with_score)

        # Если ничего не нашли с порогом >= 10, возвращаем топ-5
        if not matched_vacancies:
            for vacancy in clean_vacancies[:5]:
                score, matched, missing = calculate_match_score_detailed(
                    vacancy=vacancy, desired_role=desired_role, location=location,
                    priority_skills=priority_skills, all_skills=all_skills, user_level=user_level
                )
                vacancy_with_score = {
                    **vacancy, "relevance_score": score, "matched_skills": matched,
                    "missing_skills": missing, "location_match": location_match_score(vacancy, location),
                    "note": "Вакансия найдена, но требует дополнительных навыков",
                    "matched_count": len(matched)
                }
                matched_vacancies.append(vacancy_with_score)

        # 6. Сортировка по релевантности
        matched_vacancies.sort(key=lambda x: (x["matched_count"], x["relevance_score"]), reverse=True)

        return {
            "vacancies": matched_vacancies[:15],
            "total_found": len(matched_vacancies),
            "search_params": {"role": desired_role, "location": location, "level": user_level}
        }
        
    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.post("/search-and-save")
def search_and_save_vacancies(
    user_id: int = Form(...),
    session_id: Optional[int] = Form(None)
):
    """Поиск вакансий с сохранением результата в чат"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if not session_id:
            cur.execute("""
                INSERT INTO sessions (user_id, title, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW()) RETURNING session_id
            """, (user_id, "Поиск вакансий"))
            session_id = cur.fetchone()[0]
        
        cur.execute("""
            SELECT desired_role, location, skills, level
            FROM user_profiles WHERE user_id = %s
        """, (user_id,))
        profile = cur.fetchone()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Профиль не найден")
        
        desired_role, location, skills_json, user_level = profile
        user_level = (user_level or "junior").lower()
        
        priority_skills = []
        all_skills = []
        if skills_json:
            skills = json.loads(skills_json) if isinstance(skills_json, str) else skills_json
            for skill_name, skill_data in skills.items():
                all_skills.append(skill_name)
                if isinstance(skill_data, dict) and skill_data.get('is_priority'):
                    priority_skills.append(skill_name.lower())
        
        base_query = desired_role or "разработчик"
        level_clean = (user_level or "").lower().strip()
        
        # Добавляем уровень только если он валидный и не является заглушкой
        if level_clean and level_clean not in ["unknown", "не указан", ""]:
            search_query = f"{base_query} {level_clean}"
        else:
            search_query = base_query

        hh_vacancies = search_vacancies_hhparser(
            query=search_query,
            per_page=10,
            remote=('удален' in location.lower() if location else False),
            location=location
        )
        
        city_id = 0
        if location:
            location_lower = location.lower()
            if 'москва' in location_lower: city_id = 4
            elif 'санкт-петербург' in location_lower or 'питер' in location_lower: city_id = 14
            
        sj_vacancies = search_superjob(
            query=search_query,
            city_id=city_id,
            per_page=10
        )
        
        all_vacancies = hh_vacancies + sj_vacancies
        
        clean_vacancies = [v for v in all_vacancies if not is_vacancy_filtered(v)]
        
        matched_vacancies = []
        for vacancy in clean_vacancies:
            score, matched, missing = calculate_match_score_detailed(
                vacancy=vacancy,
                desired_role=desired_role,
                location=location,
                priority_skills=priority_skills,
                all_skills=all_skills,
                user_level=user_level
            )
            
            if score >= 10:
                matched_vacancies.append({
                    **vacancy, 
                    "relevance_score": score, 
                    "matched_skills": matched,
                    "missing_skills": missing[:10], 
                    "location_match": location_match_score(vacancy, location),
                    "matched_count": len(matched)
                })
        
        matched_vacancies.sort(key=lambda x: (x["matched_count"], x["relevance_score"]), reverse=True)
        top_vacancies = matched_vacancies[:10]
        
        assistant_message = f"✅ Найдено {len(top_vacancies)} подходящих вакансий! Вот лучшие подборки на основе вашего профиля:"
        
        cur.execute("""
            INSERT INTO messages (session_id, role, content, metadata, created_at)
            VALUES (%s, 'assistant', %s, %s, NOW())
        """, (
            session_id,
            assistant_message,
            json.dumps({"vacancies": top_vacancies, "type": "job_search"})
        ))
        
        conn.commit()
        
        return {
            "message": "Вакансии найдены и сохранены в чат",
            "vacancies_count": len(top_vacancies),
            "session_id": session_id
        }
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"Search vacancies error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()