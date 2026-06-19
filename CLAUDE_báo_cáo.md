# CLAUDE_báo_cáo.md — Kho nội dung phục vụ viết báo cáo LaTeX

> File này gom **toàn bộ nội dung, số liệu, kiến trúc, mã nguồn và lập luận** của dự án để
> tra cứu khi viết báo cáo / slide. Số liệu đều là **thật** (đã chạy 25M ratings).
> Báo cáo LaTeX nằm ở `docs/REPORT.tex`; bản markdown ở `docs/REPORT.md`.

---

## 0. Thông tin chung (cho trang bìa)

| Mục | Nội dung |
|-----|----------|
| **Tên đề tài** | Hệ thống gợi ý phim thời gian thực trên nền tảng dữ liệu lớn |
| **EN** | Real-time Movie Recommendation System on Big Data Platform |
| **Tên ngắn / web** | MovieRec |
| **Môn** | Kỹ thuật và Công nghệ Dữ liệu lớn |
| **Trường** | Đại học Công nghệ — Viện Trí tuệ Nhân tạo |
| **GVHD** | TS. Trần Hồng Việt · ThS. Ngô Minh Hương · CN. Lương Sơn Bá |
| **Email mời (thầy)** | thviet79@gmail.com (mời vào GitHub repo) |
| **Năm** | 2026 |

**Sản phẩm cần nộp:** (1) Báo cáo (LaTeX), (2) Slide (LaTeX/Beamer), (3) Demo sản phẩm,
(4) GitHub repo (slide + report + source + dataset).

---

## 1. Tóm tắt dự án (Abstract / Mở đầu)

- **Bài toán:** Hệ thống gợi ý phim (Movie Recommendation System) — cá nhân hóa phim cho người dùng.
- **Use case:** Building Product/Content Recommendation Engines (E-commerce / Media Streaming / Social Networks).
- **Dữ liệu:** MovieLens **25M** (25 triệu ratings) + nguồn real-time thật Wikimedia + poster TMDB.
- **Kiến trúc:** **Lambda Architecture** (Batch + Speed + Serving).
- **Thuật toán cốt lõi:** **ALS (Alternating Least Squares)** — Collaborative Filtering trong Spark MLlib.
- **Kết quả:** RMSE **0.7965**, MAE **0.6187**; demo web có poster + gợi ý real-time.
- **Đóng góp riêng so với bài mẫu:** dùng ALS phân tán trên 25M, nguồn real-time thật (Wikimedia),
  poster phim thật (TMDB), giao diện web phong phú.

---

## 2. Kiến trúc Lambda (3 tầng)

```
NGUỒN DỮ LIỆU                IN­GESTION        XỬ LÝ                    SERVING
─────────────────────────────────────────────────────────────────────────────
MovieLens 25M (lịch sử) ──► HDFS ─────────► Spark ALS ──► MySQL (Batch View) ─┐
                                                                              ├─► Flask Web ──► Người dùng
Wikimedia (real-time thật) ─► Kafka ──► Consumer ──► HBase (Speed View) ───────┘
                                                          ▲
TMDB (poster) ──► MySQL.poster_url           Airflow lập lịch retrain
```

- **Batch Layer:** MovieLens 25M trên HDFS → Spark huấn luyện ALS → sinh Top-N gợi ý → MySQL.
  Airflow lập lịch huấn luyện lại định kỳ.
- **Speed Layer:** Hai nguồn real-time:
  - **Wikimedia EventStreams** (thật) → Kafka → consumer tổng hợp "phim thịnh hành" → HBase row `__TRENDING__`.
  - **Replay rating** (mô phỏng) → Kafka → consumer cập nhật gợi ý theo thể loại từng user → HBase row = `userId`.
- **Serving Layer:** Flask hợp nhất gợi ý batch (MySQL) + real-time (HBase) + poster (TMDB) → web + REST API.

---

## 3. Stack công nghệ & vai trò trong dự án

