from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ===== МОДЕЛИ АВТОРИЗАЦИИ =====
class RegisterRequest(BaseModel):
    email: str
    password: str

# ===== МОДЕЛИ СООБЩЕНИЙ =====
class Message(BaseModel):
    text: str

# ===== МОДЕЛИ ДЛЯ ОТВЕТОВ =====
class ChatResponse(BaseModel):
    answer: str
    session_id: int
    user_message: Optional[str] = None

class LoginResponse(BaseModel):
    message: str
    user_id: int
    email: str
    access_token: str
    token_type: str = "bearer"

# ===== МОДЕЛИ ДЛЯ РЕЗЮМЕ =====
class ResumeCreate(BaseModel):
    title: str
    content: str
    status: str = "draft"
    is_primary: bool = False

class ResumeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    is_primary: Optional[bool] = None

# ===== МОДЕЛИ ДЛЯ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ =====
class UserProfileCreate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    social_links: Optional[Dict[str, str]] = {}

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    desired_role: Optional[str] = None
    location: Optional[str] = None
    level: Optional[str] = None
    skills: Optional[Dict[str, Any]] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

class ChangeEmailRequest(BaseModel):
    new_email: EmailStr
    current_password: str

class UserProfileResponse(BaseModel):
    profile_id: int
    user_id: int
    full_name: Optional[str] = None
    phone: Optional[str] = None
    social_links: Dict[str, str] = {}
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True