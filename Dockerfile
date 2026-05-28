# Использование официального легковесного образа Python
FROM python:3.11-slim

# Установка рабочей директории в контейнере
WORKDIR /app

# Копирование файла зависимостей
COPY clinic_app/requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего исходного кода приложения (кроме отчета, отсекаемого .dockerignore)
COPY clinic_app/ /app/clinic_app/

# Установка рабочей директории внутри папки приложения
WORKDIR /app/clinic_app

# Переменные окружения для Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Открытие порта 5000
EXPOSE 5000

# Команда для запуска инициализации бд и приложения
CMD ["sh", "-c", "python seed.py && python app.py"]
