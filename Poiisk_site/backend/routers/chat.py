from fastapi import APIRouter, HTTPException, Form
import json
from typing import Optional, List, Dict
from database import get_db_connection
from models import Message, ChatResponse
from utils.gigachat import ask_gigachat

router = APIRouter(tags=["Chat"])

@router.post("/chat", response_model=ChatResponse)
def chat(msg: Message, session_id: Optional[int] = None, user_id: int = None):
    """Отправить сообщение в чат"""
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Создание новой сессии если нужно
        if not session_id:
            cur.execute("""
                INSERT INTO sessions (user_id, title, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW()) RETURNING session_id
            """, (user_id, "Новый диалог"))
            session_id = cur.fetchone()[0]
        else:
            # Проверка доступа
            cur.execute("SELECT user_id FROM sessions WHERE session_id = %s", (session_id,))
            row = cur.fetchone()
            if not row or row[0] != user_id:
                raise HTTPException(status_code=403, detail="Доступ запрещен")

        # Сохранение сообщения пользователя
        cur.execute("""
            INSERT INTO messages (session_id, role, content, created_at)
            VALUES (%s, 'user', %s, NOW())
        """, (session_id, msg.text))

        # Загрузка истории
        cur.execute("""
            SELECT role, content FROM messages 
            WHERE session_id = %s 
            ORDER BY created_at ASC 
            LIMIT 15
        """, (session_id,))
        history = [{"role": r[0], "content": r[1]} for r in cur.fetchall()]

        # Запрос к GigaChat
        sys_prompt = """
            Ты — карьерный консультант в приложении "ПоИИск". Помогай составлять резюме через диалог.
            ФУНКЦИИ:
            1. Представься, предложи заполнить профиль (ФИО, телефон, должность, навыки) или предложи 
            заполнить информацию во вкладке "Профиль" также при желании соискателя объясни работу со 
            вкладкой "Резюме", где можно 3 способами создать резюме:
            • 💬 Из этого диалога (сейчас)
            • 📁 Из кода проекта (загружаешь папку → ИИ выделяет стек)
            • 📤 Загрузка PDF/DOCX (извлекается текст готового резюме)
            2. Собирай данные ПО ОЧЕРЕДИ (по 1-2 вопроса за сообщение):
            • Личные: ФИО, телефон, email, город
            • Цель: желаемая позиция (Junior/Middle/Senior + специализация)
            • Опыт: компания, период, должность, 3-5 достижений с цифрами, технологии
            • Образование: ВУЗ, курсы, сертификации
            • Навыки: языки, фреймворки, инструменты, уровень английского
            • Дополнительно: GitHub/LinkedIn, готовность к релокации
            3. Стиль: дружелюбный, профессиональный, умеренно используй ✅📌
            4. Завершение: "Готов сформировать резюме! Нажми 'Создать из чата' в разделе Резюме", но 
            сам резюме не составляй, так как этим занимается функционал в разделе "Резюме"

            ⚠️ ПРАВИЛА:
            • НЕ ВЫДУМЫВАЙ данные — если чего-то нет, пиши [требуется заполнить]
            • Для недостающей информации используй квадратные скобки: [ФИО], [Дата], [Компания]
            • Если пользователь уходит от темы — мягко возвращай к резюме
            • Не давай юридических/медицинских советов

            Пример начала:
            "Привет! 👋 Помогу составить резюме. Для начала:
            - Как тебя зовут?
            - На какую позицию ориентируешься? (например, Junior Python-разработчик)
            Или желаете узнать про функционал для быстрого заполнения информации и создания резюме?"
            """
        messages_for_ai = [{"role": "system", "content": sys_prompt}] + history
        answer = ask_gigachat(messages_for_ai)

        cur.execute("""
            INSERT INTO messages (session_id, role, content, metadata, created_at)
            VALUES (%s, 'assistant', %s, %s, NOW())
        """, (session_id, answer, None))  # Пока None, но можно добавить вакансии

        # Обновление времени сессии
        cur.execute("UPDATE sessions SET updated_at = NOW() WHERE session_id = %s", (session_id,))

        # Автозаголовок
        if len(history) <= 1:
            title_prompt = f"Придумай короткий заголовок (до 35 символов) для диалога: {msg.text}"
            auto_title = ask_gigachat([{"role": "user", "content": title_prompt}])
            cur.execute("UPDATE sessions SET title = %s WHERE session_id = %s", (auto_title.strip()[:35], session_id))

        conn.commit()

        return {
            "answer": answer,
            "session_id": session_id,
            "user_message": msg.text,
            "metadata": None  # Пока None
        }

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

