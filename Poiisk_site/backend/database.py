import psycopg2
from config import DB_CONFIG

def get_db_connection():
    """Создание подключения к базе данных"""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    return conn