# Используем официальный образ Python
FROM python:3.12

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Делаем main.py исполняемым
RUN chmod +x src/scripts/main.py

# Запускаем скрипт
CMD ["python3", "src/scripts/main.py"]
