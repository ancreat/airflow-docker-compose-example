from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.sdk import chain, dag, task
import datetime

db_connection_id = "data_warehouse_connection"
data_path = "/opt/airflow/import/data/transactions.csv"

@dag(
    dag_id="postgres_pipeline",
    schedule=None,
    dagrun_timeout=datetime.timedelta(minutes=10),
    tags=["example"],
)
def postgres_pipeline():
    create_transactions_table = SQLExecuteQueryOperator(
        task_id="create_transactions_table",
        conn_id=db_connection_id,
        sql="""
            DROP TABLE IF EXISTS transactions;
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                amount DECIMAL(10,2),
                category TEXT
            );
        """,
    )

    create_transactions_summary_table = SQLExecuteQueryOperator(
        task_id="create_transactions_summary_table",
        conn_id=db_connection_id,
        sql="""
            DROP TABLE IF EXISTS transactions_summary;
            CREATE TABLE transactions_summary (
                total_amount DECIMAL(15,2),
                category TEXT
            );
        """,
    )

    @task
    def import_data():
        postgres_hook = PostgresHook(postgres_conn_id=db_connection_id)
        conn = postgres_hook.get_conn()
        cur = conn.cursor()
        with open(data_path, "r") as file:
            cur.copy_expert(
                "COPY transactions FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '\"')",
                file,
            )
        conn.commit()

    @task
    def create_transactions_summary():
        postgres_hook = PostgresHook(postgres_conn_id=db_connection_id)
        conn = postgres_hook.get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO transactions_summary (total_amount, category)
            SELECT sum(amount), category
            FROM transactions
            WHERE amount IS NOT NULL
            GROUP BY category;
        """)
        conn.commit()

    chain([create_transactions_table, create_transactions_summary_table], import_data(), create_transactions_summary())

postgres_pipeline()
