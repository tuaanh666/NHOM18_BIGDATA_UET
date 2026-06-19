"""
train_als.py — BATCH LAYER
============================
Huấn luyện mô hình gợi ý phim bằng thuật toán **ALS (Alternating Least Squares)**
của Spark MLlib trên toàn bộ dữ liệu MovieLens 25M.

Quy trình (tương ứng Batch Layer trong Lambda Architecture):
  1. Đọc ratings + movies từ HDFS (Data Lake).
  2. Chia train/test, huấn luyện ALS, đánh giá bằng RMSE.
  3. Sinh Top-N gợi ý cho toàn bộ user  -> ghi vào MySQL (Batch View).
  4. Tính thống kê phim (avg_rating, num_ratings) + phim phổ biến (cold-start).
  5. Lưu mô hình + gợi ý ra HDFS (parquet) để dùng lại / phục vụ stream layer.

Cấu hình qua biến môi trường (có default chạy local được ngay):
  SPARK_MASTER        (default local[*])
  RATINGS_PATH        (default ./data/ml-25m/ratings.csv)
  MOVIES_PATH         (default ./data/ml-25m/movies.csv)
  MYSQL_URL           (vd jdbc:mysql://mysql:3306/movielens) — nếu rỗng thì ghi parquet local
  OUTPUT_DIR          (default ./batch/output)
"""
import os
import sys

# Windows console mặc định cp1252 -> in tiếng Việt sẽ lỗi. Ép UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from pyspark.sql import SparkSession, functions as F, Window
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator

# ----------------------------- Cấu hình --------------------------------------
SPARK_MASTER = os.environ.get("SPARK_MASTER", "local[*]")
RATINGS_PATH = os.environ.get("RATINGS_PATH", "./data/ml-25m/ratings.csv")
MOVIES_PATH = os.environ.get("MOVIES_PATH", "./data/ml-25m/movies.csv")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./batch/output")

MYSQL_URL = os.environ.get("MYSQL_URL", "")          # ưu tiên 1: ghi MySQL (Docker/Linux)
MYSQL_USER = os.environ.get("MYSQL_USER", "mluser")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "mlpassword")
# ưu tiên 2: ghi thẳng SQLite (local trên Windows, không cần winutils.exe)
SQLITE_PATH = os.environ.get("SQLITE_PATH", "")
SAVE_MODEL = os.environ.get("SAVE_MODEL", "0") == "1"  # model.save cần winutils trên Windows

RANK = int(os.environ.get("ALS_RANK", "64"))
MAX_ITER = int(os.environ.get("ALS_MAX_ITER", "10"))
REG_PARAM = float(os.environ.get("ALS_REG_PARAM", "0.08"))
TOP_N = int(os.environ.get("ALS_TOP_N", "20"))
# Số user tối đa sinh gợi ý batch (0 = tất cả). Giới hạn để demo nhanh nếu cần.
MAX_USERS = int(os.environ.get("ALS_MAX_USERS", "0"))


def build_spark():
    builder = (
        SparkSession.builder.appName("MovieLens-ALS-Batch")
        .master(SPARK_MASTER)
        .config("spark.sql.shuffle.partitions", "200")
        .config("spark.driver.memory", os.environ.get("SPARK_DRIVER_MEM", "4g"))
    )
    if MYSQL_URL:
        # tải driver MySQL từ Maven khi cần ghi JDBC
        builder = builder.config("spark.jars.packages", "com.mysql:mysql-connector-j:8.3.0")
    return builder.getOrCreate()


def write_table(df, table, mode="overwrite"):
    """Ghi DataFrame ra Batch View. 3 chế độ: MySQL (JDBC) | SQLite | parquet."""
    if MYSQL_URL:
        (df.write.format("jdbc")
            .option("url", MYSQL_URL)
            .option("dbtable", table)
            .option("user", MYSQL_USER)
            .option("password", MYSQL_PASSWORD)
            .option("driver", "com.mysql.cj.jdbc.Driver")
            .mode(mode).save())
        print(f"[OK] Da ghi bang MySQL: {table}")
    elif SQLITE_PATH:
        # collect ve pandas roi ghi SQLite (tranh winutils tren Windows)
        import sqlite3
        pdf = df.toPandas()
        con = sqlite3.connect(SQLITE_PATH)
        pdf.to_sql(table, con, if_exists="replace", index=False)
        con.close()
        print(f"[OK] Da ghi SQLite: {table} ({len(pdf):,} dong)")
    else:
        path = os.path.join(OUTPUT_DIR, table)
        df.write.mode("overwrite").parquet(path)
        print(f"[OK] Da ghi parquet: {path}")


