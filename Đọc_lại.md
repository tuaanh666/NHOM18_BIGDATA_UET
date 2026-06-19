# ĐỌC LẠI — Hiểu & Thuyết trình dự án

> File này viết cho **bạn đọc để hiểu và thuyết trình**: giải thích khái niệm dễ hiểu, luồng
> hoạt động, số liệu cần nhớ, kịch bản trình bày và câu hỏi phản biện.
> (Khác: `CLAUDE.md` = context cho AI; `CLAUDE_báo_cáo.md` = kho viết báo cáo; `docs/REPORT.tex` = báo cáo.)

---

## 1. Nói 30 giây về dự án (elevator pitch)

> *"Nhóm em xây **hệ thống gợi ý phim thời gian thực trên nền tảng dữ liệu lớn**. Dùng bộ
> MovieLens 25 triệu lượt đánh giá, áp dụng **kiến trúc Lambda** (xử lý lô + thời gian thực) với
> đầy đủ hệ sinh thái Big Data: Kafka, HDFS, Spark, HBase, MySQL, Airflow, Flask, Docker. Thuật
> toán cốt lõi là **ALS** (lọc cộng tác) cho RMSE 0.7965. Hệ thống còn lấy **dữ liệu real-time
> thật từ Wikimedia** để hiện phim đang thịnh hành, và có web demo kèm poster phim thật."*

**Một câu định vị:** Đây là phiên bản "phim" của bài mẫu *Bitcoin Price Streaming* — cùng kiến
trúc và stack, đổi bài toán dự đoán giá thành bài toán gợi ý.

---

## 2. Bài toán & vì sao cần Big Data

- **Bài toán:** quá nhiều phim, người dùng không biết xem gì → cần **gợi ý cá nhân hóa**.
- **Vì sao là Big Data?**
  - **Volume:** 25 triệu lượt đánh giá (647MB) — 1 máy xử lý kiểu thường không nổi.
  - **Sparsity:** ~162.000 user × ~62.000 phim = ma trận khổng lồ nhưng **rất thưa** (mỗi người chỉ xem vài phim).
  - **Velocity:** sở thích đổi liên tục → cần cập nhật real-time.
- **Giá trị thực tế:** >80% lượt xem Netflix đến từ gợi ý → bài toán có giá trị thương mại cao.

---

## 3. Khái niệm cốt lõi (giải thích để THUYẾT TRÌNH)

### 3.1 Lambda Architecture (kiến trúc tổng)
Chia hệ thống làm **2 nhánh bổ trợ**, hợp nhất ở tầng phục vụ:
- **Batch Layer (lô):** train mô hình trên *toàn bộ lịch sử* → gợi ý **chính xác** nhưng chậm.
- **Speed Layer (tốc độ):** xử lý *sự kiện vừa xảy ra* → gợi ý **tươi mới** tức thì (nhẹ, gần đúng).
- **Serving Layer (phục vụ):** web Flask gộp cả hai cho người dùng.

> Câu nói gọn: *"Batch cho độ chính xác, Speed cho độ tươi, Serving gộp lại."*

### 3.2 ALS — thuật toán gợi ý (quan trọng nhất)
- **Bài toán:** có ma trận `R` (user × phim) đầy lỗ hổng (đa số ô trống vì chưa xem). Cần **đoán
  ô trống** = user chưa xem phim này sẽ chấm mấy điểm.
- **Ý tưởng (matrix factorization):** tách `R ≈ U × Vᵀ`:
  - `U` = "gu" ẩn của mỗi user (vd thích hành động 0.8, lãng mạn 0.2…).
  - `V` = "chất" ẩn của mỗi phim.
  - Nhân 2 vector → đoán điểm. Lấy phim điểm cao nhất user chưa xem → **gợi ý**.
- **"Alternating" nghĩa là gì?** Không giải `U` và `V` cùng lúc (khó), mà **luân phiên**: cố
  định `V` giải `U`, rồi cố định `U` giải `V`, lặp lại đến hội tụ. Mỗi bước **chạy song song
  được trên Spark** → hợp Big Data.
- **Tham số:** rank=64 (số "gu" ẩn), maxIter=10, regParam=0.08 (chống học vẹt), Top-N=20.
- **Ví dụ trực giác:** user thích *Pulp Fiction* + *Shawshank* (chính kịch/tội phạm) → ALS suy
  ra gu → đoán họ cũng thích *Goodfellas, The Godfather*.

### 3.3 Lọc cộng tác (Collaborative Filtering)
Gợi ý dựa trên **hành vi người dùng giống nhau**, KHÔNG cần hiểu nội dung phim. "Người giống bạn
cũng thích phim X → gợi ý X cho bạn." ALS thuộc nhóm này.

