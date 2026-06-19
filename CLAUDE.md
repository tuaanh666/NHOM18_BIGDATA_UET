# CLAUDE.md — Tổng quan & ngữ cảnh dự án

> **Mục đích:** Đọc DUY NHẤT file này là nắm toàn bộ dự án (không cần đọc hết source) để tiết kiệm token.
> Nội dung chi tiết phục vụ viết báo cáo: xem `CLAUDE_báo_cáo.md`. Báo cáo: `docs/REPORT.tex` & `docs/REPORT.md`.
> *Cập nhật lần cuối: 2026-06-16.*

---

## 1. Tổng quan dự án

- **Tên đề tài:** Hệ thống gợi ý phim thời gian thực trên nền tảng dữ liệu lớn
  *(Real-time Movie Recommendation System on Big Data Platform)*. Tên ngắn/web: **MovieRec**.
- **Môn:** Kỹ thuật và Công nghệ Dữ liệu lớn — ĐH Công nghệ, Viện Trí tuệ Nhân tạo.
- **GVHD:** TS. Trần Hồng Việt · ThS. Ngô Minh Hương · CN. Lương Sơn Bá. **Email mời GitHub:** thviet79@gmail.com.
- **Use case:** Recommendation Engine (E-commerce / Media Streaming / Social Networks).
- **Kiến trúc:** **Lambda Architecture** (Batch + Speed + Serving).
- **Thuật toán cốt lõi:** **ALS** (Alternating Least Squares) — Collaborative Filtering, Spark MLlib.
- **3 nguồn dữ liệu:** MovieLens 25M (lịch sử) · **Wikimedia EventStreams (real-time THẬT)** · TMDB (poster).
- **Sản phẩm nộp:** Báo cáo (LaTeX) · Slide (LaTeX/Beamer, **chưa làm**) · Demo · GitHub repo (mời thầy).
- **Mô phỏng bài mẫu** "Bitcoin Price Streaming Processing" (VNU-UET): cùng kiến trúc + stack, đổi sang bài toán phim.

---

## 2. Stack công nghệ

| Layer | Công nghệ | Vai trò trong dự án |
|-------|-----------|---------------------|
| Ingestion | **Kafka** + Zookeeper | Topic `ratings-stream`: nhận rating replay + sự kiện phim Wikipedia live |
| Data Lake | **HDFS** | Lưu `ratings.csv` 647MB + `movies.csv` |
| Batch | **Spark (PySpark) + MLlib** | Train ALS, sinh Top-N, phim phổ biến |
| Speed/Real-time view | **HBase** | Gợi ý real-time theo user (row=userId) + thịnh hành (row `__TRENDING__`) |
| Batch view | **MySQL** | `movies(+poster_url)`, `user_recommendations`, `popular_movies`, `stats` |
| Orchestration | **Airflow** | DAG: load HDFS → train → verify |
| Serving | **Flask** | Web demo + REST API (`/api/recommend/<id>`, `/api/trending`) |
| Deploy | **Docker Compose** | 13 container |
| Nguồn real-time | **Wikimedia EventStreams** | SSE công khai live, không key (= vai trò WebSocket Binance) |
| Làm giàu | **TMDB API** | Poster phim thật qua `tmdbId` |

---

## 3. Cấu trúc thư mục

```
BIG DATA/
├── docker-compose.yml          # 13 service (zookeeper,kafka,namenode,datanode,spark-master,
│                               #   spark-worker,hbase,mysql,airflow,ingestion,wiki,stream,serving)
├── .env                        # Kafka/MySQL/ALS/HBase + STREAM_RATE_PER_SEC + (TMDB_API_KEY không commit)
├── CLAUDE.md                   # File này (tổng quan)
├── CLAUDE_báo_cáo.md           # Kho nội dung chi tiết để viết báo cáo
├── web.md                      # Hướng dẫn deploy GCP (1 VM Compute Engine) — tùy chọn
├── data/ml-25m/                # MovieLens 25M (KHÔNG commit): ratings/movies/links/tags/genome...
├── ingestion/
│   ├── download_data.py        # tải MovieLens
│   ├── stream_producer.py      # replay rating → Kafka (MÔ PHỎNG)
│   └── wiki_stream_producer.py # Wikimedia EventStreams → Kafka (REAL-TIME THẬT) — có --test
├── batch/train_als.py          # PySpark ALS: train, RMSE/MAE, Top-N, phim phổ biến
├── stream/consumer.py          # Kafka → HBase: gợi ý thể loại (user) + trending (Wikimedia)
├── serving/
│   ├── app.py                  # Flask: index/recommend/search/health + /api/trending + poster
│   ├── templates/              # base,index,recommend,search,_card.html
│   └── static/style.css
├── scripts/
│   ├── load_to_hdfs.sh · mysql_init.sql · build_demo_db.py
│   ├── fetch_posters.py        # lấy poster TMDB → MySQL.poster_url
│   ├── make_charts.py          # sinh biểu đồ → docs/images/*.png
│   ├── build_user_history.py · run_local.ps1
├── airflow/dags/recsys_pipeline.py
└── docs/
    ├── REPORT.tex · REPORT.md  # báo cáo (LaTeX bám khung bài mẫu)
    └── images/                 # rating_distribution / top_genres / top_popular .png
```

---

## 4. Kết quả thực nghiệm (chạy thật 25M)

- **RMSE = 0.7965 · MAE = 0.6187** (test 20% trên **25.000.095** ratings) — ngang/vượt benchmark MovieLens.
- **400.000** gợi ý (20.000 user × Top-20), lọc phim ≥1.000 lượt (MIN_REC_RATINGS=1000) → gợi ý kinh điển.
- ALS: `rank=64, maxIter=10, regParam=0.08, coldStartStrategy=drop`. Users ~162.541, phim 62.423.
- **11.866 poster** TMDB; trending Wikimedia khớp ~**2 phim/phút** (thật).
- Demo: `http://localhost:5000`. URL admin: HDFS :9870 · Spark :8080 · HBase :16010 · Airflow :8088 (admin/admin).

