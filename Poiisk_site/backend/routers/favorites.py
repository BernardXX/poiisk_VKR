from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List
from database import get_db_connection
import json
from datetime import datetime

router = APIRouter(prefix="/api/favorites", tags=["Favorites"])

@router.post("/")
def add_to_favorites(
    user_id: int = Body(...),
    hh_vacancy_id: int = Body(...),
    title: str = Body(...),
    company: str = Body(...),
    url: str = Body(...),
    salary_snapshot: Optional[str] = Body(None),
    location_snapshot: Optional[str] = Body(None)
):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        vacancy_id = hh_vacancy_id
        if vacancy_id == 0 and url:
            try:
                # URL вакансии обычно выглядит как https://hh.ru/vacancy/12345678
                vacancy_id = int(url.rstrip('/').split('/')[-1])
            except ValueError:
                vacancy_id = 0  # Если не удалось извлечь, оставляем 0
        
        cur.execute("""
            INSERT INTO favorites (
                user_id, hh_vacancy_id, title, company, url,
                salary_snapshot, location_snapshot, saved_at, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            ON CONFLICT (user_id, url) 
            DO UPDATE SET 
                hh_vacancy_id = EXCLUDED.hh_vacancy_id,
                title = EXCLUDED.title,
                company = EXCLUDED.company,
                salary_snapshot = EXCLUDED.salary_snapshot,
                location_snapshot = EXCLUDED.location_snapshot,
                status = 'saved',
                saved_at = NOW()
            RETURNING vacancy_id
        """, (
            user_id, vacancy_id, title, company, url,
            salary_snapshot, location_snapshot, 'saved'
        ))
        
        vacancy_id_result = cur.fetchone()[0]
        conn.commit()
        
        return {
            "message": "Вакансия добавлена в избранное",
            "vacancy_id": vacancy_id_result,
            "status": "added"
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Add favorite error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@router.delete("/")
def remove_from_favorites(
    user_id: int = Query(...),
    vacancy_url: str = Query(...)
):
    """Удалить вакансию из избранного"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            DELETE FROM favorites 
            WHERE user_id = %s AND url = %s
        """, (user_id, vacancy_url))
        
        conn.commit()
        
        return {"message": "Вакансия удалена из избранного"}
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Remove favorite error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@router.get("/")
def get_user_favorites(user_id: int = Query(...)):
    """Получить список вакансий в избранном"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT vacancy_id, hh_vacancy_id, title, company, url,
                   salary_snapshot, location_snapshot, saved_at, status
            FROM favorites
            WHERE user_id = %s AND status = 'saved'
            ORDER BY saved_at DESC
        """, (user_id,))
        
        rows = cur.fetchall()
        
        return [
            {
                "vacancy_id": r[0],
                "hh_vacancy_id": r[1],
                "title": r[2],
                "company": r[3],
                "url": r[4],
                "salary_snapshot": r[5],
                "location_snapshot": r[6],
                "saved_at": r[7].isoformat() if r[7] else None,
                "status": r[8]
            }
            for r in rows
        ]
        
    except Exception as e:
        print(f"Get favorites error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@router.get("/check")
def check_favorite(
    user_id: int = Query(...),
    vacancy_url: str = Query(...)
):
    """Проверить, есть ли вакансия в избранном"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT vacancy_id FROM favorites 
            WHERE user_id = %s AND url = %s AND status = 'saved'
        """, (user_id, vacancy_url))
        
        is_favorite = cur.fetchone() is not None
        
        return {"is_favorite": is_favorite}
        
    except Exception as e:
        print(f"Check favorite error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()