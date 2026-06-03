from fastapi import APIRouter, HTTPException, Form, Query, Body
from passlib.context import CryptContext
from datetime import datetime, timezone
from typing import Dict, Any
from database import get_db_connection
from models import RegisterRequest, LoginResponse, ChangePasswordRequest, ChangeEmailRequest
import logging

logger = logging.getLogger(__name__)

# ===== КОНФИГУРАЦИЯ ПАРОЛЕЙ =====
pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12, deprecated="auto")
MAX_PASSWORD_BYTES = 72

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def _truncate_for_bcrypt(password: str) -> str:
    """Обрезает пароль до 72 байт для bcrypt"""
    pw_bytes = password.encode('utf-8')
    truncated = pw_bytes[:MAX_PASSWORD_BYTES]
    return truncated.decode('utf-8', errors='ignore')

def _hash_password(password: str) -> str:
    """Безопасное хеширование пароля"""
    safe_pw = _truncate_for_bcrypt(password)
    return pwd_context.hash(safe_pw)

def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    safe_pw = _truncate_for_bcrypt(plain_password)
    return pwd_context.verify(safe_pw, hashed_password)

def register_user(email: str, password: str) -> Dict[str, Any]:
    """Регистрация нового пользователя"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверка email
        cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            return {"success": False, "error": "Email уже зарегистрирован"}
        
        # Хеширование и вставка
        hashed_pw = _hash_password(password)
        cur.execute(
            "INSERT INTO users (email, hashed_password, created_at) VALUES (%s, %s, %s) RETURNING user_id",
            (email, hashed_pw, datetime.now(timezone.utc))
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        
        print(f"User registered: {email}, id={user_id}")
        return {"success": True, "user_id": user_id, "email": email}
    
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Database error: {e}")
        return {"success": False, "error": f"Ошибка БД: {str(e)}"}
    finally:
        if conn:
            conn.close()

def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    """Аутентификация пользователя"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT user_id, hashed_password FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        
        if not row:
            return {"success": False, "error": "Неверный email или пароль"}
        
        user_id, hashed_pw = row
        if not _verify_password(password, hashed_pw):
            return {"success": False, "error": "Неверный email или пароль"}
        
        return {"success": True, "user_id": user_id, "email": email}
    
    except Exception as e:
        print(f"Database error: {e}")
        return {"success": False, "error": f"Ошибка БД: {str(e)}"}
    finally:
        if conn:
            conn.close()

# ===== ROUTER =====
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=dict)
def api_register(req: RegisterRequest):
    """Регистрация нового пользователя"""
    result = register_user(req.email, req.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": "Регистрация успешна", "user_id": result["user_id"]}

@router.post("/login", response_model=LoginResponse)
def api_login(username: str = Form(...), password: str = Form(...)):
    """Вход в систему"""
    result = authenticate_user(username, password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    
    return {
        "message": "Вход выполнен",
        "user_id": result["user_id"],
        "email": result["email"],
        "access_token": f"temp_token_{result['user_id']}",
        "token_type": "bearer"
    }

@router.put("/change-password")
def change_password(user_id: int = Query(...), data: ChangePasswordRequest = Body(...)):
    """Смена пароля с проверкой текущего"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT hashed_password FROM users WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        
        if not row or not _verify_password(data.current_password, row[0]):
            raise HTTPException(status_code=401, detail="Неверный текущий пароль")
            
        cur.execute("UPDATE users SET hashed_password = %s WHERE user_id = %s", 
                    (_hash_password(data.new_password), user_id))
        conn.commit()
        return {"message": "Пароль успешно изменён"}
    except HTTPException: raise
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.put("/change-email")
def change_email(user_id: int = Query(...), data: ChangeEmailRequest = Body(...)):
    """Смена email с подтверждением паролем"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT hashed_password, email FROM users WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        
        if not row or not _verify_password(data.current_password, row[0]):
            raise HTTPException(status_code=401, detail="Неверный пароль для подтверждения")
        if row[1] == data.new_email:
            return {"message": "Email не изменился"}
            
        cur.execute("SELECT user_id FROM users WHERE email = %s", (data.new_email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Этот email уже занят")
            
        cur.execute("UPDATE users SET email = %s WHERE user_id = %s", (data.new_email, user_id))
        conn.commit()
        return {"message": "Email успешно изменён", "email": data.new_email}
    except HTTPException: raise
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()