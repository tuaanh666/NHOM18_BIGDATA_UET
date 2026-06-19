"""
download_data.py — Tải và giải nén bộ dữ liệu MovieLens 25M.
ta lấy dữ liệu rating phim từ GroupLens (MovieLens 25M).
"""
import os
import sys
import zipfile
import urllib.request

DATA_URL = "https://files.grouplens.org/datasets/movielens/ml-25m.zip"
DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
ZIP_PATH = os.path.join(DATA_DIR, "ml-25m.zip")
EXTRACT_DIR = os.path.join(DATA_DIR, "ml-25m")


def _progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    pct = min(100, downloaded * 100 / total_size) if total_size > 0 else 0
    sys.stdout.write(f"\r  Tải về: {downloaded/1e6:7.1f} MB / {total_size/1e6:7.1f} MB ({pct:5.1f}%)")
    sys.stdout.flush()


def download():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(EXTRACT_DIR) and os.listdir(EXTRACT_DIR):
        print(f"[OK] Dữ liệu đã tồn tại tại {EXTRACT_DIR}, bỏ qua tải về.")
        return
    if not os.path.exists(ZIP_PATH):
        print(f"[..] Đang tải MovieLens 25M từ {DATA_URL}")
        urllib.request.urlretrieve(DATA_URL, ZIP_PATH, _progress)
        print("\n[OK] Tải xong.")
    print(f"[..] Giải nén vào {DATA_DIR}")
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        z.extractall(DATA_DIR)
    print(f"[OK] Giải nén xong. Các file: {os.listdir(EXTRACT_DIR)}")


if __name__ == "__main__":
    download()
