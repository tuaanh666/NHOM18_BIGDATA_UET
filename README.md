# 🎬 Hệ thống gợi ý phim thời gian thực trên nền tảng dữ liệu lớn
### *Real-time Movie Recommendation System on Big Data Platform*

Hệ thống **gợi ý phim** xây trên nền tảng Big Data theo **Lambda Architecture** (Batch + Speed +
Serving). Lõi là thuật toán **ALS (Alternating Least Squares)** của Spark MLlib, huấn luyện trên
**MovieLens 25M** (25 triệu lượt đánh giá). Điểm khác biệt: hệ thống lấy **dữ liệu real-time
THẬT** từ **Wikimedia EventStreams** để hiện phim đang thịnh hành, và làm giàu giao diện bằng
**poster phim thật** từ TMDB. Toàn bộ đóng gói bằng **Docker Compose (13 container)**.

> Môn: *Kỹ thuật và Công nghệ Dữ liệu lớn* — ĐH Công nghệ, Viện Trí tuệ Nhân tạo.

---

## ✨ Điểm nổi bật

- **ALS phân tán** huấn luyện trên toàn bộ 25M ratings → **RMSE 0.7965 · MAE 0.6187**.
- **Lambda Architecture** đầy đủ: Batch (chính xác) + Speed (tươi mới) + Serving.
- **Real-time THẬT** từ Wikimedia (không phải mô phỏng) → mục "⚡ Thịnh hành real-time".
- **Poster phim thật** (TMDB, 11.866 ảnh) + tìm phim + REST API.
- **13 container** chạy thật, verify end-to-end; chạy lại local bằng **1 lệnh**.

---

## 🏗️ Kiến trúc (Lambda Architecture)

```
NGUỒN DỮ LIỆU              INGESTION        XỬ LÝ                       SERVING
──────────────────────────────────────────────────────────────────────────────────
MovieLens 25M (lịch sử) ─► HDFS ─────────► Spark ALS ─► MySQL (Batch View) ─┐
                                          (train, Top-N)                     │
                                                                             ├─► Flask Web ─► Người dùng
Wikimedia (real-time THẬT) ─► Kafka ─► Consumer ─► HBase (Speed View) ───────┘   (+ poster TMDB)
                                       (trending + thể loại)
                                            ▲
TMDB ─► MySQL.poster_url            Airflow lập lịch train lại
```

- **Batch Layer:** MovieLens 25M trên HDFS → Spark train ALS → MySQL. Airflow lập lịch retrain.
- **Speed Layer:** Wikimedia (phim đang được sửa trên Wikipedia) + replay rating → Kafka →
  consumer → HBase (danh sách thịnh hành `__TRENDING__` + gợi ý thể loại theo user).
- **Serving Layer:** Flask hợp nhất gợi ý batch (MySQL) + real-time (HBase) + poster (TMDB).

| Layer | Công nghệ | Vai trò |
|-------|-----------|---------|
| Ingestion | **Kafka** + Zookeeper | Topic `ratings-stream`: rating replay + sự kiện phim Wikipedia live |
| Data Lake | **HDFS** | Lưu MovieLens 25M thô (`ratings.csv` ~647MB) |
| Batch | **Spark (PySpark) + MLlib (ALS)** | Train mô hình, sinh Top-N gợi ý |
| Speed View | **HBase** | Gợi ý real-time theo user + danh sách thịnh hành |
| Batch View | **MySQL** | Metadata phim (+poster) + gợi ý + thống kê |
| Orchestration | **Airflow** | Lập lịch ETL & retrain |
| Serving | **Flask** | Web demo + REST API |
| Nguồn real-time | **Wikimedia EventStreams** | Luồng SSE công khai, không key |
| Làm giàu | **TMDB API** | Poster phim thật |
| Deploy | **Docker Compose** | Đóng gói 13 container |

---

## 📊 Kết quả (chạy thật 25M)

| Chỉ số | Giá trị |
|--------|---------|
| Tổng ratings | **25.000.095** (~162.541 user, 62.423 phim) |
| **RMSE / MAE** (test 20%) | **0.7965 / 0.6187** |
| Gợi ý sinh ra | 400.000 dòng (20.000 user × Top-20) |
| Poster TMDB | 11.866 ảnh |

