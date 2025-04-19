FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y netcat-openbsd

COPY . .

RUN chmod +x wait-for-it.sh

RUN pip install -r requirements.txt

# 👇 Add this line
ENV PYTHONPATH=/app

CMD ["./wait-for-it.sh", "db", "3306", "--", "python", "app/main.py"]
