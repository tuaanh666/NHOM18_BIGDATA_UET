# Hướng dẫn tải dữ liệu MovieLens 25M

Bộ dữ liệu **MovieLens 25M** (~647MB, file `ratings.csv`), vì GitHub chặn file > 100MB. Do đó sau khi clone repo, thư mục `data/` sẽ trống
cần tải dữ liệu về **`data/ml-25m/`** trước khi chạy hệ thống.

Sau khi tải xong, thư mục dự án phải có:
BIG DATA/
└── data/
└── ml-25m/
├── ratings.csv     (~647 MB, 25 triệu dòng)
├── movies.csv      (~3 MB, 62.423 phim)
├── links.csv       (~1.4 MB, ánh xạ TMDB)
├── tags.csv
└── genome-*.csv



>  `data/` trên máy bạn  = `/app/data` bên trong container Docker(được nối với nhau bằng *volume mount*, là cùng một thư mục).

---

## Cách 1 — Tải bằng Docker 
Container `ingestion` đã cấu hình sẵn (`DATA_DIR=/app/data`, mount `./data`),  chỉ cần:
```bash
docker compose up -d
docker compose run --rm ingestion python download_data.py
→ Dữ liệu tự tải và giải nén vào /app/data/ml-25m = data/ml-25m/ trên máy bạn.

Cách 2 — Tải trên máy (không cần Docker)
Phải trỏ biến DATA_DIR về thư mục data/ của dự án (mặc định trong code là /app/data
dành cho container):


# Windows PowerShell
$env:DATA_DIR="./data"; python ingestion/download_data.py

# Git Bash / Linux / macOS
DATA_DIR=./data python ingestion/download_data.py
Cách 3 — Tải thủ công
Vào: https://grouplens.org/datasets/movielens/25m/
Tải file ml-25m.zip.
Giải nén sao cho được thư mục data/ml-25m/ chứa các file .csv như trên.
 Kiểm tra đã tải đúng

# Phải thấy ratings.csv, movies.csv, links.csv...
ls data/ml-25m/
Hoặc trên Windows:


dir data\ml-25m
 Sau khi có dữ liệu
Chạy Docker (đầy đủ):

MSYS_NO_PATHCONV=1 bash scripts/load_to_hdfs.sh   # đẩy dữ liệu lên HDFS
Chạy local: train_als.py đọc thẳng data/ml-25m/ratings.csv.




---

Đây là nội dung Markdown hoàn chỉnh
