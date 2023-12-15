from airflow import DAG
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime
import logging

import requests

def get_Redshift_connection(autocommit=True):
    hook = PostgresHook(postgres_conn_id='redshift_dev_db')
    conn = hook.get_conn()
    conn.autocommit = autocommit
    return conn.cursor()

@task
def get_country_info():
    r = requests.get('https://restcountries.com/v3/all')
    rj = r.json()
    records = []

    for d in rj:
        country = d['name']['official']
        population = d['population']
        area = d['area']
        records.append([country, population, area])
    
    return records

def _create_table(cur, schema, table):
    cur.execute(f"DROP TABLE IF EXISTS {schema}.{table}")
    cur.execute(f"""
        CREATE TABLE {schema}.{table} (
            country varchar(100),
            population bigint,
            area float
        );               
    """)

@task
def load(schema, table, records):
    logging.info("load started")
    cur = get_Redshift_connection()
    try:
        cur.execute("BEGIN;")
        _create_table(cur, schema, table)
        
        for r in records:
            sql = f'INSERT INTO {schema}.{table} (country, population, area) VALUES ("{r[0]}", {r[1]}, {r[2]});'
            print(sql)
            cur.execute(sql)
        cur.execute("COMMIT;")
    except Exception as error:
        print(error)
        cur.execute("ROLLBACK;")
        raise
    logging.info("load done")

with DAG (
    dag_id='CountryInfo',
    start_date = datetime(2023, 11, 1),
    catchup=False,
    tags=['API'],
    schedule='30 6 * * 6'  # 매주 토요일 오전 6시 30분
) as dag:
    
    results = get_country_info()
    load('leebk1124', 'country_info', results)