### 3.4 Từng công nghệ — 1 câu để nhớ
| Công nghệ | Nhớ 1 câu |
|-----------|-----------|
| **Kafka** | "Đường ống" nhận luồng sự kiện (topic `ratings-stream`) |
| **HDFS** | "Kho" lưu file lớn phân tán (chứa ratings.csv 647MB) |
| **Spark** | "Cỗ máy" tính toán phân tán — train ALS |
| **HBase** | "Tủ tra cứu nhanh" NoSQL — gợi ý real-time + trending |
| **MySQL** | "Bảng quan hệ" — gợi ý batch + metadata phim + poster |
| **Airflow** | "Đồng hồ hẹn giờ" — lập lịch train lại |
| **Flask** | "Web" hiển thị gợi ý cho người dùng |
| **Docker** | "Hộp đóng gói" — chạy cả 13 thành phần bằng 1 lệnh |
| **Wikimedia** | "Nguồn live thật" — phim đang được sửa trên Wikipedia |
| **TMDB** | "Kho poster" phim thật |

---

## 4. Luồng hoạt động end-to-end (kể như đang demo)

```
            ┌──────────── BATCH (chính xác) ────────────┐
MovieLens 25M ──► HDFS ──► Spark ALS ──► MySQL (gợi ý batch + phim phổ biến)
                                                          │
                                                          ├──► FLASK WEB ──► Người dùng
                                                          │     (gộp + poster TMDB)
Wikimedia (live) ──► Kafka ──► Consumer ──► HBase (thịnh hành real-time)
            └──────────── SPEED (tươi mới) ─────────────┘
                              ▲
                        Airflow hẹn giờ train lại
```

**Kể bằng lời khi demo:**
1. "Dữ liệu 25M ratings nằm trên HDFS; Spark train ALS sinh gợi ý, lưu MySQL." (Batch)
2. "Cùng lúc, em cắm vào luồng Wikipedia live qua Kafka; consumer lọc phim đang được sửa → ghi
   danh sách thịnh hành vào HBase." (Speed)
3. "Web Flask gộp 2 nguồn: chọn User ID ra gợi ý cá nhân (ALS), trang chủ có mục Thịnh hành
   real-time, mỗi phim có poster thật." (Serving)

---

## 5. Số liệu PHẢI NHỚ (hay bị hỏi)

| Hỏi | Trả lời |
|-----|---------|
| Bao nhiêu dữ liệu? | **25.000.095** ratings (~647MB), ~162.541 user, 62.423 phim |
| Độ chính xác? | **RMSE = 0.7965**, **MAE = 0.6187** (test 20%) |
| RMSE 0.80 tốt không? | Rất tốt — benchmark MovieLens thường 0.80–0.87 |
| Tham số ALS? | rank=64, maxIter=10, regParam=0.08, Top-N=20 |
| Sinh bao nhiêu gợi ý? | **400.000** (20.000 user × Top-20), lọc phim ≥1.000 lượt |
| Bao nhiêu container? | **13** (Docker Compose) |
| Bao nhiêu poster? | **11.866** (từ TMDB) |
| Real-time khớp bao nhiêu? | ~**2 phim/phút** từ Wikimedia (thật) |

---

## 6. Kịch bản thuyết trình (gợi ý 7 slide)

1. **Mở đầu:** Bài toán gợi ý + vì sao là Big Data (Volume/Sparsity/Velocity).
2. **Kiến trúc Lambda:** sơ đồ 3 tầng (dùng hình trong báo cáo).
3. **Công nghệ:** bảng "1 câu nhớ" mục 3.4 (lướt nhanh).
4. **Dữ liệu:** 3 nguồn (MovieLens / Wikimedia / TMDB) + biểu đồ phân bố rating.
5. **Thuật toán ALS:** giải thích matrix factorization + công thức + tham số + kết quả RMSE.
6. **Demo trực tiếp:** mở `localhost:5000` → nhập user → gợi ý + poster; trang chủ → thịnh hành real-time.
7. **Kết luận:** thành tựu + so sánh bài mẫu + hạn chế (thành thật) + hướng phát triển.

> Mẹo: dành **40% thời gian cho DEMO** — thầy thích thấy chạy thật hơn nghe lý thuyết.

---

## 7. Câu hỏi phản biện & cách trả lời (QUAN TRỌNG)

- **"Real-time có thật không?"**
  → "Có. Wikimedia EventStreams là luồng live thật, không phải mô phỏng. Cơ chế
  Kafka→consumer→HBase độ trễ mili-giây. Riêng phần replay rating là *mô phỏng nguồn*, nhưng cơ
  chế xử lý real-time là thật."

