# web.md — Triển khai web chạy thật trên Google Cloud (Cách 1: 1 VM + Docker Compose)

> **Mục tiêu:** Đưa hệ thống gợi ý phim (Lambda stack 13 container) lên **Google Cloud Compute Engine**,
> chạy 24/7 như một website thật, có URL public, real-time vẫn cập nhật.
>
> **Phương án:** Cách 1 — **1 máy ảo (VM) chạy nguyên `docker-compose`**. Gần với bản local nhất,
> real-time hoạt động y hệt, ít sửa kiến trúc.
>
> File này được **cập nhật từng bước** theo tiến độ triển khai thực tế.
> *Cập nhật lần cuối: 2026-06-15 — mới khởi tạo, chưa deploy.*

---

## 0. Tiến độ triển khai (cập nhật khi làm)

| # | Bước | Trạng thái | Ghi chú |
|---|------|-----------|---------|
| 1 | Chuẩn bị tài khoản GCP + cài `gcloud` CLI | ⬜ Chưa làm | |
| 2 | Tạo project + bật Compute Engine API | ⬜ Chưa làm | |
| 3 | Tạo VM (e2-standard-4/8) + IP tĩnh | ⬜ Chưa làm | |
| 4 | Mở firewall (80/443, tạm 5000) | ⬜ Chưa làm | |
| 5 | SSH vào VM + cài Docker & Compose | ⬜ Chưa làm | |
| 6 | Đưa code lên VM + tải dataset MovieLens 25M | ⬜ Chưa làm | |
| 7 | Đổi mật khẩu/secrets trong `.env` | ⬜ Chưa làm | |
| 8 | `docker compose up -d --build` (13 container) | ⬜ Chưa làm | |
| 9 | Nạp HDFS + train ALS + verify pipeline | ⬜ Chưa làm | |
| 10 | Lấy poster TMDB trên VM | ⬜ Chưa làm | |
| 11 | Production: gunicorn cho Flask | ⬜ Chưa làm | |
| 12 | HTTPS bằng Caddy + tên miền | ⬜ Chưa làm | |
| 13 | Khoá admin UI (chỉ mở 80/443, dùng SSH tunnel) | ⬜ Chưa làm | |
| 14 | Kiểm thử end-to-end public URL | ⬜ Chưa làm | |

> Ký hiệu: ⬜ chưa làm · 🟨 đang làm · ✅ xong · ❌ lỗi (kèm cách xử lý).

---

## 1. Tổng quan kiến trúc khi lên VM

Toàn bộ 13 container chạy **chung 1 VM, chung 1 mạng Docker** `recsys-net` (giống local):

```
Internet ──(443)── Caddy(HTTPS) ──→ serving(Flask/gunicorn:5000)
                                          │ đọc
                          ┌───────────────┼─────────────────┐
                          ▼               ▼                 ▼
                       MySQL          HBase             (popular/stats)
                     (Batch View)  (Real-time View)
                          ▲               ▲
                          │ ghi           │ ghi gợi ý real-time
                       Spark           stream(consumer)
                       (ALS)              ▲
                                          │ tiêu thụ
                                        Kafka ◀── ingestion(producer replay ratings.csv)
                          ▲
                        HDFS (ratings.csv 646MB)   Airflow (lập lịch)
```

- **Real-time vẫn sống**: `ingestion` replay rating → Kafka → `stream` → HBase → web.
- **Poster**: web đọc `movies.poster_url`, ảnh nằm trên CDN TMDB (cần VM có internet — mặc định có).

**Khác biệt chính so với local:** thêm **gunicorn** (thay Flask dev server) + **Caddy** (HTTPS) +
siết firewall. Phần lõi Lambda giữ nguyên.

---

## 2. Yêu cầu & ước lượng tài nguyên

| Hạng mục | Khuyến nghị | Lý do |
|----------|-------------|-------|
| Machine type | `e2-standard-4` (4 vCPU / 16GB) tối thiểu; `e2-standard-8` (32GB) thoải mái | Local Docker ~7.5GB đã căng với 13 container |
| Ổ đĩa | 50GB SSD (`pd-ssd`) | ratings.csv 646MB + HDFS + MySQL + ảnh build |
| Vùng (region) | `asia-southeast1` (Singapore) | Gần VN, độ trễ thấp |
| OS | Ubuntu 22.04 LTS | Cài Docker dễ |
| Chi phí | ~$50–120/tháng nếu chạy 24/7 | Tắt VM khi không demo để tiết kiệm; tài khoản mới có **$300 free / 90 ngày** |

---

## 3. Các bước chi tiết

