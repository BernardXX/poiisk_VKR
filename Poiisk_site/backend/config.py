# Конфигурация базы данных
DB_CONFIG = {
    "database": "poiisk",
    "user": "postgres",
    "password": "root",
    "host": "localhost",
    "port": "5432"
}

# Путь к токену GigaChat
TOKEN_FILE = "token.txt"

def get_token():
    """Получение токена из файла"""
    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()