- **"Sao không lấy rating real-time của MovieLens?"**
  → "MovieLens không có API real-time — lĩnh vực gợi ý không có luồng công khai như tài chính.
  Real-time đúng nghĩa phải sinh từ tương tác nền tảng (như Netflix) hoặc nguồn liên quan; em
  chọn Wikimedia làm tín hiệu phim đang được quan tâm."

- **"Sao dùng ALS mà không phải XGBoost/Deep Learning?"**
  → "Gợi ý là bài toán collaborative filtering trên ma trận thưa khổng lồ. ALS là matrix
  factorization **phân tán native** trong Spark MLlib, tối ưu đúng cho việc này. Deep learning là
  hướng phát triển."

- **"25 triệu rating để làm gì?"**
  → "Là dữ liệu huấn luyện để ALS học gu người dùng → sinh gợi ý cá nhân hóa. Càng nhiều dữ liệu,
  gợi ý càng chính xác."

- **"Cold-start (user/phim mới) xử lý sao?"**
  → "User mới chưa có lịch sử → hiển thị **phim phổ biến** (Top-100 theo weighted rating). ALS
  dùng `coldStartStrategy=drop` để không sinh điểm sai."

- **"RMSE là gì?"**
  → "Root Mean Square Error — sai số bình phương trung bình giữa điểm dự đoán và điểm thật. 0.80
  trên thang 5 nghĩa là đoán lệch trung bình ~0.8 sao."

- **"Có phải Big Data thật sự không / chạy mấy máy?"** *(câu khó — trả lời thành thật)*
  → "Đủ chuẩn đồ án: kiến trúc Lambda + đủ hệ sinh thái + ALS phân tán + 25M + real-time thật.
  Thành thật là tụi em chạy **giả lập phân tán trên 1 máy** (Spark 1 master + 1 worker), volume
  vừa RAM. Hướng phát triển là đưa lên cloud chạy đa node thật."

---

## 8. Đánh giá theo 5V (nếu thầy hỏi "thể hiện Big Data ở đâu")

| V | Trong dự án |
|---|-------------|
| **Volume** | 25 triệu ratings, 647MB |
| **Velocity** | Wikimedia live + Kafka stream (speed layer) |
| **Variety** | CSV (HDFS) + quan hệ (MySQL) + NoSQL (HBase) + luồng SSE + API |
| **Veracity** | đánh giá định lượng RMSE/MAE |
| **Value** | web gợi ý phim cá nhân hóa + trending |

---

## 9. So sánh bài mẫu (Bitcoin) — để "ghi điểm tự đánh giá"

| | Bài mẫu Bitcoin | Dự án ta |
|---|---|---|
| Bài toán | Dự đoán giá (hồi quy) | Gợi ý phim (collaborative filtering) |
| Thuật toán | XGBoost | **ALS (Spark MLlib)** |
| Real-time | Luồng Binance | **Wikimedia (thật)** |
| Dữ liệu | Giá Bitcoin 1 phút | **25M ratings** |
| Đánh giá | RMSE 5–15$ | RMSE 0.7965 / MAE 0.6187 |

**Ta nhỉnh hơn:** volume rõ ràng & lớn, thuật toán phân tán native (ALS), demo phong phú (poster,
trending), real-time thật. **Ngang nhau:** kiến trúc Lambda + đủ hệ sinh thái.

---

## 10. Điểm mạnh & hạn chế (nói trước khi thầy hỏi = chủ động ghi điểm)

**Mạnh:** Lambda đầy đủ; ALS phân tán trên 25M; RMSE tốt; real-time THẬT (Wikimedia); demo có
poster; đóng gói Docker 13 container chạy thật.

**Hạn chế (thành thật):** chạy 1 máy (pseudo-distributed); ALS thuần (chưa hybrid/deep learning);
tín hiệu Wikimedia thưa (~2 phim/phút); chưa đo Precision@K/NDCG.

**Hướng phát triển:** hybrid ALS + content-based; deep learning (Neural CF); thêm nút đánh giá
trên web (real-time từ user thật); đưa lên cloud GCP đa node.

---

## 11. Checklist trước khi thuyết trình

- [ ] Bật sẵn Docker stack: `docker compose up -d` → kiểm tra `localhost:5000` mở được.
- [ ] Mở sẵn vài tab: trang chủ (trending), `/recommend?user_id=100`, một admin UI (vd Spark :8080).
- [ ] Thuộc số liệu mục 5.
- [ ] Chuẩn bị câu trả lời mục 7 (nhất là "real-time có thật không" + "chạy mấy máy").
- [ ] Nếu trending real-time chưa có phim: bật `wiki` container vài phút trước để tích lũy.

---

*Tài liệu liên quan: báo cáo `docs/REPORT.tex`; kho nội dung `CLAUDE_báo_cáo.md`; tổng quan kỹ
thuật `CLAUDE.md`; hướng dẫn deploy `web.md`.*
