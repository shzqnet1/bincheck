FROM python:3.11-slim

WORKDIR /app

# копируем файлы
COPY . /app

# устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# запуск бота
CMD ["python", "bot.py"]
