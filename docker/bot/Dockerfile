FROM python:3.9-slim
RUN apt-get update && apt-get install -y postgresql-client
WORKDIR /bot
COPY requirements.txt .
COPY bot.py .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "bot.py"]