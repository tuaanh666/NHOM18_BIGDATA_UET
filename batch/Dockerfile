# Batch layer image — chạy spark-submit job train_als.py
FROM bitnami/spark:3.5.1

USER root
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Job được submit thủ công hoặc qua Airflow:
#   spark-submit --master spark://spark-master:7077 train_als.py
CMD ["spark-submit", "train_als.py"]
