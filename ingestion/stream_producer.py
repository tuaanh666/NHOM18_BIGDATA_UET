"""
stream_producer.py — Giả lập luồng "rating mới" của người dùng, đẩy vào Kafka.

Ở đây ta mô tả lại
 các rating trong MovieLens như thể chúng đang xảy ra theo thời gian thực,
mô phỏng người dùng liên tục đánh giá phim trên một nền tảng streaming.
"""
import os
import csv
import json
import time
import random

from kafka import KafkaProducer

KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "kafka:9092")
TOPIC = os.environ.get("KAFKA_TOPIC_RATINGS", "ratings-stream")
RATINGS_CSV = os.environ.get("RATINGS_CSV", "/app/data/ml-25m/ratings.csv")
RATE_PER_SEC = float(os.environ.get("STREAM_RATE_PER_SEC", "5"))   
MAX_EVENTS = int(os.environ.get("STREAM_MAX_EVENTS", "0"))       


def create_producer(retries=30):
    for attempt in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: str(k).encode("utf-8"),
            )
            print(f"[OK] Kết nối Kafka tại {KAFKA_BROKER}")
            return producer
        except Exception as e:
            print(f"[..] Chờ Kafka ({attempt+1}/{retries}): {e}")
            time.sleep(5)
    raise RuntimeError("Không kết nối được Kafka")


def stream():
    if not os.path.exists(RATINGS_CSV):
        print(f"[!!] Không tìm thấy {RATINGS_CSV}. Chạy download_data.py trước.")
        return

    producer = create_producer()
    sent = 0
    delay = 1.0 / RATE_PER_SEC if RATE_PER_SEC > 0 else 0

    print(f"[..] Bắt đầu phát luồng rating -> topic '{TOPIC}' (~{RATE_PER_SEC}/giây)")
    with open(RATINGS_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            event = {
                "userId": int(row["userId"]),
                "movieId": int(row["movieId"]),
                "rating": float(row["rating"]),
                "timestamp": int(time.time()),
                "event_type": "rating",
            }
            producer.send(TOPIC, key=event["userId"], value=event)
            sent += 1
            if sent % 100 == 0:
                producer.flush()
                print(f"  -> Đã gửi {sent} rating events")
            if MAX_EVENTS and sent >= MAX_EVENTS:
                break
            if delay:
                time.sleep(delay * random.uniform(0.5, 1.5))

    producer.flush()
    print(f"[OK] Hoàn tất, tổng {sent} events.")


if __name__ == "__main__":
    stream()
