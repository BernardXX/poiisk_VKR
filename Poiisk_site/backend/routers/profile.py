from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, Dict
from database import get_db_connection
from models import UserProfileUpdate
import json

router = APIRouter(prefix="/api/profile", tags=["Profile"])

@router.get("/")
def get_profile(user_id: int = Query(...)):
    """Получение профиля пользователя"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT full_name, phone, social_links, desired_role, location, level, skills
            FROM user_profiles WHERE user_id = %s
        """, (user_id,))
        row = cur.fetchone()

        if not row:
            # Создаём пустой профиль при первом обращении
            cur.execute("""
                INSERT INTO user_profiles (user_id, social_links, skills)
                VALUES (%s, %s, %s)
                RETURNING full_name, phone, social_links, desired_role, location, level, skills
            """, (user_id, '{}', '{}'))
            row = cur.fetchone()
            conn.commit()

        # Преобразуем JSONB в Python-объекты
        social_links = row[2] if isinstance(row[2], dict) else json.loads(row[2]) if row[2] else {}
        skills = row[6] if isinstance(row[6], dict) else json.loads(row[6]) if row[6] else {}

        return {
            "full_name": row[0],
            "phone": row[1],
            "social_links": social_links,
            "desired_role": row[3],
            "location": row[4],
            "level": row[5],
            "skills": skills
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.put("/")
def update_profile(user_id: int = Query(...), profile: UserProfileUpdate = Body(...)):
    """Обновление профиля пользователя"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Если профиля нет → создаём заглушку
        cur.execute("SELECT user_id FROM user_profiles WHERE user_id = %s", (user_id,))
        if not cur.fetchone():
            cur.execute("INSERT INTO user_profiles (user_id, social_links, skills) VALUES (%s, %s, %s)", 
                        (user_id, '{}', '{}'))

        updates, values = [], []
        if profile.full_name is not None:
            updates.append("full_name = %s"); values.append(profile.full_name)
        if profile.phone is not None:
            updates.append("phone = %s"); values.append(profile.phone)
        if profile.social_links is not None:
            updates.append("social_links = %s::jsonb"); values.append(json.dumps(profile.social_links))
        if profile.desired_role is not None:
            updates.append("desired_role = %s"); values.append(profile.desired_role)
        if profile.location is not None:
            updates.append("location = %s"); values.append(profile.location)
        if profile.level is not None:
            updates.append("level = %s"); values.append(profile.level)
        if profile.skills is not None:
            updates.append("skills = %s::jsonb"); values.append(json.dumps(profile.skills))

        if not updates:
            return {"message": "Нет данных для обновления"}

        updates.append("updated_at = NOW()")
        values.append(user_id)

        cur.execute(f"UPDATE user_profiles SET {', '.join(updates)} WHERE user_id = %s", values)
        conn.commit()
        return {"message": "Профиль успешно обновлён"}
    
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()