| Công nghệ | Vai trò CỤ THỂ trong dự án |
|-----------|-----------------------------|
| **Apache Kafka + Zookeeper** | Ingestion Layer — topic `ratings-stream` nhận luồng sự kiện (rating replay + sự kiện phim Wikipedia live) |
| **HDFS (Hadoop)** | Data Lake — lưu `ratings.csv` 647MB + `movies.csv` để Spark đọc song song |
| **Apache Spark (PySpark) + MLlib** | Batch — train ALS phân tán, sinh Top-N, tính phim phổ biến |
| **Apache HBase** | Real-time View — lưu gợi ý real-time theo user + danh sách thịnh hành; truy vấn nhanh qua Thrift (happybase) |
| **MySQL** | Batch View — bảng `movies` (kèm `poster_url`), `user_recommendations`, `popular_movies`, `stats` |
| **Apache Airflow** | Orchestration — DAG lập lịch: load HDFS → train ALS → verify |
| **Flask** | Serving — web demo + REST API (`/api/recommend/<id>`, `/api/trending`) |
| **Docker Compose** | Đóng gói toàn hệ thống (13 container) |
| **Wikimedia EventStreams** | Nguồn REAL-TIME THẬT (SSE công khai, miễn phí, không key) |
| **TMDB API** | Lấy poster phim thật qua `tmdbId` |

---

## 4. Nguồn dữ liệu (chi tiết)

### 4.1 Dữ liệu lịch sử — MovieLens 25M (GroupLens, ĐH Minnesota)

| Tệp | Mô tả | Kích thước | Dùng |
|-----|-------|-----------|------|
| `ratings.csv` | **25.000.095** dòng: `userId, movieId, rating, timestamp` | **647MB** | Train ALS |
| `movies.csv` | **62.423** phim: `movieId, title, genres` | 2.9MB | Metadata + khớp tên |
| `links.csv` | 62.423 dòng: `movieId, imdbId, tmdbId` | 1.4MB | Lấy poster TMDB |
| `tags.csv` | ~1 triệu tag | 38MB | **Không dùng** |
| `genome-scores.csv` | điểm genome | **416MB** | **Không dùng** |
| `genome-tags.csv` | tên genome | 18KB | **Không dùng** |

- Thang điểm rating: **0.5 → 5.0** (bước 0.5). Số người dùng ~**162.541**.
- Phân bố điểm lệch về **3.0–4.0** (người dùng hay chấm cao).
- Top thể loại theo lượt đánh giá: **Drama, Comedy, Action**.

### 4.2 Dữ liệu real-time THẬT — Wikimedia EventStreams
- Endpoint công khai: `https://stream.wikimedia.org/v2/stream/recentchange` (SSE, live 24/7, **không cần key**).
- Mỗi sự kiện = một lượt chỉnh sửa Wikipedia (có `wiki`, `type`, `title`, `user`, `namespace`, `bot`).
- Dự án **lọc** `wiki=enwiki`, `namespace=0` (bài viết), `type∈{edit,new}`, **khớp tên** trang phim
  với MovieLens → coi là tín hiệu "phim đang được quan tâm ngay bây giờ".
- **Chuẩn hóa tên** để khớp: "The Matrix" / "Rio (2011 film)" ↔ "Matrix, The (1995)" / "Rio (2011)"
  (bỏ năm, đảo `, The` → `The `, bỏ hậu tố `(film)`/`(2011 film)`, bỏ dấu câu).
- Nạp **57.822** tên phim canonical từ `movies.csv` để so khớp.
- Thực nghiệm: ~**5.100 lượt sửa/90 giây**, khớp ~**2 phim/phút** (thưa nhưng THẬT 100%).
- Tương tự vai trò luồng giá Binance trong bài mẫu — nhưng cho lĩnh vực phim.

