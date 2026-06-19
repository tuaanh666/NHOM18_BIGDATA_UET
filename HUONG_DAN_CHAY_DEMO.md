# 🎬 Hướng dẫn chạy DEMO

Tài liệu này hướng dẫn chạy nhanh sản phẩm demo của **Hệ thống gợi ý phim thời gian thực trên
nền tảng dữ liệu lớn**. Có 2 cách: **(A)** xem web ngay trong 1 phút (không cần Docker), và
**(B)** chạy toàn bộ Lambda Architecture đầy đủ (real-time + poster) bằng Docker.

---

## ⚡ Cách A — Xem web demo NGAY (không cần Docker, ~1 phút)

Repo kèm sẵn `serving/recsys.db` (kết quả gợi ý đã sinh từ ALS), nên có thể bật web ngay.

**Yêu cầu:** Python 3.10–3.12.

```bash
# 1. Cài thư viện cho web
pip install flask sqlalchemy

# 2. Chạy web (đọc SQLite, KHÔNG cần Docker/Spark)
cd serving
python app.py

# 3. Mở trình duyệt: http://localhost:5000
```

**Thử ngay:**
- Trang chủ → xem **phim phổ biến** + dashboard thống kê.
- Bấm **"Gợi ý cho tôi"** → nhập **User ID là bội số của 10** (ví dụ `10`, `100`, `200`) → xem
  danh sách phim được gợi ý cá nhân hóa.
- **"Tìm phim"** → gõ `matrix`, `star wars`…

> Ở cách A, mục *"Thịnh hành real-time"* và poster sẽ trống vì cần HBase + Wikimedia + TMDB
> (chỉ có ở cách B). Phần gợi ý ALS + phim phổ biến + tìm phim hoạt động đầy đủ.

---

## 🐳 Cách B — Chạy ĐẦY ĐỦ Lambda (Docker, real-time + poster)

Dựng toàn bộ 13 container: Kafka, HDFS, Spark, HBase, MySQL, Airflow, Flask, 2 producer
(replay + Wikimedia), consumer.

**Yêu cầu:** Docker Desktop (cấp ≥ 8GB RAM cho VM Linux).

```bash
# 1. Chuẩn bị biến môi trường
cp .env.example .env        # đổi mật khẩu MySQL; điền TMDB_API_KEY nếu muốn poster

# 2. Khởi động cụm
docker compose up -d --build
docker compose ps           # chờ 13 container Up/healthy

# 3. Nạp dữ liệu MovieLens lên HDFS  (cần tải dataset trước — xem mục Dataset)
MSYS_NO_PATHCONV=1 bash scripts/load_to_hdfs.sh

# 4. Huấn luyện ALS trên Spark (ghi gợi ý vào MySQL)
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --packages com.mysql:mysql-connector-j:8.3.0 \
  /app/batch/train_als.py

# 5. (Tùy chọn) Lấy poster phim thật từ TMDB
pip install pymysql sqlalchemy
export TMDB_API_KEY=...     # key v3 miễn phí từ themoviedb.org
python scripts/fetch_posters.py --links data/ml-25m/links.csv --limit 5000

# 6. Mở web: http://localhost:5000
```

**Real-time tự chạy:** service `wiki` đẩy sự kiện phim live từ **Wikimedia** vào Kafka, consumer
tổng hợp vào HBase → mục **"⚡ Thịnh hành real-time"** trên trang chủ tự đầy lên (~2 phim/phút).

### Các URL quản trị
| Dịch vụ | URL |
|---------|-----|
| **Web demo** | http://localhost:5000 |
| Spark Master | http://localhost:8080 |
| HDFS NameNode | http://localhost:9870 |
| HBase | http://localhost:16010 |
| Airflow | http://localhost:8088 (admin/admin) |

---

## 📦 Dataset

Bộ **MovieLens 25M** (~647MB) **không kèm trong repo**. Tải bằng một trong hai cách:

```bash
python ingestion/download_data.py
# hoặc tải thủ công, giải nén vào: data/ml-25m/
```
Nguồn: https://grouplens.org/datasets/movielens/25m/

---

## ✅ Checklist khi demo (gợi ý trình bày)

1. **Gợi ý cá nhân (Batch/ALS):** nhập User ID → danh sách phim phù hợp gu, kèm poster.
2. **Thịnh hành real-time (Speed/Wikimedia):** trang chủ → mục có badge **LIVE**, F5 vài lần
   trong ít phút thấy danh sách phim đổi theo hoạt động thật trên Wikipedia.
3. **Phim phổ biến (cold-start):** dành cho user mới.
4. **Tìm phim + REST API:** `GET /api/recommend/<id>`, `GET /api/trending`.
5. **Hạ tầng Big Data:** mở các UI Spark/HDFS/HBase/Airflow để thấy cụm chạy thật.

---

## 🛠️ Sự cố thường gặp

| Triệu chứng | Cách xử lý |
|-------------|------------|
| Kafka exit (NodeExists) sau khi restart | `docker compose up -d --force-recreate zookeeper kafka` |
| HBase :16010 trống, consumer đứng | `docker compose up -d --force-recreate hbase` rồi `docker compose restart stream` |
| Cổng 5000 bận | Dừng tiến trình Flask đang chạy local trước khi `docker compose up` |
| Container chết bất thường | Thiếu RAM → tăng RAM cho Docker Desktop |
| (Cách A) gợi ý rỗng | Bảng `movies` thiếu cột `poster_url` → chạy lại `scripts/build_demo_db.py` |

---

*Chi tiết kiến trúc & thuật toán: xem [README.md](README.md) và báo cáo [docs/REPORT.md](docs/REPORT.md).*
