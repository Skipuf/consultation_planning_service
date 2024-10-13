# Dockerfile
FROM python:3.11

# Установка зависимостей
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода проекта
COPY . /app/

# Настройка переменных окружения Django
ENV PYTHONUNBUFFERED=1

# Команда для запуска сервера
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]