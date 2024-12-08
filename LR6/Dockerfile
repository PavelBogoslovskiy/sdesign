# Используем Python 3.10
FROM python:3.10

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем PostgreSQL client для использования psql
RUN apt-get update && apt-get install -y postgresql-client


# Копируем основной код приложения
COPY main.py .
COPY create_and_insert_table.py .
COPY user_data.json .
COPY writer.py .

# # Устанавливаем команду по умолчанию
# CMD ["python", "main.py"]