### Bước 1 — Tài khoản GCP + cài `gcloud`
- Tạo tài khoản tại https://console.cloud.google.com (kích hoạt $300 free credit).
- Cài Google Cloud CLI (`gcloud`) trên máy local: https://cloud.google.com/sdk/docs/install
- Đăng nhập:
  ```bash
  gcloud auth login
  ```

### Bước 2 — Project + bật API
```bash
gcloud projects create movielens-recsys-demo --name="MovieLens RecSys"
gcloud config set project movielens-recsys-demo
gcloud services enable compute.googleapis.com
# Lưu ý: cần liên kết Billing Account cho project (qua Console) thì mới tạo được VM.
```

### Bước 3 — Tạo VM + IP tĩnh
```bash
# IP tĩnh (để URL không đổi mỗi lần restart VM)
gcloud compute addresses create recsys-ip --region=asia-southeast1

# Tạo VM
gcloud compute instances create recsys-vm \
  --zone=asia-southeast1-a \
  --machine-type=e2-standard-4 \
  --image-family=ubuntu-2204-lts --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB --boot-disk-type=pd-ssd \
  --address=recsys-ip \
  --tags=recsys-web
```
Ghi lại **External IP** in ra (gọi là `<EXTERNAL_IP>`).

### Bước 4 — Firewall
```bash
# Giai đoạn demo nhanh: mở cả 5000 để xem ngay.
# Production: chỉ nên mở 80,443 (web qua Caddy) — bỏ 5000.
gcloud compute firewall-rules create allow-recsys-web \
  --allow=tcp:80,tcp:443,tcp:5000 \
  --target-tags=recsys-web --source-ranges=0.0.0.0/0
```
> ⚠️ **KHÔNG** mở các cổng admin (9870, 8080, 16010, 8088, 3306, 9092) ra Internet.
> Truy cập chúng qua **SSH tunnel** (xem Bước 13).

### Bước 5 — SSH + cài Docker
```bash
gcloud compute ssh recsys-vm --zone=asia-southeast1-a
```
Trên VM:
```bash
curl -fsSL https://get.docker.com | sudo sh      # cài Docker Engine + Compose plugin
sudo usermod -aG docker $USER                    # chạy docker không cần sudo
exit                                             # đăng xuất rồi SSH lại để áp nhóm
```
SSH lại rồi kiểm tra:
```bash
docker version && docker compose version
```

### Bước 6 — Đưa code lên VM + tải dataset
**Code** (project KHÔNG nên kèm 646MB data khi upload):
```bash
# Cách A — từ máy local (PowerShell), bỏ qua thư mục data cho nhẹ:
#   nén project (trừ data/) rồi scp, hoặc dùng git nếu đã push lên GitHub.
# Cách B — nếu đã có Git repo:
#   git clone <repo-url> ~/bigdata
```
Ví dụ scp trực tiếp (chạy ở máy local, có thể lâu vì data lớn — nên loại data ra trước):
```powershell
gcloud compute scp --recurse "e:\BIG DATA" recsys-vm:~/bigdata --zone=asia-southeast1-a
```
**Dataset** — tải thẳng trên VM cho nhanh (không qua máy local):
```bash
cd ~/bigdata
mkdir -p data && cd data
wget https://files.grouplens.org/datasets/movielens/ml-25m.zip
unzip ml-25m.zip          # ra thư mục data/ml-25m/ (ratings.csv, movies.csv, links.csv...)
cd ~/bigdata
```

### Bước 7 — Cấu hình secrets trong `.env`
Sửa `~/bigdata/.env`:
- Đổi `MYSQL_ROOT_PASSWORD`, `MYSQL_PASSWORD` thành mật khẩu mạnh.
- Có thể chỉnh `STREAM_RATE_PER_SEC` (vd 50–200) để demo real-time rõ.
- **KHÔNG** commit `.env` lên Git công khai.

### Bước 8 — Khởi động stack
```bash
cd ~/bigdata
docker compose up -d --build      # build + chạy 13 container
docker compose ps                 # kiểm tra tất cả Up/healthy
```

### Bước 9 — Nạp HDFS, train ALS, verify
> Trên Linux **không gặp lỗi winutils/MSYS** như Windows — chạy mượt hơn.
```bash
# Nạp ratings.csv + movies.csv vào HDFS
bash scripts/load_to_hdfs.sh

# Submit train ALS (xem CLAUDE.md mục 8 cho lệnh spark-submit cụ thể trong cụm)
# Sau khi train xong: MySQL có movies/user_recommendations/popular/stats.
```
Kiểm tra nhanh:
```bash
curl -s http://localhost:5000/health
curl -s http://localhost:5000/api/recommend/100 | head
```

### Bước 10 — Lấy poster TMDB trên VM
```bash
sudo apt-get install -y python3-pip
pip3 install pymysql sqlalchemy
export TMDB_API_KEY=<KEY_CỦA_BẠN>
python3 scripts/fetch_posters.py --links data/ml-25m/links.csv --limit 5000
# Ảnh đọc từ DB lúc request → chỉ cần refresh web, không build lại.
```