### 4.3 Dữ liệu làm giàu — TMDB API
- Dùng `tmdbId` (links.csv) gọi TMDB → lấy `poster_path` → URL CDN `https://image.tmdb.org/t/p/w342/...`.
- Đã tải **11.866 poster** (top ~12.000 phim nhiều lượt đánh giá nhất + toàn bộ phim gợi ý/phổ biến).
- Lưu vào cột `movies.poster_url`; web hiển thị `<img>`, thiếu thì fallback emoji 🎞️.

---

## 5. Xử lý dữ liệu

- **Nạp:** `scripts/load_to_hdfs.sh` đưa MovieLens lên HDFS `/data/movielens/`.
- **Làm sạch:** ép kiểu `userId/movieId→int`, `rating→float`; loại bản ghi thiếu; ALS dùng
  `coldStartStrategy="drop"` để tránh NaN khi đánh giá.
- **Feature engineering:** tính `avg_rating`, `num_ratings` mỗi phim; trích `year` từ tiêu đề (regex);
  tách `genres` (theo `|`); tính **weighted rating** (công thức IMDB) cho bảng phim phổ biến.
- **Chia dữ liệu:** `train/test = 80/20` (seed cố định để tái lập).

---

## 6. Thuật toán ALS (Mô hình hóa)

### 6.1 Cơ chế
Ma trận đánh giá `R` (users × movies, rất thưa) được xấp xỉ `R ≈ U·Vᵀ`:
- `U` (users × k): vector đặc trưng ẩn của user.
- `V` (movies × k): vector đặc trưng ẩn của phim.
- `k` = số nhân tố ẩn (rank).

**Hàm mục tiêu:**
```
min Σ_(u,i)∈observed ( r_ui − uᵤᵀ·vᵢ )²  +  λ ( Σ‖uᵤ‖² + Σ‖vᵢ‖² )
```
Bài toán không lồi → ALS giải **luân phiên**: cố định `V` giải `U` (least squares có nghiệm đóng),
rồi cố định `U` giải `V`, lặp đến hội tụ. Mỗi bước **song song hóa hoàn hảo** trên Spark.

### 6.2 Đặc điểm nổi bật
- Song song hóa tốt (mỗi hàng U/V giải độc lập) → hợp Spark phân tán.
- Regularization `λ` (regParam) chống overfitting trên dữ liệu thưa.
- Xử lý cold-start `coldStartStrategy="drop"`.
- Hỗ trợ phản hồi ẩn qua `implicitPrefs`.

### 6.3 Siêu tham số đã dùng
| Tham số | Giá trị | Ý nghĩa |
|---------|---------|---------|
| `rank` (k) | 64 | Số nhân tố ẩn |
| `maxIter` | 10 | Số vòng lặp ALS |
| `regParam` (λ) | 0.08 | Hệ số điều chuẩn |
| `coldStartStrategy` | drop | Xử lý user/item mới |
| Top-N | 20 | Số phim gợi ý mỗi user |
| MIN_REC_RATINGS | 1000 | Lọc phim ≥1000 lượt khi gợi ý |

### 6.4 Sinh gợi ý
`recommendForAllUsers(N)` → explode thành `(user_id, rank, movie_id, score)` → ghi MySQL.
User mới (cold-start) → phục vụ bằng bảng phim phổ biến.

---

## 7. Speed Layer real-time (chi tiết kỹ thuật)

### 7.1 Trending từ Wikimedia (THẬT)
- `ingestion/wiki_stream_producer.py`: đọc SSE Wikimedia → lọc + khớp tên → đẩy Kafka event
  `{movieId, title, event_type:"trending", source:"wikipedia", ...}`.
- `stream/consumer.py`: nhận event → cửa sổ trượt `TREND_WINDOW=7200s (2h)` → đếm số lần mỗi phim
  → xếp hạng Top-N → ghi HBase row `__TRENDING__` (xóa cũ + ghi mới).
- Web đọc `/api/trending` → mục "⚡ Thịnh hành real-time LIVE".

