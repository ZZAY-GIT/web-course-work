import os

class Config:
    # Секретный ключ для сессий и безопасности
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clinic-super-secret-key-2026'
    
    # URI базы данных: PostgreSQL при наличии в окружении, иначе SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///clinic.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Папка для загрузки медицинских документов
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
    
    # Максимальный размер загружаемого файла (16 МБ)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
