import uvicorn
import threading
import webbrowser
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, chat, vacancies, resumes, profile, favorites
import sys
import io
from dotenv import load_dotenv
load_dotenv()  # Загружает переменные из .env

# Перенастраиваем стандартный вывод на UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ===== ПРИЛОЖЕНИЕ =====
app = FastAPI(title="Poiisk API", version="1.0")

# ===== CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== ПОДКЛЮЧЕНИЕ ROUTERS =====
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(vacancies.router)
app.include_router(resumes.router) 
app.include_router(profile.router)
app.include_router(favorites.router)

# ===== ROOT ENDPOINT =====
@app.get("/")
def root():
    return {
        "service": "Poiisk API",
        "status": "running",
        "frontend": "http://localhost:5173",
        "docs": "http://127.0.0.1:8000/docs"
    }

# ===== ЗАПУСК =====
def open_browser():
    webbrowser.open("http://localhost:5173")

if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    uvicorn.run(app, host="127.0.0.1", port=8000)