### 7.2 Gợi ý theo thể loại từ replay (mô phỏng)
- `ingestion/stream_producer.py`: replay `ratings.csv` vào Kafka với `STREAM_RATE_PER_SEC` (mặc định
  thấp; demo có thể nâng lên 200/s).
- `consumer.py`: mỗi rating ≥3.5 → cộng điểm thể loại ưa thích của user → sinh Top-N phim cùng thể loại
  chưa xem → ghi HBase row = `userId`. Web "🎬 Có thể bạn cũng thích".

> Phân biệt rõ khi bảo vệ: **Wikimedia = real-time THẬT** (nguồn live ngoài đời);
> **replay = mô phỏng** luồng rating (cơ chế xử lý real-time là thật, nguồn là phát lại).

---

## 8. Triển khai (Docker — 13 container)

`docker compose up -d --build` → **13 container**:
zookeeper, kafka, namenode (HDFS), datanode, spark-master, spark-worker, hbase, mysql, airflow,
**ingestion** (replay), **wiki** (Wikimedia real-time), **stream** (consumer), **serving** (Flask).

**URL quản trị:** HDFS `:9870` · Spark `:8080` · HBase `:16010` · Airflow `:8088` (admin/admin) · Web `:5000`.

**Quy trình:**
1. `docker compose up` dựng hạ tầng.
2. `load_to_hdfs.sh` nạp MovieLens; MySQL khởi tạo schema (`scripts/mysql_init.sql`).
3. Submit `batch/train_als.py` lên Spark → ghi Batch View.
4. `wiki_stream_producer.py` đẩy sự kiện phim live; `consumer.py` cập nhật HBase.
5. `fetch_posters.py` lấy poster TMDB lưu MySQL.
6. Flask phục vụ demo `:5000`; Airflow DAG lập lịch retrain.

---

## 9. Kết quả thực nghiệm (SỐ THẬT)

### 9.1 Quy mô dữ liệu
| Chỉ số | Giá trị |
|--------|---------|
| Tổng lượt đánh giá | **25.000.095** |
| Người dùng | ~162.541 |
| Phim | 62.423 |
| Train / Test | 80% / 20% |

### 9.2 Độ chính xác mô hình (test 20%)
| Chỉ số | Kết quả |
|--------|---------|
| **RMSE** | **0.7965** |
| **MAE** | **0.6187** |

→ Thang 0.5–5.0, RMSE ≈ 0.80 là **rất tốt** (ngang/vượt benchmark MovieLens thường ~0.80–0.87).
MAE ≈ 0.62 = sai số dự đoán trung bình ~0.62 sao.

### 9.3 Gợi ý
- Sinh **400.000** dòng gợi ý (20.000 user × Top-20).
- **Lọc phổ biến** (≥1.000 lượt) → gợi ý phim kinh điển, đáng tin.
- Bảng phim phổ biến Top-100 theo weighted rating (cold-start).
- Ví dụ User #100: *Planet Earth II, The Lives of Others, 12 Angry Men, Casablanca,
  Witness for the Prosecution* — điểm dự đoán ~4.2–4.4.

### 9.4 Real-time
- Wikimedia khớp các phim đang sửa live (vd *Rio, Mildred Pierce, The Talented Mr. Ripley*).
- HBase `__TRENDING__` + web cập nhật trực tiếp; verify lag Kafka thấp (≈35), offset tăng liên tục.

### 9.5 Demo & mở rộng
- Web: nhập User ID → phim từng thích + gợi ý ALS + thịnh hành real-time + phim phổ biến, kèm **poster thật**.
- REST API JSON; dashboard thống kê.
- Toàn bộ chạy phân tán Spark, lưu HDFS, đóng gói Docker → dễ thêm worker/DataNode.

### 9.6 Biểu đồ có sẵn (trong `docs/images/`)
- `rating_distribution.png` — phân bố điểm đánh giá.
- `top_genres.png` — top thể loại.
- `top_popular.png` — top phim phổ biến.