def write_stats(spark, pairs):
    """Ghi bảng stats nhỏ (6 dòng). Với SQLite ghi trực tiếp bằng sqlite3 để
    tránh spark.createDataFrame (vốn hay crash python-worker trên Windows)."""
    if SQLITE_PATH and not MYSQL_URL:
        import sqlite3
        con = sqlite3.connect(SQLITE_PATH)
        con.execute("DROP TABLE IF EXISTS stats")
        con.execute("CREATE TABLE stats (metric_name TEXT, metric_value TEXT)")
        con.executemany("INSERT INTO stats VALUES (?, ?)", pairs)
        con.commit()
        con.close()
        print(f"[OK] Da ghi SQLite: stats ({len(pairs)} dong)")
    else:
        df = spark.createDataFrame(pairs, ["metric_name", "metric_value"])
        write_table(df, "stats")


def recommend_among_popular(spark, model, stats, ratings, min_ratings, max_users, top_n):
    """Sinh Top-N gợi ý CHỈ trong tập phim phổ biến (>= min_ratings lượt đánh giá),
    bằng cách nhân ma trận nhân tố ẩn ALS với numpy trên driver (nhanh, gọn).
    Trả về list các tuple (user_id, rank_pos, movie_id, score) — không cần pandas."""
    import numpy as np

    # Phim đủ phổ biến + nhân tố ẩn của chúng
    elig = stats.filter(F.col("num_ratings") >= min_ratings).select("movieId")
    item_rows = (
        model.itemFactors.join(elig, model.itemFactors.id == elig.movieId)
        .select("id", "features").collect()
    )
    item_ids = np.array([r.id for r in item_rows], dtype=np.int64)
    V = np.array([r.features for r in item_rows], dtype=np.float32)  # (M, k)

    # Nhân tố ẩn của tập user mẫu
    users = ratings.select("userId").distinct().limit(max_users).withColumnRenamed("userId", "id")
    user_rows = model.userFactors.join(users, "id").select("id", "features").collect()
    user_ids = np.array([r.id for r in user_rows], dtype=np.int64)
    U = np.array([r.features for r in user_rows], dtype=np.float32)  # (N, k)

    print(f"[..] Tinh diem {U.shape[0]} user x {V.shape[0]} phim pho bien (numpy)")
    scores = U @ V.T  # (N, M)
    top_n = min(top_n, V.shape[0])
    top_idx = np.argpartition(-scores, top_n - 1, axis=1)[:, :top_n]

    rows = []
    for i in range(len(user_ids)):
        cols = top_idx[i]
        order = cols[np.argsort(-scores[i, cols])]
        uid = int(user_ids[i])
        for rank, j in enumerate(order, 1):
            rows.append((uid, int(rank), int(item_ids[j]), round(float(scores[i, j]), 4)))
    return rows


def write_recommendations(spark, rows):
    """Ghi bảng gợi ý (list tuple) ra Batch View — SQLite (local) hoặc MySQL/JDBC (cluster)."""
    cols = ["user_id", "rank_pos", "movie_id", "score"]
    if SQLITE_PATH and not MYSQL_URL:
        import sqlite3
        con = sqlite3.connect(SQLITE_PATH)
        con.execute("DROP TABLE IF EXISTS user_recommendations")
        con.execute("CREATE TABLE user_recommendations "
                    "(user_id INT, rank_pos INT, movie_id INT, score REAL)")
        con.executemany("INSERT INTO user_recommendations VALUES (?,?,?,?)", rows)
        con.commit(); con.close()
        print(f"[OK] Da ghi SQLite: user_recommendations ({len(rows):,} dong)")
    else:
        df = spark.createDataFrame(rows, cols)
        write_table(df, "user_recommendations")


def extract_year(title_col):
    return F.regexp_extract(title_col, r"\((\d{4})\)", 1).cast("int")