---

## 📂 Cấu trúc thư mục

```
BIG DATA/
├── docker-compose.yml           # 13 service (Lambda stack đầy đủ)
├── .env.example                 # mẫu biến môi trường (copy thành .env)
├── README.md · CLAUDE.md        # hướng dẫn / tổng quan
├── CLAUDE_báo_cáo.md · web.md   # kho nội dung báo cáo / hướng dẫn deploy GCP
├── data/ml-25m/                 # MovieLens 25M (KHÔNG commit — tự tải)
├── ingestion/
│   ├── download_data.py         # tải MovieLens 25M
│   ├── stream_producer.py       # replay rating → Kafka (mô phỏng)
│   └── wiki_stream_producer.py  # Wikimedia EventStreams → Kafka (REAL-TIME THẬT)
├── batch/train_als.py           # PySpark ALS: train, RMSE/MAE, Top-N, phim phổ biến
├── stream/consumer.py           # Kafka → HBase: trending (Wikimedia) + gợi ý thể loại
├── serving/
│   ├── app.py                   # Flask: recommend/search/trending + REST API
│   ├── templates/ · static/     # giao diện web (có poster)
├── scripts/
│   ├── load_to_hdfs.sh · mysql_init.sql · build_demo_db.py
│   ├── fetch_posters.py         # lấy poster TMDB → MySQL
│   ├── make_charts.py · run_local.ps1
├── airflow/dags/recsys_pipeline.py
└── docs/
    ├── REPORT.tex · REPORT.md   # báo cáo (LaTeX)
    └── images/                  # biểu đồ
```

---

## 🚀 Cách chạy (chi tiết)

### Yêu cầu chung
- **Python 3.10–3.12** và **JDK 8/11/17** (cho Spark). Với Windows cần `python.exe` thật (không
  dùng bản Microsoft Store stub).
- **Docker Desktop** (cho cách chạy đầy đủ) — cấp tối thiểu ~8GB RAM cho VM Linux.
- Lấy **TMDB API key** (miễn phí) tại themoviedb.org nếu muốn poster.

Trước hết sao chép file môi trường:
```bash
cp .env.example .env      # rồi mở .env, đổi mật khẩu MySQL và điền TMDB_API_KEY (nếu có)
```

---

### ⚡ Cách 1 — Demo nhanh trên LOCAL (khuyên dùng để chấm)

Chạy được ngay sản phẩm gợi ý mà **không cần Docker** (ghi thẳng SQLite). Nhanh nhất là dùng
script 1-lệnh đã xử lý sẵn mọi cấu hình Windows (JAVA_HOME, PYSPARK_PYTHON, setuptools<81…):

```powershell
# Windows PowerShell — chạy từ thư mục dự án
.\scripts\run_local.ps1            # chạy đầy đủ trên 25M
.\scripts\run_local.ps1 -Sample    # chạy nhanh trên mẫu nhỏ (vài phút)
```
Script sẽ: tải dữ liệu (nếu thiếu) → train ALS → nạp SQLite (`serving/recsys.db`) → bật web.
Mở **http://localhost:5000**.

> Repo đã kèm sẵn `serving/recsys.db` (17MB), nên có thể **chạy web ngay** mà chưa cần train:
> ```bash
> cd serving && python app.py     # mở http://localhost:5000
> ```

**Chạy thủ công từng bước (nếu không dùng script):**
```bash
pip install pyspark==3.5.1 "setuptools<81" pandas pyarrow flask sqlalchemy
python ingestion/download_data.py          # tải MovieLens 25M về data/ml-25m/
python batch/train_als.py                  # train ALS → batch/output (hoặc SQLite)
python scripts/build_demo_db.py            # nạp kết quả vào serving/recsys.db
cd serving && python app.py                # web demo: http://localhost:5000
```

---

### 🐳 Cách 2 — Lambda đầy đủ bằng DOCKER (13 container)

Dựng toàn bộ hệ sinh thái Big Data thật.

**Bước 1 — Khởi động cụm:**
```bash
docker compose up -d --build
docker compose ps                  # kiểm tra 13 container Up/healthy
```

