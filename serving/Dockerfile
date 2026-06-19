FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DB_URL=mysql+pymysql://mluser:mlpassword@mysql:3306/movielens
EXPOSE 5000

CMD ["python", "app.py"]