def main():
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")
    print(f"[..] Spark master = {SPARK_MASTER}")

    # ---------------- 1. Đọc dữ liệu ----------------
    ratings = (
        spark.read.csv(RATINGS_PATH, header=True, inferSchema=True)
        .select(
            F.col("userId").cast("int"),
            F.col("movieId").cast("int"),
            F.col("rating").cast("float"),
        )
    )
    movies = spark.read.csv(MOVIES_PATH, header=True, inferSchema=True)
    n_ratings = ratings.count()
    print(f"[OK] Đọc {n_ratings:,} ratings")

    # ---------------- 2. Train/test split + ALS ----------------
    train, test = ratings.randomSplit([0.8, 0.2], seed=42)
    als = ALS(
        userCol="userId", itemCol="movieId", ratingCol="rating",
        rank=RANK, maxIter=MAX_ITER, regParam=REG_PARAM,
        coldStartStrategy="drop", nonnegative=True,
        implicitPrefs=False,
    )
    print(f"[..] Huấn luyện ALS (rank={RANK}, maxIter={MAX_ITER}, reg={REG_PARAM})")
    model = als.fit(train)

    # ---------------- 3. Đánh giá RMSE ----------------
    preds = model.transform(test)
    rmse = RegressionEvaluator(
        metricName="rmse", labelCol="rating", predictionCol="prediction"
    ).evaluate(preds)
    mae = RegressionEvaluator(
        metricName="mae", labelCol="rating", predictionCol="prediction"
    ).evaluate(preds)
    print(f"[KQ] RMSE = {rmse:.4f} | MAE = {mae:.4f}")

    # ---------------- 4. Thống kê phim + phim phổ biến ----------------
    stats = ratings.groupBy("movieId").agg(
        F.avg("rating").alias("avg_rating"),
        F.count("rating").alias("num_ratings"),
    )
    movies_enriched = (
        movies.join(stats, "movieId", "left")
        .withColumn("year", extract_year(F.col("title")))
        .select(
            F.col("movieId").alias("movie_id"),
            "title", "genres", "year",
            F.coalesce(F.round("avg_rating", 3), F.lit(0.0)).alias("avg_rating"),
            F.coalesce("num_ratings", F.lit(0)).alias("num_ratings"),
        )
    )
    write_table(movies_enriched, "movies")

    # Phim phổ biến — weighted rating (IMDB formula) để tránh phim ít lượt vote
    C = stats.agg(F.avg("avg_rating")).first()[0]
    m = int(os.environ.get("POPULAR_MIN_RATINGS", "1000"))  # ngưỡng số lượt rating tối thiểu
    popular = (
        movies_enriched.filter(F.col("num_ratings") >= m)
        .withColumn(
            "weighted",
            (F.col("num_ratings") / (F.col("num_ratings") + m)) * F.col("avg_rating")
            + (m / (F.col("num_ratings") + m)) * F.lit(C),
        )
        .orderBy(F.desc("weighted"))
        .limit(100)
    )
    w = Window.orderBy(F.desc("weighted"))
    popular_ranked = popular.withColumn("rank_pos", F.row_number().over(w)).select(
        "rank_pos", "movie_id", "title", "avg_rating", "num_ratings"
    )
    write_table(popular_ranked, "popular_movies")

    # ---------------- 5. Sinh Top-N gợi ý cho user ----------------
    min_rec_ratings = int(os.environ.get("MIN_REC_RATINGS", "0"))

    if min_rec_ratings > 0 and MAX_USERS > 0:
        # Gợi ý CHỈ trong tập phim đủ phổ biến (>= ngưỡng lượt đánh giá), tính trực
        # tiếp từ nhân tố ẩn ALS bằng numpy. Cách này đảm bảo mỗi user có đủ Top-N
        # phim quen thuộc, tránh việc ALS xếp hạng cao các phim quá hiếm.
        recs_pdf = recommend_among_popular(
            spark, model, stats, ratings, min_rec_ratings, MAX_USERS, TOP_N
        )
        write_recommendations(spark, recs_pdf)
    else:
        # Cách chuẩn của MLlib: lấy Top-N trong toàn bộ phim
        if MAX_USERS > 0:
            users = ratings.select("userId").distinct().limit(MAX_USERS)
            user_recs = model.recommendForUserSubset(users, TOP_N)
        else:
            user_recs = model.recommendForAllUsers(TOP_N)
        exploded = (
            user_recs.select("userId", F.posexplode("recommendations").alias("pos", "rec"))
            .select(
                F.col("userId").alias("user_id"),
                (F.col("pos") + 1).alias("rank_pos"),
                F.col("rec.movieId").alias("movie_id"),
                F.round(F.col("rec.rating"), 4).alias("score"),
            )
        )
        write_table(exploded, "user_recommendations")

    # ---------------- 6. Lưu thống kê tổng quan ----------------
    n_users = ratings.select("userId").distinct().count()
    n_movies = movies.count()
    stat_pairs = [
        ("num_ratings", str(n_ratings)),
        ("num_users", str(n_users)),
        ("num_movies", str(n_movies)),
        ("als_rmse", f"{rmse:.4f}"),
        ("als_mae", f"{mae:.4f}"),
        ("als_rank", str(RANK)),
    ]
    write_stats(spark, stat_pairs)

    # Lưu mô hình ALS (chỉ khi SAVE_MODEL=1 — trên Windows cần winutils.exe)
    if SAVE_MODEL:
        model_path = os.path.join(OUTPUT_DIR, "als_model")
        model.write().overwrite().save(model_path)
        print(f"[OK] Da luu mo hinh ALS: {model_path}")

    print("[DONE] Batch layer hoan tat.")
    spark.stop()


if __name__ == "__main__":
    main()
