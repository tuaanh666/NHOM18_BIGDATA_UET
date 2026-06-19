from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    "owner": "bigdata-team",
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
}

with DAG(
    dag_id="movielens_recsys_batch",
    description="Batch layer: nạp HDFS -> train ALS -> nạp Batch View",
    default_args=default_args,
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["recsys", "spark", "als", "bigdata"],
) as dag:

    start = EmptyOperator(task_id="start")

    # 1) Đảm bảo dữ liệu MovieLens đã nằm trên HDFS (Data Lake)
    load_hdfs = BashOperator(
        task_id="load_to_hdfs",
        bash_command=(
            "hdfs dfs -test -e /data/movielens/ratings.csv "
            "&& echo 'Dữ liệu đã có trên HDFS' "
            "|| echo 'Cần chạy scripts/load_to_hdfs.sh trước'"
        ),
    )

    # 2) Huấn luyện ALS trên Spark cluster (ghi Batch View vào MySQL)
    train = BashOperator(
        task_id="train_als",
        bash_command=(
            "spark-submit --master spark://spark-master:7077 "
            "--packages com.mysql:mysql-connector-j:8.3.0 "
            "/opt/airflow/jobs/train_als.py"
        ),
        env={
            "SPARK_MASTER": "spark://spark-master:7077",
            "RATINGS_PATH": "hdfs://namenode:9000/data/movielens/ratings.csv",
            "MOVIES_PATH": "hdfs://namenode:9000/data/movielens/movies.csv",
            "MYSQL_URL": "jdbc:mysql://mysql:3306/movielens",
            "MYSQL_USER": "mluser",
            "MYSQL_PASSWORD": "mlpassword",
            "ALS_RANK": "64",
            "ALS_MAX_ITER": "10",
            "ALS_TOP_N": "20",
        },
    )
    verify = BashOperator(
        task_id="verify_batch_view",
        bash_command="echo 'Batch View (MySQL) đã cập nhật. Serving layer sẵn sàng.'",
    )

    done = EmptyOperator(task_id="done")

    start >> load_hdfs >> train >> verify >> done
