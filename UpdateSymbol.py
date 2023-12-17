from airflow import DAG
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime
from pandas import Timestamp

import yfinance as yf
import pandas as pd
import logging


def get_Redshift_connection(autocommit=True):
    hook = PostgresHook(postgres_conn_id='***')
    conn = hook.get_conn()
    conn.autocommit = autocommit
    return conn.cursor()


@task
def get_historical_prices(symbol):
    ticket = yf.Ticker(symbol)
    data = ticket.history()
    records = []

    for index, row in data.iterrows():
        date = index.strftime('%Y-%m-%d %H:%M:%S')
        records.append("('{}', {}, {}, {}, {}, {})".format(date, row["Open"], row["High"], row["Low"], row["Close"], row["Volume"]))

    return records


@task
def load(schema, table, records):
    logging.info("load started")
    cur = get_Redshift_connection()

    # 원본 테이블이 없으면 생성
    create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {schema}.{table} (
            date date,
            "open" float,
            high float,
            low float,
            close float,
            volume bigint,
            created_date timestamp default GETDATE()
        );
    """
    logging.info(create_table_sql)

    # 임시 테이블 생성
    create_t_sql = f"""CREATE TEMP TABLE t AS SELECT * FROM {schema}.{table};"""
    logging.info(create_t_sql)
    try:
        cur.execute("BEGIN;")
        cur.execute(create_table_sql)
        cur.execute(create_t_sql)
        cur.execute("COMMIT;")
    except Exception as e:
        cur.execute("ROLLBACK;")
        raise

    # 임시 테이블 데이터 입력
    insert_sql = f"INSERT INTO t VALUES " + ",".join(records)
    logging.info(insert_sql)
    try:
        cur.execute("BEGIN;")
        cur.execute(insert_sql)
        cur.execute("COMMIT;")
    except Exception as e:
        cur.execute("ROLLBACK;")
        raise

    # 기존 테이블 대체
    alter_sql = f"""
        DELETE FROM {schema}.{table};
        INSERT INTO {schema}.{table}
        SELECT date, "open", high, low, close, volume 
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY date ORDER BY created_date DESC) seq
            FROM t
        )
        WHERE seq = 1;
    """
    logging.info(alter_sql)
    try:
        cur.execute("BEGIN;")
        cur.execute(alter_sql)
        cur.execute("COMMIT;")
    except Exception as e:
        cur.execute("ROLLBACK;")
        raise


with DAG(
    dag_id = 'UpdateSymbol_v3',
    start_date = datetime(2023,11,1),
    catchup=False,
    tags=['API'],
    schedule = '0 10 * * *'
) as dag:

    results = get_historical_prices("AAPL")
    load("***", "stock_info_v3", results)