### Bước 11 — Production: gunicorn (thay Flask dev server)
Sửa **`serving/requirements.txt`** thêm:
```
gunicorn==22.0.0
```
Sửa **`serving/Dockerfile`** dòng cuối:
```dockerfile
# CMD ["python", "app.py"]
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "4", "--timeout", "120", "app:app"]
```
> Nhớ bỏ `debug=True` (gunicorn không dùng `app.run`). Rồi:
```bash
docker compose up -d --build serving
```

### Bước 12 — HTTPS bằng Caddy + tên miền
Caddy tự xin chứng chỉ Let's Encrypt. Thêm service vào `docker-compose.yml`:
```yaml
  caddy:
    image: caddy:2
    container_name: caddy
    depends_on: [serving]
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    networks: [recsys-net]
# nhớ thêm 'caddy_data:' vào mục volumes:
```
Tạo file `Caddyfile`:
```
# Có tên miền thật:
your-domain.com {
    reverse_proxy serving:5000
}
# KHÔNG có tên miền? Dùng DNS-IP miễn phí sslip.io (thay dấu . bằng -):
# 34-1-2-3.sslip.io {
#     reverse_proxy serving:5000
# }
```
Sau đó:
```bash
docker compose up -d caddy
```
→ Truy cập `https://your-domain.com` (hoặc `https://<ip-gạch>.sslip.io`).
Khi đã có Caddy, **đóng cổng 5000** trong firewall, chỉ giữ 80/443.

### Bước 13 — Khoá admin UI (không mở ra Internet)
Xem HDFS/Spark/HBase/Airflow an toàn qua **SSH tunnel** (không mở firewall):
```bash
gcloud compute ssh recsys-vm --zone=asia-southeast1-a -- \
  -L 9870:localhost:9870 -L 8080:localhost:8080 \
  -L 16010:localhost:16010 -L 8088:localhost:8088
# Rồi mở trên máy local: http://localhost:9870 , :8080 , :16010 , :8088
```

### Bước 14 — Kiểm thử end-to-end
- [ ] `https://<domain>` mở trang chủ có poster.
- [ ] `/recommend?user_id=100` ra gợi ý batch + real-time.
- [ ] Counter consumer tăng (real-time sống): `docker logs stream --tail 5`.
- [ ] Lag Kafka thấp: `docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group stream-recsys`.

---

## 4. Real-time "tự cập nhật" trên giao diện (tuỳ chọn)
Backend đã real-time, nhưng web hiện phải **F5** mới thấy mới. Muốn tự nhảy:
- **Đơn giản:** thêm JS `setInterval` gọi lại `/api/recommend/<user>` mỗi 5–10s rồi vẽ lại lưới phim.
- **Mượt hơn:** Server-Sent Events (SSE) / WebSocket đẩy gợi ý mới khi HBase đổi.
> Đây là sửa **frontend**, độc lập với deploy.

---

## 5. Vận hành & chi phí
```bash
# Tắt VM khi không demo (ngưng tính tiền compute, vẫn giữ đĩa):
gcloud compute instances stop recsys-vm --zone=asia-southeast1-a
# Bật lại:
gcloud compute instances start recsys-vm --zone=asia-southeast1-a
```
- IP tĩnh giữ nguyên URL sau khi bật lại.
- Backup MySQL định kỳ: `docker exec mysql mysqldump ... > backup.sql`.

---

## 6. Sự cố thường gặp (sẽ bổ sung khi deploy thật)
| Triệu chứng | Nguyên nhân | Cách xử lý |
|-------------|-------------|------------|
| Container chết lác đác | VM thiếu RAM | Tăng machine type / `docker stats` kiểm tra |
| HBase 16010 trống, consumer đứng | HBase standalone kẹt state | `docker compose up -d --force-recreate hbase` rồi `restart stream` |
| Web 5000 không vào được | Firewall chưa mở / Caddy chưa lên | Kiểm tra firewall-rules; `docker compose ps` |
| Poster không hiện | Chưa chạy fetch_posters / VM chặn ra ngoài | Chạy lại Bước 10; kiểm tra internet VM |
| `load_to_hdfs.sh` lỗi path | (Chỉ trên Windows/MSYS) | Trên Linux VM không bị; nếu có, dùng `MSYS_NO_PATHCONV=1` |

---

## 7. Nhật ký triển khai (ghi lại mỗi lần làm)
> Mỗi khi thực hiện 1 bước, ghi 1 dòng: ngày — bước — kết quả/lỗi.

- *(chưa có — sẽ cập nhật khi bắt đầu deploy)*