---

## 10. Cấu trúc thư mục & file chính

```
BIG DATA/
├── docker-compose.yml        # 13 service
├── .env                      # biến môi trường (Kafka, MySQL, ALS, STREAM_RATE_PER_SEC...)
├── ingestion/
│   ├── download_data.py      # tải MovieLens
│   ├── stream_producer.py    # replay rating → Kafka (mô phỏng)
│   └── wiki_stream_producer.py # Wikimedia EventStreams → Kafka (REAL-TIME THẬT)
├── batch/train_als.py        # PySpark ALS: train, RMSE/MAE, Top-N, phim phổ biến
├── stream/consumer.py        # Kafka → HBase (gợi ý thể loại + trending)
├── serving/
│   ├── app.py                # Flask: index/recommend/search/api + trending + poster
│   ├── templates/            # base, index, recommend, search, _card
│   └── static/style.css
├── scripts/
│   ├── load_to_hdfs.sh       # nạp HDFS
│   ├── mysql_init.sql        # schema MySQL (movies có poster_url)
│   ├── build_demo_db.py      # parquet → SQLite/MySQL
│   ├── fetch_posters.py      # lấy poster TMDB
│   ├── make_charts.py        # sinh biểu đồ báo cáo
│   ├── build_user_history.py # lịch sử user cho demo
│   └── run_local.ps1         # chạy local 1 lệnh
├── airflow/dags/recsys_pipeline.py  # DAG load → train → verify
├── docs/
│   ├── REPORT.md / REPORT.tex # báo cáo
│   └── images/*.png          # biểu đồ
└── web.md                    # hướng dẫn deploy GCP (1 VM Compute Engine)
```

**Bảng MySQL:** `movies(movie_id,title,genres,year,avg_rating,num_ratings,poster_url)`,
`user_recommendations(user_id,rank_pos,movie_id,score)`, `popular_movies`, `stats`.
**HBase table:** `user_recommendations` (row = userId cho gợi ý thể loại; row `__TRENDING__` cho trending).
**Kafka topic:** `ratings-stream`.

---

## 11. So sánh với bài mẫu (Bitcoin Price Streaming Processing)

| Tiêu chí | Bài mẫu Bitcoin | Dự án ta (MovieLens) |
|----------|-----------------|----------------------|
| Bài toán | Dự đoán giá Bitcoin (hồi quy) | Gợi ý phim (collaborative filtering) |
| Kiến trúc | Lambda | Lambda (giống) |
| Stack | Kafka/HDFS/Spark/HBase/MySQL/Airflow/Flask/Docker | **Y hệt** (+ Wikimedia, TMDB) |
| Dữ liệu | Binance (giá lịch sử 1 phút + WebSocket) | MovieLens 25M + Wikimedia live + TMDB |
| Thuật toán | XGBoost | **ALS (Spark MLlib)** |
| Real-time | Luồng Binance | **Wikimedia EventStreams (thật)** |
| Đánh giá | RMSE 5–15$ | RMSE 0.7965 / MAE 0.6187 |
| Serving | Flask + Power BI | Flask web (poster, search, trending) |

**Điểm ta nhỉnh hơn:** volume rõ ràng & lớn (25M > ~3,1M nến), thuật toán phân tán native (ALS),
demo phong phú, đánh giá định lượng vững. **Điểm tương đương:** kiến trúc + hệ sinh thái.

---

## 12. Đánh giá theo 5V (Big Data)

| V | Đáp ứng |
|---|---------|
| **Volume** | 25 triệu ratings, 647MB |
| **Velocity** | Wikimedia live + Kafka stream (speed layer) |
| **Variety** | CSV (HDFS) + quan hệ (MySQL) + NoSQL (HBase) + luồng SSE + API |
| **Veracity** | train/test split, RMSE/MAE |
| **Value** | Web gợi ý phim cá nhân hóa + trending |

