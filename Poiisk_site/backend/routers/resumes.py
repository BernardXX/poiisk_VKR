import io
import PyPDF2
from docx import Document
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Body
from typing import List, Optional
from datetime import datetime
import os
import json
from database import get_db_connection
from models import ResumeCreate, ResumeUpdate
from utils.gigachat import ask_gigachat

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])

# Вспомогательные функции
def _extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Реальное извлечение текста из PDF или DOCX файла"""
    ext = os.path.splitext(filename)[1].lower()
    
    try:
        if ext == '.pdf':
            # Извлечение текста из PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip() or "[Не удалось извлечь текст из PDF. Возможно, файл отсканирован как изображение.]"
            
        elif ext == '.docx':
            # Извлечение текста из DOCX
            doc = Document(io.BytesIO(file_content))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip() or "[Не удалось извлечь текст из DOCX. Файл пуст или содержит только таблицы/изображения.]"
            
        else:
            # Для обычных текстовых файлов (.txt, .md и т.д.)
            return file_content.decode('utf-8', errors='ignore')[:10000]
            
    except Exception as e:
        print(f"⚠️ Ошибка при чтении {filename}: {e}")
        return f"[Ошибка чтения файла: {filename}. Проверь формат и целостность.]"

def _analyze_code_files(files: List[tuple[str, bytes]]) -> dict:
    """Анализ файлов проекта для извлечения технологий"""
    tech_map = {
        '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript', '.vue': 'Vue.js',
        '.java': 'Java', '.cpp': 'C++', '.c': 'C', '.cs': 'C#', '.php': 'PHP',
        '.rb': 'Ruby', '.go': 'Go', '.rs': 'Rust', '.sql': 'SQL',
        '.html': 'HTML', '.css': 'CSS', '.json': 'JSON', '.yaml': 'YAML',
        '.yml': 'YAML', '.md': 'Markdown', 'dockerfile': 'Docker',
    }
    
    tech_stack = set()
    code_samples = []
    
    for filename, content in files:
        ext = os.path.splitext(filename)[1].lower()
        
        # Определение технологий
        for ext_key, tech in tech_map.items():
            if ext_key in filename.lower() or ext == ext_key:
                tech_stack.add(tech)
                break
        
        # Сохранение примеров кода
        try:
            text = content.decode('utf-8')[:1000]
            code_samples.append(f"Файл: {filename}\n```{text}...```")
        except:
            pass
    
    return {
        "tech_stack": list(tech_stack),
        "code_samples": code_samples[:5]  # Первые 5 файлов
    }

def _get_user_profile_data(user_id: int) -> dict:
    """Внутренняя функция получения данных профиля (включая email из таблицы users)"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                u.email,
                up.full_name, 
                up.phone, 
                up.social_links, 
                up.desired_role, 
                up.location, 
                up.level, 
                up.skills
            FROM users u
            LEFT JOIN user_profiles up ON u.user_id = up.user_id
            WHERE u.user_id = %s
        """, (user_id,))
        
        row = cur.fetchone()
        
        if not row:
            return {
                "email": "[Email]",
                "full_name": "[ФИО]",
                "phone": "[Телефон]",
                "social_links": {},
                "desired_role": "[Желаемая должность]",
                "location": "[Город/Формат работы]",
                "level": "[Уровень]",
                "skills": {}
            }
        
        email = row[0] or "[Email]"
        full_name = row[1] or "[ФИО]"
        phone = row[2] or "[Телефон]"
        
        # Обработка JSONB полей
        social_links = row[3]
        if social_links and not isinstance(social_links, dict):
            social_links = json.loads(social_links) if social_links else {}
        elif not social_links:
            social_links = {}
        
        skills = row[7]
        if skills and not isinstance(skills, dict):
            skills = json.loads(skills) if skills else {}
        elif not skills:
            skills = {}
        
        return {
            "email": email,
            "full_name": full_name,
            "phone": phone,
            "social_links": social_links,
            "desired_role": row[4] or "[Желаемая должность]",
            "location": row[5] or "[Город/Формат работы]",
            "level": row[6] or "[Уровень]",
            "skills": skills
        }
    except Exception as e:
        print(f"Ошибка получения данных профиля: {e}")
        # Возвращаем безопасные значения по умолчанию
        return {
            "email": "[Email]",
            "full_name": "[ФИО]",
            "phone": "[Телефон]",
            "social_links": {},
            "desired_role": "[Желаемая должность]",
            "location": "[Город/Формат работы]",
            "level": "[Уровень]",
            "skills": {}
        }
    finally:
        if conn: 
            conn.close()

# Эндпоинты
@router.get("/user-profile-data/{user_id}")
def get_user_profile_data(user_id: int):
    return _get_user_profile_data(user_id)

@router.post("/{resume_id}/improve")
async def improve_resume(
    resume_id: int,
    user_id: int = Form(...),
    improvement_type: str = Form("professional")
):
    """Улучшение резюме с помощью ИИ"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверка доступа и получение текущего резюме
        cur.execute("""
            SELECT title, content FROM resumes 
            WHERE resume_id = %s AND user_id = %s
        """, (resume_id, user_id))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Резюме не найдено")
        
        current_title, current_content = row
        
        profile_data = _get_user_profile_data(user_id)
        
        # Определяем тип улучшения
        improvement_prompts = {
            "professional": "Сделай резюме более профессиональным, добавь сильные глаголы действия, выдели достижения и результаты",
            "concise": "Сделай резюме более лаконичным и структурированным, убери лишнее, оставь только важное",
            "detailed": "Расширь описание, добавь больше деталей о проектах и достижениях",
            "ats": "Оптимизируй резюме для ATS-систем (автоматических систем отбора), добавь ключевые слова"
        }
        
        improvement_instruction = improvement_prompts.get(improvement_type, improvement_prompts["professional"])
        
        prompt = f"""
        Ты — профессиональный карьерный консультант и эксперт по резюме.

        ТЕКУЩЕЕ РЕЗЮМЕ:
        {current_content}

        ДАННЫЕ ИЗ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ:
        - Email: {profile_data['email']}
        - ФИО: {profile_data.get('full_name', '[ФИО]')}
        - Телефон: {profile_data.get('phone', '[Телефон]')}
        - Ссылки: {json.dumps(profile_data.get('social_links', {}), ensure_ascii=False)}
        - Желаемая должность: {profile_data.get('desired_role', '[Желаемая должность]')}
        - Локация: {profile_data.get('location', '[Город/Формат работы]')}
        - Уровень: {profile_data.get('level', '[Уровень]')}
        - Навыки: {json.dumps(profile_data.get('skills', {}), ensure_ascii=False)}

        ЗАДАЧА:
        {improvement_instruction}

        ВАЖНО:
        1. Сохрани всю важную информацию из текущего резюме
        2. Если каких-то данных не хватает, оставь пометки в квадратных скобках, например [Дата начала работы]
        3. Структурируй резюме профессионально
        4. Используй сильные глаголы действия (разработал, внедрил, оптимизировал и т.д.)
        5. Выдели конкретные достижения и результаты (с цифрами, если возможно)
        6. НЕ ВЫДУМЫВАЙ информацию, которой нет в диалоге. В особенности "Навыки и технологии"
        7. Если каких-то данных не хватает, оставляй пометки в квадратных скобках, например: [ФИО], [Город], [Название компании], [Дата начала работы]
        8. Если раздел не может быть заполнен из-за отсутствия информации, оставь только заголовок раздела с пометкой [требуется заполнить]


        Отформатированное улучшенное резюме:
        """
        
        improved_content = ask_gigachat([{"role": "user", "content": prompt}])
        
        cur.execute("""
            UPDATE resumes 
            SET content = %s, updated_at = NOW()
            WHERE resume_id = %s AND user_id = %s
        """, (improved_content, resume_id, user_id))
        
        conn.commit()
        
        return {
            "resume_id": resume_id,
            "message": "Резюме улучшено",
            "improvement_type": improvement_type
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.post("/{resume_id}/append-from-chat")
async def append_to_resume_from_chat(
    resume_id: int,
    user_id: int = Form(...),
    session_id: int = Form(...),
    append_type: str = Form("all")  # skills, experience, projects, all
):
    """Дополнение резюме информацией из чата"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверка доступа к резюме
        cur.execute("SELECT content FROM resumes WHERE resume_id = %s AND user_id = %s", (resume_id, user_id))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Резюме не найдено")
        
        current_content = row[0]
        
        # Проверка доступа к сессии
        cur.execute("SELECT session_id FROM sessions WHERE session_id = %s AND user_id = %s", (session_id, user_id))
        if not cur.fetchone():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Получение истории сообщений
        cur.execute("""
            SELECT role, content FROM messages 
            WHERE session_id = %s ORDER BY created_at ASC LIMIT 50
        """, (session_id,))
        messages = cur.fetchall()
        
        if not messages:
            raise HTTPException(status_code=400, detail="Чат пуст")
        
        chat_history = "\n".join([f"{msg[0]}: {msg[1]}" for msg in messages])
        
        append_types = {
            "skills": "извлеки и добавь навыки и технологии",
            "experience": "извлеки и добавь опыт работы",
            "projects": "извлеки и добавь информацию о проектах",
            "all": "извлеки всю релевантную информацию (навыки, опыт, проекты, образование)"
        }
        
        instruction = append_types.get(append_type, append_types["all"])
        
        prompt = f"""
        Ты — карьерный консультант. Проанализируй диалог и дополни резюме.

        ВАЖНОЕ ПРАВИЛО:
        - НЕ ВЫДУМЫВАЙ информацию, которой нет в диалоге. В особенности "Навыки и технологии"
        - Если каких-то данных не хватает, оставляй пометки в квадратных скобках, например: [ФИО], [Город], [Название компании], [Дата начала работы]
        - Если раздел не может быть заполнен из-за отсутствия информации, оставь только заголовок раздела с пометкой [требуется заполнить]


        ТЕКУЩЕЕ РЕЗЮМЕ:
        {current_content}

        ДИАЛОГ С ПОЛЬЗОВАТЕЛЕМ:
        {chat_history}

        ЗАДАЧА:
        {instruction}

        Верни ТОЛЬКО новые разделы или информацию, которую нужно добавить в резюме. Не повторяй то, что уже есть.
        Если информация уже присутствует в резюме, не добавляй её повторно.

        Новая информация для добавления:
        """
        
        new_content = ask_gigachat([{"role": "user", "content": prompt}])
        
        updated_content = f"{current_content}\n\n---\n\nДополнительная информация:\n{new_content}"
    
        cur.execute("""
            UPDATE resumes 
            SET content = %s, updated_at = NOW()
            WHERE resume_id = %s AND user_id = %s
        """, (updated_content, resume_id, user_id))
        
        conn.commit()
        
        return {
            "resume_id": resume_id,
            "message": "Резюме дополнено информацией из чата",
            "append_type": append_type
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.post("/{resume_id}/append-from-project")
async def append_to_resume_from_project(
    resume_id: int,
    user_id: int = Form(...),
    project_files: List[UploadFile] = File(...),
    project_name: str = Form("Новый проект")
):
    """Дополнение резюме информацией из проекта"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT content FROM resumes WHERE resume_id = %s AND user_id = %s", (resume_id, user_id))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Резюме не найдено")
        
        current_content = row[0]
        
        files_data = []
        for file in project_files:
            content = await file.read()
            files_data.append((file.filename, content))
        
        analysis = _analyze_code_files(files_data)
        
        # Формирование промпта
        files_summary = "\n\n".join(analysis["code_samples"])
        
        prompt = f"""
        Проанализируй код проекта и создай описание для добавления в резюме.

        ВАЖНОЕ ПРАВИЛО:
        - Описывай ТОЛЬКО то, что видишь в коде
        - НЕ ВЫДУМЫВАЙ технологии, которые не используются в проекте. В особенности "Навыки и технологии"
        - Если какая-то информация не очевидна из кода, оставляй пометки в квадратных скобках

        ТЕКУЩЕЕ РЕЗЮМЕ:
        {current_content}

        НОВЫЙ ПРОЕКТ "{project_name}":
        Стек технологий: {', '.join(analysis["tech_stack"])}
        Примеры кода:
        {files_summary}

        ЗАДАЧА:
        Создай профессиональное описание этого проекта для раздела "Опыт работы / Проекты" в резюме.
        Включи:
        1. Название проекта
        2. Используемые технологии
        3. Ключевой функционал
        4. Достижения и результаты

        Формат: 3-5 пунктов, профессионально и лаконично.

        Описание проекта для добавления:
        """
        
        project_description = ask_gigachat([{"role": "user", "content": prompt}])
        
        updated_content = f"{current_content}\n\n---\n\nПроект: {project_name}\n{project_description}"
        
        cur.execute("""
            UPDATE resumes 
            SET content = %s, updated_at = NOW()
            WHERE resume_id = %s AND user_id = %s
        """, (updated_content, resume_id, user_id))
        
        conn.commit()
        
        return {
            "resume_id": resume_id,
            "message": "Проект добавлен к резюме",
            "tech_stack": analysis["tech_stack"]
        }
    
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.post("/upload")
async def upload_resume(
    user_id: int = Form(...),
    file: UploadFile = File(...),
    title: str = Form(...)
):
    """Загрузка готового резюме (PDF/DOCX)"""
    allowed_extensions = [".pdf", ".docx", ".txt"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions and file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        pass
    
    content = await file.read()
    extracted_text = _extract_text_from_file(content, file.filename)
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO resumes (user_id, title, content, status, is_primary, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING resume_id
        """, (user_id, title, extracted_text, "draft", False))
        
        resume_id = cur.fetchone()[0]
        conn.commit()
        
        return {"resume_id": resume_id, "message": "Резюме загружено"}
    
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.post("/from-chat")
async def create_resume_from_chat(
    user_id: int = Form(...),
    session_id: int = Form(...),
    title: str = Form(...)
):
    """Создание резюме из истории чата"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверка доступа к сессии
        cur.execute("SELECT session_id FROM sessions WHERE session_id = %s AND user_id = %s", (session_id, user_id))
        if not cur.fetchone():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Получение истории сообщений
        cur.execute("""
            SELECT role, content FROM messages 
            WHERE session_id = %s ORDER BY created_at ASC LIMIT 50
        """, (session_id,))
        messages = cur.fetchall()
        
        if not messages:
            raise HTTPException(status_code=400, detail="Чат пуст")
        
        profile_data = _get_user_profile_data(user_id)
        
        # Формирование промпта для GigaChat
        chat_history = "\n".join([f"{msg[0]}: {msg[1]}" for msg in messages])
        
        prompt = f"""
        Ты — профессиональный карьерный консультант. На основе истории диалога создай структурированное резюме соискателя.

        ДАННЫЕ ИЗ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ:
        - Email: {profile_data['email']}
        - ФИО: {profile_data['full_name']}
        - Телефон: {profile_data['phone']}
        - Желаемая должность: {profile_data['desired_role']}
        - Локация: {profile_data['location']}
        - Уровень: {profile_data['level']}
        - Навыки: {json.dumps(profile_data['skills'], ensure_ascii=False)}

        ВАЖНОЕ ПРАВИЛО:
        - НЕ ВЫДУМЫВАЙ информацию, которой нет в диалоге. В особенности "Навыки и технологии"
        - Если каких-то данных не хватает, оставляй пометки в квадратных скобках, например: [ФИО], [Город], [Название компании], [Дата начала работы]
        - Если раздел не может быть заполнен из-за отсутствия информации, оставь только заголовок раздела с пометкой [требуется заполнить]

        ИСТОРИЯ ДИАЛОГА:
        {chat_history}

        ИЗВЛЕКИ И СТРУКТУРИРУЙ ТОЛЬКО ТО, ЧТО ЕСТЬ В ДИАЛОГЕ:
        1. Контактная информация (если упомянута)
        2. Желаемая должность и специализация
        3. Навыки и технологии (стек)
        4. Опыт работы (проекты, задачи, достижения)
        5. Образование и курсы
        6. Дополнительные компетенции (языки, сертификаты)

        ФОРМАТ ОТВЕТА:
        Чёткий, профессиональный текст для резюме. Используй маркеры, раздели на секции. Не добавляй лишних комментариев. Для отсутствующей информации используй квадратные скобки.
        """
        resume_content = ask_gigachat([{"role": "user", "content": prompt}])
        
        # Сохранение резюме
        cur.execute("""
            INSERT INTO resumes (user_id, title, content, status, is_primary, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING resume_id
        """, (user_id, title, resume_content, "draft", False))
        
        resume_id = cur.fetchone()[0]
        conn.commit()
        
        return {"resume_id": resume_id, "message": "Резюме создано из чата"}
    
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.post("/from-project")
async def create_resume_from_project(
    user_id: int = Form(...),
    title: str = Form(...),
    project_files: List[UploadFile] = File(...)
):
    """Создание резюме через анализ проекта"""
    conn = None
    try:
        # Чтение и анализ файлов
        files_data = []
        for file in project_files:
            content = await file.read()
            files_data.append((file.filename, content))
        
        analysis = _analyze_code_files(files_data)
        
        # Формирование промпта для GigaChat
        files_summary = "\n\n".join(analysis["code_samples"])

        # Получаем данные профиля
        profile_data = _get_user_profile_data(user_id)
        
        prompt = f"""
        Ты — профессиональный карьерный консультант. Создай структурированное резюме соискателя.
        А для раздела Опыта работы и Проектов проанализируй код проекта, чтобы создать 
        профессиональное описание.

        ДАННЫЕ ИЗ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ:
        - Email: {profile_data['email']}
        - ФИО: {profile_data['full_name']}
        - Телефон: {profile_data['phone']}
        - Желаемая должность: {profile_data['desired_role']}
        - Локация: {profile_data['location']}
        - Уровень: {profile_data['level']}
        - Навыки: {json.dumps(profile_data['skills'], ensure_ascii=False)}

        ВАЖНОЕ ПРАВИЛО:
        - Описывай ТОЛЬКО то, что видишь в коде
        - НЕ ВЫДУМЫВАЙ технологии, которые не используются в проекте. В особенности "Навыки и технологии"
        - Если какая-то информация не очевидна из кода, оставляй пометки в квадратных скобках

        СТЕК ТЕХНОЛОГИЙ (определён автоматически): {', '.join(analysis["tech_stack"])}

        ПРИМЕРЫ КОДА:
        {files_summary}

        СОЗДАЙ ОПИСАНИЕ, ВКЛЮЧАЯ:
        1. Название и тип проекта (веб-приложение, API, библиотека и т.д.) — если не очевидно, пиши [Название проекта]
        2. Используемый стек технологий — ТОЛЬКО те, что реально используются
        3. Ключевой функционал и реализованные фичи — на основе анализа кода
        4. Технические достижения (оптимизация, архитектура, тесты) — только если это видно из кода
        5. Роль разработчика в проекте — если не очевидно, пиши [Роль в проекте]

        ФОРМАТ: Профессиональный, лаконичный текст для резюме. 3-5 пунктов. Для отсутствующей информации используй квадратные скобки.
        """
        project_description = ask_gigachat([{"role": "user", "content": prompt}])
        
        # Формирование полного резюме
        resume_content = f"""# {title}
        ## Технологии
        {', '.join(analysis["tech_stack"]) if analysis["tech_stack"] else "Не определены"}

        ## Описание проекта
        {project_description}

        ## Структура
        Проанализировано файлов: {len(files_data)}
        """

        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO resumes (user_id, title, content, status, is_primary, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING resume_id
        """, (user_id, title, resume_content, "draft", False))
        
        resume_id = cur.fetchone()[0]
        conn.commit()
        
        return {
            "resume_id": resume_id,
            "tech_stack": analysis["tech_stack"],
            "message": "Резюме создано из проекта"
        }
    
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.get("/")
def get_user_resumes(user_id: int):
    """Получение списка резюме пользователя"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT resume_id, title, status, is_primary, created_at, updated_at
            FROM resumes
            WHERE user_id = %s
            ORDER BY is_primary DESC, updated_at DESC
        """, (user_id,))
        
        return [
            {
                "resume_id": r[0], "title": r[1], "status": r[2],
                "is_primary": r[3], "created_at": r[4].isoformat(), "updated_at": r[5].isoformat()
            }
            for r in cur.fetchall()
        ]
    finally:
        if conn: conn.close()

@router.get("/{resume_id}")
def get_resume(resume_id: int, user_id: int):
    """Получение конкретного резюме"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT resume_id, title, content, status, is_primary, created_at, updated_at
            FROM resumes WHERE resume_id = %s AND user_id = %s
        """, (resume_id, user_id))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Резюме не найдено")
        
        return {
            "resume_id": row[0], "title": row[1], "content": row[2],
            "status": row[3], "is_primary": row[4],
            "created_at": row[5].isoformat(), "updated_at": row[6].isoformat()
        }
    finally:
        if conn: conn.close()

@router.put("/{resume_id}")
def update_resume(
    resume_id: int,
    user_id: int = Query(...),
    resume_data: ResumeUpdate = Body(...)
):
    """Обновление резюме (текст, заголовок, статус, пометка 'основное')"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверка доступа
        cur.execute("SELECT resume_id FROM resumes WHERE resume_id = %s AND user_id = %s", (resume_id, user_id))
        if not cur.fetchone():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Собираем только те поля, которые пришли не None
        updates, values = [], []
        if resume_data.title is not None:
            updates.append("title = %s"); values.append(resume_data.title)
        if resume_data.content is not None:
            updates.append("content = %s"); values.append(resume_data.content)
        if resume_data.status is not None:
            updates.append("status = %s"); values.append(resume_data.status)
        if resume_data.is_primary is not None:
            updates.append("is_primary = %s"); values.append(resume_data.is_primary)
            
            # Если делаем основным → сбрасываем флаг у остальных резюме этого юзера
            if resume_data.is_primary:
                cur.execute(
                    "UPDATE resumes SET is_primary = FALSE WHERE user_id = %s AND resume_id != %s",
                    (user_id, resume_id)
                )
        
        if not updates:
            return {"message": "Нет данных для обновления"}
        
        updates.append("updated_at = NOW()")
        values.append(resume_id)
        
        cur.execute(f"UPDATE resumes SET {', '.join(updates)} WHERE resume_id = %s", values)
        conn.commit()
        
        return {"message": "Резюме обновлено"}
    
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.delete("/{resume_id}")
def delete_resume(resume_id: int, user_id: int):
    """Удаление резюме"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT resume_id FROM resumes WHERE resume_id = %s AND user_id = %s", (resume_id, user_id))
        if not cur.fetchone():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        cur.execute("DELETE FROM resumes WHERE resume_id = %s", (resume_id,))
        conn.commit()
        
        return {"message": "Резюме удалено"}
    
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.get("/{resume_id}/skills")
async def get_resume_skills(resume_id: int, user_id: int = Query(...)):
    """
    Анализ резюме ИИ и извлечение списка навыков (стека)
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Проверка доступа
        cur.execute("SELECT content FROM resumes WHERE resume_id = %s AND user_id = %s", (resume_id, user_id))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=403, detail="Резюме не найдено или доступ запрещен")
        
        content = row[0]
        
        # 2. Промпт для GigaChat
        prompt = f"""
        Извлеки из текста резюме ВСЕ технические навыки, языки программирования, фреймворки и инструменты.

        ТЕКСТ РЕЗЮМЕ:
        {content}

        ВЕРНИ ТОЛЬКО JSON-МАССИВ СТРОК. Не добавляй комментарии.
        Пример формата: ["Python", "Vue.js", "PostgreSQL", "Docker"]
        """
        
        raw_response = ask_gigachat([{"role": "user", "content": prompt}])
        
        # 3. Парсинг ответа ИИ
        try:
            # ИИ часто оборачивает JSON в markdown блоки (```json ... ```), убираем их
            clean_json = raw_response.replace("```json", "").replace("```", "").strip()
            skills_list = json.loads(clean_json)
            
            if isinstance(skills_list, list):
                # Фильтруем только строки
                return [skill for skill in skills_list if isinstance(skill, str)]
            else:
                return []
        except Exception as e:
            print(f"⚠️ Ошибка парсинга навыков от ИИ: {e}")
            return []
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()