# ===== ЭНДПОИНТЫ ДЛЯ УПРАВЛЕНИЯ ЧАТАМИ =====
@router.get("/api/chats")
def get_user_chats(user_id: int):
    """Получить список чатов пользователя"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT session_id, title, created_at, updated_at
            FROM sessions
            WHERE user_id = %s
            ORDER BY updated_at DESC
        """, (user_id,))
        rows = cur.fetchall()
        return [
            {"session_id": r[0], "title": r[1], "created_at": r[2].isoformat(), "updated_at": r[3].isoformat()}
            for r in rows
        ]
    finally:
        if conn:
            conn.close()

@router.post("/api/chats")
def create_new_chat(title: str = "Новый диалог", user_id: int = None):
    """Создать новую сессию"""
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sessions (user_id, title, created_at, updated_at)
            VALUES (%s, %s, NOW(), NOW()) RETURNING session_id
        """, (user_id, title))
        session_id = cur.fetchone()[0]
        conn.commit()
        return {"session_id": session_id, "title": title}
    finally:
        if conn:
            conn.close()

@router.get("/api/chats/{session_id}/messages")
def get_chat_messages(session_id: int, user_id: int = None):
    """Загрузить историю сообщений"""
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT user_id FROM sessions WHERE session_id = %s", (session_id,))
        row = cur.fetchone()
        if not row or row[0] != user_id:
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        cur.execute("""
            SELECT role, content, metadata, created_at 
            FROM messages 
            WHERE session_id = %s 
            ORDER BY created_at ASC
        """, (session_id,))
        rows = cur.fetchall()
        return [
            {"role": r[0], "content": r[1], "metadata": r[2], "created_at": r[3].isoformat()}
            for r in rows
        ]
    finally:
        if conn:
            conn.close()

@router.delete("/api/chats/{session_id}")
def delete_chat(session_id: int, user_id: int = None):
    """Удалить чат"""
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT user_id FROM sessions WHERE session_id = %s", (session_id,))
        row = cur.fetchone()
        if not row or row[0] != user_id:
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        cur.execute("DELETE FROM messages WHERE session_id = %s", (session_id,))
        cur.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
        conn.commit()
        return {"status": "deleted"}
    finally:
        if conn:
            conn.close()


@router.post("/search-vacancies")
def search_vacancies_in_chat(
    user_id: int = Form(...),
    session_id: Optional[int] = Form(None)
):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Создаем сессию если не передана
        if not session_id:
            cur.execute("""
                INSERT INTO sessions (user_id, title, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW()) RETURNING session_id
            """, (user_id, "Поиск вакансий"))
            session_id = cur.fetchone()[0]
        
        # Получаем данные профиля для поиска
        cur.execute("""
            SELECT desired_role, location, skills
            FROM user_profiles WHERE user_id = %s
        """, (user_id,))
        profile = cur.fetchone()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Профиль не найден")
        
        desired_role, location, skills_json = profile
        
        # Вызывов поиска вакансий
        from utils.hh_parser_service import search_vacancies_hhparser
        
        vacancies = search_vacancies_hhparser(
            query=desired_role or "разработчик",
            per_page=10,
            remote=('удален' in location.lower() if location else False),
            location=location
        )
        
        cur.execute("""
            INSERT INTO messages (session_id, role, content, metadata, created_at)
            VALUES (%s, 'assistant', %s, %s, NOW())
            RETURNING message_id
        """, (
            session_id,
            f"✅ Найдено {len(vacancies)} подходящих вакансий! Вот лучшие подборки на основе вашего профиля:",
            json.dumps({"vacancies": vacancies, "type": "job_search"})
        ))
        
        conn.commit()
        
        return {
            "message": "Вакансии найдены и сохранены в чат",
            "vacancies_count": len(vacancies),
            "session_id": session_id
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Search vacancies error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()