**Giới hạn thành thật:** chạy giả lập trên 1 máy (Spark 1 master + 1 worker = pseudo-distributed);
volume vẫn vừa RAM; tín hiệu Wikimedia thưa (~2 phim/phút). → "trình diễn đúng & đủ hệ sinh thái
Big Data ở quy mô học thuật".

---

## 13. Hạn chế & Hướng phát triển

**Hạn chế:** mới dùng ALS thuần (chưa hybrid/deep learning); real-time Wikimedia thưa;
chưa đánh giá Precision@K / NDCG.

**Hướng phát triển:**
- Hybrid: ALS + content-based (tags, genres) giảm cold-start.
- Deep learning: Neural CF, two-tower.
- Chỉ số xếp hạng: Precision@K, Recall@K, NDCG, MAP.
- Thêm **nút đánh giá trên web** → sinh sự kiện real-time từ chính người dùng (như Netflix).
- Spark Structured Streaming; đưa lên cloud GCP (xem `web.md`).

---

## 14. Ghi chú vận hành / kỹ thuật (để tái lập)

- **Chạy local 1 lệnh:** `.\scripts\run_local.ps1` (thêm `-Sample` để nhanh).
- **JAVA_HOME** phải trỏ JDK thật (máy có `C:\Program Files\Eclipse Adoptium\jdk-8.0.482.8-hotspot`);
  biến hệ thống `C:\Java\jre1.8.0_361` KHÔNG tồn tại → override.
- **PYSPARK_PYTHON / PYSPARK_DRIVER_PYTHON** trỏ python.exe thật (không dùng MS Store stub).
- Cần `setuptools<81` (py3.12 bỏ distutils). `PYTHONUTF8=1` để in tiếng Việt.
- Windows thiếu `winutils.exe` → ghi thẳng SQLite thay vì parquet/model.save.
- **Docker:** ảnh `bde2020/spark` Alpine + Python 3.7 không có numpy → `apk add py3-numpy`;
  HBase hay kẹt khi restart → `docker compose up -d --force-recreate hbase`.
- **Poster:** cần `TMDB_API_KEY` (v3). Chạy `python scripts/fetch_posters.py --links data/ml-25m/links.csv`.
  KHÔNG commit key.
- **Tài liệu tham khảo (báo cáo):** Koren et al. 2009 (Matrix Factorization); Harper & Konstan 2015
  (MovieLens); Spark MLlib ALS docs; Marz & Warren (Lambda Architecture); Wikimedia EventStreams.

---

## 15. Hỏi-đáp khi bảo vệ (gợi ý trả lời)

- **"Real-time có thật không?"** → Có. Wikimedia EventStreams là luồng live thật; cơ chế
  Kafka→consumer→HBase độ trễ mili-giây. Phần replay rating là mô phỏng nguồn, ghi rõ trong báo cáo.
- **"Sao không lấy luồng rating MovieLens live?"** → MovieLens không có API real-time; lĩnh vực gợi ý
  không có luồng công khai như tài chính. Real-time đúng nghĩa phải sinh từ tương tác nền tảng (như Netflix)
  hoặc nguồn liên quan (Wikimedia) — đó là lựa chọn của nhóm.
- **"Vì sao ALS chứ không XGBoost?"** → Bài toán gợi ý là collaborative filtering; ALS là matrix
  factorization phân tán native trong Spark MLlib, tối ưu cho ma trận thưa khổng lồ.
- **"25M ratings để làm gì?"** → Dữ liệu huấn luyện ALS học gu người dùng → sinh gợi ý cá nhân hóa.
- **"Có phải Big Data chuẩn không?"** → Đủ chuẩn cho đồ án: Lambda + đủ hệ sinh thái + ALS phân tán +
  25M + real-time; thành thật về giới hạn 1 máy / mô phỏng.

---

*Cập nhật: 2026-06-16. Mọi số liệu lấy từ lần chạy thật 25M (RMSE 0.7965). Dùng kèm `docs/REPORT.tex`.*