**Bước 2 — Nạp dữ liệu MovieLens lên HDFS:**
```bash
# Git Bash:
MSYS_NO_PATHCONV=1 bash scripts/load_to_hdfs.sh
# (hoặc nạp bằng lệnh hdfs dfs -put trong PowerShell nếu MSYS đổi path)
```
MySQL tự khởi tạo schema từ `scripts/mysql_init.sql` khi container `mysql` lần đầu chạy.

**Bước 3 — Huấn luyện ALS trên Spark (ghi Batch View vào MySQL):**
```bash
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --packages com.mysql:mysql-connector-j:8.3.0 \
  /app/batch/train_als.py
# (hoặc kích hoạt DAG `movielens_recsys_batch` trên Airflow UI :8088)
```

**Bước 4 — Real-time tự chạy:** service `wiki` đẩy sự kiện phim live từ Wikimedia vào Kafka,
service `stream` (consumer) tổng hợp vào HBase. Producer replay (`ingestion`) cũng tự chạy.

**Bước 5 — Lấy poster TMDB (tùy chọn):**
```bash
pip install pymysql sqlalchemy
export TMDB_API_KEY=...            # key v3 của bạn
python scripts/fetch_posters.py --links data/ml-25m/links.csv --limit 5000
# ảnh đọc từ DB lúc request → chỉ cần refresh web, không build lại
```

**Bước 6 — Mở web demo:** http://localhost:5000

| Dịch vụ | URL |
|---------|-----|
| **Web demo (Flask)** | http://localhost:5000 |
| Spark Master UI | http://localhost:8080 |
| HDFS NameNode UI | http://localhost:9870 |
| HBase UI | http://localhost:16010 |
| Airflow UI | http://localhost:8088 (admin/admin) |

> Muốn xem mục **"⚡ Thịnh hành real-time"** đầy lên: để service `wiki` chạy vài phút (luồng
> Wikimedia khớp ~2 phim/phút), rồi F5 trang chủ.

---

### 🛠️ Xử lý sự cố thường gặp

| Triệu chứng | Cách xử lý |
|-------------|------------|
| **HBase :16010 trống, consumer đứng** | `docker compose up -d --force-recreate hbase` rồi `docker compose restart stream` |
| Spark worker thiếu numpy (ảnh bde2020) | `docker exec spark-master apk add py3-numpy` (và spark-worker) |
| Cổng 5000 bận | Dừng Flask local trước khi `docker compose up` |
| Container chết bất thường | Thiếu RAM — `docker stats`, tăng RAM cho Docker Desktop |
| (Local) Spark worker crash trên Windows | Đặt `PYSPARK_PYTHON` trỏ python.exe thật; cần `setuptools<81` |
| Container `wiki` không có log | Đặt `PYTHONUNBUFFERED=1` (đã set trong compose) |

---

## 🧮 Thuật toán ALS

ALS phân rã ma trận đánh giá `R (users × movies)` thành hai ma trận ẩn `U (users × k)` và
`V (movies × k)`, tối thiểu hóa:

```
min Σ_(u,i) (r_ui − uᵤᵀ·vᵢ)² + λ(Σ‖uᵤ‖² + Σ‖vᵢ‖²)
```

giải **luân phiên** (cố định `V` giải `U`, rồi ngược lại) — song song hóa tốt trên Spark, phù
hợp dữ liệu lớn. Siêu tham số: `rank=64, maxIter=10, regParam=0.08, coldStartStrategy=drop`,
Top-N=20, lọc phim ≥1000 lượt. Đánh giá bằng **RMSE / MAE** trên tập test 20%.

---

## 📑 Tài liệu

- Báo cáo LaTeX: [docs/REPORT.tex](docs/REPORT.tex) · bản markdown: [docs/REPORT.md](docs/REPORT.md)
- Tổng quan & ghi chú kỹ thuật: [CLAUDE.md](CLAUDE.md)
- Hướng dẫn deploy lên Google Cloud: [web.md](web.md)

> **Dataset:** MovieLens 25M (~647MB) không kèm trong repo. Tải bằng `ingestion/download_data.py`
> hoặc tại [grouplens.org/datasets/movielens/25m](https://grouplens.org/datasets/movielens/25m/).