---

## 5. Tiến độ

### ✅ Đã hoàn thành (hệ thống + demo)
- Toàn bộ Lambda stack code xong; **13 container Docker chạy thật**, verify real-time SỐNG end-to-end.
- ALS train trên **toàn bộ 25M** → RMSE 0.7965; sinh 400k gợi ý; bảng phim phổ biến (weighted rating).
- **Speed layer 2 nguồn:** Wikimedia (trending THẬT → HBase `__TRENDING__`) + replay (gợi ý thể loại/user).
- **Poster TMDB** (11.866 ảnh) + sửa lỗi emoji đè + cache-bust CSS `?v=2`.
- Demo web: gợi ý batch + real-time + trending + poster + search; REST API; dashboard.
- **Báo cáo LaTeX** `docs/REPORT.tex` (bám khung bài mẫu, có sơ đồ TikZ + 3 biểu đồ + công thức ALS).
- Tài liệu: `CLAUDE_báo_cáo.md` (kho nội dung), `web.md` (deploy GCP).

### ⏳ Còn lại để NỘP
- [ ] **Slide** (LaTeX/Beamer) — chưa làm.
- [ ] **GitHub repo**: push source + report + slide + dataset (xử lý 647MB: download script + sample, KHÔNG commit raw); **mời `thviet79@gmail.com`**.
- [ ] (Tùy chọn) Biên dịch REPORT.tex ra PDF trên Overleaf (cần upload `docs/images/` + dùng pdfLaTeX cho nhanh, hoặc XeLaTeX); chèn ảnh chụp web demo.
- [ ] (Tùy chọn) Deploy GCP theo `web.md`; thêm nút đánh giá trên web (real-time từ user thật).

---

## 6. Ghi chú kỹ thuật (quan trọng để chạy lại)

**Chạy local 1 lệnh:** `.\scripts\run_local.ps1` (thêm `-Sample` để nhanh). Windows gotchas (run_local tự xử lý):
- **JAVA_HOME** phải trỏ JDK thật: `C:\Program Files\Eclipse Adoptium\jdk-8.0.482.8-hotspot`
  (biến hệ thống `C:\Java\jre1.8.0_361` KHÔNG tồn tại → override).
- **PYSPARK_PYTHON / PYSPARK_DRIVER_PYTHON** → python.exe thật
  (`C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe`), tránh MS Store stub.
- **PYTHONUTF8=1** (in tiếng Việt, tránh cp1252). Cần **`setuptools<81`** (py3.12 bỏ distutils).
- Thiếu **`winutils.exe`** → KHÔNG ghi parquet/model local; ghi thẳng SQLite. DB demo `serving/recsys.db`.

**Poster TMDB:** cần `TMDB_API_KEY` (v3). `set TMDB_API_KEY=... && python scripts/fetch_posters.py --links data/ml-25m/links.csv [--limit N]` (nối MySQL localhost:3306). KHÔNG commit key. Tải xong chỉ cần refresh web.

**Real-time Wikimedia:** `wiki_stream_producer.py` đọc SSE → lọc `enwiki`+namespace bài viết → khớp tên phim (chuẩn hoá "The X"↔"X, The (year)", bỏ `(film)`) → Kafka. `consumer.py` cửa sổ trượt 2h → HBase `__TRENDING__`. Chạy thử host: `python ingestion/wiki_stream_producer.py --test --seconds 90`. Container cần `PYTHONUNBUFFERED=1` để thấy log.

---

## 7. Triển khai Docker (đã chạy thật) + lưu ý

`docker compose up -d --build` → 13 container. Lưu ý đã xử lý:
- Ảnh `bde2020/spark` (Alpine + Python 3.7, **không có numpy**) → `apk add py3-numpy` trên spark-master/worker;
  `train_als.py` bỏ phụ thuộc pandas (ghi SQLite bằng sqlite3, ghi MySQL bằng spark.createDataFrame).
- `load_to_hdfs.sh` từ Git Bash bị MSYS đổi path → thêm `MSYS_NO_PATHCONV=1` (hoặc nạp HDFS bằng PowerShell).
- Cổng 5000: dừng Flask local trước khi `up`.
- **HBase (`harisekhon/hbase:2.1`) hay crash khi `restart`** → sửa: `docker compose up -d --force-recreate hbase` rồi `docker compose restart stream`.
- Docker Desktop ~7.5 GiB cho VM → 13 container căng; service chết bất thường thì kiểm tra `docker stats` / tăng RAM.
- Spark (Linux) ghi thẳng MySQL qua JDBC `com.mysql:mysql-connector-j`.

---

## 8. So sánh bài mẫu & đánh giá Big Data (tóm tắt)

- **Ngang bài mẫu:** kiến trúc Lambda + đủ hệ sinh thái (Kafka/HDFS/Spark/HBase/MySQL/Airflow/Flask/Docker).
- **Ta nhỉnh hơn:** volume lớn rõ ràng (25M), thuật toán phân tán native (ALS), demo phong phú (poster/trending), real-time THẬT (Wikimedia).
- **5V:** Volume (25M) · Velocity (Wikimedia+Kafka) · Variety (CSV/MySQL/HBase/SSE/API) · Veracity (RMSE/MAE) · Value (web gợi ý).
- **Giới hạn thành thật khi bảo vệ:** chạy 1 máy (pseudo-distributed), volume vừa RAM, tín hiệu Wikimedia thưa, replay rating là mô phỏng nguồn (cơ chế xử lý real-time là thật).
